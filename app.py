import streamlit as st
import pandas as pd

st.title("System sammenligning")

# læs Excel
df = pd.read_excel("10_list.xlsx", header=1)

# gør kolonner unikke
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

# kolonner
name_col = "System_Variant_Name_Local_sys_desc_pdm_gpdm"
id_col = "System_Variant_Number_sys_desc_pdm_gpdm"
image_col = "Picture_System_Variant_sys_desc_pdm_gpdm"

# mapping
mapping = {
    "Global_Warming_Potential_sys_met_td_pdm_gpdm": "GWP",
    "Sound_Reduction_Index_sys_td_pdm_gpdm": "Rw",
    "Fire_Resistance_Class_sys_desc_pdm_gpdm": "Brand",
    "Weight_Per_Unit_Area_sys_met_td_pdm_gpdm": "Vægt",

    "Partition_Height_sys_met_td_pdm_gpdm": "Højde",
    "Finished_Wall_Thickness_sys_desc_pdm_gpdm": "Tykkelse",
    "Stud_Spacing_sys_met_td_pdm_gpdm": "Stolpeafstand",
    "Wall_Grid_sys_desc_pdm_gpdm": "Skelet",

    "Cladding_sys_desc_pdm_gpdm": "Beklædning",
    "Cladding_Layers_sys_td_pdm_gpdm": "Pladelag",
    "Profile_sys_desc_pdm_gpdm": "Profil",
    "Insulation_Material_sys_desc_pdm_gpdm": "Isolering",
    "Insulation_Thickness_sys_met_td_pdm_gpdm": "Isolering tykkelse",

    "Spectrum_Adaption_Term_C50_3150_sys_met_td_pdm_gpdm": "C50",
    "Surface_Quality_Class_sys_desc_pdm_gpdm": "Overflade"
}

# enheder
units = {
    "GWP": "kg CO₂e",
    "Højde": "mm",
    "Tykkelse": "mm",
    "Stolpeafstand": "mm",
    "Isolering tykkelse": "mm",
    "Vægt": "kg/m²",
    "Rw": "dB",
    "C50": "dB"
}

# dropdown
df_valid = df[[id_col, name_col]].dropna()
df_valid = df_valid[df_valid[name_col] != "Optional"]
df_valid["display"] = df_valid[name_col] + " (" + df_valid[id_col] + ")"
df_valid = df_valid.drop_duplicates(subset=[id_col])

valg_display = st.multiselect("Vælg systemer", sorted(df_valid["display"]))
valgte_ids = df_valid[df_valid["display"].isin(valg_display)][id_col]

# billeder
if len(valgte_ids) > 0:
    selected = df[df[id_col].isin(valgte_ids)].drop_duplicates(subset=[id_col])
    cols_layout = st.columns(len(selected))

    for i, (_, row) in enumerate(selected.iterrows()):
        with cols_layout[i]:
            img = row.get(image_col, None)
            if pd.notna(img):
                st.image(img, width=120)
            st.markdown(f"<div style='text-align:center'>{row[name_col]}</div>", unsafe_allow_html=True)

# data
if len(valgte_ids) > 0:
    comp = df[df[id_col].isin(valgte_ids)].drop_duplicates(subset=[id_col])

    available_cols = [col for col in mapping.keys() if col in comp.columns]
    comp = comp[[name_col] + available_cols]

    comp = comp.rename(columns={k: v for k, v in mapping.items() if k in comp.columns})
    comp = comp.set_index(name_col).T
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

    # ---------- TABS ----------
    tab1, tab2, tab3, tab4 = st.tabs(["Basis", "Geometri", "Opbygning", "Overflade"])

    def show_tab(rows):
        existing = [r for r in rows if r in comp.index]
        if existing:
            st.dataframe(comp.loc[existing], use_container_width=True)
        else:
            st.info("Ingen data")

    # 🔥 C50 flyttet til Basis
    with tab1:
        show_tab(["GWP", "Rw", "C50", "Brand", "Vægt"])

    with tab2:
        show_tab(["Højde", "Tykkelse", "Stolpeafstand", "Skelet"])

    with tab3:
        show_tab(["Beklædning", "Pladelag", "Profil", "Isolering", "Isolering tykkelse"])

    # 🔥 Kun overflade
    with tab4:
        show_tab(["Overflade"])
