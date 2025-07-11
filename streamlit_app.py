"""Scene & Shot Planner – Streamlit App
Author: ChatGPT (OpenAI)
Updated: 2025-07-11

Features
--------
* Scene‑based planner: Title + Hook, Problem, Conflict, Resolution
* Four‑shot cycle per scene (Wide → Medium Shot → Close‑Up → user‑choice)
* Inspiration image preview, autosave cache, high‑quality JPEG & PDF export
* **New footer**: explains the classic shot sequence and story‑beat structure,
  with a link to a detailed YouTube breakdown.
"""

import json
import os
import io
from typing import List, Dict, Any
import time
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

st.set_page_config(page_title="🎬 Scene & Shot Planner", page_icon="🎬", layout="wide")
st.title("🎬 Scene & Shot Planner")

CACHE_FILE = "shot_cache.json"
SHOT_CYCLE = ["Wide", "Medium Shot", "Close‑Up", None]

# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------

def load_cached() -> List[Dict[str, Any]]:
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as fp:
                data = json.load(fp)
                for sc in data:
                    for sh in sc.get("shots", []):
                        sh.setdefault("file", None)
                return data
        except Exception:
            pass
    return []

def save_cache(scenes: List[Dict[str, Any]]):
    sanitized = []
    for sc in scenes:
        sc_copy = sc.copy()
        sc_copy["shots"] = [ {k: v for k, v in sh.items() if k != "file"} for sh in sc["shots"] ]
        sanitized.append(sc_copy)
    with open(CACHE_FILE, "w") as fp:
        json.dump(sanitized, fp, indent=2)

# ---------------------------------------------------------------------------
# Session init
# ---------------------------------------------------------------------------

if "scenes" not in st.session_state:
    st.session_state.scenes = load_cached()


def make_scene(idx: int) -> Dict[str, Any]:
    shots = [
        {"id": i + 1, "type": t, "alt_type": "Wide" if t is None else None, "description": "", "file": None}
        for i, t in enumerate(SHOT_CYCLE)
    ]
    return {"id": idx + 1, "title": "", "hook": "", "problem": "", "conflict": "", "resolution": "", "shots": shots}

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
        save_cache(st.session_state.scenes)

st.divider()

# ---------------------------------------------------------------------------
# Scene Loop
# ---------------------------------------------------------------------------

for scene_idx, scene in enumerate(st.session_state.scenes):
    with st.container():
        st.subheader(f"Scene {scene['id']}")
        scene["title"] = st.text_input("Scene Title", scene["title"], key=f"title_{scene_idx}")
        scene["hook"] = st.text_input("Hook", scene["hook"], key=f"hook_{scene_idx}")
        scene["problem"] = st.text_input("Problem", scene["problem"], key=f"prob_{scene_idx}")
        scene["conflict"] = st.text_input("Conflict", scene["conflict"], key=f"conf_{scene_idx}")
        scene["resolution"] = st.text_input("Resolution", scene["resolution"], key=f"res_{scene_idx}")

        st.markdown("**Shots** (4 per scene)")
        for shot_idx, shot in enumerate(scene["shots"]):
            with st.expander(f"Shot {shot['id']}"):
                if shot["type"] is None:
                    shot["alt_type"] = st.selectbox("Shot Size", ["Wide", "Medium Shot", "Close‑Up"],
                        index=["Wide", "Medium Shot", "Close‑Up"].index(shot["alt_type"]), key=f"stype_{scene_idx}_{shot_idx}")
                    shot_type_display = shot["alt_type"]
                else:
                    shot_type_display = shot["type"]
                    st.markdown(f"**Type:** {shot_type_display}")

                shot["description"] = st.text_area("Description / Action", shot["description"], key=f"sdesc_{scene_idx}_{shot_idx}")

                shot["file"] = st.file_uploader("Inspiration Image (optional)", type=["png", "jpg", "jpeg"], key=f"sfile_{scene_idx}_{shot_idx}")
                if shot["file"] is not None:
                    shot["file"].seek(0)
                    st.image(shot["file"], caption=f"Scene {scene['id']} – Shot {shot['id']} ({shot_type_display})", use_column_width=True)
        st.divider()

# Save cache each run
save_cache(st.session_state.scenes)

# ---------------------------------------------------------------------------
# Export helpers (JPEG quality max, PDF via Pillow)
# ---------------------------------------------------------------------------

def build_lines(scenes):
    lines = []
    for sc in scenes:
        lines.append(f"Scene {sc['id']}: {sc['title']}")
        lines.append(f"  Hook: {sc['hook']}")
        lines.append(f"  Problem: {sc['problem']}")
        lines.append(f"  Conflict: {sc['conflict']}")
        lines.append(f"  Resolution: {sc['resolution']}")
        for sh in sc['shots']:
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
# Downloads
# ---------------------------------------------------------------------------

if st.session_state.scenes:
    st.header("Download Plan")
    pdf_bytes = scenes_to_pdf(st.session_state.scenes)
    st.download_button("📄 PDF", data=pdf_bytes, file_name="scene_shot_plan.pdf", mime="application/pdf")

    jpeg_bytes = scenes_to_jpeg(st.session_state.scenes)
    st.download_button("🖼️ JPEG", data=jpeg_bytes, file_name="scene_shot_plan.jpg", mime="image/jpeg")

# ---------------------------------------------------------------------------
# Educational footer
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
# 7️⃣  Bottom image (optional) ------------------------------------------------
st.image("8K2A2685.jpg", use_container_width=True, caption="Powered by Hill Technologies, LLC")

# 🎉 Share With A Friend Button ----------------------------------------------
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
        """
        <script>
        navigator.clipboard.writeText(window.location.href);
        </script>
        """,
        height=0,
    )