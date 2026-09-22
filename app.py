import streamlit as st

import pandas as pd

import json

import streamlit.components.v1 as components


# ============================================================

# PAGE SETUP

# ============================================================

st.set_page_config(

    page_title="System sammenligning",

    layout="wide",

)


# ============================================================

# KONSTANTER

# ============================================================

logo_url = (

    "https://knauf.com/api/download-center/v1/assets/"

    "9cafb5b4-2a20-4020-ac0d-a0475600aeee?download=true"

)

name_col = "System_Variant_Name_Local_sys_desc_pdm_gpdm"

id_col = "System_Variant_Number_sys_desc_pdm_gpdm"

image_col = "Picture_System_Variant_sys_desc_pdm_gpdm"


# ============================================================

# LOGO

# ============================================================

st.image(

    logo_url,

    width=150,

)

st.title(

    "System sammenligning"

)


# ============================================================

# LOAD DATA

# ============================================================

df = pd.read_excel(

    "10_list.xlsx",

    header=1,

)


# ============================================================

# GØR KOLONNENAVNE UNIKKE

# ============================================================

cols = []

counts = {}

for col in df.columns:

    if col in counts:

        counts[col] += 1

        cols.append(

            f"{col}_{counts[col]}"

        )

    else:

        counts[col] = 0

        cols.append(col)

df.columns = cols


# ============================================================

# VARIANT LOGIK

# ============================================================

df["variant_type"] = (

    df[id_col]

    .astype(str)

    .str.extract(

        r"_(A|B)\.dk$",

        expand=False,

    )

)

df["base_id"] = (

    df[id_col]

    .astype(str)

    .str.replace(

        r"_(A|B)\.dk$",

        "",

        regex=True,

    )

)


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


df_unique["display_name"] = (

    df_unique[name_col]

)


# ============================================================

# SYSTEMVÆLGER

# ============================================================

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


# ============================================================

# GEM SYSTEMER I VALGT RÆKKEFØLGE

# ============================================================

selected_systems = []


for position, display_name in enumerate(

    valg_display

):

    row = df_unique[

        df_unique["display_name"]

        == display_name

    ]

    if not row.empty:

        image_value = (

            row[image_col].iloc[0]

        )

        if pd.isna(image_value):

            image_value = ""

        else:

            image_value = str(

                image_value

            )

        selected_systems.append(

            {

                "position":

                    position,

                "display_name":

                    str(display_name),

                "base_id":

                    str(

                        row[

                            "base_id"

                        ].iloc[0]

                    ),

                "name":

                    str(

                        row[

                            name_col

                        ].iloc[0]

                    ),

                "image":

                    image_value,

            }

        )


valg_base_ids = [

    system["base_id"]

    for system

    in selected_systems

]


# ============================================================

# SYSTEMBILLEDER I APP

# ============================================================

st.subheader(

    "Systemer"

)


cols_img = st.columns(

    len(selected_systems)

)


for i, system in enumerate(

    selected_systems

):

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


# ============================================================

# MAPPING

# ============================================================

mapping = {

    "Global_Warming_Potential_sys_met_td_pdm_gpdm":

        "GWP",

    "Sound_Reduction_Index_sys_td_pdm_gpdm":

        "Rw",

    "Spectrum_Adaption_Term_C50_3150_sys_met_td_pdm_gpdm":

        "C50",

    "Fire_Resistance_Class_sys_desc_pdm_gpdm":

        "Brand",

    "Weight_Per_Unit_Area_sys_met_td_pdm_gpdm":

        "Vægt",

    # --------------------------------------------------------

    # NY HØJDELOGIK

    # --------------------------------------------------------

    "Partition_Height_Fire_sys_met_td_pdm_gpdm":

        "Højde iht. brand",

    "Partition_Height_sys_met_td_pdm_gpdm":

        "Højde ift. statik",

    # --------------------------------------------------------

    "Finished_Wall_Thickness_sys_desc_pdm_gpdm":

        "Samlet vægtykkelse",

    "Stud_Spacing_sys_met_td_pdm_gpdm":

        "Stolpeafstand",

    "Wall_Grid_sys_desc_pdm_gpdm":

        "Skelet",

    "Cladding_sys_desc_pdm_gpdm":

        "Beklædning",

    "Cladding_Layers_sys_td_pdm_gpdm":

        "Pladelag",

    "Profile_sys_desc_pdm_gpdm":

        "Profil",

    "Insulation_Material_sys_desc_pdm_gpdm":

        "Isolering",

    "Insulation_Thickness_sys_met_td_pdm_gpdm":

        "Isolering tykkelse",

    "Surface_Quality_Class_sys_desc_pdm_gpdm":

        "Overflade",

}


