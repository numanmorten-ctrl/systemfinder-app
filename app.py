import streamlit as st
import pandas as pd

st.title("System sammenligning")

# læs Excel (række 2 = header)
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

# mapping til pæne Systemfinder-navne
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

# system navn kolonne
name_col = "System_Variant_Name_Local_sys_desc_pdm_gpdm"

# dropdown (rens data)
systemer = df[name_col].dropna()
systemer = systemer[systemer != "Optional"]

valg = st.multiselect(
    "Vælg systemer",
    sorted(systemer.unique())
)

# vis sammenligning
if valg:
    comp = df[df[name_col].isin(valg)]

    # find kun kolonner der findes
    available_cols = [col for col in mapping.keys() if col in df.columns]

    # behold kun relevante kolonner
    comp = comp[[name_col] + available_cols]

    # rename kun eksisterende
    comp = comp.rename(columns={k: v for k, v in mapping.items() if k in comp.columns})

    # transponer (Systemfinder style)
    comp = comp.set_index(name_col).T

    # ---------- FORMATTERING ----------

    # fjern None / NaN
    comp = comp.fillna("-")

    # rund tal pænt (stabil version)
    comp = comp.apply(lambda col: col.map(
        lambda x: round(x, 2) if isinstance(x, (int, float)) else x
    ))

    # tilføj enhed til GWP
    if "Globalt opvarmningspotentiale" in comp.index:
        comp.loc["Globalt opvarmningspotentiale"] = comp.loc["Globalt opvarmningspotentiale"].apply(
            lambda x: f"{x} kg CO₂e" if x != "-" else x
        )

    st.dataframe(comp)
