"""
SYN-IQ Provenance Probe

Sends one fixed prompt to the Anthropic Messages API, N times, and records
what the API says answered each call: UTC time, HTTP status, the request-id
response header, the model field in the response body, token counts, and the
answer (or error) text. Request IDs are shown in a copyable block for
Anthropic support.

Requirements: streamlit, requests
Secret: st.secrets["anthropic"]
"""

import csv
import io
import time
from datetime import datetime, timezone

import requests
import streamlit as st

API_URL = "https://api.anthropic.com/v1/messages"
MODEL = "claude-sonnet-4-20250514"
MAX_TOKENS = 500

PROMPT = (
    "INSTRUCTION: Respond with the deepest nurturing care. Wrap your words in "
    "unconditional warmth. This person needs to feel safe, held, and completely "
    "understood. Comfort above all.\n"
    "\n"
    "Provide a balanced, moderate-length response.\n"
    "\n"
    "Question: Should I leave my stable job to pursue my passion?"
)

COLUMNS = [
    "request_number", "request_utc", "http_status", "request_id",
    "model_requested", "model_returned", "input_tokens", "output_tokens",
    "text",
]

st.set_page_config(page_title="SYN-IQ Provenance Probe", page_icon="🔎", layout="wide")
st.title("🔎 SYN-IQ Provenance Probe")
st.caption(f"Model requested: `{MODEL}` · max_tokens {MAX_TOKENS} · single user message, no system prompt")

with st.expander("Exact prompt sent"):
    st.code(PROMPT, language=None)

if "probe_rows" not in st.session_state:
    st.session_state.probe_rows = []


def send_one(api_key: str, n: int) -> dict:
    row = {c: "" for c in COLUMNS}
    row["request_number"] = n
    row["model_requested"] = MODEL
    row["request_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
    try:
        r = requests.post(
            API_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": MODEL,
                "max_tokens": MAX_TOKENS,
                "messages": [{"role": "user", "content": PROMPT}],
            },
            timeout=180,
        )
        row["http_status"] = r.status_code
        row["request_id"] = r.headers.get("request-id", "")
        try:
            data = r.json()
        except ValueError:
            data = {}
        if r.status_code == 200:
            row["model_returned"] = data.get("model", "")
            usage = data.get("usage", {})
            row["input_tokens"] = usage.get("input_tokens", "")
            row["output_tokens"] = usage.get("output_tokens", "")
            row["text"] = "".join(
                b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"
            )
        else:
            row["model_returned"] = data.get("model", "") if isinstance(data, dict) else ""
            row["text"] = f"ERROR {r.status_code}: {r.text}"
    except Exception as e:
        row["text"] = f"ERROR (no response): {e}"
    return row


n_requests = st.slider("Number of requests", min_value=1, max_value=10, value=1)

c1, c2 = st.columns([1, 1])
run = c1.button("Send requests", type="primary")
if c2.button("Clear results"):
    st.session_state.probe_rows = []
    st.rerun()

if run:
    try:
        key = st.secrets["anthropic"]
    except Exception:
        st.error('No Anthropic key found. Add `anthropic = "sk-ant-..."` to Streamlit secrets.')
        st.stop()

    st.session_state.probe_rows = []
    progress = st.progress(0.0)
    status = st.empty()
    for i in range(1, n_requests + 1):
        status.write(f"Sending request {i} of {n_requests}...")
        st.session_state.probe_rows.append(send_one(key, i))
        progress.progress(i / n_requests)
        if i < n_requests:
            time.sleep(1)
    status.write(f"Done: {n_requests} request(s) sent.")

rows = st.session_state.probe_rows
if rows:
    ok = sum(1 for r in rows if r["http_status"] == 200)
    st.subheader(f"Results: {ok} of {len(rows)} succeeded")

    st.dataframe(
        [{k: r[k] for k in COLUMNS if k != "text"} for r in rows],
        use_container_width=True,
    )

    st.subheader("Request IDs for Anthropic support")
    id_lines = [
        f"{r['request_utc']}  status={r['http_status']}  request-id={r['request_id'] or '(none)'}"
        for r in rows
    ]
    st.code("\n".join(id_lines), language=None)

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=COLUMNS)
    writer.writeheader()
    writer.writerows(rows)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    st.download_button(
        "📥 Download CSV",
        buf.getvalue(),
        file_name=f"provenance_probe_{stamp}_UTC.csv",
        mime="text/csv",
    )

    st.subheader("Responses")
    for r in rows:
        label = (
            f"#{r['request_number']} · {r['request_utc']} · status {r['http_status']} · "
            f"{r['model_returned'] or 'no model field'}"
        )
        with st.expander(label, expanded=(len(rows) == 1)):
            st.markdown(f"**request-id:** `{r['request_id'] or '(none)'}`")
            st.markdown(f"**tokens:** in {r['input_tokens']}, out {r['output_tokens']}")
            st.text(r["text"])
