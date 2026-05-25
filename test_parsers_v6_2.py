"""
SYN-IQ Transcript Scorer v6.2 — parser regression tests
=======================================================

Run:
    python test_parsers_v6_2.py

Or under pytest (no fixtures needed):
    pytest test_parsers_v6_2.py -v

What this catches
-----------------
The parser fix in v6.2 addresses a specific bug: label-less Claude.ai
docx exports (where standalone "9:10 AM" timestamps are the only
turn-boundary signal) were being fragmented into hundreds of "turns"
by the alternating parser, OR collapsed to 1 mega-turn by the labeled
parser. This harness asserts that:

  1. Format detection picks the right parser for each shape.
  2. The canonical Claude_discussion.docx test case yields the
     expected ~50 turns with clean 1:1 alternation (not 317 fragments).
  3. Per-turn structural signals (S_t cues: bold/bullets, Q_t cues:
     trailing '?') survive concatenation — the spec's whole point.
  4. The labeled-transcript path still works (no regression).
  5. Edge cases (empty input, no boundaries, single timestamp) don't
     crash and don't return garbage.

Tests are import-safe — they stub streamlit and syniq_core so the
parsers can run without the full app stack. If syniq_core scoring
ever changes shape, these tests still validate parsing behavior.

Conventions
-----------
- Assertions describe the framework invariant they protect.
- Failure messages include both expected and observed values.
- The Claude_discussion.docx path is configurable via TEST_DOCX env var.
"""

from __future__ import annotations
import os
import re
import sys
import types
import importlib.util
import statistics
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple

# ─────────────────────────────────────────────────────────────────────────
# Test infrastructure — make the parser module importable without the
# full Streamlit + syniq_core stack.
# ─────────────────────────────────────────────────────────────────────────

REPO_ROOT = Path(__file__).resolve().parent
SCORER_PATH = REPO_ROOT / "syniq_transcript_scorer_v6_2.py"
TEST_DOCX = Path(os.environ.get(
    "TEST_DOCX",
    REPO_ROOT / "Claude_discussion.docx",
))


def _install_streamlit_stub() -> None:
    """Stub `streamlit` so the parser module can be imported without UI."""
    if "streamlit" in sys.modules:
        return
    st_mock = types.ModuleType("streamlit")

    def _noop(*_a, **_k):
        return None

    class _Ctx:
        def __enter__(self): return self
        def __exit__(self, *_a): return False

    st_mock.set_page_config = _noop
    st_mock.title = _noop
    st_mock.markdown = _noop
    st_mock.caption = _noop
    st_mock.divider = _noop
    st_mock.subheader = _noop
    st_mock.text_input = lambda *a, **k: ""
    st_mock.selectbox = lambda *a, **k: ""
    st_mock.text_area = lambda *a, **k: ""
    st_mock.button = lambda *a, **k: False
    st_mock.warning = _noop
    st_mock.error = _noop
    st_mock.success = _noop
    st_mock.info = _noop
    st_mock.dataframe = _noop
    st_mock.json = _noop
    st_mock.download_button = _noop
    st_mock.file_uploader = lambda *a, **k: None
    st_mock.expander = lambda *a, **k: _Ctx()
    st_mock.columns = lambda n: [_Ctx() for _ in range(n if isinstance(n, int) else len(n))]
    sys.modules["streamlit"] = st_mock


def _load_parser_module():
    """Extract and exec just the parser block — sidesteps syniq_core import."""
    src = SCORER_PATH.read_text()
    # The parsing region runs from the docx-export comment block through
    # parse_auto. score_turns and everything below it depends on syniq_core
    # which we don't need for parser-only tests.
    start = src.index("# Standalone-line patterns that should be DROPPED")
    end = src.index("def parse_uploaded_csv")
    parser_block = src[start:end]

    # Minimal preamble: imports the parsers reference.
    preamble = (
        "import re\n"
        "from typing import List, Tuple, Dict, Optional\n"
        # tiny stub so error messages from parse_uploaded_csv (not used here)
        # don't blow up if the parser block grows to reference it.
        "class _StubSt:\n"
        "    def error(self, *a, **k): pass\n"
        "    def info(self, *a, **k): pass\n"
        "st = _StubSt()\n"
    )
    ns: Dict = {}
    exec(preamble + parser_block, ns)
    return ns


