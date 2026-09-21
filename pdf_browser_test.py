import streamlit as st

import streamlit.components.v1 as components


st.set_page_config(

    page_title="Knauf browser PDF test",

    layout="wide",

)


st.title("Knauf – browser PDF test")

st.write(

    """

    Denne test undersøger, om browseren ikke kun kan vise et Knauf-billede,

    men også hente billeddata med JavaScript. Det er nødvendigt, hvis vi

    skal generere PDF'en direkte i browseren.

    """

)


logo_url = (

    "https://knauf.com/api/download-center/v1/assets/"

    "9cafb5b4-2a20-4020-ac0d-a0475600aeee?download=true"

)


system_url = (

    "https://knauf.com/api/download-center/v1/assets/"

    "aa90b60d-9e6c-43b8-8d72-9a597a4bd3f1?download=true"

)


html = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>

body {{

    font-family: Arial, sans-serif;

    padding: 20px;

}}

.testbox {{

    border: 1px solid #cccccc;

    padding: 20px;

    margin-bottom: 25px;

    border-radius: 8px;

}}

img {{

    max-width: 220px;

    max-height: 180px;

    margin-top: 10px;

}}

.success {{

    color: green;

    font-weight: bold;

}}

.error {{

    color: red;

    font-weight: bold;

}}

.info {{

    color: #333333;

}}

pre {{

    white-space: pre-wrap;

    background: #f4f4f4;

    padding: 10px;

}}

button {{

    padding: 10px 18px;

    font-size: 15px;

    cursor: pointer;

    margin-top: 10px;

}}
</style>
</head>
<body>
<h2>Browser-test</h2>
<p>

Først tester vi, om browseren kan vise billederne normalt.

Derefter forsøger JavaScript at hente de samme URL'er med fetch().
</p>

<div class="testbox">
<h3>1. Knauf logo</h3>
<p>

Direkte visning:
</p>
<img

    src="{logo_url}"

    alt="Knauf logo"
>
<p id="logo-result" class="info">

JavaScript-test ikke kørt endnu.
</p>
<pre id="logo-details"></pre>
<button onclick="testImage(

    '{logo_url}',

    'logo-result',

    'logo-details'

)">

Test JavaScript-adgang
</button>
</div>

<div class="testbox">
<h3>2. Systembillede</h3>
<p>

Direkte visning:
</p>
<img

    src="{system_url}"

    alt="Systembillede"
>
<p id="system-result" class="info">

JavaScript-test ikke kørt endnu.
</p>
<pre id="system-details"></pre>
<button onclick="testImage(

    '{system_url}',

    'system-result',

    'system-details'

)">

Test JavaScript-adgang
</button>
</div>

<div class="testbox">
<h3>3. Canvas-test</h3>
<p>

Denne test undersøger, om browseren kan tegne systembilledet

på et canvas og derefter læse billeddata ud igen.
</p>
<button onclick="canvasTest()">

Test canvas
</button>
<p id="canvas-result" class="info">

Canvas-test ikke kørt endnu.
</p>
<canvas

    id="test-canvas"

    width="300"

    height="250"

    style="

        border:1px solid #cccccc;

        display:block;

        margin-top:15px;

    "
></canvas>
<pre id="canvas-details"></pre>
</div>

<script>

async function testImage(url, resultId, detailsId) {{

    const result =

        document.getElementById(resultId);

    const details =

        document.getElementById(detailsId);

    result.className = "info";

    result.innerText = "Tester...";

    details.innerText = "";

    try {{

        const response = await fetch(

            url,

            {{

                method: "GET",

                mode: "cors",

                credentials: "omit"

            }}

        );

        const contentType =

            response.headers.get("content-type");

        const blob =

            await response.blob();

        details.innerText =

            "HTTP status: " + response.status +

            "\\nOK: " + response.ok +

            "\\nContent-Type: " + contentType +

            "\\nBlob type: " + blob.type +

            "\\nBytes: " + blob.size;

        if (

            response.ok &&

            blob.type.startsWith("image/")

        ) {{

            result.className = "success";

            result.innerText =

                "SUCCESS – JavaScript kan hente billedets bytes.";

        }}

        else {{

            result.className = "error";

            result.innerText =

                "FEJL – Browseren fik ikke et gyldigt billede.";

        }}

    }}

    catch (error) {{

        result.className = "error";

        result.innerText =

            "FEJL – JavaScript kunne ikke hente billedet.";

        details.innerText =

            error.name + ": " + error.message;

    }}

}}


async function canvasTest() {{

    const result =

        document.getElementById(

            "canvas-result"

        );

    const details =

        document.getElementById(

            "canvas-details"

        );

    const canvas =

        document.getElementById(

            "test-canvas"

        );

    const ctx =

        canvas.getContext("2d");

    result.className = "info";

    result.innerText = "Tester...";

    details.innerText = "";

    ctx.clearRect(

        0,

        0,

        canvas.width,

        canvas.height

    );

    try {{

        const response =

            await fetch(

                "{system_url}",

                {{

                    mode: "cors",

                    credentials: "omit"

                }}

            );

        if (!response.ok) {{

            throw new Error(

                "HTTP " + response.status

            );

        }}

        const blob =

            await response.blob();

        const objectUrl =

            URL.createObjectURL(blob);

        const img =

            new Image();

        img.onload = function() {{

            try {{

                const scale = Math.min(

                    canvas.width / img.width,

                    canvas.height / img.height

                );

                const width =

                    img.width * scale;

                const height =

                    img.height * scale;

                ctx.drawImage(

                    img,

                    (canvas.width - width) / 2,

                    (canvas.height - height) / 2,

                    width,

                    height

                );

                const dataUrl =

                    canvas.toDataURL(

                        "image/png"

                    );

                result.className =

                    "success";

                result.innerText =

                    "SUCCESS – billedet kan læses via canvas.";

                details.innerText =

                    "PNG data URL oprettet. Længde: "

                    + dataUrl.length

                    + " tegn.";

                URL.revokeObjectURL(

                    objectUrl

                );

            }}

            catch (error) {{

                result.className =

                    "error";

                result.innerText =

                    "FEJL – canvas kunne ikke læses.";

                details.innerText =

                    error.name

                    + ": "

                    + error.message;

            }}

        }};


        img.onerror = function() {{

            result.className =

                "error";

            result.innerText =

                "FEJL – blob kunne ikke indlæses som billede.";

            URL.revokeObjectURL(

                objectUrl

            );

        }};


        img.src =

            objectUrl;

    }}

    catch (error) {{

        result.className =

            "error";

        result.innerText =

            "FEJL – fetch/canvas-testen mislykkedes.";

        details.innerText =

            error.name

            + ": "

            + error.message;

    }}

}}
</script>
</body>
</html>

"""


components.html(

    html,

    height=1200,

    scrolling=True,

)
 
