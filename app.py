import streamlit as st
import pandas as pd

st.title("System sammenligning")

df = pd.read_excel("10_list.xlsx", header=1)

# ryd data
systemer = df["System_Variant_Name_Local_sys_desc_pdm_gpdm"].dropna()
systemer = systemer[systemer != "Optional"]
systemer = systemer.unique()

valg = st.multiselect(
    "Vælg systemer",
    sorted(systemer)
)

if valg:
    comp = df[df["System_Variant_Name_Local_sys_desc_pdm_gpdm"].isin(valg)]
    comp = comp.set_index("System_Variant_Name_Local_sys_desc_pdm_gpdm").T
    st.dataframe(comp)
