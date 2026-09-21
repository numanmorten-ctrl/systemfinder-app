import streamlit as st
import pandas as pd
import io
import requests
from PIL import Image as PILImage
from reportlab.platypus import (
   SimpleDocTemplate,
   Table,
   TableStyle,
   Paragraph,
   Spacer,
   Image as RLImage,
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER

st.set_page_config(layout="wide")

# ---------- KONSTANTER ----------
logo_url = (
   "https://knauf.com/api/download-center/v1/assets/"
   "9cafb5b4-2a20-4020-ac0d-a0475600aeee?download=true"
)
name_col = "System_Variant_Name_Local_sys_desc_pdm_gpdm"
id_col = "System_Variant_Number_sys_desc_pdm_gpdm"
image_col = "Picture_System_Variant_sys_desc_pdm_gpdm"

# ---------- LOGO ----------
st.image(
   logo_url,
   width=150,
)
st.title("System sammenligning")

# ---------- LOAD DATA ----------
df = pd.read_excel(
   "10_list.xlsx",
   header=1,
)

# Gør kolonnenavne unikke
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

# ---------- VARIANT LOGIK ----------
df["variant_type"] = df[id_col].str.extract(
   r"_(A|B)\.dk$"
)
df["base_id"] = df[id_col].str.replace(
   r"_(A|B)\.dk$",
   "",
   regex=True,
)

# B prioriteres, når A/B er to datavarianter
df_sorted = df.sort_values(
   "variant_type",
   ascending=False,
)
df_unique = (
   df_sorted
   .drop_duplicates(
       subset="base_id",
       keep="first",
   )
   .copy()
)
df_unique["display_name"] = df_unique[name_col]

# ---------- SELECT ----------
max_systemer = 5
valg_display = st.multiselect(
   "Vælg systemer (max 5)",
   df_unique["display_name"],
)
if len(valg_display) > max_systemer:
   st.warning(
       f"Du kan maks vælge {max_systemer} systemer"
   )
   st.stop()
if not valg_display:
   st.stop()

# Gem valgrækkefølgen eksplicit
selected_systems = []
for position, display_name in enumerate(valg_display):
   row = df_unique[
       df_unique["display_name"] == display_name
   ]
   if not row.empty:
       selected_systems.append(
           {
               "position": position,
               "display_name": display_name,
               "base_id": row["base_id"].iloc[0],
               "name": row[name_col].iloc[0],
               "image": row[image_col].iloc[0],
           }
       )

valg_base_ids = [
   item["base_id"]
   for item in selected_systems
]

# ---------- BILLEDER I APP ----------
st.subheader("Systemer")
cols_img = st.columns(
   len(selected_systems)
)
for i, system in enumerate(selected_systems):
   img_url = system["image"]
   if (
       isinstance(img_url, str)
       and img_url.startswith("http")
   ):
       cols_img[i].image(
           img_url,
           width=180,
       )
   cols_img[i].caption(
       system["name"]
   )

# ---------- MAPPING ----------
mapping = {
   "Global_Warming_Potential_sys_met_td_pdm_gpdm": "GWP",
   "Sound_Reduction_Index_sys_td_pdm_gpdm": "Rw",
   "Spectrum_Adaption_Term_C50_3150_sys_met_td_pdm_gpdm": "C50",
   "Fire_Resistance_Class_sys_desc_pdm_gpdm": "Brand",
   "Weight_Per_Unit_Area_sys_met_td_pdm_gpdm": "Vægt",
   "Finished_Wall_Thickness_sys_desc_pdm_gpdm": "Tykkelse",
   "Stud_Spacing_sys_met_td_pdm_gpdm": "Stolpeafstand",
   "Wall_Grid_sys_desc_pdm_gpdm": "Skelet",
   "Cladding_sys_desc_pdm_gpdm": "Beklædning",
   "Cladding_Layers_sys_td_pdm_gpdm": "Pladelag",
   "Profile_sys_desc_pdm_gpdm": "Profil",
   "Insulation_Material_sys_desc_pdm_gpdm": "Isolering",
   "Insulation_Thickness_sys_met_td_pdm_gpdm": "Isolering tykkelse",
   "Surface_Quality_Class_sys_desc_pdm_gpdm": "Overflade",
}

# ---------- DATA ----------
comp_raw = df[
   df["base_id"].isin(valg_base_ids)
].copy()

# ---------- SPLIT A OG B ----------
comp_A = comp_raw[
   comp_raw["variant_type"] == "A"
]
comp_B = comp_raw[
   comp_raw["variant_type"] == "B"
]

# ---------- MERGE HØJDER ----------
height_merge = pd.merge(
   comp_B[
       [
           "base_id",
           "Partition_Height_sys_met_td_pdm_gpdm",
       ]
   ],
   comp_A[
       [
           "base_id",
           "Partition_Height_sys_met_td_pdm_gpdm",
       ]
   ],
   on="base_id",
   how="outer",
   suffixes=(
       "_brand",
       "_statik",
   ),
)
height_merge = height_merge.rename(
   columns={
       "Partition_Height_sys_met_td_pdm_gpdm_brand":
           "Højde iht. brand",
       "Partition_Height_sys_met_td_pdm_gpdm_statik":
           "Højde ift. statik",
   }
)
height_merge["Højde iht. brand"] = (
   height_merge["Højde iht. brand"]
   .fillna("-")
)

# ---------- ÉN VARIANT TIL ØVRIGE DATA ----------
comp = (
   comp_raw
   .sort_values(
       "variant_type",
       ascending=False,
   )
   .drop_duplicates(
       subset="base_id",
       keep="first",
   )
)

# Sørg for samme rækkefølge som brugerens valg
order_map = {
   base_id: position
   for position, base_id
   in enumerate(valg_base_ids)
}
comp["_selection_order"] = (
   comp["base_id"]
   .map(order_map)
)
comp = (
   comp
   .sort_values("_selection_order")
   .drop(
       columns=["_selection_order"]
   )
)

existing_cols = [
   col
   for col in mapping
   if col in comp.columns
]
cols_to_use = (
   existing_cols
   + ["base_id", name_col]
)
comp = comp[cols_to_use]

# ---------- MERGE HØJDER IND ----------
comp = comp.merge(
   height_merge,
   on="base_id",
   how="left",
   sort=False,
)

# Merge kan ændre rækkefølgen, så håndhæv
# brugerens valgrækkefølge igen.
comp["_selection_order"] = (
   comp["base_id"]
   .map(order_map)
)
comp = (
   comp
   .sort_values("_selection_order")
   .drop(
       columns=["_selection_order"]
   )
)

comp = comp.rename(
   columns=mapping
)
comp = (
   comp
   .set_index(name_col)
   .T
)
comp = comp.dropna(
   how="all"
)

# ---------- FORMAT ----------
comp = comp.astype(object)

def format_value(x):
   if pd.isna(x) or str(x).lower() == "nan":
       return "-"
   if isinstance(x, float):
       return (
           f"{x:.2f}"
           .rstrip("0")
           .rstrip(".")
       )
   return x

for col in comp.columns:
   comp[col] = comp[col].map(
       format_value
   )

# ---------- UNITS ----------
comp_display = comp.copy()
units = {
   "GWP": " kgCO2ekv/m²",
   "Rw": " dB",
   "C50": " dB",
   "Vægt": " kg/m²",
   "Højde": " mm",
   "Højde iht. brand": " mm",
   "Højde ift. statik": " mm",
   "Stolpeafstand": " mm",
   "Isolering tykkelse": " mm",
}

for row, unit in units.items():
   if row in comp_display.index:
       comp_display.loc[row, :] = [
           f"{x}{unit}"
           if x != "-"
           else "-"
           for x in comp_display.loc[row, :].tolist()
       ]

# ---------- STYR RÆKKEFØLGE ----------
preferred_order = [
   "GWP",
   "Rw",
   "C50",
   "Brand",
   "Vægt",
   "Højde iht. brand",
   "Højde ift. statik",
   "Tykkelse",
   "Stolpeafstand",
   "Skelet",
   "Beklædning",
   "Pladelag",
   "Profil",
   "Isolering",
   "Isolering tykkelse",
   "Overflade",
]
comp_display = comp_display.loc[
   [
       row
       for row in preferred_order
       if row in comp_display.index
   ]
]

# ---------- TABS ----------
def show_tab(rows):
   rows_existing = [
       row for row in rows
       if row in comp_display.index
   ]
   if rows_existing:
       df_show = comp_display.loc[rows_existing]
       df_show = df_show[
           ~(df_show == "-").all(axis=1)
       ]
       if not df_show.empty:
           st.dataframe(
               df_show,
               width="stretch",
               height=100 + len(df_show) * 35,
           )
       else:
           st.info("Ingen data")
   else:
       st.info("Ingen data")

tab1, tab2, tab3, tab4 = st.tabs(
   ["Basis", "Geometri", "Opbygning", "Overflade"]
)
with tab1:
   show_tab(["GWP", "Rw", "C50", "Brand", "Vægt"])
with tab2:
   show_tab([
       "Højde iht. brand",
       "Højde ift. statik",
       "Tykkelse",
       "Stolpeafstand",
       "Skelet",
   ])
with tab3:
   show_tab([
       "Beklædning",
       "Pladelag",
       "Profil",
       "Isolering",
       "Isolering tykkelse",
   ])
with tab4:
   show_tab(["Overflade"])

# ---------- PDF TITEL ----------
pdf_title = st.text_input(
   "Titel til PDF"
)

# ---------- BILLEDHÅNDTERING TIL PDF ----------
def download_and_convert_image(url):
   if (
       not isinstance(url, str)
       or not url.startswith("http")
   ):
       return None
   try:
       response = requests.get(
           url,
           timeout=15,
           headers={
               "User-Agent": "Mozilla/5.0"
           },
       )
       response.raise_for_status()
       source = io.BytesIO(
           response.content
       )
       # Pillow åbner billedet og konverterer
       # det til et format ReportLab kan læse.
       image = PILImage.open(source)
       if image.mode not in ("RGB", "RGBA"):
           image = image.convert("RGBA")
       output = io.BytesIO()
       image.save(
           output,
           format="PNG",
       )
       output.seek(0)
       return output
   except Exception:
       return None

# ---------- PDF ----------
def lav_pdf(comp, pdf_title):
   buffer = io.BytesIO()
   doc = SimpleDocTemplate(
       buffer,
       pagesize=landscape(A4),
       topMargin=20,
       bottomMargin=20,
       leftMargin=30,
       rightMargin=30,
   )
   styles = getSampleStyleSheet()
   elements = []

   # ---------- KNAUF LOGO ----------
   logo_data = download_and_convert_image(
       logo_url
   )
   if logo_data:
       try:
           logo = RLImage(
               logo_data
           )
           ratio = (
               logo.imageHeight
               / logo.imageWidth
           )
           logo.drawWidth = 120
           logo.drawHeight = (
               120 * ratio
           )
           logo.hAlign = "CENTER"
           elements.append(
               logo
           )
           elements.append(
               Spacer(1, 10)
           )
       except Exception:
           pass

   # ---------- SYSTEMBILLEDER ----------
   image_cells = [""]
   # selected_systems er allerede i
   # præcis brugerens valgte rækkefølge.
   for system in selected_systems:
       img_data = (
           download_and_convert_image(
               system["image"]
           )
       )
       if img_data:
           try:
               pil_image = PILImage.open(
                   img_data
               )
               width, height = (
                   pil_image.size
               )
               img_data.seek(0)
               max_width = 80
               max_height = 80
               scale = min(
                   max_width / width,
                   max_height / height,
               )
               draw_width = (
                   width * scale
               )
               draw_height = (
                   height * scale
               )
               pdf_image = RLImage(
                   img_data,
                   width=draw_width,
                   height=draw_height,
               )
               image_cells.append(
                   pdf_image
               )
           except Exception:
               image_cells.append("")
       else:
           image_cells.append("")

   # ---------- PDF TABEL ----------
   header_row = (
       ["Egenskab"]
       + list(comp.columns)
   )
   data = [
       image_cells,
       header_row,
   ]
   for index, row in comp.iterrows():
       data.append(
           [index]
           + list(row)
       )

   col_widths = (
       [100]
       + [140] * len(comp.columns)
   )

   table = Table(
       data,
       colWidths=col_widths,
   )

   table.setStyle(
       TableStyle(
           [
               (
                   "BACKGROUND",
                   (0, 1),
                   (-1, 1),
                   colors.HexColor(
                       "#005AA7"
                   ),
               ),
               (
                   "TEXTCOLOR",
                   (0, 1),
                   (-1, 1),
                   colors.white,
               ),
               (
                   "ALIGN",
                   (1, 0),
                   (-1, 0),
                   "CENTER",
               ),
               (
                   "VALIGN",
                   (0, 0),
                   (-1, -1),
                   "MIDDLE",
               ),
               (
                   "GRID",
                   (0, 1),
                   (-1, -1),
                   0.5,
                   colors.grey,
               ),
               (
                   "FONTSIZE",
                   (0, 0),
                   (-1, -1),
                   8,
               ),
           ]
       )
   )

   elements.append(
       table
   )

   # ---------- PDF TITEL ----------
   style_center = styles["Heading2"]
   style_center.alignment = TA_CENTER
   elements.append(
       Spacer(1, 20)
   )
   elements.append(
       Paragraph(
           pdf_title,
           style_center,
       )
   )

   doc.build(
       elements
   )
   buffer.seek(0)
   return buffer

# ---------- DOWNLOAD ----------
final_title = (
   pdf_title
   if pdf_title
   else "System sammenligning"
)

safe_title = "".join(
   c
   for c in final_title
   if c.isalnum()
   or c in " _-"
).strip()

st.download_button(
   "📄 Download PDF",
   lav_pdf(
       comp_display,
       final_title,
   ),
   file_name=f"{safe_title}.pdf",
   mime="application/pdf",
)
