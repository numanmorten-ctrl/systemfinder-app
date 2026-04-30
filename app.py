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

# ---------- DATA ----------
comp = df[df[id_col].isin(valg_ids)].copy()

existing_cols = [col for col in mapping if col in comp.columns]
cols_to_use = existing_cols + ["display_name"]

comp = comp[cols_to_use]

mapping_filtered = {k: v for k, v in mapping.items() if k in comp.columns}
comp = comp.rename(columns=mapping_filtered)

comp = comp.set_index("display_name").T
comp = comp.dropna(how="all")

# ---------- SIMPEL FORMAT ----------
comp = comp.apply(lambda col: col.map(lambda x: "-" if pd.isna(x) else str(x)))

# ---------- DISPLAY MED UNITS (SAFE) ----------
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
        comp_display.loc[row] = comp_display.loc[row].apply(
            lambda x: (str(x) + units[row]) if str(x) != "-" else "-"
        )

# ---------- TAB FUNKTION ----------
def show_tab(rows):
    rows_existing = [r for r in rows if r in comp_display.index]

    if rows_existing:
        df_show = comp_display.loc[rows_existing]

        # fjern rækker hvor ALLE værdier er "-"
        df_show = df_show[~(df_show == "-").all(axis=1)]

        if not df_show.empty:
            st.dataframe(
                df_show,
                use_container_width=True,
                height=100 + len(df_show) * 35  # 👈 dynamisk højde
            )
        else:
            st.info("Ingen data")
    else:
        st.info("Ingen data")

# ---------- TABS ----------
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

    logo = download_image("https://knauf.com/api/download-center/v1/assets/9cafb5b4-2a20-4020-ac0d-a0475600aeee?download=true")
    if logo:
        elements.append(Image(logo, width=120, height=50))

    elements.append(Spacer(1, 10))
    elements.append(Paragraph("System sammenligning", styles['Title']))
    elements.append(Spacer(1, 10))
# ---------- SYSTEM BILLEDER I RÆKKE ----------

image_row = []

for system in valg_display:
    try:
        row = df[df["display_name"] == system]
        if not row.empty:
            img_url = row[image_col].values[0]
            img = download_image(img_url)

            if img:
                cell = Table([
                    [Image(img, width=100, height=100)],
                    [Paragraph(system, styles['Normal'])]
                ])
                image_row.append(cell)

    except Exception as e:
        print(e)

if image_row:
    img_table = Table([image_row], hAlign='CENTER')
    elements.append(img_table)
    elements.append(Spacer(1, 15))
    
    data = [["Egenskab"] + list(comp.columns)]

    for index, row in comp.iterrows():
        data.append([index] + list(row))

col_widths = [120] + [180] * (len(comp.columns))
table = Table(data, colWidths=col_widths)

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
    lav_pdf(comp_display),
    file_name="system_sammenligning.pdf",
    mime="application/pdf"
)