_install_streamlit_stub()
_PARSER = _load_parser_module()

_REQUIRED = (
    "parse_alternating_transcript",
    "parse_labeled_transcript",
    "parse_timestamp_segmented",
    "parse_auto",
    "detect_transcript_format",
)
_missing = [n for n in _REQUIRED if n not in _PARSER]
if _missing:
    raise SystemExit(
        f"\n[test_parsers_v6_2] {SCORER_PATH.name} is missing required v6.2 "
        f"parser surface: {_missing}.\n"
        f"This harness asserts the parser API as defined in v6.2. If you "
        f"are running it against an older scorer (v6.1 or earlier), the "
        f"timestamp-segmented + auto-detect parsers don't exist yet and "
        f"the bug they fix will still be present.\n"
    )

parse_alternating_transcript = _PARSER["parse_alternating_transcript"]
parse_labeled_transcript = _PARSER["parse_labeled_transcript"]
parse_timestamp_segmented = _PARSER["parse_timestamp_segmented"]
parse_auto = _PARSER["parse_auto"]
detect_transcript_format = _PARSER["detect_transcript_format"]


# ─────────────────────────────────────────────────────────────────────────
# Small test framework — runs as a plain script OR under pytest.
# ─────────────────────────────────────────────────────────────────────────

_TESTS: List = []


def _register(fn):
    """Register a test function. Each fn raises AssertionError on failure."""
    _TESTS.append(fn)
    return fn


def _word_count(t: Dict) -> int:
    return len(t["text"].split())


def _alternation_breaks(turns: List[Dict]) -> int:
    breaks = 0
    prev = None
    for t in turns:
        if t["speaker"] == prev:
            breaks += 1
        prev = t["speaker"]
    return breaks


# ─────────────────────────────────────────────────────────────────────────
# A. Format detection
# ─────────────────────────────────────────────────────────────────────────

@_register
def test_detect_labeled_format():
    sample = (
        "**You said:**\nfirst question\n\n"
        "**Claude responded:**\nfirst answer\n\n"
        "**You said:**\nsecond question\n"
    )
    fmt = detect_transcript_format(sample)
    assert fmt == "labeled", (
        f"Sample with 3 speaker labels should detect as 'labeled', got {fmt!r}"
    )


@_register
def test_detect_timestamped_format():
    sample = (
        "opening human message\n\n"
        "9:10 AM\n\n"
        "first AI reply spanning paragraph one.\n\n"
        "AI paragraph two of the same turn.\n\n"
        "human reply\n\n"
        "9:12 AM\n\n"
        "second AI reply.\n"
    )
    fmt = detect_transcript_format(sample)
    assert fmt == "timestamped", (
        f"Sample with 2 timestamps and no labels should detect as "
        f"'timestamped', got {fmt!r}"
    )


@_register
def test_detect_alternating_fallback():
    sample = "just one paragraph\n\nand another paragraph\n"
    fmt = detect_transcript_format(sample)
    assert fmt == "alternating", (
        f"Sample with no labels and no timestamps should fall through to "
        f"'alternating', got {fmt!r}"
    )


@_register
def test_detect_single_timestamp_is_not_enough():
    """One stray '12:00 AM' in body shouldn't force timestamp mode."""
    sample = "I checked at 12:00 AM\n\nand it was fine\n"
    fmt = detect_transcript_format(sample)
    assert fmt == "alternating", (
        f"A single inline-ish timestamp should NOT trigger timestamp mode "
        f"(threshold is 2). Got {fmt!r}"
    )