# ============================================================

# DATA

# ============================================================

comp_raw = df[

    df["base_id"].isin(

        valg_base_ids

    )

].copy()


# ============================================================

# ÉN HOVEDVARIANT PR. SYSTEM

# ============================================================

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


# ============================================================

# VALGT RÆKKEFØLGE

# ============================================================

order_map = {

    base_id: position

    for position, base_id

    in enumerate(

        valg_base_ids

    )

}


comp["_selection_order"] = (

    comp["base_id"].map(

        order_map

    )

)


comp = (

    comp

    .sort_values(

        "_selection_order"

    )

    .drop(

        columns=[

            "_selection_order"

        ]

    )

)


# ============================================================

# VÆLG DATAKOLONNER

# ============================================================

existing_cols = [

    col

    for col in mapping

    if col in comp.columns

]


cols_to_use = (

    existing_cols

    + [

        "base_id",

        name_col,

    ]

)


comp = comp[

    cols_to_use

]


# ============================================================

# RENAME

# ============================================================

comp = comp.rename(

    columns=mapping

)


# ============================================================

# BEVAR VALGT RÆKKEFØLGE

# ============================================================

comp["_selection_order"] = (

    comp["base_id"].map(

        order_map

    )

)


comp = (

    comp

    .sort_values(

        "_selection_order"

    )

    .drop(

        columns=[

            "_selection_order"

        ]

    )

)


# ============================================================

# FJERN BASE ID INDEN TRANSPOSE

# ============================================================

comp = comp.drop(

    columns=[

        "base_id"

    ]

)


# ============================================================

# TRANSPOSE

# ============================================================

comp = (

    comp

    .set_index(

        name_col

    )

    .T

)


comp = comp.dropna(

    how="all"

)


# ============================================================

# FORMAT

# ============================================================

comp = comp.astype(

    object

)


def format_value(x):

    if (

        pd.isna(x)

        or str(x).lower() == "nan"

    ):

        return "-"

    if isinstance(

        x,

        float,

    ):

        return (

            f"{x:.2f}"

            .rstrip("0")

            .rstrip(".")

        )

    return str(x)


for col in comp.columns:

    comp[col] = (

        comp[col].map(

            format_value

        )

    )


# ============================================================

# UNITS

# ============================================================

comp_display = comp.copy()


units = {

    "GWP":

        " kgCO2ekv/m²",

    "Rw":

        " dB",

    "C50":

        " dB",

    "Vægt":

        " kg/m²",

    "Højde iht. brand":

        " mm",

    "Højde ift. statik":

        " mm",
    
    "Samlet vægtykkelse":

        " mm",

    "Stolpeafstand":

        " mm",

    "Isolering tykkelse":

        " mm",

}


for row, unit in units.items():

    if row in comp_display.index:

        comp_display.loc[

            row,

            :

        ] = [

            f"{x}{unit}"

            if x != "-"

            else "-"

            for x in

            comp_display.loc[

                row,

                :

            ].tolist()

        ]


# ============================================================

# RÆKKEFØLGE PÅ EGENSKABER

