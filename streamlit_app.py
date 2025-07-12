"""Scene & Shot Planner – Streamlit App
Author: ChatGPT (OpenAI)
Updated: 2025-07-11

Browser‑only version using **`st.query_params`** (no more experimental APIs).
Each project is serialized into the URL `data` parameter; every tab gets its own
plan unless you share the link.
"""

import json, io, base64, zlib, time
from typing import List, Dict, Any

import streamlit as st
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="🎬 Scene & Shot Planner", page_icon="🎬", layout="wide")
st.title("🎬 Scene & Shot Planner")

SHOT_CYCLE = ["Wide", "Medium Shot", "Close‑Up", None]

# ---------------------------------------------------------------------------
# URL‑based storage helpers
# ---------------------------------------------------------------------------

def encode_scenes(scenes: List[Dict[str, Any]]) -> str:
    """Compress + base64 the scenes list, excluding live file objects."""
    def strip_files(obj):
        return [
            {
                **sc,
                "shots": [{k: v for k, v in sh.items() if k != "file"} for sh in sc["shots"]],
            }
            for sc in obj
        ]

    raw = json.dumps(strip_files(scenes)).encode()
    compressed = zlib.compress(raw)
    return base64.urlsafe_b64encode(compressed).decode()


def decode_scenes(token: str) -> List[Dict[str, Any]]:
    try:
        data = zlib.decompress(base64.urlsafe_b64decode(token)).decode()
        scenes = json.loads(data)
        for sc in scenes:
            for sh in sc.get("shots", []):
                sh.setdefault("file", None)
        return scenes
    except Exception:
        return []

# ---------------------------------------------------------------------------
# Load scenes from URL or start empty
# ---------------------------------------------------------------------------

params = st.query_params  # new API
initial_token = params.get("data", "")
initial_scenes: List[Dict[str, Any]] = decode_scenes(initial_token) if initial_token else []

if "scenes" not in st.session_state:
    st.session_state.scenes = initial_scenes

# ---------------------------------------------------------------------------
# Scene/shot factory
# ---------------------------------------------------------------------------

def make_scene(idx: int) -> Dict[str, Any]:
    shots = [
        {
            "id": i + 1,
            "type": t,
            "alt_type": "Wide" if t is None else None,
            "description": "",
            "file": None,
        }
        for i, t in enumerate(SHOT_CYCLE)
    ]
    return {
        "id": idx + 1,
        "title": "",
        "hook": "",
        "problem": "",
        "conflict": "",
        "resolution": "",
        "shots": shots,
    }

# ---------------------------------------------------------------------------
# Controls
# ---------------------------------------------------------------------------

st.header("Scene Controls")
col_add, col_reset = st.columns(2)
with col_add:
    if st.button("➕ Add Scene"):
        st.session_state.scenes.append(make_scene(len(st.session_state.scenes)))
with col_reset:
    if st.button("🗑️ Reset All", type="secondary"):
        st.session_state.scenes.clear()

st.divider()

# ---------------------------------------------------------------------------
# Scene editor loop
# ---------------------------------------------------------------------------

for scene_idx, scene in enumerate(st.session_state.scenes):
    with st.container():
        st.subheader(f"Scene {scene['id']}")
        scene["title"] = st.text_area("Scene Title", scene["title"], key=f"title_{scene_idx}")
        scene["hook"] = st.text_area("Hook", scene["hook"], key=f"hook_{scene_idx}")
        scene["problem"] = st.text_area("Problem", scene["problem"], key=f"prob_{scene_idx}")
        scene["conflict"] = st.text_area("Conflict", scene["conflict"], key=f"conf_{scene_idx}")
        scene["resolution"] = st.text_area("Resolution", scene["resolution"], key=f"res_{scene_idx}")

        st.markdown("**Shots** (4 per scene)")
        for shot_idx, shot in enumerate(scene["shots"]):
            with st.expander(f"Shot {shot['id']}"):
                if shot["type"] is None:
                    shot["alt_type"] = st.selectbox(
                        "Shot Size",
                        ["Wide", "Medium Shot", "Close‑Up"],
                        index=["Wide", "Medium Shot", "Close‑Up"].index(shot["alt_type"]),
                        key=f"stype_{scene_idx}_{shot_idx}",
                    )
                    shot_type_display = shot["alt_type"]
                else:
                    shot_type_display = shot["type"]
                    st.markdown(f"**Type:** {shot_type_display}")

                shot["description"] = st.text_area(
                    "Description / Action", shot["description"], key=f"sdesc_{scene_idx}_{shot_idx}"
                )

                shot["file"] = st.file_uploader(
                    "Inspiration Image (optional)",
                    type=["png", "jpg", "jpeg"],
                    key=f"sfile_{scene_idx}_{shot_idx}",
                )
                if shot["file"] is not None:
                    shot["file"].seek(0)
                    st.image(
                        shot["file"],
                        caption=f"Scene {scene['id']} – Shot {shot['id']} ({shot_type_display})",
                        use_container_width=True,
                    )
        st.divider()