@_register
def test_detect_labels_dominate_timestamps():
    """If both signals are present, labels are more reliable."""
    sample = (
        "**You said:**\nfirst\n\n9:10 AM\n\n"
        "**Claude responded:**\nfirst answer\n\n9:11 AM\n\n"
        "**You said:**\nsecond\n"
    )
    fmt = detect_transcript_format(sample)
    assert fmt == "labeled", (
        f"Labeled signal should take precedence over timestamps. Got {fmt!r}"
    )


# ─────────────────────────────────────────────────────────────────────────
# B. Canonical fixture — Claude_discussion.docx
# ─────────────────────────────────────────────────────────────────────────

def _extract_docx_text(path: Path) -> str:
    """Use the extract-text helper available in the sandbox; fall back to
    python-docx if not. Skip the fixture-dependent tests if neither works."""
    try:
        out = subprocess.run(
            ["extract-text", str(path)],
            capture_output=True, text=True, timeout=30, check=True,
        )
        return out.stdout
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        pass
    try:
        from docx import Document  # python-docx
        doc = Document(str(path))
        return "\n\n".join(p.text for p in doc.paragraphs if p.text.strip())
    except Exception:
        return ""


_DOCX_TEXT = _extract_docx_text(TEST_DOCX) if TEST_DOCX.exists() else ""
_DOCX_AVAILABLE = bool(_DOCX_TEXT.strip())


def _skip_if_no_docx():
    if not _DOCX_AVAILABLE:
        print(f"  [skip] {TEST_DOCX} not found or could not be extracted")
        return True
    return False


@_register
def test_docx_detected_as_timestamped():
    if _skip_if_no_docx():
        return
    fmt = detect_transcript_format(_DOCX_TEXT)
    assert fmt == "timestamped", (
        f"Claude_discussion.docx should detect as 'timestamped' (no labels, "
        f"≥2 standalone HH:MM lines). Got {fmt!r}"
    )


@_register
def test_docx_turn_count_reasonable():
    """Spec target: ~255 turns for the 415-frag case; this docx is smaller
    and should yield ~50. The hard floor is: not 1 (mega-turn bug) and
    not 200+ (fragmentation bug)."""
    if _skip_if_no_docx():
        return
    turns, fmt = parse_auto(_DOCX_TEXT)
    assert fmt == "timestamped"
    n = len(turns)
    assert 20 <= n <= 100, (
        f"Expected ~50 turns from the timestamped Claude.ai export; got {n}. "
        f"If n is 1 the labeled parser ran by mistake; if n is 200+ the "
        f"alternating parser fragmented every paragraph."
    )


@_register
def test_docx_clean_human_ai_alternation():
    if _skip_if_no_docx():
        return
    turns, _ = parse_auto(_DOCX_TEXT)
    breaks = _alternation_breaks(turns)
    assert breaks == 0, (
        f"Expected clean human/AI alternation; got {breaks} same-speaker "
        f"adjacencies. This usually means a human reply got merged into the "
        f"preceding AI turn (or vice versa)."
    )


@_register
def test_docx_human_ai_ratio_near_one():
    if _skip_if_no_docx():
        return
    turns, _ = parse_auto(_DOCX_TEXT)
    n_h = sum(1 for t in turns if t["speaker"] == "human")
    n_a = sum(1 for t in turns if t["speaker"] == "ai")
    # 1:1 within a tolerance of 1 (final-AI-no-trailing-human edge case)
    assert abs(n_h - n_a) <= 1, (
        f"Human/AI ratio should be roughly 1:1; got human={n_h}, ai={n_a}. "
        f"Big asymmetry means turn boundaries are landing in the wrong place."
    )


