import io
import threading
import requests
import streamlit as st
from pathlib import Path

from comtext_sr_pseudonymizer import run_anonymization
import cyrtranslit
# --- Config & Setup ---
INPUT_FILE_PATH = Path("uploaded_input.conllu")
RESULTS_DIR = Path("results")
RESULTS_DIR.mkdir(exist_ok=True)

NLP_SERVICE_URL = "https://ICEF-NLP-PseudonymizerDemo.hf.space"

IGNORED_TAGS = {"REF", "LAW", "INST"}

VIBRANT_21 = [
    "#FF4444",  # red
    "#4488FF",  # blue
    "#44DD44",  # green
    "#FFD700",  # yellow
    "#FF44FF",  # magenta
    "#44FFFF",  # cyan
    "#FF8800",  # orange
    "#AA44FF",  # purple
    "#FF4488",  # pink
    "#00CC88",  # teal
    "#FFAA00",  # amber
    "#4444FF",  # indigo
    "#88FF44",  # lime
    "#FF6644",  # coral
    "#44FFAA",  # mint
    "#FF44AA",  # hot pink
    "#AAFFAA",  # light green
    "#AAAAFF",  # periwinkle
    "#FFAAAA",  # light red
    "#AAFFFF",  # light cyan
    "#FFDDAA",  # peach
]

def get_vibrant_color(tag, all_tags_list):
    try:
        idx = list(all_tags_list).index(tag)
        return VIBRANT_21[idx % len(VIBRANT_21)]
    except:
        return "#EEEEEE"

def parse_conllu_bytes(data: bytes):
    documents, found_tags, temp_tokens = [], set(), []
    current_doc = {"id": "Unknown", "sentences": []}

    def flush_sentence():
        nonlocal temp_tokens
        if temp_tokens:
            sent, i = [], 0
            while i < len(temp_tokens):
                word, tag = temp_tokens[i]
                if tag and tag.startswith("B-"):
                    t_type = tag.split("-")[-1]
                    ent = [word]; j = i + 1
                    while j < len(temp_tokens) and temp_tokens[j][1] == f"I-{t_type}":
                        ent.append(temp_tokens[j][0]); j += 1
                    if t_type not in IGNORED_TAGS:
                        found_tags.add(t_type)
                        sent.append((" ".join(ent), t_type))
                    else:
                        for w in ent:
                            sent.append((w, "O"))
                    i = j
                else:
                    sent.append((word, "O")); i += 1
            current_doc["sentences"].append(sent)
            temp_tokens = []

    for line in io.TextIOWrapper(io.BytesIO(data), encoding="utf-8"):
        line = line.strip()
        if line.startswith("# newdoc id"):
            flush_sentence()
            if current_doc["sentences"]: documents.append(current_doc)
            current_doc = {"id": line.split("=")[-1].strip(), "sentences": []}
        elif not line or line.startswith("#"):
            flush_sentence()
        else:
            parts = line.split("\t")
            if len(parts) >= 2:
                word, tag = parts[1], "O"
                if len(parts) >= 5 and parts[4] not in ["_", "O", ""]: tag = parts[4]
                elif len(parts) >= 3 and parts[2] not in ["_", "O", ""]: tag = parts[2]
                temp_tokens.append((word, tag))

    flush_sentence()
    if current_doc["sentences"]:
        documents.append(current_doc)

    return documents, sorted(list(found_tags))

def parse_conllu_path(file_path: Path):
    if not file_path.exists(): return [], []
    with open(file_path, "rb") as f:
        return parse_conllu_bytes(f.read())

def count_tags_in_doc(doc, all_tags):
    counts = {tag: 0 for tag in all_tags}
    for sent in doc['sentences']:
        for _, tag in sent:
            if tag in counts:
                counts[tag] += 1
    return counts

def warmup_nlp_service():
    try:
        requests.get(f"{NLP_SERVICE_URL}/health", timeout=300)
    except:
        pass

# --- UI Setup ---
st.set_page_config(page_title="COMtext.SR", layout="wide")

if 'warmed_up' not in st.session_state:
    st.session_state.warmed_up = True
    threading.Thread(target=warmup_nlp_service, daemon=True).start()

