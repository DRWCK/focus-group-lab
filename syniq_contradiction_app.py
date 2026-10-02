"""
SYN-IQ Contradiction Detector V1: Streamlit app
Upload a session (Focus Group Lab CSV or docx, or the Ensemble Chat transcript),
optionally a source text, press Run, download the results.

The measurement code lives in syniq_contradiction_detector_v1.py, which must
sit beside this file in the repo. This file is only the front end.

Deployment notes (Streamlit Community Cloud):
- requirements.txt installs the CPU build of torch. The default CUDA build is
  several GB and can fail to install on Cloud.
- The model downloads on first use and is cached for the life of the app.
- Set app_password in the app's Secrets. There is no built-in default.
"""

import io
import os
import tempfile
import time
import zipfile

import streamlit as st

import syniq_contradiction_detector_v1 as det

st.set_page_config(page_title="SYN-IQ Contradiction Detector V1", page_icon="⚖️",
                   layout="wide")

MODELS = {
    "Fast: nli-deberta-v3-xsmall": "cross-encoder/nli-deberta-v3-xsmall",
    "Accurate: nli-deberta-v3-base": "cross-encoder/nli-deberta-v3-base",
    "Stub (TEST ONLY, numbers meaningless)": "stub",
}

# ----------------------------------------------------------------- password --
def check_password() -> bool:
    if st.session_state.get("ok"):
        return True
    pw_secret = st.secrets.get("app_password") if hasattr(st, "secrets") else None
    if not pw_secret:
        st.error("Set app_password in this app's Secrets to use it.")
        return False
    pw = st.text_input("Password", type="password")
    if pw and pw == pw_secret:
        st.session_state.ok = True
        st.rerun()
    elif pw:
        st.error("Incorrect password")
    return False


@st.cache_resource(show_spinner=False)
def get_backend(model_id: str):
    if model_id == "stub":
        return det.StubBackend()
    return det.HFBackend(model_id)


def save_upload(up, folder) -> str:
    path = os.path.join(folder, up.name)
    with open(path, "wb") as f:
        f.write(up.getbuffer())
    return path


def zip_folder(folder: str) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for name in sorted(os.listdir(folder)):
            z.write(os.path.join(folder, name), arcname=name)
    return buf.getvalue()


# --------------------------------------------------------------------- page --
if not check_password():
    st.stop()

st.title("⚖️ SYN-IQ Contradiction Detector V1")
st.caption("Claim-level contradiction between agents, within agents across turns, "
           "against the conductor, and against a source text. Unvalidated: label the "
           "sample sheets before reporting any figure.")

c1, c2 = st.columns(2)
with c1:
    session_up = st.file_uploader("Session file (.docx, .csv, .txt)",
                                  type=["docx", "csv", "txt"])
with c2:
    source_up = st.file_uploader("Source text, optional (e.g. lyrics)",
                                 type=["docx", "txt"])

with st.expander("Settings", expanded=True):
    s1, s2, s3, s4 = st.columns(4)
    with s1:
        model_label = st.selectbox("Model", list(MODELS.keys()), index=0)
    with s2:
        thr = st.number_input("Threshold", 0.1, 0.99, 0.5, 0.05,
                              help="Placeholder until set from human labels.")
    with s3:
        min_overlap = st.number_input("Min shared words", 0, 5, 1, 1,
                                      help="0 scores every pair (slow, most complete). "
                                           "1 skips pairs with no shared content word "
                                           "(much faster, can miss paraphrased contradictions).")
    with s4:
        src_rounds = st.text_input("Source applies to rounds", "",
                                   help="e.g. 10-16. Blank means all rounds.")
    lab_n = st.slider("Label sample size (pairs)", 40, 200, 100, 20)

if "stub" in MODELS[model_label]:
    st.warning("Stub backend selected. Use it only to check the app works. "
               "Its numbers mean nothing.")

run = st.button("▶️ Run detector", type="primary", disabled=session_up is None)

if run and session_up is not None:
    work = tempfile.mkdtemp(prefix="syniq_cd_")
    sess_path = save_upload(session_up, work)
    src_path = save_upload(source_up, work) if source_up else None

    turns, fmt = det.load_session(sess_path)
    st.info(f"Parsed **{len(turns)} turns** ({fmt}), "
            f"{sum(t.is_error for t in turns)} error turns excluded.")

    model_id = MODELS[model_label]
    with st.spinner("Loading model (first run downloads it, a few minutes)..."):
        try:
            backend = get_backend(model_id)
        except Exception as e:
            st.error(f"Model failed to load: {e}\n\nTry the other model, or check "
                     "the app logs. If memory is exceeded, use the Fast model.")
            st.stop()

    status = st.empty()
    t0 = time.time()

    def progress(n):
        status.write(f"Evaluated **{n:,}** sentence pairs ... "
                     f"{time.time() - t0:,.0f}s elapsed")

    scorer = det.CachedScorer(backend, on_progress=progress)
    source = det.load_source(src_path) if src_path else None
    live, cross, selfp, trows, cond, ground, shared = det.analyze(
        turns, scorer, source, thr, int(min_overlap), det.parse_rounds(src_rounds))

    out_dir = os.path.join(work, "results")
    meta = {"tool_version": det.TOOL_VERSION + "+app", "session_file": session_up.name,
            "session_format": fmt, "source_file": source_up.name if source_up else None,
            "source_rounds": src_rounds or None, "backend": backend.name,
            "threshold": thr, "min_overlap": int(min_overlap),
            "n_turns": len(turns), "n_error_turns": len(turns) - len(live),
            "n_nli_calls": len(scorer.cache),
            "run_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    summary_path = det.write_outputs(out_dir, meta, live, cross, selfp, trows, cond,
                                     ground, shared, lab_n, thr)
    status.write(f"Done: {len(scorer.cache):,} pairs in {time.time() - t0:,.0f}s")

    st.session_state.result_summary = open(summary_path).read()
    st.session_state.result_zip = zip_folder(out_dir)
    st.session_state.result_name = os.path.splitext(session_up.name)[0] + "_contradiction.zip"

if st.session_state.get("result_zip"):
    st.download_button("📥 Download all results (zip)", st.session_state.result_zip,
                       file_name=st.session_state.result_name, mime="application/zip")
    st.markdown(st.session_state.result_summary)