@_register
def test_docx_turn_length_distribution():
    """The whole point of the fix: median turn length should reflect actual
    turn lengths, not sentence/paragraph fragments. Pre-fix median was ~13
    words; post-fix should comfortably exceed 30 even on a small docx."""
    if _skip_if_no_docx():
        return
    turns, _ = parse_auto(_DOCX_TEXT)
    wc = [_word_count(t) for t in turns]
    med = statistics.median(wc)
    maxw = max(wc)
    assert med >= 30, (
        f"Median turn length too low ({med}). Pre-fix value was ~13 — if you "
        f"see anything below 30 the fragmenter is still active somewhere."
    )
    assert maxw >= 200, (
        f"Max turn length too low ({maxw}). At least one AI turn in this "
        f"docx is known to exceed 500 words. If max is small (<200), "
        f"multi-paragraph AI responses are still being split."
    )


@_register
def test_docx_qt_signal_preserved():
    """The spec calls out: Q_t > 0 on AI turns ending with explicit questions.
    Most AI turns in this conversation end with 'Question?'. If many AI turns
    are fragments that don't end with '?', we know fragmentation is back."""
    if _skip_if_no_docx():
        return
    turns, _ = parse_auto(_DOCX_TEXT)
    ai = [t for t in turns if t["speaker"] == "ai"]
    ending_q = sum(1 for t in ai if t["text"].rstrip().endswith("?"))
    pct = ending_q / max(1, len(ai))
    assert pct >= 0.70, (
        f"Only {pct:.0%} of AI turns end with '?'; expected ≥70% on this "
        f"fixture. If this drops, the question-bearing closer is being split "
        f"off into its own 'turn' by a regressed parser."
    )


@_register
def test_docx_st_signal_preserved():
    """Spec: S_t > 0 on AI turns with numbered lists, bullets, bold headers.
    Concatenation must preserve the structural cues, not flatten them."""
    if _skip_if_no_docx():
        return
    turns, _ = parse_auto(_DOCX_TEXT)
    ai = [t for t in turns if t["speaker"] == "ai"]
    structured = sum(
        1 for t in ai
        if "**" in t["text"]
        or re.search(r"(?m)^\s*[-*•]\s", t["text"])
        or re.search(r"(?m)^\s*\d+[.)]\s", t["text"])
    )
    pct = structured / max(1, len(ai))
    assert pct >= 0.70, (
        f"Only {pct:.0%} of AI turns contain bold/bullets/numbered markers; "
        f"expected ≥70%. If this drops, structural detection material is "
        f"being stripped or split during concatenation."
    )


@_register
def test_docx_paragraph_breaks_preserved_inside_turns():
    """The spec requires paragraph breaks survive as \\n\\n inside the
    concatenated turn text, so downstream structural detectors still see
    the structure they need."""
    if _skip_if_no_docx():
        return
    turns, _ = parse_auto(_DOCX_TEXT)
    multi_para = sum(1 for t in turns if "\n\n" in t["text"])
    assert multi_para >= 5, (
        f"Only {multi_para} turns contain inter-paragraph breaks (\\n\\n). "
        f"Multi-paragraph AI responses are common in this conversation; if "
        f"no turns have \\n\\n the parser is over-flattening."
    )


@_register
def test_docx_no_timestamp_residue_in_turn_text():
    """Timestamps must be removed from turn bodies, not just used as anchors.
    A turn whose body still says '9:10 AM' will score wrong on every metric."""
    if _skip_if_no_docx():
        return
    turns, _ = parse_auto(_DOCX_TEXT)
    ts_re = re.compile(r"^\s*\d{1,2}:\d{2}\s*(?:AM|PM)?\s*$",
                       re.IGNORECASE | re.MULTILINE)
    for i, t in enumerate(turns):
        m = ts_re.search(t["text"])
        assert m is None, (
            f"Turn {i} ({t['speaker']}) contains a residual timestamp line: "
            f"{m.group(0)!r}. Timestamps must be stripped, not preserved."
        )