# ============================================================

preferred_order = [

    # BASIS

    "GWP",

    "Rw",

    "C50",

    "Brand",

    "Vægt",

    # GEOMETRI

    "Højde iht. brand",

    "Højde ift. statik",

    "Samlet vægtykkelse",

    "Stolpeafstand",

    "Skelet",

    # OPBYGNING

    "Beklædning",

    "Pladelag",

    "Profil",

    "Isolering",

    "Isolering tykkelse",

    # OVERFLADE

    "Overflade",

]


comp_display = (

    comp_display.loc[

        [

            row

            for row

            in preferred_order

            if row

            in comp_display.index

        ]

    ]

)


# ============================================================

# TABS

# ============================================================

def show_tab(rows):

    rows_existing = [

        row

        for row in rows

        if row in comp_display.index

    ]

    if rows_existing:

        df_show = (

            comp_display.loc[

                rows_existing

            ]

        )

        df_show = df_show[

            ~(

                df_show == "-"

            ).all(

                axis=1

            )

        ]

        if not df_show.empty:

            st.dataframe(

                df_show,

                width="stretch",

                height=(

                    100

                    + len(df_show)

                    * 35

                ),

            )

        else:
            st.info(

                "Ingen data"

            )

    else:
        st.info(

            "Ingen data"

        )


tab1, tab2, tab3, tab4 = (

    st.tabs(

        [

            "Basis",

            "Geometri",

            "Opbygning",

            "Overflade",

        ]

    )

)


with tab1:

    show_tab(

        [

            "GWP",

            "Rw",

            "C50",

            "Brand",

            "Vægt",

        ]

    )


with tab2:

    show_tab(

        [

            "Højde iht. brand",

            "Højde ift. statik",

            "Samlet vægtykkelse",

            "Stolpeafstand",

            "Skelet",

        ]

    )


with tab3:

    show_tab(

        [

            "Beklædning",

            "Pladelag",

            "Profil",

            "Isolering",

            "Isolering tykkelse",

        ]

    )


with tab4:

    show_tab(

        [

            "Overflade"

        ]

    )


# ============================================================

# PDF

# ============================================================

st.divider()

st.subheader(

    "PDF"

)


pdf_title = st.text_input(

    "Titel til PDF",

    value="System sammenligning",

)


# ============================================================

# DATA TIL JAVASCRIPT

# ============================================================

pdf_systems = []

for system in selected_systems:

    pdf_systems.append(

        {

            "name":

                system["name"],

            "image":

                system["image"],

        }

    )


pdf_rows = []

for row_name, row in (

    comp_display.iterrows()

):

    pdf_rows.append(

        [

            str(row_name)

        ]

        + [

            str(value)

            for value

            in row.tolist()

        ]

    )


pdf_payload = {

    "title":

        pdf_title,

    "logo":

        logo_url,

    "systems":

        pdf_systems,

    "columns":

        [

            str(col)

            for col

            in comp_display.columns

        ],

    "rows":

        pdf_rows,

}


payload_json = json.dumps(

    pdf_payload,

    ensure_ascii=False,

)


# ============================================================

# BROWSER PDF COMPONENT

# ============================================================

