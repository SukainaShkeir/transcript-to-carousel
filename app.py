import os
import io
import zipfile
import streamlit as st

# 1. Online: copy Streamlit secrets into the environment BEFORE loading the agents
#    (on your laptop there are no secrets, so .env is used instead)
try:
    for key, value in st.secrets.items():
        if isinstance(value, str):
            os.environ[key] = value
except Exception:
    pass

from guards import input_guard
from agents.content_writer import content_writer
from agents.prompt_writer import prompt_writer
from agents.designer import designer

st.set_page_config(page_title="Transcript to Carousel", page_icon="🎠")
st.title("Transcript → Instagram Carousel")


# Arabic right-to-left, English left-to-right
def show(text):
    st.markdown(f"<div dir='auto'>{text}</div>", unsafe_allow_html=True)


# 2. Password (only if APP_PASSWORD is set)
password = os.getenv("APP_PASSWORD")
if password and st.text_input("Password", type="password") != password:
    st.info("Enter the password to use the app.")
    st.stop()

# 3. Input
transcript = st.text_area("Paste the video transcript", height=250)
uploaded = st.file_uploader("...or upload a .txt file", type="txt")
if uploaded:
    transcript = uploaded.read().decode("utf-8")

# 4. Generate slides (text only)
if st.button("Generate slides"):
    state = {"transcript": transcript}
    try:
        input_guard(state)
    except ValueError as e:
        st.error(f"Blocked: {e}")
        st.stop()

    with st.spinner("Writing slides and prompts..."):
        state.update(content_writer(state))
        state.update(prompt_writer(state))

    st.session_state["state"] = state

# 5. Show slides + approval
if "state" in st.session_state:
    s = st.session_state["state"]

    st.subheader(f"Slides ({s['language']})")
    for i, text in enumerate(s["slide_texts"], 1):
        show(f"<b>{i}.</b> {text}")
    st.subheader("Caption")
    show(s["caption"])

    st.divider()

    # Human approval = this button
    if st.button(f"Approve & create {len(s['slide_texts'])} images"):
        with st.spinner("Creating and reviewing images... (1–3 minutes)"):
            s.update(designer(s))
        st.session_state["state"] = s

    # 6. Show images + download
    if s.get("image_paths"):
        if s["flagged_slides"]:
            st.warning(f"Needs human review: slides {s['flagged_slides']}")
        else:
            st.success("All slides passed review.")

        cols = st.columns(3)
        for i, path in enumerate(s["image_paths"]):
            with cols[i % 3]:
                st.image(path, caption=f"Slide {i + 1}")

        # Zip: all images + a text file with slides and caption
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as z:
            for path in s["image_paths"]:
                z.write(path, os.path.basename(path))
            texts = "\n\n".join(f"Slide {i}: {t}" for i, t in enumerate(s["slide_texts"], 1))
            z.writestr("texts.txt", f"{texts}\n\nCaption:\n{s['caption']}")

        st.download_button("Download carousel (.zip)", buffer.getvalue(), "carousel.zip", "application/zip")