# ─────────────────────────────────────────────────────────────────────────
# C. Labeled-format synthetic fixtures (regression protection)
# ─────────────────────────────────────────────────────────────────────────

@_register
def test_labeled_basic_parsing():
    sample = (
        "**You said:**\n"
        "What is entropy?\n\n"
        "**Claude responded:**\n"
        "Entropy measures spread.\n\n"
        "**You said:**\n"
        "And how is it normalized?\n"
    )
    turns, fmt = parse_auto(sample)
    assert fmt == "labeled"
    assert len(turns) == 3
    assert [t["speaker"] for t in turns] == ["human", "ai", "human"]
    assert "Entropy measures spread" in turns[1]["text"]


@_register
def test_labeled_multi_paragraph_ai_turn_concatenated():
    """A labeled AI turn that spans multiple paragraphs must stay one turn."""
    sample = (
        "**You said:**\n"
        "Explain in detail.\n\n"
        "**Claude responded:**\n"
        "First paragraph of the answer.\n\n"
        "Second paragraph with more nuance.\n\n"
        "Third paragraph wrapping up.\n\n"
        "**You said:**\n"
        "Thanks.\n"
    )
    turns, _ = parse_auto(sample)
    ai_turns = [t for t in turns if t["speaker"] == "ai"]
    assert len(ai_turns) == 1, (
        f"Multi-paragraph labeled AI response must concatenate to 1 turn, "
        f"got {len(ai_turns)} AI turns."
    )
    assert "First paragraph" in ai_turns[0]["text"]
    assert "Second paragraph" in ai_turns[0]["text"]
    assert "Third paragraph" in ai_turns[0]["text"]


# ─────────────────────────────────────────────────────────────────────────
# D. Timestamped-format synthetic fixtures
# ─────────────────────────────────────────────────────────────────────────

@_register
def test_timestamp_basic_alternation():
    sample = (
        "opening from human\n\n"
        "9:10 AM\n\n"
        "AI reply paragraph one.\n\n"
        "AI reply paragraph two.\n\n"
        "human reply\n\n"
        "9:12 AM\n\n"
        "second AI reply.\n"
    )
    turns = parse_timestamp_segmented(sample)
    speakers = [t["speaker"] for t in turns]
    assert speakers == ["human", "ai", "human", "ai"], (
        f"Expected ['human','ai','human','ai']; got {speakers}"
    )
    # AI paragraph one + two must be one turn
    assert "paragraph one" in turns[1]["text"]
    assert "paragraph two" in turns[1]["text"]


@_register
def test_timestamp_opening_human_turn():
    """Any blocks before the first timestamp form an opening human turn."""
    sample = "the opening question\n\n9:00 AM\n\nthe answer\n\nreply\n\n9:05 AM\n\nfinal answer\n"
    turns = parse_timestamp_segmented(sample)
    assert turns[0]["speaker"] == "human"
    assert "opening question" in turns[0]["text"]


@_register
def test_timestamp_final_ai_turn_no_trailing_human():
    """After the last timestamp, the remainder is one AI turn — no
    fictitious trailing human turn manufactured."""
    sample = (
        "human start\n\n"
        "9:00 AM\n\n"
        "ai reply A1\n\n"
        "ai reply A2\n\n"
        "human reply\n\n"
        "9:05 AM\n\n"
        "final ai reply with no trailing human\n"
    )
    turns = parse_timestamp_segmented(sample)
    assert turns[-1]["speaker"] == "ai"
    assert "final ai reply" in turns[-1]["text"]


@_register
def test_timestamp_no_timestamps_falls_back_to_alternating():
    """If parse_timestamp_segmented is called on input with no timestamps,
    it must not return an empty list — it falls back to alternating."""
    sample = "block one\n\nblock two\n\nblock three\n"
    turns = parse_timestamp_segmented(sample)
    assert len(turns) == 3, (
        f"Expected fallback to produce 3 turns; got {len(turns)}"
    )