pdf_component = f"""
<!DOCTYPE html>
<html lang="da">
<head>
<meta charset="UTF-8">
<script

    src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js">
</script>
<script

    src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.8.2/jspdf.plugin.autotable.min.js">
</script>
<style>

body {{

    font-family:

        Arial,

        sans-serif;

    margin: 0;

    padding: 0;

}}

#pdf-button {{

    background: white;

    color: #262730;

    border:

        1px solid

        rgba(49, 51, 63, 0.2);

    border-radius: 0.5rem;

    padding:

        0.5rem

        0.75rem;

    font-size: 14px;

    font-weight: 400;

    cursor: pointer;

}}

#pdf-button:hover {{

    border-color:

        rgb(255, 75, 75);

    color:

        rgb(255, 75, 75);

}}

#pdf-button:disabled {{

    opacity: 0.6;

    cursor: wait;

}}

#status {{

    margin-top: 10px;

    font-size: 13px;

}}

.error {{

    color: #b00020;

}}

.success {{

    color: green;

}}
</style>
</head>
<body>
<button

    id="pdf-button"

    onclick="createPdf()"
>

    📄 Download PDF
</button>
<div id="status"></div>

<script>

const payload = {payload_json};


function setStatus(

    text,

    className = ""

) {{

    const status =

        document.getElementById(

            "status"

        );

    status.innerText =

        text;

    status.className =

        className;

}}


async function imageUrlToDataUrl(

    url

) {{

    if (

        !url

        || typeof url !== "string"

        || !url.startsWith("http")

    ) {{

        return null;

    }}

    const response =

        await fetch(

            url,

            {{

                mode: "cors",

                credentials: "omit"

            }}

        );

    if (!response.ok) {{

        throw new Error(

            "HTTP "

            + response.status

            + " ved billede: "

            + url

        );

    }}

    const blob =

        await response.blob();

    if (

        !blob.type.startsWith(

            "image/"

        )

    ) {{

        throw new Error(

            "URL returnerede ikke et billede."

        );

    }}

    return await new Promise(

        (

            resolve,

            reject

        ) => {{

            const reader =

                new FileReader();

            reader.onloadend =

                () => resolve(

                    reader.result

                );

            reader.onerror =

                reject;

            reader.readAsDataURL(

                blob

            );

        }}

    );

}}


function loadImage(

    dataUrl

) {{

    return new Promise(

        (

            resolve,

            reject

        ) => {{

            const img =

                new Image();

            img.onload =

                () => resolve(img);

            img.onerror =

                reject;

            img.src =

                dataUrl;

        }}

    );

}}


async function prepareImage(

    url

) {{

    try {{

        const dataUrl =

            await imageUrlToDataUrl(

                url

            );

        if (!dataUrl) {{

            return null;

        }}

        const img =

            await loadImage(

                dataUrl

            );

        return {{

            dataUrl:

                dataUrl,

            width:

                img.naturalWidth,

            height:

                img.naturalHeight

        }};

    }}

    catch (error) {{

        console.error(

            error

        );

        return null;

    }}

}}


function fitImage(

    width,

    height,

    maxWidth,

    maxHeight

) {{

    const scale =

        Math.min(

            maxWidth / width,

            maxHeight / height

        );

    return {{

        width:

            width * scale,

        height:

            height * scale

    }};

}}


function safeFileName(

    value

) {{

    let name =

        value

        || "System sammenligning";

    name = name.replace(

        /[\\\\/:*?"<>|]/g,

        "_"

    );

    name = name.trim();

    if (!name) {{

        name =

            "System sammenligning";

    }}

    return name;

}}


async function createPdf() {{

    const button =

        document.getElementById(

            "pdf-button"

        );

    button.disabled =

        true;

    setStatus(

        "Henter billeder og opretter PDF..."

    );

    try {{

        const {{

            jsPDF

        }} =

            window.jspdf;


        // ----------------------------------------------------

        // HENT LOGO

        // ----------------------------------------------------

        const logo =

            await prepareImage(

                payload.logo

            );


        // ----------------------------------------------------

        // HENT SYSTEMBILLEDER

        // ----------------------------------------------------

        const systemImages =

            [];

        for (

            const system

            of payload.systems

        ) {{

            const image =

                await prepareImage(

                    system.image

                );

            systemImages.push(

                image

            );

        }}


        // ----------------------------------------------------

        // PDF

        // ----------------------------------------------------

        const doc =

            new jsPDF({{

                orientation:

                    "landscape",

                unit:

                    "mm",

                format:

                    "a4"

            }});


        const pageWidth =

            doc.internal

            .pageSize

            .getWidth();


        // ----------------------------------------------------

        // LOGO

        // ----------------------------------------------------

        let currentY =

            10;

        if (logo) {{

            const fitted =

                fitImage(

                    logo.width,

                    logo.height,

                    35,

                    16

                );

            doc.addImage(

                logo.dataUrl,

                "PNG",

                (

                    pageWidth

                    - fitted.width

                ) / 2,

                currentY,

                fitted.width,

                fitted.height

            );

            currentY +=

                fitted.height

                + 5;

        }}


        // ----------------------------------------------------

        // TITEL

        // ----------------------------------------------------

        doc.setFont(

            "helvetica",

            "bold"

        );

        doc.setFontSize(

            15

        );

        doc.text(

            payload.title

            || "System sammenligning",

            pageWidth / 2,

            currentY + 5,

            {{

                align:

                    "center"

            }}

        );

        currentY +=

            15;


        // ----------------------------------------------------

        // SYSTEMBILLEDER

        // ----------------------------------------------------

        const firstColWidth =

            42;

        const usableWidth =

            pageWidth

            - 20

            - firstColWidth;

        const systemColWidth =

            usableWidth

            / payload.systems.length;

        const imageAreaHeight =

            35;


        for (

            let i = 0;

            i < payload.systems.length;

            i++

        ) {{

            const image =

                systemImages[i];

            if (!image) {{

                continue;

            }}

            const fitted =

                fitImage(

                    image.width,

                    image.height,

                    Math.min(

                        28,

                        systemColWidth - 6

                    ),

                    27

                );


            const centerX =

                10

                + firstColWidth

                + (

                    systemColWidth

                    * i

                )

                + (

                    systemColWidth

                    / 2

                );


            doc.addImage(

                image.dataUrl,

                "PNG",

                centerX

                - (

                    fitted.width

                    / 2

                ),

                currentY,

                fitted.width,

                fitted.height

            );

        }}


        currentY +=

            imageAreaHeight;


        // ----------------------------------------------------

        // TABLE HEADER

        // ----------------------------------------------------

        const head = [

            [

                "Egenskab",

                ...payload.columns

            ]

        ];


        // ----------------------------------------------------

        // TABLE

        // ----------------------------------------------------

        doc.autoTable({{

            startY:

                currentY,

            head:

                head,

            body:

                payload.rows,

            theme:

                "grid",

            margin: {{

                left:

                    10,

                right:

                    10

            }},

            styles: {{

                font:

                    "helvetica",

                fontSize:

                    7.5,

                cellPadding:

                    2,

                valign:

                    "middle",

                overflow:

                    "linebreak"

            }},

            headStyles: {{

                fillColor:

                    [0, 90, 167],

                textColor:

                    [255, 255, 255],

                fontStyle:

                    "bold",

                halign:

                    "center"

            }},

            columnStyles: {{

                0: {{

                    fontStyle:

                        "bold",

                    cellWidth:

                        firstColWidth

                }}

            }},

            didParseCell:

                function(data) {{

                    if (

                        data.section

                        === "body"
&& data.column.index
> 0

                    ) {{

                        data.cell.styles.halign =

                            "center";

                    }}

                }}

        }});


        // ----------------------------------------------------

        // DOWNLOAD

        // ----------------------------------------------------

        const fileName =

            safeFileName(

                payload.title

            )

            + ".pdf";


        doc.save(

            fileName

        );


        setStatus(

            "PDF oprettet.",

            "success"

        );

    }}

    catch (error) {{

        console.error(

            error

        );

        setStatus(

            "PDF kunne ikke oprettes: "

            + error.message,

            "error"

        );

    }}

    finally {{

        button.disabled =

            false;

    }}

}}
</script>
</body>
</html>

"""


components.html(

    pdf_component,

    height=80,

    scrolling=False,

)
 
