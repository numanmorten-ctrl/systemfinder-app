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

# ----------- KOLONNER -----------
name_col = "System_Variant_Name_Local_sys_desc_pdm_gpdm"
id_col = "System_Variant_Number_sys_desc_pdm_gpdm"
image_col = "Picture_System_Variant_sys_desc_pdm_gpdm"

# ----------- MAPPING (ALLE EGENSKABER) -----------
mapping = {
    "Grid_sys_desc_pdm_gpdm": "Skelet type",
    "Wall_Grid_sys_desc_pdm_gpdm": "Skelet type",
    "Ceilings_Grid_sys_desc_pdm_gpdm": "Underlagstype",

    "Cladding_Layers_sys_td_pdm_gpdm": "Antal pladelag pr. side",
    "Cladding_sys_desc_pdm_gpdm": "Beklædningstype",
    "Finished_Wall_Thickness_sys_desc_pdm_gpdm": "Samlet vægtykkelse",

    "Fire_Resistance_Class_sys_desc_pdm_gpdm": "Brandklasse",
    "Global_Warming_Potential_sys_met_td_pdm_gpdm": "Globalt opvarmningspotentiale",

    "Insulation_Material_sys_desc_pdm_gpdm": "Isoleringsmateriale",
    "Insulation_Thickness_sys_met_td_pdm_gpdm": "Isoleringstykkelse",

    "Partition_Height_sys_met_td_pdm_gpdm": "Maksimal væghøjde",
    "Profile_sys_desc_pdm_gpdm": "Profil type",

    "Screw_Tight_sys_desc_pdm_gpdm": "Skruefast",

    "Spectrum_Adaption_Term_C50_3150_sys_met_td_pdm_gpdm": "Luftlydisolation - dB [R'w] C50",

    # 👉 BEVIDST kun én Rw (numeric prioriteres)
    "Sound_Reduction_Index_sys_td_pdm_gpdm": "Lydklasse (R’w)",

    "Stud_Spacing_sys_met_td_pdm_gpdm": "Stolpe afstand c/c",
    "Surface_Quality_Class_sys_desc_pdm_gpdm": "Størst mulig overfladeniveau",

    "Weight_Per_Unit_Area_sys_met_td_pdm_gpdm": "Vægt pr. m²"
}

# ----------- ENHEDER -----------
units = {
    "Globalt opvarmningspotentiale": "kg CO₂e",
    "Isoleringstykkelse": "mm",
    "Maksimal væghøjde": "mm",
    "Stolpe afstand c/c": "mm",
    "Samlet vægtykkelse": "mm",
    "Vægt pr. m²": "kg/m²",
    "Luftlydisolation - dB [R'w] C50": "dB",
    "Lydklasse (R’w)": "dB"
}

# ----------- DROPDOWN -----------
df_valid = df[[id_col, name_col]].dropna()
df_valid = df_valid[df_valid[name_col] != "Optional"]

df_valid["display"] = df_valid[name_col] + " (" + df_valid[id_col] + ")"
df_valid = df_valid.drop_duplicates(subset=[id_col])

valg_display = st.multiselect(
    "Vælg systemer",
    sorted(df_valid["display"])
)

valgte_ids = df_valid[df_valid["display"].isin(valg_display)][id_col]

# ----------- BILLEDER -----------
if len(valgte_ids) > 0:
    st.subheader("Systemer")

    selected = df[df[id_col].isin(valgte_ids)].drop_duplicates(subset=[id_col])
    cols_layout = st.columns(len(selected))

    for i, (_, row) in enumerate(selected.iterrows()):
        with cols_layout[i]:
            img = row.get(image_col, None)

            if pd.notna(img):
                st.image(img, width=150)

            st.markdown(
                f"<div style='text-align:center'>{row[name_col]}</div>",
                unsafe_allow_html=True
            )

# ----------- DATA -----------
if len(valgte_ids) > 0:
    comp = df[df[id_col].isin(valgte_ids)].drop_duplicates(subset=[id_col])

    available_cols = [col for col in mapping.keys() if col in comp.columns]

    comp = comp[[name_col] + available_cols]

    comp = comp.rename(columns={k: v for k, v in mapping.items() if k in comp.columns})

    comp = comp.set_index(name_col).T

    # fjern duplicate rækker (meget vigtigt!)
    comp = comp[~comp.index.duplicated(keep="first")]

    comp = comp.fillna("-")

    comp = comp.apply(lambda col: col.map(
        lambda x: round(x, 2) if isinstance(x, (int, float)) else x
    ))

    # enheder
    for row in comp.index:
        if row in units:
            unit = units[row]
            comp.loc[row] = comp.loc[row].apply(
                lambda x: f"{x} {unit}" if x != "-" else x
            )

    st.dataframe(comp, height=500, use_container_width=True)
