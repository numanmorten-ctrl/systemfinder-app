import streamlit as st
import pandas as pd
import io
import requests
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

# ---------- CONFIG ----------
st.set_page_config(layout="wide")

# ---------- LOGO ----------
st.image(
    "https://knauf.com/api/download-center/v1/assets/9cafb5b4-2a20-4020-ac0d-a0475600aeee?download=true",
    width=150
)

st.title("System sammenligning")

# ---------- CSS ----------
st.markdown("""
<style>
html, body {
    font-family: 'Segoe UI', sans-serif;
}

h1 {
    font-weight: 600;
}

.stTabs [data-baseweb="tab"] {
    background-color: #EDEFF2;
    border-radius: 6px;
    padding: 8px 16px;
}

.stTabs [aria-selected="true"] {
    background-color: #005AA7 !important;
    color: white !important;
}

.stDataFrame {
    border: 1px solid #E1E5EA;
    border-radius: 8px;
}
</style>
""", unsafe_allow_html=True)

# ---------- LOAD DATA ----------
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

# ---------- KOLONNER ----------
name_col = "System_Variant_Name_Local_sys_desc_pdm_gpdm"
id_col = "System_Variant_Number_sys_desc_pdm_gpdm"
image_col = "Picture_System_Variant_sys_desc_pdm_gpdm"

# ---------- VÆLG SYSTEMER ----------
valg = st.multiselect("Vælg systemer", df[name_col])

if valg:

    comp = df[df[name_col].isin(valg)].copy()

    # brug navn som index
    comp = comp.set_index(name_col).T

    # fjern dubletter (vigtigt for Streamlit)
    comp = comp.loc[~comp.index.duplicated()]

    # ---------- BILLEDER ----------
    st.subheader("Systemer")
    cols_img = st.columns(len(valg))

    for i, system in enumerate(valg):
        try:
            img_url = df[df[name_col] == system][image_col].values[0]
            if isinstance(img_url, str) and img_url.startswith("http"):
                cols_img[i].image(img_url, width=200)
                cols_img[i].caption(system)
        except:
            pass

    # ---------- TABS ----------
    tab1, tab2, tab3, tab4 = st.tabs(["Basis", "Geometri", "Opbygning", "Overflade"])

    # ---------- MAPPING ----------
    mapping = {
        "Global_Warming_Potential_sys_met_td_pdm_gpdm": "GWP (kg CO2e)",
        "Sound_Reduction_Index_sys_td_pdm_gpdm": "Rw (dB)",
        "Spectrum_Adaption_Term_C50_3150_sys_met_td_pdm_gpdm": "C50 (dB)",
        "Fire_Resistance_Class_sys_desc_pdm_gpdm": "Brandklasse",
        "Weight_Per_Unit_Area_sys_met_td_pdm_gpdm": "Vægt (kg/m²)",
        "Partition_Height_sys_met_td_pdm_gpdm": "Højde (mm)",
        "Stud_Spacing_sys_met_td_pdm_gpdm": "Stolpeafstand (mm)",
        "Insulation_Thickness_sys_met_td_pdm_gpdm": "Tykkelse (mm)",
        "Profile_sys_desc_pdm_gpdm": "Profil",
        "Wall_Grid_sys_desc_pdm_gpdm": "Skelet",
        "Surface_Quality_Class_sys_desc_pdm_gpdm": "Overflade klasse"
    }

    comp = comp.rename(index=mapping)

    # ---------- CLEAN ----------
    comp = comp.fillna("-")

    # ---------- TABS CONTENT ----------
    with tab1:
        st.dataframe(comp, use_container_width=True, height=400)

    with tab2:
        st.dataframe(comp, use_container_width=True, height=400)

    with tab3:
        st.dataframe(comp, use_container_width=True, height=400)

    with tab4:
        st.dataframe(comp.loc[["Overflade klasse"]], use_container_width=True)

    # ---------- PDF GENERATOR ----------
    def download_image(url):
        try:
            response = requests.get(url)
            return io.BytesIO(response.content)
        except:
            return None

    def lav_pdf(comp, valg):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)

        styles = getSampleStyleSheet()
        elements = []

        # LOGO
        logo_url = "https://knauf.com/api/download-center/v1/assets/9cafb5b4-2a20-4020-ac0d-a0475600aeee?download=true"
        logo = download_image(logo_url)
        if logo:
            elements.append(Image(logo, width=120, height=50))

        elements.append(Spacer(1, 10))
        elements.append(Paragraph("System sammenligning", styles['Title']))
        elements.append(Spacer(1, 10))

        # SYSTEM BILLEDER
        for system in valg:
            try:
                img_url = df[df[name_col] == system][image_col].values[0]
                img = download_image(img_url)
                if img:
                    elements.append(Image(img, width=120, height=120))
                    elements.append(Paragraph(system, styles['Normal']))
                    elements.append(Spacer(1, 10))
            except:
                pass

        # TABLE
        data = [["Egenskab"] + list(comp.columns)]

        for index, row in comp.iterrows():
            data.append([index] + list(row))

        table = Table(data)

        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#005AA7")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ]))

        elements.append(table)

        doc.build(elements)
        buffer.seek(0)
        return buffer

    # ---------- DOWNLOAD ----------
    pdf = lav_pdf(comp, valg)

    st.download_button(
        "📄 Download PDF",
        pdf,
        file_name="system_sammenligning.pdf",
        mime="application/pdf"
    )
