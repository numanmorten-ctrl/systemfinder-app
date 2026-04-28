import streamlit as st
import pandas as pd

st.title("System sammenligning")

df = pd.read_excel("10_list.xlsx", header=1)

# gør kolonnenavne unikke
df.columns = pd.io.parsers.ParserBase({'names': df.columns})._maybe_dedup_names(df.columns)

# ryd systemnavne
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