# ---------------------------------------------------------------------------
# Persist scenes back to URL
# ---------------------------------------------------------------------------

st.query_params.update(data=encode_scenes(st.session_state.scenes))

# ---------------------------------------------------------------------------
# Export helpers – JPEG + PDF (unchanged)
# ---------------------------------------------------------------------------

def build_lines(scenes):
    lines = []
    for sc in scenes:
        lines.append(f"Scene {sc['id']}: {sc['title']}")
        lines.append(f"  Hook: {sc['hook']}")
        lines.append(f"  Problem: {sc['problem']}")
        lines.append(f"  Conflict: {sc['conflict']}")
        lines.append(f"  Resolution: {sc['resolution']}")
        for sh in sc["shots"]:
            stype = sh['type'] if sh['type'] else sh['alt_type']
            lines.append(f"    Shot {sh['id']} ({stype}) – {sh['description']}")
        lines.append("")
    return lines

def scenes_to_jpeg(scenes):
    lines = build_lines(scenes)
    font = ImageFont.load_default()
    lh = font.getbbox('Hg')[3] + 4
    w = int(max(font.getlength(l) for l in lines) + 20)
    h = lh * len(lines) + 20
    img = Image.new('RGB', (w, h), 'white')
    draw = ImageDraw.Draw(img)
    y = 10
    for line in lines:
        draw.text((10, y), line, fill='black', font=font)
        y += lh
    buf = io.BytesIO()
    img.save(buf, format='JPEG', quality=95, subsampling=0, optimize=True)
    return buf.getvalue()

def scenes_to_pdf(scenes):
    jpeg_bytes = scenes_to_jpeg(scenes)
    img = Image.open(io.BytesIO(jpeg_bytes))
    buf = io.BytesIO()
    img.save(buf, format='PDF')
    return buf.getvalue()

# ---------------------------------------------------------------------------
# Download buttons
# ---------------------------------------------------------------------------

if st.session_state.scenes:
    st.header("Download Plan")
    st.download_button(
        "📄 PDF",
        data=scenes_to_pdf(st.session_state.scenes),
        file_name="scene_shot_plan.pdf",
        mime="application/pdf",
    )
    st.download_button(
        "🖼️ JPEG",
        data=scenes_to_jpeg(st.session_state.scenes),
        file_name="scene_shot_plan.jpg",
        mime="image/jpeg",
    )

# ---------------------------------------------------------------------------
# Educational footer & share button (unchanged)
# ---------------------------------------------------------------------------

st.divider()
st.markdown(
    """
### 🎥 Understanding the Shot Sequence
A classic **Wide → Medium → Close‑Up** progression guides the audience from context to intimacy:

* **Wide Shot (WS)** – Establishes setting and spatial relationships, giving viewers the *where* and *who*.
* **Medium Shot (MS)** – Brings us closer to the subject, capturing posture, gestures, and interactions.
* **Close‑Up (CU)** – Zeroes in on emotion and detail, ensuring the audience *feels* the moment.

Repeating this rhythm keeps visual pacing fresh while maintaining geographic clarity.

### 📝 Scene Story Beats
Every scene is its own miniature story arc:

1. **Hook** – Grabs attention.
2. **Problem** – Introduces a challenge.
3. **Conflict** – Escalates stakes or tension.
4. **Resolution** – Provides payoff and transitions to the next beat.

Designing shots around these beats ensures your visuals serve the narrative, not just aesthetics.

[📺 *Watch a quick breakdown of shot sequencing*](https://www.youtube.com/watch?v=y7si6iAo0V)
    """
)

import streamlit.components.v1 as components

if "copy_clicked" not in st.session_state:
    st.session_state.copy_clicked = False
if "last_copy_time" not in st.session_state:
    st.session_state.last_copy_time = 0.0

current_time = time.time()
if st.session_state.copy_clicked and (current_time - st.session_state.last_copy_time > 3):
    st.session_state.copy_clicked = False

button_text = "Copied ✅" if st.session_state.copy_clicked else "📤 Share With A Friend"

if st.button(button_text):
    st.session_state.copy_clicked = True
    st.session_state.last_copy_time = time.time()
    st.toast("Copied to clipboard!")
    st.balloons()
    components.html(
        "<script>navigator.clipboard.writeText(window.location.href);</script>", height=0
    )
