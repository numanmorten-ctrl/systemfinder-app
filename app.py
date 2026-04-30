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

df["display_name"] = df[name_col] + " (" + df[id_col] + ")"

valg_display = st.multiselect("Vælg systemer", df["display_name"])
valg_ids = df[df["display_name"].isin(valg_display)][id_col]

if len(valg_ids) > 0:

    # ---------- BILLEDER ----------
    st.subheader("Systemer")
    cols_img = st.columns(len(valg_display))

    for i, system in enumerate(valg_display):
        rows = df[df["display_name"] == system]
        if not rows.empty:
            img_url = rows[image_col].values[0]
            if isinstance(img_url, str) and img_url.startswith("http"):
                cols_img[i].image(img_url, width=180)
                cols_img[i].caption(system)

    # ---------- MAPPING ----------
    mapping = {
        "Global_Warming_Potential_sys_met_td_pdm_gpdm": "GWP",
        "Sound_Reduction_Index_sys_td_pdm_gpdm": "Rw",
        "Spectrum_Adaption_Term_C50_3150_sys_met_td_pdm_gpdm": "C50",
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

        "Surface_Quality_Class_sys_desc_pdm_gpdm": "Overflade"
    }

    # ---------- SIKKER KOLONNEVALG ----------
    existing_cols = [col for col in mapping.keys() if col in df.columns]
    cols_to_use = existing_cols + ["display_name"]

    comp = df[df[id_col].isin(valg_ids)][cols_to_use].copy()

    # rename
    mapping_filtered = {k: v for k, v in mapping.items() if k in comp.columns}
    comp = comp.rename(columns=mapping_filtered)

# ---------- FIX DECIMALER (SMART) ----------
for col in comp.columns:
    if col != "display_name":
        # prøv kun hvis det faktisk er tal
        if pd.api.types.is_numeric_dtype(comp[col]):
            comp[col] = comp[col].round(2)

    # ---------- TRANSPOSE ----------
    comp = comp.set_index("display_name").T
    comp = comp.dropna(how="all")

    # ---------- FORMATTERING ----------
def format_value(val):
    if pd.isna(val):
        return "-"
    if isinstance(val, float):
        return f"{val:.2f}".rstrip("0").rstrip(".")
    return str(val)

comp = comp.applymap(format_value)
comp = comp.fillna("-")

units = {
    "GWP": " kg CO₂e",
    "Rw": " dB",
    "C50": " dB",
    "Vægt": " kg/m²",
    "Højde": " mm",
    "Tykkelse": " mm",
    "Stolpeafstand": " mm",
    "Isolering tykkelse": " mm"
}

    for row in comp.index:
        if row in units:
            comp.loc[row] = comp.loc[row].apply(lambda x: x + units[row] if x != "-" else x)

    # ---------- TAB ----------
    def show_tab(rows):
        rows_existing = [r for r in rows if r in comp.index]

        if rows_existing:
            st.dataframe(
                comp.loc[rows_existing],
                use_container_width=True,
                height=400
            )
        else:
            st.info("Ingen data")

    tab1, tab2, tab3, tab4 = st.tabs(["Basis", "Geometri", "Opbygning", "Overflade"])

    with tab1:
        show_tab(["GWP", "Rw", "C50", "Brand", "Vægt"])

    with tab2:
        show_tab(["Højde", "Tykkelse", "Stolpeafstand", "Skelet"])

    with tab3:
        show_tab(["Beklædning", "Pladelag", "Profil", "Isolering", "Isolering tykkelse"])

    with tab4:
        show_tab(["Overflade"])

    # ---------- PDF ----------
    def download_image(url):
        try:
            return io.BytesIO(requests.get(url).content)
        except:
            return None

    def lav_pdf(comp, valg_display):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)

        styles = getSampleStyleSheet()
        elements = []

        logo = download_image("https://knauf.com/api/download-center/v1/assets/9cafb5b4-2a20-4020-ac0d-a0475600aeee?download=true")
        if logo:
            elements.append(Image(logo, width=120, height=50))

        elements.append(Spacer(1, 10))
        elements.append(Paragraph("System sammenligning", styles['Title']))
        elements.append(Spacer(1, 10))

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

    st.download_button(
        "📄 Download PDF",
        lav_pdf(comp, valg_display),
        file_name="system_sammenligning.pdf",
        mime="application/pdf"
    )
