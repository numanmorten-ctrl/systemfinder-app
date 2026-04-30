import streamlit as st
import pandas as pd
import io
import requests
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(layout="wide")

# ---------- LOGO ----------
st.image(
    "https://knauf.com/api/download-center/v1/assets/9cafb5b4-2a20-4020-ac0d-a0475600aeee?download=true",
    width=150
)

st.title("System sammenligning")

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

# ---------- FIX: DISPLAY LABEL ----------
df["display_name"] = df[name_col] + "  (" + df[id_col] + ")"

# ---------- SELECT ----------
valg_display = st.multiselect("Vælg systemer", df["display_name"])

# find tilbage til ID (det unikke)
valg_ids = df[df["display_name"].isin(valg_display)][id_col]

if len(valg_ids) > 0:

    comp = df[df[id_col].isin(valg_ids)].copy()

    # brug display navn som kolonne (så brugeren ser begge)
    comp = comp.set_index("display_name").T

    # fjern dubletter
    comp = comp.loc[~comp.index.duplicated()]

    # ---------- BILLEDER ----------
    st.subheader("Systemer")
    cols_img = st.columns(len(valg_display))

    for i, system in enumerate(valg_display):
        try:
            img_url = df[df["display_name"] == system][image_col].values[0]
            if isinstance(img_url, str) and img_url.startswith("http"):
                cols_img[i].image(img_url, width=180)
                cols_img[i].caption(system)
        except:
            pass

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
    comp = comp.astype(str).fillna("-")

    # ---------- TABS ----------
    tab1, tab2, tab3, tab4 = st.tabs(["Basis", "Geometri", "Opbygning", "Overflade"])

    with tab1:
        st.dataframe(comp, width="stretch", height=400)

    with tab2:
        st.dataframe(comp, width="stretch", height=400)

    with tab3:
        st.dataframe(comp, width="stretch", height=400)

    with tab4:
        if "Overflade klasse" in comp.index:
            st.dataframe(comp.loc[["Overflade klasse"]], width="stretch")

    # ---------- PDF ----------
    def download_image(url):
        try:
            response = requests.get(url)
            return io.BytesIO(response.content)
        except:
            return None

    def lav_pdf(comp, valg_display):
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

        # SYSTEMER + BILLEDER
        for system in valg_display:
            try:
                img_url = df[df["display_name"] == system][image_col].values[0]
                img = download_image(img_url)
                if img:
                    elements.append(Image(img, width=100, height=100))
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

    pdf = lav_pdf(comp, valg_display)

    st.download_button(
        "📄 Download PDF",
        pdf,
        file_name="system_sammenligning.pdf",
        mime="application/pdf"
    )
