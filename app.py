import streamlit as st
import pandas as pd

st.title("System sammenligning")

# læs Excel
df = pd.read_excel("10_list.xlsx", header=1)

# gør kolonnenavne unikke
cols = []
counts = {}
for col in df.columns:
    if col in counts:
        counts[col] += 1
        cols.append(f"{col}_{counts[col]}")
    else:
        counts[col] = 0
        cols.append(col)
df.columns = cols

# mapping til labels
mapping = {
    "Fire_Resistance_Class_sys_desc_pdm_gpdm": "Brandklasse",
    "Global_Warming_Potential_sys_met_td_pdm_gpdm": "Globalt opvarmningspotentiale",
    "Insulation_Material_sys_desc_pdm_gpdm": "Isoleringsmateriale",
    "Insulation_Thickness_sys_met_td_pdm_gpdm": "Isoleringstykkelse",
    "Partition_Height_sys_met_td_pdm_gpdm": "Maksimal væghøjde",
    "Profile_sys_desc_pdm_gpdm": "Profil type",
    "Screw_Tight_sys_desc_pdm_gpdm": "Skruefast",
    "Spectrum_Adaption_Term_C50_3150_sys_met_td_pdm_gpdm": "Luftlydisolation - dB [R'w] C50",
    "Sound_Reduction_Index_sys_td_pdm_gpdm": "Lydklasse (R’w)",
    "Stud_Spacing_sys_met_td_pdm_gpdm": "Stolpe afstand c/c",
    "Weight_Per_Unit_Area_sys_met_td_pdm_gpdm": "Vægt pr. m²",
    "Wall_Grid_sys_desc_pdm_gpdm": "Skelet type"
}

# enheder
units = {
    "Globalt opvarmningspotentiale": "kg CO₂e",
    "Isoleringstykkelse": "mm",
    "Maksimal væghøjde": "mm",
    "Stolpe afstand c/c": "mm",
    "Vægt pr. m²": "kg/m²",
    "Luftlydisolation - dB [R'w] C50": "dB",
    "Lydklasse (R’w)": "dB"
}

name_col = "System_Variant_Name_Local_sys_desc_pdm_gpdm"

# dropdown
systemer = df[name_col].dropna()
systemer = systemer[systemer != "Optional"]

valg = st.multiselect(
    "Vælg systemer",
    sorted(systemer.unique())
)

if valg:
    comp = df[df[name_col].isin(valg)]

    gwp_col = "Global_Warming_Potential_sys_met_td_pdm_gpdm"

    if gwp_col in comp.columns:
        comp = comp.sort_values(by=gwp_col, ascending=True)
        best = comp.iloc[0]
        st.success(f"Bedste løsning (lavest CO₂): {best[name_col]}")

    available_cols = [col for col in mapping.keys() if col in comp.columns]

    comp = comp[[name_col] + available_cols]

    comp = comp.rename(columns={k: v for k, v in mapping.items() if k in comp.columns})

    comp = comp.set_index(name_col).T

    # ---------- FORMATTERING ----------

    comp = comp.fillna("-")

    comp = comp.apply(lambda col: col.map(
        lambda x: round(x, 2) if isinstance(x, (int, float)) else x
    ))

    # tilføj enheder
    for row in comp.index:
        if row in units:
            unit = units[row]
            comp.loc[row] = comp.loc[row].apply(
                lambda x: f"{x} {unit}" if x != "-" else x
            )

    st.dataframe(comp, height=500, use_container_width=True)