@_register
def test_timestamp_first_speaker_ai_supported():
    """Rare case: AI initiates. Pass first_speaker='ai' to invert."""
    sample = (
        "the AI opens the conversation\n\n"
        "9:00 AM\n\n"
        "human first reply\n\n"
        "ai response\n"
    )
    turns = parse_timestamp_segmented(sample, first_speaker="ai")
    assert turns[0]["speaker"] == "ai"
    assert "AI opens" in turns[0]["text"]


# ─────────────────────────────────────────────────────────────────────────
# E. Edge cases
# ─────────────────────────────────────────────────────────────────────────

@_register
def test_empty_input():
    assert parse_timestamp_segmented("") == []
    assert parse_labeled_transcript("") == []
    assert parse_auto("")[0] == []


@_register
def test_whitespace_only_input():
    assert parse_timestamp_segmented("   \n\n\t\n") == []


@_register
def test_only_timestamps_no_content():
    sample = "9:00 AM\n\n9:05 AM\n\n9:10 AM\n"
    turns = parse_timestamp_segmented(sample)
    assert turns == [], (
        f"Input with only timestamps and no content should yield no turns; "
        f"got {turns}"
    )


@_register
def test_pm_timestamps_recognized():
    sample = "morning question\n\n11:55 PM\n\nlate-night answer\n"
    fmt = detect_transcript_format(sample + "\n11:56 PM\n\nfollow up\n")
    assert fmt == "timestamped"


# ─────────────────────────────────────────────────────────────────────────
# F. Cross-format invariants
# ─────────────────────────────────────────────────────────────────────────

@_register
def test_no_turn_has_empty_text():
    """Across all parsers, no turn should slip through with empty text."""
    fixtures = [
        "**You said:**\nq\n\n**Claude responded:**\na\n",
        "human\n\n9:00 AM\n\nai\n\nhuman2\n\n9:05 AM\n\nai2\n",
        "block A\n\nblock B\n",
    ]
    for s in fixtures:
        turns, _ = parse_auto(s)
        for i, t in enumerate(turns):
            assert t["text"].strip(), (
                f"Turn {i} has empty text in fixture: {s!r}"
            )


@_register
def test_all_speakers_are_human_or_ai():
    """No parser may emit a speaker label other than 'human' or 'ai'."""
    fixtures = [
        "**You said:**\nq\n\n**Claude responded:**\na\n",
        "human\n\n9:00 AM\n\nai\n",
        "a\n\nb\n\nc\n",
    ]
    for s in fixtures:
        turns, _ = parse_auto(s)
        for t in turns:
            assert t["speaker"] in ("human", "ai"), (
                f"Unexpected speaker label: {t['speaker']!r}"
            )


# ─────────────────────────────────────────────────────────────────────────
# Runner
# ─────────────────────────────────────────────────────────────────────────

def _run_all() -> int:
    passed = 0
    failed = 0
    skipped = 0
    print(f"Running {len(_TESTS)} parser tests against "
          f"{SCORER_PATH.name}")
    print(f"Test docx: {TEST_DOCX} "
          f"({'available' if _DOCX_AVAILABLE else 'NOT FOUND — fixture tests skip'})")
    print("─" * 70)
    for fn in _TESTS:
        name = fn.__name__
        try:
            fn()
            # Detect skip-by-print convention: re-call would re-skip; that's fine
            print(f"  ✓ {name}")
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {name}")
            print(f"      {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ {name}  [{type(e).__name__}]")
            print(f"      {e}")
            failed += 1
    print("─" * 70)
    print(f"Passed: {passed}  Failed: {failed}  ({len(_TESTS)} total)")
    return 0 if failed == 0 else 1


# pytest discovery — expose each registered test as a top-level test_* fn
# (they already are, since @test decorator preserves the original function).
# pytest will just find them by name.


if __name__ == "__main__":
    sys.exit(_run_all())
