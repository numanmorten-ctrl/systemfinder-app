import streamlit as st
import pandas as pd
import io
import requests
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
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
df["display_name"] = df[name_col].astype(str) + " (" + df[id_col].astype(str) + ")"
# ---------- SELECT ----------
valg_display = st.multiselect("Vælg systemer", df["display_name"])
if not valg_display:
   st.stop()
valg_ids = df[df["display_name"].isin(valg_display)][id_col]
# ---------- BILLEDER (UI) ----------
st.subheader("Systemer")
cols_img = st.columns(len(valg_display))
for i, system in enumerate(valg_display):
   row = df[df["display_name"] == system]
   if not row.empty:
       img_url = row[image_col].values[0]
       local_name = row[name_col].values[0]
       if isinstance(img_url, str) and img_url.startswith("http"):
           cols_img[i].image(img_url, width=180)
           cols_img[i].caption(local_name)
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
# ---------- DATA ----------
comp = df[df[id_col].isin(valg_ids)].copy()
existing_cols = [col for col in mapping if col in comp.columns]
cols_to_use = existing_cols + ["display_name"]
comp = comp[cols_to_use]
mapping_filtered = {k: v for k, v in mapping.items() if k in comp.columns}
comp = comp.rename(columns=mapping_filtered)
# map display_name -> local_name
name_map = df.set_index("display_name")[name_col].to_dict()

comp = comp.set_index("display_name").T

# skift kolonnenavne til local name
comp.columns = [name_map.get(col, col) for col in comp.columns]
comp = comp.dropna(how="all")
# ---------- FORMAT ----------
comp = comp.astype(object)
def format_value(x):
   if pd.isna(x) or str(x).lower() == "nan":
       return "-"
   if isinstance(x, float):
       return f"{x:.2f}".rstrip("0").rstrip(".")
   return x
for col in comp.columns:
   comp[col] = comp[col].map(format_value)
# ---------- UNITS ----------
comp_display = comp.copy()
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
for row in comp_display.index:
   if row in units:
       comp_display.loc[row] = comp_display.loc[row].map(
           lambda x: f"{x}{units[row]}" if x != "-" else "-"
       )
# ---------- TAB ----------
def show_tab(rows):
   rows_existing = [r for r in rows if r in comp_display.index]
   if rows_existing:
       df_show = comp_display.loc[rows_existing]
       df_show = df_show[~(df_show == "-").all(axis=1)]
       if not df_show.empty:
           st.dataframe(
               df_show,
               use_container_width=True,
               height=100 + len(df_show) * 35
           )
       else:
           st.info("Ingen data")
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
def lav_pdf(comp):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4))
    styles = getSampleStyleSheet()

    elements = []

    # ---------- LOGO ----------
    logo_url = "https://knauf.com/api/download-center/v1/assets/9cafb5b4-2a20-4020-ac0d-a0475600aeee?download=true"
    logo = download_image(logo_url)

if logo:
    img = Image(logo)

    ratio = img.imageHeight / img.imageWidth
    img.drawWidth = 120
    img.drawHeight = 120 * ratio

    img.hAlign = "CENTER"

    elements.append(img)

    # ---------- TITLE ----------
    elements.append(Paragraph("System sammenligning", styles['Title']))
    elements.append(Spacer(1, 10))

    # ---------- HEADER MED BILLEDER ----------
    image_cells = [""]

    for col in comp.columns:
        try:
            row = df[df[name_col] == col]

            if not row.empty:
                img_url = row[image_col].values[0]
                img = download_image(img_url)

                if img:
                    image_cells.append(Image(img, width=80, height=80))
                else:
                    image_cells.append("")
            else:
                image_cells.append("")
        except:
            image_cells.append("")

    # ---------- HEADER MED NAVNE ----------
    header_row = ["Egenskab"] + list(comp.columns)

    # ---------- DATA ----------
    data = [image_cells, header_row]

    for index, row in comp.iterrows():
        data.append([index] + list(row))

    # ---------- TABLE ----------
    col_widths = [120] + [180] * len(comp.columns)
    table = Table(data, colWidths=col_widths)

    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 1), (-1, 1), colors.HexColor("#005AA7")),
        ("TEXTCOLOR", (0, 1), (-1, 1), colors.white),
        ("ALIGN", (1, 0), (-1, 0), "CENTER"),
        ("GRID", (0, 1), (-1, -1), 0.5, colors.grey),
    ]))

    elements.append(table)

    doc.build(elements)
    buffer.seek(0)

    return buffer

st.download_button(
    "📄 Download PDF",
    lav_pdf(comp_display),
    file_name="system_sammenligning.pdf",
    mime="application/pdf"
)
