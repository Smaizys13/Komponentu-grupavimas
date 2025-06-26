import streamlit as st
import pandas as pd
from io import BytesIO

# Grupavimo raktiniai žodžiai — atnaujinta versija
GROUP_KEYWORDS = {
    "Kabeliai": ["cable", "wire", "LIYY", "CY", "PVC", "4-pin", "bridge"],
    "Pneumatika": ["festo", "SMC", "filter", "connector", "piping", "fitting", "Pneumatic", "silencer", "valve", "air", "pressure", "cylinder"],
    "Automatika": ["Sick", "Abb", "Phoenix", "PLC", "contact", "breaker", "PB", "Em. stop", "Lamp", "end cover", "End clamp", "fuse", "CPU", "pole", "led", "panel", "resistor", "Terminal", "relay", "module", "contactor", "HMI", "ModBus", "controller","terminals", "Photocell"],
    "Starteriai": ["starter", "motor protection"],
    "Varikliai": ["motor", "inverter", "ACS"],
    "Jutikliai": ["sensor", "prox", "encoder", "switch", "reflector", "lock"],
    "Maitinimas": ["power supply", "PSU", "SMPS"],
    "Montažiniai": ["DIN", "rail", "frame", "plate", "bracket", "holder", "bar", "DIX", "locknut", "polyamide"],
    "Spintos, dėžutės": ["enclosure", "cabinet"]
}

# Funkcija priskirti komponentą grupei
import re  # Į viršų įsitikink, kad įrašytas šitas importas

def classify_component(description, manufacturer):
    desc = str(description).lower() if pd.notna(description) else ""
    manu = str(manufacturer).lower() if pd.notna(manufacturer) else ""

    # 1. Pirmiausia pagal gamintoją
    for group, keywords in GROUP_KEYWORDS.items():
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', manu):
                return group

    # 2. Jei nerado – tada aprašymas
    for group, keywords in GROUP_KEYWORDS.items():
        for keyword in keywords:
            if re.search(r'\b' + re.escape(keyword.lower()) + r'\b', desc):
                return group

    return "Kita"


st.set_page_config(page_title="Excel komponentų grupavimas", layout="wide")
st.title("Excel komponentų analizė ir grupavimas")

uploaded_file = st.file_uploader("Įkelkite komponentų sąrašą (Excel):", type=["xlsx", "xls"])

if uploaded_file:
    df = pd.read_excel(uploaded_file)

    st.subheader("Originalus Excel turinys")
    st.dataframe(df, use_container_width=True)

    # Patikrinam ar reikalingi stulpeliai yra
    required_cols = ['Part Number', 'Qty', 'Description', 'Manufacturer', 'Device']
    if not all(col in df.columns for col in required_cols):
        st.error(f"Trūksta vieno ar kelių laukų: {required_cols}. Patikrink Excel antraštes!")
        st.stop()

    # Per-vadinam stulpelius į 'Art.no', 'Qty'
    df = df.rename(columns={
        'Part Number': 'Art.no',
        'Qty': 'Qty'
    })

    # Tvarkom Qty — kad būtų float(kad neatpažintų skaičių kaip teksto)!
    df["Qty"] = pd.to_numeric(
    df["Qty"].astype(str).str.replace(',', '.').str.extract(r'([0-9.]+)')[0],
    errors='coerce'
    ).fillna(0)

    # Priskirti grupes
    df["Group"] = df.apply(lambda row: classify_component(row["Description"], row["Manufacturer"]), axis=1)

    # Sumuoti kiekius pagal Art.no
    df_grouped = (
    df.groupby("Art.no", as_index=False)
    .agg({
        "Qty": "sum",
        "Group": "first",
        "Device": "first",
        "Manufacturer": "first",
        "Description": "first"
    })
     )

    st.subheader("Sugrupuoti komponentai pagal Art.no")
    st.dataframe(df_grouped, use_container_width=True)

    # Eksportas į Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_grouped.to_excel(writer, index=False, sheet_name="Komponentai")
    excel_data = output.getvalue()

    st.download_button(
        label="📥 Atsisiųsti Excel",
        data=excel_data,
        file_name="komponentai_grupuoti.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("Prašome įkelti Excel failą.")
