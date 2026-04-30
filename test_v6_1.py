"""
V6.1 self-test — verifies the rewritten parser handles the actual
Claude.ai docx export format that V6 broke on.

This test does NOT require syniq_core (which is the runtime dependency
of V6.1 itself). It extracts just the parser functions from the V6.1
source and runs them against the canonical fixture: Bill's actual
Scored_dialogue_4_29_2026.docx text.

Pass criteria:
  - Parses to exactly 6 turns (3 human, 3 AI), NOT 48.
  - Speaker assignment matches the expected interleaving.
  - Each turn is missing the duplicated preview-line artifact.
  - Total word count is meaningfully lower than the un-deduped reference
    (each turn drops one copy of its opener — typically 5-15 words).
  - Standalone timestamps are dropped (not present in any turn body).
  - Bolded section headings ("**The pivot.**") are kept inside the turn
    they belong to, NOT split into separate turns.
"""
import re
import sys
import textwrap
import importlib.util
from typing import List, Dict, Optional

# ──────────────────────────────────────────────────────────────────────────
# Extract just the parser functions from V6.1 source.
# We can't `import syniq_transcript_scorer_v6_1` because it imports
# syniq_core at module load, and we don't need syniq_core to test
# parsing. Instead, we exec just the parser block in a clean namespace.
# ──────────────────────────────────────────────────────────────────────────

V61_PATH = "/home/claude/work/syniq_transcript_scorer_v6_1.py"
src = open(V61_PATH).read()

# Slice from the parser-section banner through the end of parse_uploaded_csv.
start_marker = "# Transcript parsing (V6.1"
end_marker = "def parse_uploaded_csv"
start = src.index(start_marker)
# find end of parse_uploaded_csv (next top-level "# ─" banner after it)
after_func = src.index(end_marker, start)
banner_after = src.index("\n# ──", after_func)
parser_block = src[start:banner_after]

# Build a minimal namespace with the things the parser needs
ns = {
    "re": re,
    "List": List,
    "Dict": Dict,
    "Optional": Optional,
    # Stub st.error so parse_uploaded_csv doesn't NameError if exercised
    "st": type("StStub", (), {"error": staticmethod(lambda *a, **kw: None)})(),
    "pd": __import__("pandas"),
}
exec(parser_block, ns)

parse_labeled_transcript = ns["parse_labeled_transcript"]
parse_alternating_transcript = ns["parse_alternating_transcript"]
_dedupe_preview_sentence = ns["_dedupe_preview_sentence"]

failures = []

def check(name, cond, detail=""):
    status = "PASS" if cond else "FAIL"
    print(f"[{status}] {name}")
    if detail:
        print(f"        {detail}")
    if not cond:
        failures.append(name)


# ──────────────────────────────────────────────────────────────────────────
# CANONICAL FIXTURE: the actual docx export Bill uploaded.
# ──────────────────────────────────────────────────────────────────────────
print("\n--- Canonical fixture: Scored_dialogue_4_29_2026.docx ---\n")

with open("/home/claude/work/scored_dialogue.txt") as f:
    real_export = f.read()

source_word_count = len(real_export.split())
print(f"Source text: {source_word_count} words (raw whitespace split)\n")

turns = parse_labeled_transcript(real_export)

# 1. Turn count
check(
    "Parses to exactly 6 turns (not 48)",
    len(turns) == 6,
    f"got: {len(turns)}",
)

