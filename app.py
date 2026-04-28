import streamlit as st
import pandas as pd

st.title("System sammenligning")

# læs Excel (vigtigt!)
df = pd.read_excel("10_list.xlsx", header=1)

# vælg systemer (brug korrekt kolonne!)
valg = st.multiselect(
    "Vælg systemer",
    df["System_Variant_Name_Local_sys_desc_pdm_gpdm"]
)

if valg:
    comp = df[df["System_Variant_Name_Local_sys_desc_pdm_gpdm"].isin(valg)]
    comp = comp.set_index("System_Variant_Name_Local_sys_desc_pdm_gpdm").T
    st.dataframe(comp)