st.markdown("""
    <style>
    .view-container {
        min-height: 200px; border: 1px solid #ddd; padding: 25px;
        border-radius: 12px; background-color: white; color: black;
    }
    .st-key-execute_btn button, .st-key-execute_paste_btn button {
        background-color: #1565C0 !important;
        color: white !important;
        border: none !important;
        width: fit-content !important;
    }
    .st-key-execute_btn button:hover, .st-key-execute_paste_btn button:hover {
        background-color: #1976D2 !important;
    }
    .st-key-process_paste_btn button {
        background-color: #2E7D32 !important;
        color: white !important;
        border: none !important;
        width: fit-content !important;
    }
    .st-key-process_paste_btn button:hover {
        background-color: #388E3C !important;
    }
    [data-testid="stSidebar"] {
        min-width: 180px !important;
        max-width: 180px !important;
    }
    [data-testid="stSidebar"] [data-testid="stSidebarContent"] {
        padding: 1rem 0.6rem !important;
    }
    [data-testid="stSidebar"] .stCheckbox {
        margin: 0 !important;
        padding: 0 !important;
        min-height: 0 !important;
        line-height: 1 !important;
    }
    [data-testid="stSidebar"] .stCheckbox > label {
        padding: 3px 8px !important;
        border-radius: 10px !important;
        font-weight: bold !important;
        font-size: 12px !important;
        color: black !important;
        border: 1.5px solid #333 !important;
        display: inline-flex !important;
        align-items: center !important;
        gap: 5px !important;
        margin-bottom: 2px !important;
        width: fit-content !important;
        cursor: pointer !important;
    }
    [data-testid="stSidebar"] [data-testid="element-container"] {
        margin: 0 !important;
        padding: 0 !important;
        min-height: 0 !important;
        line-height: 1 !important;
    }
    [data-testid="stSidebar"] [data-testid="stVerticalBlock"] {
        gap: 0 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("COMtext.SR Pseudonymization Demo")

# ----------------------------------------------------------------
# INPUT ROW — upload left, paste right, side by side
# ----------------------------------------------------------------
col_upload, col_paste = st.columns(2)

with col_upload:
    st.subheader("📂 Upload CoNLL-U File")
    uploaded_file = st.file_uploader(
        "Upload CoNLL-U File",
        type=["conllu"],
        label_visibility="collapsed"
    )
    if uploaded_file:
        file_id = uploaded_file.file_id
        if st.session_state.get("file_id") != file_id:
            st.session_state.file_id = file_id
            st.session_state.manual_overrides = {}
            st.session_state.selected_id = None
            st.session_state.output_docs = None
            st.session_state.last_output_path = None
            st.session_state.nav_version = 0
            st.session_state.input_source = "upload"
            st.session_state.paste_conllu_bytes = None

        uploaded_bytes = uploaded_file.getvalue()
        upload_docs, upload_tags = parse_conllu_bytes(uploaded_bytes)

        output_tags = []
        if st.session_state.get("input_source") == "upload" and st.session_state.get("last_output_path"):
            _, output_tags = parse_conllu_path(st.session_state.last_output_path)
        upload_all_tags = sorted(list(set(upload_tags) | set(output_tags)))

        if st.session_state.get("input_source") == "upload" and st.session_state.selected_id is None and upload_docs:
            st.session_state.selected_id = upload_docs[0]['id']

        if st.button("🚀 EXECUTE PSEUDONYMIZATION", key="execute_btn"):
            st.session_state.input_source = "upload"
            st.session_state.input_docs = upload_docs
            st.session_state.all_tags = upload_all_tags
            st.session_state.selected_id = upload_docs[0]['id'] if upload_docs else None
            st.session_state.output_docs = None
            st.session_state.last_output_path = None
            st.session_state.nav_version = 0
            with st.spinner("Processing..."):
                with open(INPUT_FILE_PATH, "wb") as f:
                    f.write(uploaded_bytes)
                result = run_anonymization(str(INPUT_FILE_PATH), "results")
                if result is None:
                    st.warning("No entities found to pseudonymize.")
                else:
                    returned_path, _ = result
                    possible_paths = [Path(returned_path), RESULTS_DIR / returned_path, RESULTS_DIR / Path(returned_path).name]
                    found_path = next((p for p in possible_paths if p.exists()), None)
                    if found_path:
                        st.session_state.output_docs, output_tags_new = parse_conllu_path(found_path)
                        st.session_state.last_output_path = found_path
                        st.session_state.all_tags = sorted(
                            list(set(upload_all_tags) | set(output_tags_new))
                        )
                        st.success("Done.")

        if st.session_state.get("input_source") == "upload":
            st.session_state.input_docs = upload_docs
            st.session_state.all_tags = upload_all_tags

with col_paste:
    st.subheader("📝 Paste Legal Text")
    pasted_text = st.text_area(
        "Paste Serbian legal text here",
        height=200,
        label_visibility="collapsed",
        placeholder="Unesite pravni tekst ovde...",
        key="paste_input"
    )

    has_text = bool(pasted_text.strip())

    if has_text:
        process_clicked = st.button("🔬 PROCESS TEXT", key="process_paste_btn")
    else:
        st.button("🔬 PROCESS TEXT", key="process_paste_btn_disabled", disabled=True)
        process_clicked = False

    if process_clicked:
        if 'paste_doc_counter' not in st.session_state:
            st.session_state.paste_doc_counter = 1
        doc_id = f"doc_{st.session_state.paste_doc_counter}"
        text_to_send = cyrtranslit.to_latin(pasted_text.strip(), "sr")
        st.session_state.paste_doc_counter += 1
        st.session_state.output_docs = None
        st.session_state.last_output_path = None
        st.session_state.input_docs = []
        st.session_state.all_tags = []
        st.session_state.manual_overrides = {}
        st.session_state.selected_id = None
        st.session_state.nav_version = 0
        st.session_state.paste_conllu_bytes = None
        st.session_state.input_source = "paste"

        with st.spinner("Running NLP pipeline... (first run may take a minute to wake up)"):
            try:
                response = requests.post(
                    f"{NLP_SERVICE_URL}/process",
                    json={"text": text_to_send, "doc_id": doc_id},
                    timeout=300
                )
                response.raise_for_status()
                conllu_str = response.json()["conllu"]
                conllu_bytes = conllu_str.encode("utf-8")

                paste_docs, paste_tags = parse_conllu_bytes(conllu_bytes)

                st.session_state.manual_overrides = {}
                st.session_state.selected_id = paste_docs[0]['id'] if paste_docs else None
                st.session_state.nav_version = 0
                st.session_state.paste_conllu_bytes = conllu_bytes
                st.session_state.input_docs = paste_docs
                st.session_state.all_tags = sorted(list(set(paste_tags)))

                st.success(f"Processed — {len(paste_docs)} document(s), {len(paste_tags)} entity types found.")
            except requests.exceptions.Timeout:
                st.error("NLP service timed out — try again in 30 seconds.")
            except Exception as e:
                st.error(f"Error calling NLP service: {e}")

    if st.session_state.get("input_source") == "paste" and st.session_state.get("paste_conllu_bytes"):
        if st.button("🚀 EXECUTE PSEUDONYMIZATION", key="execute_paste_btn"):
            with st.spinner("Processing..."):
                with open(INPUT_FILE_PATH, "wb") as f:
                    f.write(st.session_state.paste_conllu_bytes)
                result = run_anonymization(str(INPUT_FILE_PATH), "results")
                if result is None:
                    st.warning("No entities found to pseudonymize.")
                else:
                    returned_path, _ = result
                    possible_paths = [Path(returned_path), RESULTS_DIR / returned_path, RESULTS_DIR / Path(returned_path).name]
                    found_path = next((p for p in possible_paths if p.exists()), None)
                    if found_path:
                        st.session_state.output_docs, output_tags_new = parse_conllu_path(found_path)
                        st.session_state.last_output_path = found_path
                        st.session_state.all_tags = sorted(
                            list(set(st.session_state.all_tags) | set(output_tags_new))
                        )
                        st.success("Done.")

# ----------------------------------------------------------------
# SHARED: SIDEBAR + VIEWER
# ----------------------------------------------------------------
input_docs = st.session_state.get("input_docs", [])
all_tags = st.session_state.get("all_tags", [])

if 'manual_overrides' not in st.session_state:
    st.session_state.manual_overrides = {}

tag_counts = {}
if input_docs and all_tags and st.session_state.get("selected_id"):
    doc_ids = [d['id'] for d in input_docs]
    if st.session_state.selected_id in doc_ids:
        curr_for_counts = next(d for d in input_docs if d['id'] == st.session_state.selected_id)
        tag_counts = count_tags_in_doc(curr_for_counts, all_tags)

def is_active(tag):
    if tag in st.session_state.manual_overrides:
        return st.session_state.manual_overrides[tag]
    return True

# --- Sidebar ---
with st.sidebar:
    st.write("### 🏷️ Entities")
    st.divider()

    if all_tags:
        for tag in all_tags:
            current_active = is_active(tag)
            count = tag_counts.get(tag, 0)
            has_entities = count > 0
            bg = get_vibrant_color(tag, all_tags) if (current_active and has_entities) else "transparent"

            checked = st.checkbox(
                f"{tag} ({count})",
                value=current_active,
                key=f"cb_{tag}"
            )
            st.markdown(f"""
                <style>
                .st-key-cb_{tag} label {{
                    background-color: {bg} !important;
                    {"opacity: 0.35 !important;" if not has_entities else ""}
                }}
                </style>
            """, unsafe_allow_html=True)

            if checked != current_active:
                st.session_state.manual_overrides[tag] = checked
                st.rerun()
    else:
        st.info("Upload a file or paste text to see entities.")

# --- Main viewer ---
if input_docs:
    doc_ids = [d['id'] for d in input_docs]

    if st.session_state.get("selected_id") not in doc_ids:
        st.session_state.selected_id = doc_ids[0]

    if 'nav_version' not in st.session_state:
        st.session_state.nav_version = 0

    st.divider()
    nav_left, nav_right = st.columns([2, 3])

    with nav_left:
        st.selectbox(
            "📄 Jump to Document",
            options=doc_ids,
            index=doc_ids.index(st.session_state.selected_id),
            key=f"doc_dropdown_{st.session_state.nav_version}",
            on_change=lambda: st.session_state.update({
                "selected_id": st.session_state[f"doc_dropdown_{st.session_state.nav_version}"],
                "nav_version": st.session_state.nav_version + 1
            })
        )

    with nav_right:
        if len(doc_ids) > 1:
            st.select_slider(
                "📄 Navigate Documents",
                options=doc_ids,
                value=st.session_state.selected_id,
                key=f"doc_slider_{st.session_state.nav_version}",
                on_change=lambda: st.session_state.update({
                    "selected_id": st.session_state[f"doc_slider_{st.session_state.nav_version}"],
                    "nav_version": st.session_state.nav_version + 1
                })
            )
        else:
            st.info("Only one document.")

    selected_id = st.session_state.selected_id
    curr_in = next(d for d in input_docs if d['id'] == selected_id)
    curr_out = None
    if st.session_state.get("output_docs"):
        curr_out = next((d for d in st.session_state.output_docs if d['id'] == selected_id), None)

    active_list = [t for t in all_tags if is_active(t)]
    l, r = st.columns(2)

    def render_doc(doc, tags, ref):
        if not doc: return "<p><i>No data.</i></p>"
        html = f"<div style='color:#888; font-size:0.8rem; margin-bottom:10px;'>ID: {doc['id']}</div>"
        for sent in doc['sentences']:
            line = ""
            for txt, tag in sent:
                if tag in tags:
                    line += f"<span style='background-color:{get_vibrant_color(tag, ref)}; padding:2px 4px; border-radius:3px; font-weight:bold;'>{txt}</span> "
                else:
                    line += f"{txt} "
            html += f"<p style='line-height:1.7; margin-bottom:18px;'>{line}</p>"
        return html

    with l:
        st.subheader("Source")
        st.markdown(f"<div class='view-container'>{render_doc(curr_in, active_list, all_tags)}</div>", unsafe_allow_html=True)
    with r:
        st.subheader("Output")
        if curr_out:
            st.markdown(f"<div class='view-container'>{render_doc(curr_out, active_list, all_tags)}</div>", unsafe_allow_html=True)
        else:
            st.info("Run EXECUTE PSEUDONYMIZATION.")