# 2. Speaker pattern: human, ai, human, ai, human, ai
if len(turns) == 6:
    expected = ["human", "ai", "human", "ai", "human", "ai"]
    actual = [t["speaker"] for t in turns]
    check(
        "Speakers interleave human / ai correctly",
        actual == expected,
        f"got: {actual}",
    )

    # 3. Per-turn previews (first 80 chars) for visual confirmation
    print("\n  Per-turn first 80 chars:")
    for i, t in enumerate(turns, 1):
        preview = t["text"][:80].replace("\n", " ⏎ ")
        wc = len(t["text"].split())
        print(f"    Turn {i} ({t['speaker']}, {wc:>4}w): {preview}...")

    # 4. None of the turns should contain a literal "10:31 AM" / "10:36 AM" /
    #    "10:41 AM" timestamp anywhere in their body — those are separators
    #    and must be dropped entirely.
    for i, t in enumerate(turns, 1):
        no_timestamp = not re.search(r"\b\d{1,2}:\d{2}\s*(?:AM|PM)\b", t["text"])
        check(
            f"Turn {i}: no embedded timestamp",
            no_timestamp,
            f"sample: {t['text'][:120]!r}",
        )

    # 5. None of the turns should have the speaker tag "Claude responded:"
    #    or "You said:" embedded inside their body — those are turn
    #    boundaries and must be consumed by the parser.
    for i, t in enumerate(turns, 1):
        no_speaker_tag = not re.search(
            r"(?i)(?:Claude\s+responded|You\s+said|User\s+said)\s*:",
            t["text"],
        )
        check(
            f"Turn {i}: no embedded speaker tag",
            no_speaker_tag,
            f"sample: {t['text'][:120]!r}",
        )

    # 6. Dedup verification: turn 2 (the genuinely-significant-detail
    #    AI response) should contain the sentence ONCE, not twice.
    t2_text = turns[1]["text"]
    sent = "That's a genuinely significant detail"
    occurrences_t2 = t2_text.count(sent)
    check(
        f"Turn 2 contains '{sent[:30]}...' exactly once",
        occurrences_t2 == 1,
        f"occurrences: {occurrences_t2}",
    )

    # 7. Dedup verification turn 4: "That's a much better opening line"
    t4_text = turns[3]["text"]
    sent4 = "That's a much better opening line than what I was sketching"
    occurrences_t4 = t4_text.count(sent4)
    check(
        f"Turn 4 contains '{sent4[:30]}...' exactly once",
        occurrences_t4 == 1,
        f"occurrences: {occurrences_t4}",
    )

    # 8. Dedup verification turn 6: "Yes." opener, then "Yes. That's the right version..."
    t6_text = turns[5]["text"]
    # The turn opens with "Yes." which should appear once at the start.
    # Then the next sentence begins with "That's the right version" or similar.
    yes_starts = t6_text.startswith("Yes.")
    check(
        "Turn 6 starts with 'Yes.' (preview-line artifact removed)",
        yes_starts,
        f"first 60 chars: {t6_text[:60]!r}",
    )

    # 9. Bolded section heading preserved inside its turn — e.g. the
    #    crystallization / Selinger / pivot mini-headers should appear
    #    as plain text inside turn 2 (NOT as their own separate turns).
    has_crystal_header = "The crystallization" in t2_text
    check(
        "Turn 2 contains its 'The crystallization point first.' section header",
        has_crystal_header,
        f"present: {has_crystal_header}",
    )
    has_selinger_header = "The Selinger conversation" in t2_text
    check(
        "Turn 2 contains its 'The Selinger conversation.' section header",
        has_selinger_header,
        f"present: {has_selinger_header}",
    )

    # 10. The final word counts should add up to substantially less than
    #     the raw source (because we drop standalone preview lines and
    #     timestamps), but well above zero (we don't lose content).
    deduped_word_total = sum(len(t["text"].split()) for t in turns)
    print(f"\n  Source raw words:     {source_word_count}")
    print(f"  Sum of turn words:    {deduped_word_total}")
    print(f"  Removed by parsing:   {source_word_count - deduped_word_total}")

    # The removal should be modest — just the preview echoes (one
    # sentence per turn, ~5-15 words each) plus three 2-word timestamps.
    # Across 6 turns that's roughly 30-100 words removed.
    diff = source_word_count - deduped_word_total
    check(
        "Words removed by parsing is in expected 20-150 range",
        20 <= diff <= 150,
        f"removed: {diff}",
    )

    # 11. Sanity: each turn should be substantial (these are real,
    #     substantive turns — not fragments).
    for i, t in enumerate(turns, 1):
        wc = len(t["text"].split())
        # Turn 1 is the opening human message (~45 words); later
        # turns vary widely. Anything under 5 words is a parse failure.
        check(
            f"Turn {i} has at least 5 words",
            wc >= 5,
            f"words: {wc}",
        )


# ──────────────────────────────────────────────────────────────────────────
# Dedup unit tests (sanity check that the V5.2 helper made it across)
# ──────────────────────────────────────────────────────────────────────────
print("\n--- _dedupe_preview_sentence unit tests ---\n")

# Canonical pattern: keep one copy of opener, drop standalone echo
ai_artifact = (
    "That's a genuinely significant detail.\n"
    "That's a genuinely significant detail. The crystallization point first."
)
ai_expected = "That's a genuinely significant detail. The crystallization point first."
check(
    "Preview-line dedup keeps one copy of opener",
    _dedupe_preview_sentence(ai_artifact) == ai_expected,
    f"got: {_dedupe_preview_sentence(ai_artifact)!r}",
)

# Single-line passes through
single = "This is just one line."
check(
    "Single-line turn unchanged",
    _dedupe_preview_sentence(single) == single,
)

# Similar-but-not-identical opening
similar = "That's a good point.\nThat's a great point — different."
check(
    "Similar-but-not-identical opening unchanged",
    _dedupe_preview_sentence(similar) == similar,
)

# First line without sentence-final punctuation
no_punct = "no terminal punct\nno terminal punct continues here."
check(
    "First line without . ! ? unchanged",
    _dedupe_preview_sentence(no_punct) == no_punct,
)


# ──────────────────────────────────────────────────────────────────────────
# Negative test: clean transcript with bare prefixes still works
# ──────────────────────────────────────────────────────────────────────────
print("\n--- Backward compat: bare prefixes still work ---\n")

clean = (
    "Human: What's the deadline?\n"
    "\n"
    "Claude: The deadline is next Friday.\n"
    "\n"
    "Human: Okay, let's plan from there.\n"
    "\n"
    "Claude: Sounds good. I'll start outlining tonight.\n"
)
clean_turns = parse_labeled_transcript(clean)
check(
    "Clean transcript: 4 turns parsed",
    len(clean_turns) == 4,
    f"got: {len(clean_turns)}",
)
if len(clean_turns) == 4:
    check(
        "Clean turn 1 unchanged",
        clean_turns[0]["text"] == "What's the deadline?",
        f"got: {clean_turns[0]['text']!r}",
    )
    check(
        "Clean turn 2 unchanged",
        clean_turns[1]["text"] == "The deadline is next Friday.",
        f"got: {clean_turns[1]['text']!r}",
    )
    check(
        "Clean speakers correct",
        [t["speaker"] for t in clean_turns] == ["human", "ai", "human", "ai"],
    )


# ──────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
if failures:
    print(f"FAILED: {len(failures)} test(s)")
    for f in failures:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("ALL TESTS PASSED")
    sys.exit(0)
