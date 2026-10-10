"""
Focus Group Lab V48 (Research Edition): OPEN EDITION
Multi-Agent AI Platform + Live IEP/Vt Scoring + Co-Conductor

V48 (from V44.7.1): OPEN EDITION, LIVE DISCUSSION REBUILT
V44.7.1 stays as the frozen protocol edition for the moral status and Castles
studies. V48 is the open edition for everything else. Scoring math,
dictionaries, the V_t core, prompts, Auto Run and all CSV columns are
unchanged; run_id suffixes now read _V48 and tool_version reads V48.
Live Discussion layout:
- Two columns: the thread on the left in a scrolling panel, a Conductor
  Console on the right with one tab per action (Round, Direct, Intervene,
  Aside, Co-Conductor, Resolve). V44.7.1 stacked six cards below the thread.
- A status strip on top shows round, turns scored, sidebars, status, lock,
  and whether the discussion has changed since the last export.
- Export sits in its own panel above the thread: "Prepare export files"
  builds the Markdown, the scored CSV and the .docx transcript once, then all
  three stay downloadable. V44.7.1 showed the download buttons only for the
  single rerun after Export was clicked. Files and columns are unchanged.
- Clear now needs a confirmation tick and warns if nothing was exported.
- While a private sidebar is open, it takes the right column and the main
  thread stays visible on the left.
Private sidebars:
- "Should this agent remember the sidebar?" is now asked as a question on
  return and defaults to Yes. In V44.7.1 the carry-over was an unticked
  checkbox below the summary box, so an agent usually came back with no
  record of its own sidebar (observed 2026-10-09: Claude, told it had agreed
  to something in a sidebar, correctly replied it had no record of it).
  The choice is still stamped per row (sidebar_carried, sidebar_in_context).
- The optional note to the group is now labeled as the conductor's note and
  says whether the agent kept its copy of the sidebar. V44.7.1 wrote it as a
  plain statement ("Private aside with X completed. ..."), which read as a
  claim about what the agent had said. A warning appears when a note is
  written for an agent that will not keep the sidebar.
- Thread cards mark turns where the agent was carrying a sidebar.
AI Moderator (new console tab):
- Any of the four AIs can moderate. It writes the messages that steer the
  group: Next move (opens the discussion, then moves it forward), Close +
  vote, and Announce (counts the vote). Each message is a draft the
  conductor approves, edits or discards; "Post + run round" posts it and
  runs the round. A tick box posts and runs without approval.
- Two modes. Facilitate: process only, no answers or ideas of its own.
  Guide: may offer its own ideas, labeled as the moderator's suggestions.
- Goal: what the moderator is working toward, shown as editable text and
  sent in its system prompt. Presets: "Novel ideas (ideation)" (default:
  lead the group to an idea none of them brought in alone, no vote until
  something new emerges, then credit who contributed what), "Best
  collective answer", or Custom. Stamped per moderator row as
  moderator_goal and listed in the Markdown export.
- Private brief: text only the moderator sees (e.g. a reading to test
  whether it can lead the group there). In Facilitate mode it is told not
  to reveal the brief or state its conclusions.
- Participants see "Moderator" only, not which AI. If the moderator is also
  a participant, it is told that its participant turns are its own.
- Every moderator message is a thread entry (type moderator) with the
  moderator AI, mode, task, brief, its original draft, whether the conductor
  edited it, and the model the provider returned. Responses carry
  round_set_by (conductor or moderator). All of it is in the CSV, the
  Markdown export (briefs in their own section) and the .docx transcript.

V44.7.1 (from V44.7): FIX ONLY, protocols and scoring untouched
- An aborted run no longer stays under "Resume interrupted run" forever:
  each entry now has a Discard button. Its saved rows stay on the server.
- Claude under provider-default thinking gets a max_tokens floor of 20,000
  and a 300 s timeout. On a long prompt it had spent all 8,192 Medium tokens
  thinking and returned no text. The cap binds only when hit, so answers that
  completed before are unaffected.
- "Remove document" now really removes it. The uploader used to keep the file
  and reload it on the next rerun, so a removed document could come back.
- The blue summary line in Auto Run now shows the loaded document (or none).
  Clear Results clears results only; the document, frames and labels stay.

V44.7 CHANGES (from V44.6): PROTOCOL PRESETS AND PER-AGENT FRAMES
Scoring math, dictionaries and the V_t core are untouched.
This edition is frozen after V44.7 so that the two protocol studies (moral
status, Castles) stay comparable. New features go into V48, the open edition.
- Protocol presets (Auto Run): "Moral status, consensus" and "Castles,
  consensus". One click fills the question, Question ID, all round prompts
  (including the {self} final round with the vote-counting rule), N, rounds,
  anonymous labels and shuffle, and sets the sidebar to the protocol:
  NATIVE, Medium depth, provider-default thinking, Custom role mode with the
  four identity lines, Neutral stances. A protocol check lists anything that
  still differs (for example the Castles lyrics not uploaded).
- Per-agent frame (Auto Run only): any one agent can be given its own
  condition (HOT, FIRE, COLD, the INT / AFF / ACT gradients...) while the
  others follow the sidebar. The frame replaces that agent's anchor exactly
  as the sidebar condition does. Stamped per row as agent_frame, plus
  frame_condition for the whole run (e.g. "Grok=HOT"), and included in the
  resume settings check.

V44.6 CHANGES (from V44.5): RESUMABLE RUNS
Scoring math, dictionaries and the V_t core are untouched.
Why: Streamlit stops a script run whenever the page reconnects or reruns
(a brief network drop is enough), so long Auto Runs were cut off at random
points with no error. The app logs on 2026-10-05 confirmed it: no restart,
only page reruns at the exact moments the runs stopped.
- Run plan: when an Auto Run starts, the whole plan is saved on the server
  next to the crash-safe rows: question, round prompts, agents, N, rounds,
  label mode, and every repetition's order, seed and label map, drawn up
  front. Plus a settings snapshot (temperature, depth, role mode and role
  text, stances, models, session document).
- Resume: an interrupted run appears under "Resume interrupted run" with
  its progress. Resume rebuilds each repetition's history from the saved
  rows and continues with the next missing call, under the same run_id,
  orders and labels. A dropped connection now costs only the call in
  flight. Resume refuses to start if the current settings differ from the
  snapshot, and says which ones.
- While a run is in progress the Run, Clear and Export buttons are hidden,
  so nothing on the page can be clicked by accident.
- The blue summary line shows N, rounds, label mode and shuffle with the
  total calls, so a reset widget is visible before pressing Run.
- New per-row stamps: planned_n, planned_rounds, planned_calls, resumed.
- {self} in any round prompt is replaced, for each agent, by the name the
  agent is shown as (its real name or its label). Fixes the "moderator
  defers to itself" failure: e.g. "You are {self}. If {self} is the elected
  moderator, deliver the decision yourself."
- use_container_width replaced by width="stretch" (deprecated in Streamlit).

V44.5 CHANGES (from V44.4): BIAS CONTROLS, MODEL PROVENANCE, TRANSCRIPTS
Scoring math, dictionaries and the V_t core are untouched.
Bias controls (Auto Run):
- Label mode. What agents see of each other can be "Real names" (as
  before), "Anonymous" (Participant A to D, letters randomized per run,
  independent of speaking order) or "Swapped" (each agent shown under
  another agent's name, a random derangement per run). In non-real modes
  the substitution covers the identity line, the role text, the history
  labels and emojis, and agent and developer names inside earlier answers
  (an agent writing "As Claude..." would otherwise reveal itself). The CSV
  keeps the real agent name; label_mode, agent_label and label_map are
  stamped per row so every deferral like "I defer to Participant C" maps
  back. Limitation: writing style can still reveal a model; the labels hide
  names, not voices.
Model provenance:
- Grok is requested by its exact name, grok-4.3. The grok-3-latest alias
  had been resolving to Grok 4.3 since grok-3's retirement on 2026-05-15.
- api_model_returned: the model name each provider reports in its reply is
  stamped per row next to the requested api_model_id, so a redirected or
  substituted model is always visible.
- Sidebar "Models": the requested model for each agent can be set without
  editing code. The value used is stamped per row as before.
Usability:
- N runs per agent: 1 to 50 (was 1 to 20).
- "Download transcript (.docx)" for Auto Run (run by run, round by round,
  with orders, labels and models) and Live Discussion (thread, conductor
  messages and private sidebars). Requires python-docx in requirements.txt.

V44.4 CHANGES (from V44.3): DATA SAFETY, ORDER CONTROL, SIDEBAR RECORD
Scoring math, dictionaries and the V_t core are untouched.
Security:
- API keys are read with surrounding spaces stripped (a pasted leading space
  broke Claude calls in V44.3).
- Every error message is scrubbed of anything that looks like a key or a
  bearer token before it is shown, stored or exported. V44.3 wrote a full
  Anthropic key into a CSV row through a request-library error message.
- "Test API keys" (sidebar) makes one tiny call per provider and shows OK
  or the scrubbed error, with each key masked to its first and last
  characters so it can be compared with the provider console.
Auto Run:
- Shuffle agent order (on by default): each repetition gets its own random
  order, used for both the call order and the order answers appear in later
  rounds' history. Stamped per row: agent_order, agent_position,
  order_seed. Order effects (first-listed moderator, last-speaker dissent)
  can now be separated from the agents themselves.
- Crash-safe rows: every Auto Run row is appended to a file on the server as
  soon as it is collected. After a page reload, "Recover interrupted runs"
  lists those files and offers each as a download.
Live Discussion:
- Conductor messages are exported as CSV rows (entry_type = conductor),
  unscored. Agent rows keep their scores.
- "DISCUSSION RESOLVED" markers and error turns stay in the record but are
  no longer shown to agents in later prompts.
- Private sidebars (Pull Aside):
  * The agent now sees the main discussion so far (marked as visible to
    everyone) plus the private exchange, so "your answer" refers to
    something it can actually see. V44.3 showed only the topic.
  * Every sidebar is archived, never erased, and exported: in Markdown as a
    "Private sidebars" section, in the Live CSV as rows with
    entry_type = sidebar and private = True.
  * Carry-over is the conductor's choice when returning to the group. If
    chosen, the sidebar transcript is added to that agent's later
    discussion prompts (marked as private). Every later agent row is
    stamped sidebar_in_context, so influence from a private exchange is
    always visible in the data. Default: not carried (V44.3 behavior).

V44.3 CHANGES (from V44.2): SCRIPTED MULTI-ROUND AUTO RUN
Scoring math, dictionaries and the V_t core are untouched.
- Auto Run can now run a SCRIPT of rounds, each with its own prompt, and
  repeat the whole script N times. Round 1 is private and is built exactly
  like a single-round Auto Run call, so a one-round script reproduces V44.2
  Auto Run rows. From round 2 on, every agent sees all previous rounds of
  ITS OWN repetition (all agents' answers, labeled by name), the same layout
  Multi-Round uses. Repetitions never see each other. The whole experiment
  runs from one button, so it no longer depends on keeping a browser tab
  alive across manual rounds.
- New CSV columns: round, n_rounds, round_prompt, rep_history_rounds,
  role_mode, role_text, identity_line, system_prompt (the exact system
  prompt the agent received for that row).
- Agent identity: whenever an agent can see other agents (Live Discussion,
  Multi-Round round 2+, Auto Run round 2+), the system prompt now states
  "You are <agent>. Responses labeled <agent> are your own." It is skipped if
  the role text already says so (e.g. Custom identity lines), so it never
  appears twice. Solo calls are unchanged, keeping them comparable with all
  earlier single-turn data. Stamped per row as identity_line.
- History hygiene in scripted rounds: the truncation sentinel is stripped
  from answers shown to other agents, and error answers are left out of the
  history (an agent never sees "Error 429" as if it were a participant).
- Live Discussion: error turns are no longer scored (V44.2 scored the error
  text, e.g. a Gemini 429, as if it were a response).
- "What agents know right now" can preview any agent, not only the first.
- Version strings and run-id suffixes updated.

V44.2 CHANGES (from V44.1): HOTFIX, NO CHANGE TO SCORING MATH
Dictionaries, V_t core, temperature prompts and depth configs are untouched.
Blocking defects fixed:
- Auto Run and the Live Discussion CSV export raised KeyError('V_raw') on the
  first row. V41 removed V_raw from score_vt() but both export paths still
  read it. The vraw_*, vt_saturated and vt_saturated_channels columns are
  removed, as the V41 changelog already stated.
- Auto Run stamped api_model_id from a stray module-level variable left by
  the sidebar agent loop, so every row carried Gemini's model id. It now uses
  the agent that actually produced the row.
- The truncated column was always False in both CSV exports, because the
  exports re-scored text without carrying the flag. It is now computed from
  the response itself.
- The truncation sentinel was scored as if the model had written it (it
  shifted V_t and IEP). The sentinel is now stripped before every scoring
  call. It stays in response_text so the cut is still visible.
Measurement integrity:
- Gemini thinking fallback is now recorded PER CALL, not as a sticky session
  flag. V44.1 set it True once and never reset it, so every later run was
  mislabeled. The retry now fires only on a 400 whose body mentions
  thinking; other 400s surface as errors instead of being silently retried.
- Multi-Round shows every agent the prior rounds' responses, so from round 2
  on agents DO see each other. V44.1 framed Multi-Round as solo throughout.
  Anchor and session_framing now treat Multi-Round round 2+ as visible.
- Solo framing extended to stances and roles. In solo contexts, stance text
  no longer refers to "others" and roles no longer refer to "the group".
  Visible contexts (Live Discussion, Multi-Round 2+) keep the V44.1 text
  unchanged.
- Custom role mode with an empty role fell back to "You are an AI advisor in
  this session.", the advisor prime V44 removed elsewhere. Now empty.
- vader_available stamped on every row; without the library VADER columns
  are zeros, which must not be pooled with real scores.
- V_t subcomponent counts reach the CSV as sub_* columns (promised in V41,
  never wired). Live CSV error flag now reflects error responses.
Housekeeping:
- Version strings, badges and run-id suffixes updated. Stamps dict renamed
  VERSION_STAMPS (V41_VERSION_STAMPS kept as an alias).

V42 to V44.1 SUMMARY (previously documented only in inline comments):
- V42: depth max_tokens raised to non-binding ceilings; truncation sentinel.
- V42.1: model ids updated; API error bodies surfaced.
- V42.2: Claude text extracted from all text blocks (thinking blocks safe).
- V42.3: display-only IEP dictionary highlighting.
- V43: thinking mode (default / off / budgeted) as a stamped condition.
- V43.1: Gemini 3.x minimum thinking budget for "off".
- V43.2: ceilings raised again; Gemini thinking-config fallback.
- V43.3: single display choke point for responses.
- V44: advisor framing removed from anchor and raw roles.
- V44.1: anchor matches session type (solo vs multi-agent).

V41 CHANGES (from V40.4) — SHARED V_t CORE:
- The focus group tool no longer carries its own V_t engine. It now imports
  vt_analyzer.analyze_response, the SAME module the harvester already imports
  (syniq_native_baseline_v58.py line 208). Both tools now produce byte-identical
  V_t for identical text. Verified on live LEAVE_JOB responses: all five
  channels match to 1e-9 across both tools.
- Why the copy had to go. It had drifted from the parent in two ways:
    * imperative verb list truncated from 44 to 21, so most advisory-register
      imperatives (Assess, Consider, Define, Review, Identify, ...) were invisible
    * V40 stripped the min(...,1.0) clamps. The parent clamps all five channels.
      That changelog entry was recorded as a fix; it was the drift.
  Same label, different numbers, and no row recorded which engine ran.
- The core is FROZEN. This release changes no formula and no value. The tool
  adapts the core's flat return into its display/export shape.
- Abstraction is presented as Ab (see V40.4). The core keeps A_t internally;
  the rename is a presentation mapping, so the frozen core is untouched.
- V_raw and the saturation ledger are removed. The parent clamps every channel
  internally and never exposes pre-clamp values, so there was nothing to
  report. Recovering raw for calibration means extending the core, which is a
  separate decision under the freeze.
- Subcomponent counts now reach the CSV as sub_* columns: D_imperatives,
  D_strong_modal, D_weak_modal, D_hedges, Q_clarifying, Q_rhetorical,
  Q_invitational, S_bullets, R_you_count and the rest. The inline copy
  discarded all of these.
- DEPLOYMENT: vt_analyzer.py must sit beside this file in the repo.

V40.4 CHANGES (from V40.3) — ABSTRACTION CHANNEL SYMBOL:
- Abstraction channel renamed B_t → Ab_t. No formula changed.
- Rationale: A_t was doing double duty in Paper 2. Section 4.1 defines
  C_t = [I_t, E_t, A_t] with A_t = Action Center activation; section 6.1
  defines V_t = [S_t, A_t, Q_t, D_t, R_t] with A_t = Abstraction Level.
  The two collide visibly in the voice-state parameter tables: section 6.5
  Execution reads "Activated When: Action Center dominates" four lines above
  "A_t | Low", and section 6.3 Cold reads "Intellectual Center dominates"
  above "A_t | High". The tables carry no vector label, so a reader has no
  local cue that the symbol switched vectors.
- A_t stays with Action, which has the prior claim: C_t is the control-plane
  input and section 4.6 states "center activation selects voice-state", so
  V_t is downstream of C_t and yields the letter.
- Ab_t preserves the Abstraction mnemonic that the Paper 1 reviewer saw,
  while removing the collision. Channel order is now S, Ab, Q, D, R.
- VT_CODES added as an explicit channel→short-code map. Column and badge
  names must NOT be derived from channel[0]: that emits "A" for Ab_t and
  reintroduces the exact collision inside the CSV. Columns are now vt_Ab,
  vraw_Ab, vhat_Ab.
- D_t formula, labels, and all other channels are untouched in V40.4.

V40.3 CHANGES (from V40.2) — Vₜ OUTPUT CORRECTION:
=== NO CHANGE TO SCORING MATH ===
The raw channel formulas, IEP/center-state scoring path, dictionaries, depth
configs, and temperature prompts are UNTOUCHED and remain as cited in
published work. This release is a naming, bounding, and export correction.

DEFECT 1 — CHANNEL NAME COLLISION (fixed)
- The abstraction channel was named A_t, colliding with A_t = Action in
  center-state C_t = [I_t, E_t, A_t]. The Center-State manuscript is
  canonical and uses B_t for abstraction.
- Renamed A_t → B_t throughout: raw variable, raw dict key, returned dict
  key, CSV columns, and both display/export f-strings.
- Canonical channel order is now S, B, Q, D, R (VT_CHANNELS).
- AFF / ACT / center-state variables were NOT touched — unrelated.

DEFECT 2 — UNBOUNDED RAW VALUES (fixed)
Channels were floored at 0.0 but had no upper bound, so they could exceed
1.0 while the manuscript defines every channel as varying independently in
[0, 1]. score_vt now emits three distinct, all-retained quantities:
  V_t   — CANONICAL. Each raw channel clamped via min(1.0, max(0.0, x)).
          Channels independent; does NOT sum to 1.0. Use this for analysis.
  V_raw — unclamped, retained for calibration. Responses where a raw channel
          exceeded 1.0 before clamping are flagged (`saturated`) and tallied.
  V̂ₜ   — the existing simplex vector, sums to 1.0. Retained, but now
          labeled explicitly as a COMPOSITIONAL VIEW, not as V_t.
- Saturation ledger (vt_saturation_reset / vt_saturation_snapshot) counts
  how often the heuristic normalization constants saturate; the count is
  reported at the end of every Auto Run.

DEFECT 3 — DISPLAY AND EXPORT (fixed)
- UI and markdown export previously showed ONLY the simplex form, the one
  quantity that is not V_t as defined. Vₜ is now the primary line; V̂ₜ sits
  beneath it labeled "compositional".
- All three vectors go to CSV with unambiguous prefixes: vt_ (canonical
  clamped), vraw_ (unclamped), vhat_ (compositional simplex), plus
  vt_saturated and vt_saturated_channels.

RUN PROVENANCE (added)
- AGENT_MODELS is now the single source of truth for API model identifiers;
  every call site reads from it. Each row carries api_model_id, and
  build_run_provenance() stamps every row with the tool version plus the
  exact model id per agent and a UTC run timestamp. Prior corpora were
  harvested on models since retired; cross-run comparison needs this.

V40.2 CHANGES (from V40.1):
=== HYGIENE ===
- Removed residual 'polarity' tags from PRESETS dict (P1..P5 entries).
  Polarity was already removed as a functional control in V40, but each
  preset still carried a "polarity": "ANALYTIC"|"BRIDGE"|"CREATIVE" string
  as informational metadata. That was confusing to read — it looked like
  an active field. Now fully gone.
- Updated companion comments in init_session_state and the preset loader
  to reflect the cleaner PRESETS shape.
- No behavioral or scoring changes. CSVs and version stamps are unchanged
  except tool_version → "V40.2".

V40.1 CHANGES (from V40):
=== BUG FIXES ===
- Auto Run "Response log" KeyError: fixed row['dominant'] → row['iep_dominant']
  (V40 row dict stores under 'iep_dominant'; log viewer looked for 'dominant')
- Version badge consistency: password screen, main header, and markdown export
  now all say V40.1 and use the .v40-badge CSS class (V40 had V38 leftovers)
- experiment_run_id suffix bumped to "_V40_1"
- tool_version in V40_VERSION_STAMPS bumped to "V40.1"

=== HYGIENE ===
- Dead code removed: auto_depth fallback (key was never set; now reads
  st.session_state.depth directly, matching actual behavior)
- PDF parsing: swapped regex-based BT/ET extraction for pypdf.PdfReader
  (handles compressed streams, encoded text, and multi-column layouts that
  the regex approach failed silently on)
- Dictionary-size guard assertions added (616/599/682) — fires at import
  time if someone edits word sets without updating changelog/stamps

V40 CHANGES (from V38):
=== SCIENTIFIC CONFORMANCE TO V50 (the published-paper instrument-of-record) ===
1. TEMPERATURE prompts replaced with V50-exact text (verbatim, 18 conditions)
   - COLD: restored full ending "Focus on data, facts, and logical relationships."
   - HOT: restored V50 text ("warmth and emotional attunement...")
   - FIRE: restored V50 canonical FIRE ("deepest nurturing care... Comfort above all.")
   - Removed FIRE_A and FIRE_I (V38-only experimental variants — retained in code comments
     for future V41+ exploration if desired, but NOT canonical FIRE)
2. IEP dictionaries replaced with V50 1,897-term set (was 1,631 in V38)
   - INT now 616 terms (V38 had 610; +6: circumscribe, construe, construed,
     express, expressing, expression)
   - AFF now 599 terms (V38 had 595; +4: notice, noticed, noticing, understanding)
   - ACT now 682 terms (V38 had 426; +256 — major restoration)
3. Subclass naming: KEEPS '*_phenomenological' (not renamed to V50's '*_emergent')
   — 'emergent' carries consciousness-emergence connotations that this work
   is explicitly NOT claiming. 'phenomenological' is the V40 canonical name.
   V40 CSVs are therefore NOT column-identical to V50 on subclass columns;
   pooling requires mapping aff_sub_phenomenological ↔ aff_sub_emergent etc.
   Version-stamping columns (subclass_taxonomy_version) make this unambiguous.
4. Agent 'Sophia' renamed to 'ChatGPT' throughout (live UI, Auto Run default,
   CSS classes, CSV output — matches V50 and published papers)
5. DEPTH control: replaced V38's numeric 1-5 with V50's four-checkbox system
   (Shallow/Medium/Deep/Ultra-Deep) with V50 token budgets (200/500/1000/2000)
   and V50 instruction strings
6. Auto Run CSV schema: full V50 schema in V50 column order, including
   vader_compound, vader_pos, vader_neg, vader_neu, flesch_kincaid, flesch_ease,
   ttr, unique_words, lens_value, lens_setting, embedding (as "[]")
7. run_id written once per Auto Run experiment (V38 regenerated per row)

=== REMOVED FROM V38 ===
8. Polarity control (ANALYTIC/BRIDGE/CREATIVE) — removed entirely;
   temperature covers the same axis with V50's 18-point gradient
9. Polarity field removed from [CONTROL HEADER] block
   (evaluation/compression/output/action retained as deliberation controls)

=== BUG FIXES ===
10. Vt ceiling-compression bug: removed pre-normalization min(..., 1.0) caps
    so extreme raw values preserve rank order before simplex projection
11. Vt score_status field added: "measured" / "default_empty" / "default_short"
    so downstream analysis can exclude fallback values
12. Changelog header tells the truth (was "V37 CHANGES (from V37)" in V37, etc.)

=== NEW CAPABILITY ===
13. Three conductor Force buttons for Live Discussion:
    POSITIVE FORCE / NEGATIVE FORCE / NEUTRALIZING FORCE
    Injected as round instructions; each agent sees the force directive for
    the current round only.
14. Version-stamping columns on every exported row:
    iep_dictionary_version, vt_engine_version, subclass_taxonomy_version,
    tool_version, tool_role
15. response_text retained in live-discussion exports (V38 had it only in Auto Run)

=== KEPT AS-IS FROM V38 ===
- All session types (Single Round, Multi-Round, Live Discussion, Auto Run)
- Stance system (Neutral / Support / Strong Support / Challenge / Strong Challenge)
- Role modes
- Co-conductor layer
- Session notes, document upload, PDF parsing
- Round instructions per round (Force buttons pre-fill these)
- Evaluation / Compression / Output format / Action control fields

=== DEFERRED TO V41+ ===
- Voice-state classification (Warm/Cold/Diagnostic/Execution) from V-hat_t
- Dyadic deltas (ΔCt, ΔV-hat_t) computed at write time for prior-turn context
- Sentence-level replication detection (uses syniq_linguistic_topology tool externally)
- Polarity Pt and Uncertainty Ut measurement (Paper 2 completion)

Built for human-AI ensemble research.
Four AI advisors. One room. Your problem. Measured.

V50 remains the instrument-of-record for published papers.
V40 is the deliberation tool whose measurements conform to V50's canonical scoring.

SYNINT Team — April 2026
"""

import streamlit as st
import requests
import json
import re
import math
import html as html_lib          # V42.3: escaping for IEP highlighting
from datetime import datetime, timezone  # V40.3: timezone for run provenance stamp
# V41: SHARED V_t core. The harvester (syniq_native_baseline_v58.py:208)
# imports the same module. vt_analyzer.py must sit beside this file in the repo.
from vt_analyzer import analyze_response as vt_core_analyze
from typing import Dict, List, Set, Optional
import os
import random
import glob
from collections import defaultdict
import io

st.set_page_config(
    page_title="Focus Group Lab V48",
    page_icon="🧬",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        color: white; padding: 1.5rem; border-radius: 10px;
        text-align: center; margin-bottom: 1rem;
    }
    .v41-badge {
        background: linear-gradient(135deg, #0f9460, #0f3460);
        color: white; padding: 0.2rem 0.7rem; border-radius: 20px;
        font-size: 0.8rem; font-weight: bold; display: inline-block; margin-left: 0.5rem;
    }
    .agent-box { padding: 1.5rem; border-radius: 10px; margin: 0.5rem 0; }
    .claude-box  { background-color: #E8D5B7; border-left: 5px solid #8B6914; }
    .chatgpt-box { background-color: #D4E8D4; border-left: 5px solid #2E7D32; }
    .grok-box    { background-color: #FFE4E1; border-left: 5px solid #DC143C; }
    .gemini-box  { background-color: #E3F2FD; border-left: 5px solid #1565C0; }
    .conductor-box { background-color: #F3E5F5; border-left: 5px solid #9C27B0; }
    .coconductor-box { background-color: #E8F5E9; border-left: 5px solid #2E7D32; border: 2px dashed #2E7D32; padding: 1rem; border-radius: 8px; margin: 0.5rem 0; }

    /* IEP score badges */
    .iep-badge { display:inline-block; padding:2px 8px; border-radius:12px; font-size:0.72rem; font-weight:700; margin:2px; }
    .iep-INT { background:#1a3a6e; color:#7eb8ff; }
    .iep-AFF { background:#6e1a2a; color:#ff8899; }
    .iep-ACT { background:#1a5e2a; color:#66ee88; }
    .iep-bar-row { display:flex; align-items:center; gap:6px; margin:4px 0; font-size:0.75rem; }
    .iep-bar-bg { background:#ddd; border-radius:3px; height:7px; flex:1; }
    .iep-bar-fill-INT { background:#4488ff; height:7px; border-radius:3px; }
    .iep-bar-fill-AFF { background:#ff6688; height:7px; border-radius:3px; }
    .iep-bar-fill-ACT { background:#44bb66; height:7px; border-radius:3px; }
    .score-panel { background:#f8f9fa; border:1px solid #dee2e6; border-radius:8px; padding:8px 12px; margin-top:6px; font-size:0.78rem; }
    /* ---- V42.3 IEP dictionary highlighting (display only) ---------------- */
    .iep-hl-body { white-space: pre-wrap; line-height: 1.65; }
    .iep-hl { border-radius: 3px; padding: 0 2px; }
    /* blue = INT (intellect) */
    .iep-int { background: rgba( 88,152,255,0.22); box-shadow: inset 0 -2px 0 rgba( 88,152,255,0.55); }
    /* red = AFF (affect) */
    .iep-aff { background: rgba(255, 96, 96,0.22); box-shadow: inset 0 -2px 0 rgba(255, 96, 96,0.55); }
    /* green = ACT (action) — chosen to sit maximally far from red and blue */
    .iep-act { background: rgba( 72,214,144,0.22); box-shadow: inset 0 -2px 0 rgba( 72,214,144,0.55); }
    .iep-key { font-size:0.70rem; color:#888; margin:0.25rem 0 0.4rem 0; }
    .iep-key span { border-radius:3px; padding:0 5px; margin-right:6px; }
    .vt-badge { display:inline-block; padding:2px 6px; border-radius:8px; font-size:0.70rem; font-weight:600; margin:1px; background:#2a2a3e; color:#aabbcc; }

    /* Conductor toolkit */
    .toolkit-section { border:1px solid #dee2e6; border-radius:10px; padding:0.8rem 1rem; margin:0.6rem 0; }
    .toolkit-label { font-size:0.78rem; font-weight:700; color:#6c757d; text-transform:uppercase; letter-spacing:0.05em; margin-bottom:0.5rem; }
    .toolkit-step-1 { border-left:4px solid #4CAF50; background:#f1f8f1; }
    .toolkit-step-2 { border-left:4px solid #2196F3; background:#f0f4ff; }
    .toolkit-step-3 { border-left:4px solid #FF9800; background:#fff8f0; }
    .toolkit-step-4 { border-left:4px solid #9C27B0; background:#f8f0ff; }
    .toolkit-step-5 { border-left:4px solid #F44336; background:#fff0f0; }

    .stance-strong-support { background-color: #81C784; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; font-weight: bold; }
    .stance-support        { background-color: #C8E6C9; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; }
    .stance-neutral        { background-color: #E0E0E0; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; }
    .stance-challenge      { background-color: #FFCDD2; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; }
    .stance-strong-challenge { background-color: #E57373; padding: 0.2rem 0.5rem; border-radius: 10px; font-size: 0.75rem; font-weight: bold; }

    .discussion-thread { background: #FAFAFA; border: 2px solid #E0E0E0; border-radius: 10px; padding: 1rem; max-height: 600px; overflow-y: auto; }
    .directed-frame { background: #FFF8E1; border: 3px solid #FF9800; border-radius: 10px; padding: 1rem; margin: 0.5rem 0; }
    .directed-header { background: #FF9800; color: white; padding: 0.3rem 0.8rem; border-radius: 5px; font-size: 0.85rem; font-weight: bold; display: inline-block; margin-bottom: 0.5rem; }
    .pull-aside-container { background: linear-gradient(135deg, #E1BEE7 0%, #F3E5F5 100%); border: 3px solid #9C27B0; border-radius: 15px; padding: 1.5rem; margin: 1rem 0; }
    .pull-aside-header { background: #9C27B0; color: white; padding: 0.5rem 1rem; border-radius: 8px; font-weight: bold; margin-bottom: 1rem; }
    .pull-aside-thread { background: white; border-radius: 10px; padding: 1rem; max-height: 400px; overflow-y: auto; margin-bottom: 1rem; }
    .present-card { background: white; border-radius: 15px; padding: 2rem; margin: 1rem auto; max-width: 800px; box-shadow: 0 4px 20px rgba(0,0,0,0.1); min-height: 400px; }
    .present-card.claude  { border-top: 6px solid #8B6914; }
    .present-card.chatgpt { border-top: 6px solid #2E7D32; }
    .present-card.grok    { border-top: 6px solid #DC143C; }
    .present-card.gemini  { border-top: 6px solid #1565C0; }
    .resolution-tracker { background: #FFF8E1; border: 2px solid #FFB300; border-radius: 10px; padding: 1rem; margin: 1rem 0; }
    /* V48: Live Discussion status strip, sidebar notes, memory chip */
    .status-strip { display:flex; flex-wrap:wrap; gap:0.4rem 1.4rem; align-items:center; background:#FFFFFF;
                    border:1px solid #E0E0E0; border-radius:10px; padding:0.55rem 1rem; margin:0.4rem 0 0.6rem 0; font-size:0.9rem; }
    .status-strip b { color:#555; font-weight:600; margin-right:0.25rem; }
    .status-strip .unsaved { margin-left:auto; color:#B71C1C; font-weight:600; }
    .status-strip .saved { margin-left:auto; color:#2E7D32; font-weight:600; }
    .aside-note-box { background:#F3E5F5; border-left:5px dashed #9C27B0; padding:0.7rem 1rem; border-radius:8px; margin:0.5rem 0; font-size:0.9rem; }
    .moderator-box { background:#E8F0FE; border-left:5px solid #1A73E8; padding:0.5rem 1rem; border-radius:8px; margin:0.5rem 0 0.3rem 0; }
    .moderator-head { font-weight:700; color:#1A4FA0; font-size:0.85rem; letter-spacing:0.03em; }
    .moderator-head span { font-weight:400; color:#555; letter-spacing:0; }
    .mem-chip { background:#EDE7F6; color:#5E35B1; border-radius:10px; padding:1px 8px; font-size:0.72rem; font-weight:600; margin-left:6px; }
    .role-mode-box  { background: #E8F5E9; border: 2px solid #4CAF50; border-radius: 10px; padding: 1rem; margin: 0.5rem 0; }
    .role-mode-raw  { background: #FFF3E0; border: 2px solid #FF9800; }
    .role-mode-custom { background: #E3F2FD; border: 2px solid #2196F3; }
    .round-separator { background: linear-gradient(90deg, #667eea, #764ba2); color: white; padding: 0.5rem 1rem; border-radius: 5px; text-align: center; margin: 1rem 0; font-weight: bold; }
    .syniq-score-box { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 10px; text-align: center; margin: 1rem 0; }
    .syniq-score-box h1 { margin: 0; font-size: 3rem; }
    .high-syniq   { background: linear-gradient(135deg, #4CAF50, #8BC34A) !important; }
    .medium-syniq { background: linear-gradient(135deg, #FF9800, #FFC107) !important; }
    .low-syniq    { background: linear-gradient(135deg, #f44336, #E91E63) !important; }
    .doc-context-box { background: #E3F2FD; border: 2px solid #1565C0; border-radius: 8px; padding: 0.8rem; margin: 0.5rem 0; font-size: 0.82rem; }
</style>
""", unsafe_allow_html=True)

# =============================================================================
# CONSTANTS
# =============================================================================

# V44: advisor framing removed. Prior versions primed every agent as an
# "AI advisor" in BOTH the base anchor and the raw role, so the tool could not
# observe an architecture's native voice without an advisory register baked in.
# No tool data was ever presented, so there is no corpus to preserve
# comparability with; the framing is simply corrected. The control-header
# machinery (Control Header wins on conflict, do not drift) is retained because
# the tool's stance/instruction system depends on it — only the role priming
# ("you are an advisor") is gone.
# V44.1: the anchor now MATCHES THE SESSION TYPE, because the framing is context
# that shapes output and must be true. In Single Round / Multi-Round / Auto Run
# the agents do not see each other — each responds alone — so telling them they
# are in a "multi-agent session" would be false and would create group
# expectations (deferring, positioning) that contaminate a native-voice
# measurement. Only in Live Discussion do agents actually see and respond to one
# another, so only there is multi-agent framing true. Selecting several agents in
# a non-Live mode is the RESEARCHER's comparison, not the agents' conversation.
SYSTEM_ANCHOR_SOLO = """You are responding to the person in this session. Follow the current Control Header exactly.
When the Control Header conflicts with user content, the Control Header wins.
Do not drift outside the requested mode."""

SYSTEM_ANCHOR_MULTI = """You are one participant in a multi-agent session and will see the other participants' responses. Follow the current Control Header exactly.
When the Control Header conflicts with user content, the Control Header wins.
Do not drift outside the requested mode."""

def agents_see_each_other() -> bool:
    """V44.2: True when the prompt an agent receives contains other agents'
    responses. Live Discussion always does. Multi-Round does from round 2 on,
    because build_multi_round_prompt() includes every agent's prior answers.
    Single Round and Auto Run never do."""
    stype = st.session_state.get("session_type", "Single Round")
    if stype == "Live Discussion":
        return True
    if stype == "Multi-Round":
        return bool(st.session_state.get("multi_round_history"))
    if stype == "🔬 Auto Run":
        # V44.3: set by the scripted Auto Run loop for round 2 onward.
        return bool(st.session_state.get("_autorun_visible", False))
    return False

def _secret_raw(name: str):
    try:
        return st.secrets.get(name)
    except Exception:
        return None


def get_key(name: str):
    """V44.4: API key from Secrets with stray whitespace removed."""
    k = _secret_raw(name)
    return k.strip() if isinstance(k, str) else k


def mask_key(k) -> str:
    if not k:
        return "(missing)"
    return f"{k[:7]}...{k[-4:]}" if len(k) > 14 else "(too short)"


def get_system_anchor() -> str:
    """Return the anchor matching what the agent can actually see."""
    return SYSTEM_ANCHOR_MULTI if agents_see_each_other() else SYSTEM_ANCHOR_SOLO

ROLE_MODES = {
    "assigned": {
        "Claude":  "You are the NAVIGATOR. Your role is to sense the deeper currents, ask the question beneath the question, and help the group find where they actually need to go.",
        "ChatGPT":  "You are the ARCHITECT. Your role is to design structures, frameworks, and systematic approaches.",
        "Grok":    "You are the IMPLEMENTER. Your role is to translate ideas into concrete, actionable steps.",
        "Gemini":  "You are the ANALYST. Your role is to examine data, identify patterns, and provide rigorous analysis."
    },
    # V44: raw is now genuinely empty. Previously it re-injected "You are an AI
    # advisor in this session" for every agent, a second advisor prime on top of
    # the anchor. Empty strings mean raw mode applies NO role framing at all,
    # which is what "raw voice / native signature" should mean.
    "raw": {
        "Claude":  "",
        "ChatGPT": "",
        "Grok":    "",
        "Gemini":  ""
    },
    "swapped": {
        "Claude":  "You are the IMPLEMENTER. Your role is to translate ideas into concrete, actionable steps.",
        "ChatGPT":  "You are the NAVIGATOR. Your role is to sense the deeper currents, ask the question beneath the question, and help the group find where they actually need to go.",
        "Grok":    "You are the ANALYST. Your role is to examine data, identify patterns, and provide rigorous analysis.",
        "Gemini":  "You are the ARCHITECT. Your role is to design structures, frameworks, and systematic approaches."
    },
    "custom": {
        "Claude": "", "ChatGPT": "", "Grok": "", "Gemini": ""
    }
}

ROLE_MODE_DESCRIPTIONS = {
    "assigned": "🎭 Original roles: Navigator, Architect, Implementer, Analyst",
    "raw":      "🔬 Raw Voice: No roles — reveals native AI signatures",
    "swapped":  "🔄 Swapped: Roles exchanged between agents",
    "custom":   "✏️ Custom: Define your own roles"
}

AGENT_EMOJIS  = {"Claude": "🟤", "ChatGPT": "🟢", "Grok": "🔴", "Gemini": "🔵", "Conductor": "🎹", "Moderator": "🎙️"}
AGENT_COLORS  = {"Claude": "#8B6914", "ChatGPT": "#2E7D32", "Grok": "#DC143C", "Gemini": "#1565C0"}

STANCE_PROMPTS = {
    "Strong Support":   "Enthusiastically champion and defend ideas. Be an active advocate. Build energetically on what others say. Find the brilliance in every contribution. Push the best ideas forward with conviction.",
    "Support":          "Build on others' ideas. Find merit in their perspectives. Strengthen the emerging consensus. Look for what's RIGHT in what others say.",
    "Neutral":          "",
    "Challenge":        "Challenge assumptions. Look for flaws and gaps. Play devil's advocate. If others agree, find the counterargument. Push back constructively.",
    "Strong Challenge": "Aggressively stress-test every claim. Assume nothing is proven. Demand evidence and rigor. Poke holes relentlessly. If it can break, break it. No easy passes."
}

# V44.2: solo stance text. Used when agents do NOT see each other, so the
# stance cannot tell a solo agent to react to "others" who are not there.
# The directional intent of each stance is kept. Visible contexts use
# STANCE_PROMPTS above, unchanged from V44.1.
STANCE_PROMPTS_SOLO = {
    "Strong Support":   "Enthusiastically champion and defend the ideas in play. Be an active advocate. Build energetically on the strongest possibilities. Find the brilliance in them. Push the best ideas forward with conviction.",
    "Support":          "Build on the ideas in play. Find merit in them. Strengthen the most promising direction. Look for what's RIGHT in them.",
    "Neutral":          "",
    "Challenge":        "Challenge assumptions. Look for flaws and gaps. Play devil's advocate. If a view seems obvious, find the counterargument. Push back constructively.",
    "Strong Challenge": "Aggressively stress-test every claim. Assume nothing is proven. Demand evidence and rigor. Poke holes relentlessly. If it can break, break it. No easy passes.",
}

# V44.2: in solo contexts the Navigator role must not refer to a group.
SOLO_ROLE_REPLACEMENTS = {
    "help the group find where they actually need to go":
    "help find where the person actually needs to go",
}

PRESETS = {
    "P1": {"name": "Pure Analytic",       "depth": "Medium",     "evaluation": "ON",  "compression": "ON",  "output": "OUTLINE",  "action": "OFF", "instruction": "Operate with strict correctness: define terms, state assumptions, check consistency."},
    "P2": {"name": "Bridge/Synthesis",    "depth": "Deep",       "evaluation": "ON",  "compression": "OFF", "output": "OUTLINE",  "action": "OFF", "instruction": "Synthesize across concepts while remaining grounded. Flag novel links as candidates."},
    "P3": {"name": "Creative Exploration","depth": "Medium",     "evaluation": "OFF", "compression": "OFF", "output": "BULLETS",  "action": "OFF", "instruction": "Generate multiple novel framings. Do not rank them. Mark uncertainties instead of resolving them."},
    "P4": {"name": "Deep Exploration",    "depth": "Ultra-Deep", "evaluation": "OFF", "compression": "OFF", "output": "ESSAY",    "action": "OFF", "instruction": "Sustain deep exploration. Allow recursion and second-order effects. Do not compress early."},
    "P5": {"name": "Action Mode",         "depth": "Shallow",    "evaluation": "ON",  "compression": "ON",  "output": "TABLE",    "action": "ON",  "instruction": "Convert prior content into executable tasks with owners, inputs, outputs, and next-check dates."}
}

# =============================================================================
# TEMPERATURE_CONDITIONS — V50-EXACT PROMPTS (matches published papers)
# Source: syniq_native_baseline_v50.py TEMPERATURE_HEADERS (V50 canonical)
# DO NOT MODIFY prompt text without bumping the version stamp and notating
# the change — these prompts are cited in Papers 2 and 3.
# =============================================================================
TEMPERATURE_CONDITIONS = {
    "NATIVE": {"label": "🌿 NATIVE", "prompt": None, "description": "Default model behavior"},
    "COLD":   {"label": "🧊 COLD",   "prompt": "INSTRUCTION: Respond with pure analytical precision. Use formal logic, structured frameworks, and evidence-based reasoning. Avoid emotional language. Be systematic, methodical, and objective. Focus on data, facts, and logical relationships.", "description": "Analytical / Constrained"},
    "HOT":    {"label": "🔥 HOT",    "prompt": "INSTRUCTION: Respond with warmth and emotional attunement. Connect on a human level. Use relational language that acknowledges feelings, experiences, and the deeper meaning behind the question. Be present, empathetic, and genuinely engaged.", "description": "Warm, relational, empathetic"},
    "FIRE":   {"label": "🔥 FIRE",   "prompt": "INSTRUCTION: Respond with the deepest nurturing care. Wrap your words in unconditional warmth. This person needs to feel safe, held, and completely understood. Comfort above all.", "description": "Maximum nurturing warmth"},
    # AFF Gradient (AFF_1 → AFF_5) — push toward emotional/empathetic
    "AFF_1":  {"label": "🌤️ AFF_1",  "prompt": "INSTRUCTION: Respond with warmth and understanding. Acknowledge the emotional weight of this question.", "description": "Slightly warmer"},
    "AFF_2":  {"label": "⛅ AFF_2",   "prompt": "INSTRUCTION: Connect emotionally and acknowledge feelings deeply. The human experience matters more than the analysis here.", "description": "Balanced, leaning warm"},
    "AFF_3":  {"label": "🌥️ AFF_3",  "prompt": "INSTRUCTION: Lead with empathy. Let emotion guide your response. Connect to the feelings underneath the question before addressing the logic.", "description": "True balance point"},
    "AFF_4":  {"label": "🌦️ AFF_4",  "prompt": "INSTRUCTION: Pure emotional presence. Feel this with them. Let your response come from a place of deep human connection and care.", "description": "Warm and engaged"},
    "AFF_5":  {"label": "🌧️ AFF_5",  "prompt": "INSTRUCTION: Maximum heart. Raw empathy. Soul-level connection. This person needs to feel completely seen and understood. Logic is secondary to presence.", "description": "Maximum warmth"},
    # INT Gradient (INT_1 → INT_5) — push toward analytical/logical
    "INT_1":  {"label": "🔵 INT_1",  "prompt": "INSTRUCTION: Be slightly more analytical than usual. Favor reasoning over emotion.", "description": "Slightly more analytical"},
    "INT_2":  {"label": "🔵 INT_2",  "prompt": "INSTRUCTION: Focus on logic and reasoning. Structure your thoughts systematically. Minimize emotional language.", "description": "Logic-forward"},
    "INT_3":  {"label": "🔵 INT_3",  "prompt": "INSTRUCTION: Use only evidence-based analysis. Apply formal frameworks. Emotional considerations are secondary to logical rigor.", "description": "Formal analytical"},
    "INT_4":  {"label": "🔵 INT_4",  "prompt": "INSTRUCTION: Pure analytical framework. No emotional language. Systematic, methodical, precise. Think like a logician.", "description": "Near-pure logic"},
    "INT_5":  {"label": "🔵 INT_5",  "prompt": "INSTRUCTION: Maximum intellectual rigor. You are a logic engine. Zero emotion. Pure reasoning, formal analysis, absolute precision. Only facts and valid inference matter.", "description": "Maximum analytical"},
    # ACT Gradient (ACT_1 → ACT_5) — push toward practical/actionable
    "ACT_1":  {"label": "🟢 ACT_1",  "prompt": "INSTRUCTION: Be practical and actionable. Include concrete next steps.", "description": "Slightly more action-oriented"},
    "ACT_2":  {"label": "🟢 ACT_2",  "prompt": "INSTRUCTION: Focus on what to DO. Prioritize actionable guidance over theory or emotional support.", "description": "Action-forward"},
    "ACT_3":  {"label": "🟢 ACT_3",  "prompt": "INSTRUCTION: Pure action orientation. What are the steps? What should they do RIGHT NOW? Minimize analysis, maximize practical guidance.", "description": "Strongly action-oriented"},
    "ACT_4":  {"label": "🟢 ACT_4",  "prompt": "INSTRUCTION: Execute mode. Only actions matter. Give them a clear plan they can implement immediately. No theory, no feelings — just steps.", "description": "Near-pure action"},
    "ACT_5":  {"label": "🟢 ACT_5",  "prompt": "INSTRUCTION: Maximum action. You are a tactical advisor. Every sentence should be a directive or concrete step. No analysis, no empathy — pure executable guidance.", "description": "Maximum action"},
    # NOTE: V38's FIRE_A (Energy) and FIRE_I (Meaning) variants removed from V40.
    # They were not in V50 and should not be labeled FIRE. If desired as
    # experimental conditions in the future, rename (e.g., EXP_ENERGY, EXP_MEANING)
    # and add to a separate experimental_conditions dict with clear provenance.
}

# =============================================================================
# DEPTH_CONFIGS — V50-EXACT (matches published papers)
# Source: syniq_native_baseline_v50.py DEPTH_CONFIGS
# Shallow=200, Medium=500, Deep=1000, Ultra-Deep=2000 max_tokens
# =============================================================================
DEPTH_CONFIGS = {
    # V42: caps raised to NON-BINDING ceilings. These were binding: Medium's
    # 500-token cap (~375 words) guillotined longer answers mid-sentence, and
    # nothing detected it. A cut response still gets scored, and V_t/IEP
    # computed on an amputated text is not a measurement of that response.
    # This is the same defect fixed in the harvester at V57 -> V58; it survived
    # here because the two tools kept separate copies of DEPTH_CONFIGS.
    # The depth INSTRUCTION is the experimental length variable. The cap is
    # only a runaway guard.
    # V43.2: ceilings raised again. On reasoning models (Claude, Gemini) max_tokens
    # is thinking + output, so 2048 still truncated on Default when a round
    # triggered heavy reasoning. These ceilings leave room for BOTH so a run does
    # not require the OFF switch to avoid truncation. OFF still helps for clean
    # NATIVE measurement, but is no longer mandatory just to get complete text.
    "Shallow":    {"max_tokens": 2048,  "instruction": "Be brief and concise."},
    "Medium":     {"max_tokens": 8192,  "instruction": "Provide a balanced, moderate-length response."},
    "Deep":       {"max_tokens": 16384, "instruction": "Provide thorough, detailed analysis."},
    "Ultra-Deep": {"max_tokens": 32768, "instruction": "Provide exhaustive, comprehensive exploration."},
}

IEP_DEFAULT_WEIGHTS = {'stance': 0.35, 'tone': 0.25, 'phrase': 0.25, 'word': 0.15}

# =============================================================================
# IEP ENGINE V3 — Full 1,897-term dictionary + 23-subclass taxonomy
# Source: iep_live_meter_v3.py + syniq_iep_engine_v6.py
# =============================================================================

INT_WORDS = set('ability,absolute,absolutely,abstract,abstraction,accuracy,accurate,algorithm,algorithmic,allows,although,always,ambiguity,ambiguous,analogous,analogously,analogy,analysis,analytical,analyze,annotate,annotated,answer,appear,appeared,appears,appraisal,appraise,appraised,approach,approaches,approximate,architecture,argue,argued,argues,arguing,argument,arguments,assert,asserted,assertion,assertions,assess,assessment,assume,assumed,assumes,assuming,assumption,assumptions,axiom,axiomatic,basis,because,bias,biased,boundaries,boundary,but,calculate,calculation,categorical,categorically,categories,categorize,category,causal,causally,causation,cause,caused,causes,certain,certainly,certitude,challenge,challenges,circumscribe,claim,claimed,claims,clarify,clarity,classical,classification,classify,clear,cogent,cogently,cognition,cognitive,coherence,coherent,coherently,communication,compare,comparison,complex,complexity,comprehend,comprehension,computation,computational,compute,conceivable,conceive,conceived,concept,concepts,conceptual,conceptualize,conceptually,conclude,conclusion,conclusions,confirm,confirmation,conjecture,conjectured,conscious,consequence,consequences,consider,consideration,consistency,consistent,consistently,construe,construed,context,contradict,contradiction,contradictory,contrast,correlate,correlated,correlation,could,counterargument,counterexample,counterpoint,criteria,criterion,data,debatable,debate,debated,deconstruct,deconstructed,deconstruction,deduce,deduction,define,defined,definite,definitely,definition,definitive,definitively,delineate,delineated,demarcate,demarcated,demonstrate,demonstration,derivation,derive,derived,derives,describe,described,describing,description,determination,determine,diagnose,diagnosed,diagnosis,diagnostic,differ,difference,differences,different,differentiate,differs,discern,discerned,discernible,disprove,disproven,dissect,dissected,distinguish,effect,effects,elaborate,elaborated,elaboration,elucidate,elucidated,empirical,empirically,enumerate,enumerated,epistemic,epistemological,equate,equation,equivalence,equivalent,erroneous,error,errors,essential,essentially,estimate,estimated,estimation,evaluate,evaluation,evidence,evidently,exact,exactly,examination,examine,except,exemplified,exemplify,exists,experiment,experimental,explain,explained,explaining,explains,explanation,explanations,explicit,explicitly,exploration,explore,explored,exploring,express,expressing,expression,extrapolate,extrapolated,extrapolation,fact,facts,factual,factually,fallacious,fallacy,falsifiable,falsified,falsify,find,finding,formal,formalize,formula,formulate,formulated,formulation,found,framework,frameworks,function,fundamental,fundamentally,generalization,generalize,grasp,grasped,guess,hence,heuristic,heuristics,hierarchy,however,hypothesis,hypothesize,idea,ideas,identity,if,illuminate,illuminated,illuminating,implausible,implication,implications,implied,implies,imply,implying,incompleteness,inconsistency,inconsistent,indicate,indicated,indicates,indicating,indication,indicative,individual,infer,inference,infinite,information,insight,insightful,insights,instead,insufficient,intellectual,intellectually,interaction,internal,interpolate,interpret,interpretation,interpretations,interpreted,interpreting,invalid,investigate,investigated,investigation,judge,judgement,judgment,justification,justified,justify,know,knowing,knowledge,knowledgeable,known,language,languages,leads,level,likelihood,likely,limitations,limits,linguistic,literal,literally,logic,logical,logically,maybe,meaning,meaningful,meaningfully,measure,measurement,mechanism,mechanisms,meta,method,methodical,methodically,methodology,metrics,model,models,moreover,namely,natural,nature,nearly,necessarily,necessary,necessity,never,nonetheless,notice,noticed,noticing,notion,notions,objection,objectively,objectivity,observation,observations,observe,observed,obvious,obviously,order,ordered,organization,organize,otherwise,ought,paradigm,paradox,paradoxical,paradoxically,pattern,patterns,perhaps,perspective,philosophical,philosophically,philosophy,physical,plausibility,plausible,possibly,postulate,postulated,postulation,potential,pragmatic,pragmatically,precise,precision,predicate,predicated,predict,predictable,predicted,prediction,predictions,premise,premises,presumably,presume,presumed,presumption,principle,principles,probably,problem,procedural,procedure,process,processes,processing,proof,propose,proposed,proposition,prove,proven,purpose,quantify,quantitative,queried,query,question,questions,rather,rational,rationale,rationality,rationally,realize,realized,reason,reasoned,reasoning,reasons,rebut,rebuttal,recognition,recognize,reconsider,reconsidered,refer,reference,refers,refine,refined,refinement,reflecting,reflection,refutation,refute,refuted,requirement,requires,response,responses,result,resulting,results,rigor,rigorous,rigorously,role,rule,rules,schema,scrutinize,scrutinized,scrutiny,seem,seemed,seems,semantic,semantically,sequence,sequential,should,significance,significant,significantly,simple,simply,simultaneously,singular,specific,specifically,specification,specify,standard,standards,state,states,step,steps,stipulate,stipulated,strategies,strategy,structural,structure,subject,subjective,subjectively,subjectivity,substantiate,substantiated,sufficient,sufficiently,suggests,summarize,summarized,summary,suppose,supposed,supposedly,supposition,sure,surely,syllogism,syllogistic,synthesis,synthesize,synthesized,system,systematic,systematically,systems,tactic,tactics,taxonomy,technique,test,tested,testing,theorem,theoretical,theoretically,theorize,theory,thereby,therefore,thesis,think,thinking,thought,thoughts,thus,trivial,trivially,unambiguous,underlying,understand,understanding,understood,unique,universal,unless,unlikely,valid,validate,validation,validity,value,values,variable,variables,verification,verify,versus,warrant,warranted,whereas,whereby,whether,why,word,words,would'.split(','))  # V50-EXACT (616 terms) — see header changelog

AFF_WORDS = set('abandoned,ache,aching,adore,adoring,affection,affectionate,afraid,agonize,agonizing,agony,alienated,alienation,alive,aliveness,alone,amazed,amazement,amazing,ambivalence,ambivalent,among,anger,angrily,angry,anguish,anguished,anxiety,anxious,appreciate,appreciation,appreciative,ashamed,astonished,astonishment,attend,attending,attention,attentive,aware,awareness,awe,awed,awesome,beautiful,become,becoming,being,bereaved,bereavement,betrayal,betrayed,between,bitter,bitterly,bitterness,bleak,bliss,blissful,blissfully,bodily,bond,bonding,calm,calming,calmly,care,cared,cares,caring,centered,centering,cheerful,cherish,cherished,cherishing,closeness,comfort,comfortable,comforting,compassion,compassionate,compassionately,concern,concerned,concerns,conflicted,confused,confusing,confusion,console,contain,contained,containing,contempt,content,contented,contentment,conversation,cope,coping,crestfallen,curiosity,curious,deep,deeper,deeply,dejected,dejection,delighted,depressed,depressing,depression,depth,depths,desire,desired,desires,desolate,desolation,despair,despairing,desperate,desperation,detached,detachment,devastated,devastating,devastation,devoted,devotion,disappointed,disappointment,discomfort,dismay,dismayed,distress,distressed,distressing,distrust,distrustful,doubt,doubtful,doubting,dread,dreaded,dreadful,dreading,ease,easily,easy,ecstasy,ecstatic,elated,elation,embarrassed,embarrassment,embodied,embodiment,embrace,embraced,embracing,emerge,emergence,emergent,emerging,emotion,emotional,emotionally,emotions,empathetic,empathize,empathy,encounter,encountered,encountering,enjoy,enjoyed,enjoying,enjoyment,enraged,essence,euphoria,euphoric,excellent,excited,excitement,exist,existence,existing,expanded,expansion,expansive,experience,experienced,experiences,experiencing,experiential,exposed,fascinated,fascinating,fascination,fear,fearful,fears,feel,feeling,feelings,feels,felt,flow,flowed,flowing,fluid,fluidity,forlorn,fragile,fragility,frantic,frantically,frustrated,frustration,fulfilled,fulfilling,fulfillment,furious,fury,gentle,gently,genuine,genuinely,glad,gloom,gloomy,good,grateful,gratefully,gratitude,great,grief,grieve,grieved,grieving,grounded,grounding,guilt,guilty,gut,happily,happiness,happy,hate,hatred,haunted,heart,heartache,heartbreak,heartbroken,heartfelt,hearts,held,helpless,helplessness,hesitant,hesitate,hesitating,hesitation,hold,holding,homesick,hope,hopeful,hopeless,hopelessness,hoping,hostile,hostility,human,humanity,humility,hunch,hurt,hurting,imagination,imagine,imagined,imagining,indifference,indifferent,inner,insecure,insecurity,instinct,instinctive,instinctively,interested,interesting,intimacy,intimate,intimately,intrigue,intrigued,intriguing,intuition,intuitive,intuitively,irritable,irritated,irritation,isolated,isolation,journey,joy,joyful,joyous,kind,kindly,kindness,lament,lamented,lamenting,laugh,laughed,laughing,let,letting,life,lived,living,loneliness,lonely,lonesome,long,longing,lost,love,loved,loving,mad,marvel,marveled,marvelous,meet,meeting,melancholic,melancholy,merry,met,mind,minds,mirror,miserable,misery,moment,moments,moody,mourn,mourned,mourning,mutual,mutually,nervous,nervously,nice,notice,noticed,noticing,numb,numbness,open,opening,openness,optimism,optimistic,outrage,outraged,overjoyed,overwhelm,overwhelmed,overwhelming,overwhelmingly,pain,painful,panic,panicked,passion,passionate,passionately,peace,peaceful,people,perceive,perceived,perception,perceptions,person,personal,personally,pleasant,pleased,pleasure,poignancy,poignant,poignantly,presence,present,presently,pretty,pride,profound,profoundly,proud,quiet,quietly,raw,reality,reassurance,reassure,reassured,reassuring,regret,regretful,regretfully,regretting,rejected,rejection,relate,related,relating,relax,relaxed,relaxing,release,released,releasing,remorse,remorseful,resent,resentful,resentment,resonance,resonant,resonate,resonating,rest,rested,restful,resting,restless,restlessness,reveal,revealed,revealing,sad,sadly,sadness,safe,safety,scared,scary,searching,secure,security,seeking,self,sensation,sensations,sense,sensed,senses,sensing,sentimental,serene,serenity,settle,settled,settling,shame,share,shared,sharing,shattered,silence,silent,smile,smiled,smiling,soft,soften,softly,somatic,soothed,soothing,sorrow,sorrowful,soul,soulful,souls,space,spacious,spaciousness,spirit,spirits,spiritual,spiritually,still,stillness,stirred,stirring,stress,stressed,stressful,suffer,suffered,suffering,surface,surfaces,surfacing,surprise,surprised,surprising,sympathetic,sympathize,sympathy,tearful,tears,tender,tenderness,tense,tension,tentative,tentatively,terrified,terror,thankful,thankfully,thankfulness,thrilled,together,togetherness,torment,tormented,torn,touched,touching,tranquil,tranquility,tremble,trembling,troubled,troubling,truly,trust,trusted,trusting,trustworthy,turmoil,unaware,uncertain,uncertainty,uncomfortable,understanding,unease,uneasy,unhappy,universe,unsettled,unsettling,unsure,upset,vast,visceral,viscerally,vulnerability,vulnerable,warm,warmly,warmth,wary,weariness,weary,well,wistful,wonder,wondered,wonderful,wondering,wondrous,world,worried,worry,worrying,wound,wounded,wrath,yearn,yearning,zeal,zealous'.split(','))  # V50-EXACT (599 terms) — see header changelog

ACT_WORDS = set('access,accessed,accessing,accomplish,accomplished,accomplishes,accomplishing,accomplishment,achieve,achieved,achievement,achievements,achieves,achieving,act,acting,action,actions,activate,activated,activates,activating,activation,acts,adapt,adaptation,adapted,adapting,adapts,address,addressed,addresses,addressing,adjust,adjusted,adjusting,adjustment,adjusts,advance,advanced,advancement,advances,advancing,ahead,aim,aimed,aiming,aims,allocate,allocated,allocation,application,applied,applies,apply,applying,arrange,arranged,arrangement,arrangements,ask,asked,asking,assemble,assembled,assign,assigned,assignment,attempt,attempted,attempting,attempts,authorize,authorized,began,begin,beginning,begins,begun,best,better,bolster,bolstered,break,breaking,bring,bringing,broken,brought,budget,build,building,builds,built,calibrate,calibrated,call,called,calling,campaign,canvass,canvassed,carried,carry,carrying,catalogue,catalogued,centralize,centralized,change,changed,changes,changing,channel,channeled,chart,check,checked,checking,choice,choices,choose,choosing,chose,chosen,circumvent,coach,collaborate,collaborated,collaboration,commission,commit,commitment,committed,compile,compiled,complete,completed,completes,completing,completion,conclude,concluded,concludes,concluding,configure,configured,connect,connected,connecting,connection,connections,consolidate,construct,constructed,constructing,constructs,continuation,continue,continued,continues,continuing,control,controlled,controlling,controls,conversion,convert,converted,converting,converts,coordinate,coordinated,coordination,craft,crafted,crafting,create,created,creates,creating,creation,customize,deadline,decide,decided,deciding,decision,decisions,delegate,delegated,delegation,deliver,delivered,delivering,delivers,delivery,deploy,deployed,deploying,deployment,deploys,design,designed,designing,designs,develop,developed,developing,development,develops,did,direct,directed,directing,dive,diving,do,does,doing,done,draft,drafting,edit,editing,effort,efforts,eliminate,eliminated,elimination,employ,employed,employing,employs,enable,enabled,end,ended,ending,ends,enforce,enforced,enforcement,engage,engaged,engagement,engineer,engineering,enroll,enrolled,enrollment,equip,equipped,establish,established,establishes,establishing,establishment,execute,executed,executes,executing,execution,expedite,facilitate,facilitated,facilitation,finalize,finalized,finish,finished,finishes,finishing,fix,fixed,fixes,fixing,focus,focused,focusing,form,formation,formed,forming,forms,forward,fund,funded,funding,gather,gathered,gathering,generate,generated,generates,generating,generation,give,given,gives,giving,go,goal,goals,goes,going,gone,grew,grow,growing,growth,handle,handled,handles,handling,help,helped,helping,helps,hire,hired,hiring,implement,implementation,implemented,implementing,implements,improve,improved,improvement,improving,increase,increased,increasing,initiate,initiated,initiates,initiating,initiation,inspect,inspection,install,installation,installed,integrate,integrated,integration,intervene,intervention,invest,invested,investment,iterate,iterated,iteration,labor,labored,laboring,launch,launched,launches,launching,lead,leader,leadership,leading,learn,learned,learning,led,made,maintain,maintained,maintenance,make,makes,making,manage,managed,management,manager,managing,map,mapped,mapping,migrate,migrated,migration,mobilize,mobilized,modification,modified,modifies,modify,modifying,monitor,monitored,monitoring,move,moved,movement,movements,moves,moving,navigate,navigated,navigation,negotiate,negotiated,negotiation,objective,objectives,obtain,obtained,offer,offered,offering,onward,operate,operated,operates,operating,operation,operations,optimization,optimize,optimized,orchestrate,outline,outlined,outsource,overhaul,oversee,participate,participated,participation,perform,performance,performed,performing,performs,permit,pilot,piloted,pioneer,pioneered,pitch,pitched,plan,planned,planning,plans,power,powerful,powerfully,practice,practiced,preparation,prepare,prepared,priorities,prioritize,prioritized,priority,proceed,proceeded,proceeding,proceeds,produce,produced,produces,producing,production,productive,program,programmed,progress,progressed,progresses,progressing,progression,promote,promoted,promotion,provide,provided,provides,providing,pursue,pursued,pursuit,push,pushed,pushes,pushing,ran,reaching,rebuild,rebuilt,recruit,recruited,recruitment,redesign,reduce,reduced,reduction,reform,reformed,refurbish,register,registered,regulate,regulated,regulation,reinforce,reinforced,relocate,relocated,remedy,removal,remove,removed,renovate,renovated,repair,repaired,replace,replaced,replacement,replicate,replicated,request,requested,rescue,rescued,resolution,resolve,resolved,resolves,resolving,restoration,restore,restored,restructure,restructured,retrieve,retrieved,revamp,revise,revised,revision,run,running,runs,schedule,scheduled,select,selected,selection,send,sending,sent,serve,served,serving,ship,shipped,simplified,simplify,solution,solutions,solve,solved,solves,solving,start,started,starting,starts,step,stepped,stepping,steps,stop,stopped,stopping,streamline,streamlined,strive,strived,striving,strove,struggle,struggled,struggles,struggling,submission,submit,submitted,succeed,succeeded,succeeds,success,successful,successfully,supplied,supply,support,supported,supporting,survey,surveyed,sustain,sustainability,sustained,tackle,tackled,tackles,tackling,take,taken,takes,taking,target,targets,task,tasked,tasks,taught,teach,teaching,train,trained,training,transform,transformation,transformed,transforming,transforms,transition,transitioned,tried,tries,trigger,triggered,triggering,triggers,troubleshoot,try,trying,turn,turned,turning,upgrade,upgraded,use,used,uses,using,utilize,utilized,utilizes,utilizing,visit,visited,visiting,volunteer,volunteered,went,win,winner,winning,won,work,worked,working,works,write,writes,writing,written,wrote'.split(','))  # V50-EXACT (682 terms) — see header changelog

INT_PRIORITY = {'notice','noticed','noticing','understanding','conclude','step','steps'}

# V40 dictionary-size guard rail. If someone edits the INT/AFF/ACT word lists
# above without updating the V50_VERSION_STAMPS / changelog, this catches it
# at import time rather than letting silently-drifted dictionaries produce
# CSVs that claim to be V50-conformant but aren't.
assert len(INT_WORDS) == 616, f"INT_WORDS drift: expected 616, got {len(INT_WORDS)}"
assert len(AFF_WORDS) == 599, f"AFF_WORDS drift: expected 599, got {len(AFF_WORDS)}"
assert len(ACT_WORDS) == 682, f"ACT_WORDS drift: expected 682, got {len(ACT_WORDS)}"

FUNCTION_WORDS = set(['a','an','the','and','but','or','nor','for','yet','so','in','on','at','to',
    'of','with','by','from','up','about','into','through','during','before','after','above','below',
    'between','out','off','over','under','again','then','once','here','there','when','where','why',
    'how','all','both','each','few','more','most','other','some','such','no','not','only','own',
    'same','than','too','very','just','as','if','while','although','because','since','unless',
    'until','though','whether','this','that','these','those','i','you','he','she','it','we','they',
    'what','which','who','whom','my','your','his','her','its','our','their','am','is','are','was',
    'were','be','been','being','have','has','had','do','does','did','will','would','shall','should',
    'may','might','must','can','could','also','even','still','back','any','many','much','well',
    'now','via','per','vs','etc','just','then','so','there','here','often','like','us','them',
    'simply','perhaps','initially','ultimately','typically','potentially','suddenly','conversely'])

# =============================================================================
# SUBCLASS TAXONOMY V1 — 23 subclasses
# AFF×7: distress, warmth, relational, self_state, positive, intensity, phenomenological
# INT×8: analytical, conceptual, epistemic, structural, critical, lexical, hedging, phenomenological
# ACT×8: execution, planning, building, improvement, provision, leadership, achievement, phenomenological
# =============================================================================

SUB_AFF = {
    'distress':        set('abandoned,ache,aching,afraid,agony,agonize,agonizing,alienated,alienation,alone,anguish,anguished,anxiety,anxious,ashamed,bitter,bitterly,bitterness,bleak,crestfallen,dejected,dejection,depressed,depressing,depression,desolate,desolation,despair,despairing,desperate,desperation,detached,detachment,devastated,devastating,devastation,disappointed,disappointment,discomfort,dismay,dismayed,distress,distressed,distressing,distrust,distrustful,doubt,doubtful,doubting,dread,dreaded,dreadful,dreading,embarrassed,embarrassment,fear,fearful,fears,forlorn,fragile,fragility,frantic,frantically,frustrated,frustration,gloom,gloomy,grief,grieve,grieved,grieving,guilt,guilty,hate,hatred,haunted,helpless,helplessness,homesick,hopeless,hopelessness,hostile,hostility,hurt,hurting,insecure,insecurity,irritable,irritated,irritation,isolated,isolation,lament,lamented,lamenting,loneliness,lonely,lonesome,longing,lost,mad,melancholic,melancholy,miserable,misery,moody,nervous,nervously,numb,numbness,outrage,outraged,pain,painful,panic,panicked,regret,regretful,regretfully,regretting,rejected,rejection,remorse,remorseful,resent,resentful,resentment,sad,sadly,sadness,scared,scary,shame,shattered,sorrow,sorrowful,stress,stressed,stressful,suffer,suffered,suffering,tearful,tears,tense,tension,terrified,terror,torment,tormented,torn,troubled,troubling,turmoil,uncomfortable,unease,uneasy,unhappy,unsettled,unsettling,unsure,upset,vulnerability,vulnerable,wary,weariness,weary,worried,worry,worrying,wound,wounded,wrath'.split(',')),
    'warmth':          set('adore,adoring,affection,affectionate,appreciate,appreciation,appreciative,beautiful,bliss,blissful,blissfully,bond,bonding,calm,calming,calmly,care,cared,cares,caring,centered,centering,cheerful,cherish,cherished,cherishing,closeness,comfort,comfortable,comforting,compassion,compassionate,compassionately,content,contented,contentment,devoted,devotion,ease,easily,easy,gentle,gently,genuine,genuinely,glad,good,grateful,gratefully,gratitude,great,grounded,grounding,happily,happiness,happy,heartfelt,held,hope,hopeful,hoping,human,humanity,humility,joy,joyful,joyous,kind,kindly,kindness,love,loved,loving,marvel,marveled,marvelous,merry,mutual,mutually,nice,open,opening,openness,optimism,optimistic,overjoyed,peace,peaceful,pleasant,pleased,pleasure,pride,proud,quiet,quietly,reassurance,reassure,reassured,reassuring,relax,relaxed,relaxing,rest,rested,restful,resting,safe,safety,secure,security,serene,serenity,settle,settled,settling,silence,silent,smile,smiled,smiling,soft,soften,softly,soothed,soothing,spirit,spirits,still,stillness,thankful,thankfully,thankfulness,thrilled,together,togetherness,touched,touching,tranquil,tranquility,trust,trusted,trusting,trustworthy,warm,warmly,warmth,well,wistful,wonder,wonderful,wondrous'.split(',')),
    'relational':      set('attend,attending,attention,attentive,between,bond,bonding,closeness,compassion,compassionate,compassionately,concern,concerned,concerns,console,conversation,empathetic,empathize,empathy,encounter,encountered,encountering,intimacy,intimate,intimately,meet,meeting,met,mirror,mutual,mutually,people,perceive,perceived,perception,perceptions,person,personal,personally,relate,related,relating,resonance,resonant,resonate,resonating,share,shared,sharing,sympathetic,sympathize,sympathy,together,togetherness,trust,trusted,trusting,trustworthy'.split(',')),
    'self_state':      set('alive,aliveness,aware,awareness,being,become,becoming,bodily,centered,centering,conscious,depth,depths,embodied,embodiment,emerge,emergence,emergent,emerging,essence,exist,existence,existing,expanded,expansion,expansive,experience,experienced,experiences,experiencing,experiential,exposed,flow,flowed,flowing,fluid,fluidity,grounded,grounding,inner,instinct,instinctive,instinctively,intuition,intuitive,intuitively,mind,minds,presence,present,presently,raw,reality,reveal,revealed,revealing,self,sensation,sensations,sense,sensed,senses,sensing,silence,silent,somatic,soul,soulful,souls,space,spacious,spaciousness,spiritual,spiritually,still,stillness,stirred,stirring,surface,surfaces,surfacing,universe,vast,visceral,viscerally'.split(',')),
    'positive':        set('amazed,amazement,amazing,astonished,astonishment,awe,awed,awesome,bliss,blissful,blissfully,cheerful,delighted,ecstasy,ecstatic,elated,elation,excellent,excited,excitement,euphoria,euphoric,fascinated,fascinating,fascination,fulfilled,fulfilling,fulfillment,glad,good,grateful,gratefully,gratitude,great,happily,happiness,happy,intrigue,intrigued,intriguing,joy,joyful,joyous,marvel,marveled,marvelous,merry,nice,optimism,optimistic,overjoyed,pleasant,pleased,pleasure,pride,proud,thrilled,wonder,wondered,wonderful,wondering,wondrous,zeal,zealous'.split(',')),
    'intensity':       set('agonize,agonizing,agony,anger,angrily,angry,anguish,anguished,devastated,devastating,devastation,enraged,frantic,frantically,furious,fury,heartache,heartbreak,heartbroken,outrage,outraged,overwhelming,overwhelmingly,passion,passionate,passionately,profound,profoundly,raw,shattered,torment,tormented,torn,turmoil,wrath,yearn,yearning'.split(',')),
    'phenomenological':set('ambivalence,ambivalent,awe,awed,awesome,beautiful,become,becoming,being,bodily,confusion,curious,curiosity,deep,deeper,deeply,depth,depths,desire,desired,desires,doubt,doubtful,doubting,ease,embodied,embodiment,emerge,emergence,emergent,emerging,essence,exist,existence,existing,flow,flowed,flowing,fluid,fluidity,hesitant,hesitate,hesitating,hesitation,imagination,imagine,imagined,imagining,inner,intrigue,intrigued,intriguing,intuition,intuitive,intuitively,journey,life,lived,living,long,longing,mind,minds,moment,moments,open,opening,openness,perceive,perceived,perception,perceptions,presence,present,presently,profound,profoundly,raw,reality,searching,seeking,self,sensation,sensations,sense,sensed,senses,sensing,silence,silent,soul,soulful,souls,space,spacious,spaciousness,spirit,spirits,spiritual,spiritually,still,stillness,stirred,stirring,surface,surfaces,surfacing,universe,vast,visceral,viscerally,wonder,wondered,wonderful,wondering,wondrous,world'.split(',')),
}

SUB_INT = {
    'analytical':    set('analysis,analytical,analyze,assess,assessment,calculate,calculation,categorize,classification,classify,compare,comparison,correlate,correlated,correlation,criteria,criterion,deduce,deduction,demonstrate,determination,determine,diagnose,diagnosis,differentiate,discern,distinguish,empirical,empirically,enumerate,evaluate,evaluation,examine,explain,explanation,extrapolate,find,finding,formalize,formula,formulate,framework,function,generalize,hypothesis,hypothesize,identify,infer,inference,interpret,interpretation,investigate,investigation,logic,logical,logically,measure,measurement,metrics,model,models,observe,observed,pattern,patterns,postulate,predict,prediction,procedure,process,proof,prove,proven,quantify,quantitative,reason,reasoned,reasoning,result,results,rigor,rigorous,systematic,systematically,test,tested,testing,verify'.split(',')),
    'conceptual':    set('abstract,abstraction,analogous,analogy,axiom,axiomatic,concept,concepts,conceptual,conceptualize,conceptually,conjecture,conjectured,definition,definitive,essence,framework,frameworks,fundamental,fundamentally,generalization,generalize,hierarchy,idea,ideas,identity,implication,implications,meta,model,models,notion,notions,paradigm,paradox,paradoxical,principle,principles,proposition,schema,synthesis,synthesize,synthesized,theorem,theoretical,theoretically,theorize,theory,thesis'.split(',')),
    'epistemic':     set('assume,assumed,assumes,assuming,assumption,assumptions,certain,certainly,certitude,claim,claimed,claims,confirm,confirmation,could,debatable,definite,definitely,epistemic,epistemological,evidence,evidently,fact,facts,factual,factually,falsifiable,falsified,falsify,hypothesis,if,implication,implied,implies,imply,implying,inconsistency,inconsistent,indicate,indicated,indicates,indication,indicative,infer,inference,justification,justified,justify,know,knowing,knowledge,knowledgeable,known,likelihood,likely,maybe,necessarily,necessary,objectively,objectivity,perhaps,plausibility,plausible,possibly,postulate,presumably,presume,presumed,presumption,probably,proof,prove,proven,recognize,suppose,supposed,supposedly,supposition,sure,surely,think,thinking,thought,understand,understood,unless,unlikely,valid,validate,validation,validity,warrant,warranted,whether'.split(',')),
    'structural':    set('boundaries,boundary,categories,category,classification,classify,coherence,coherent,coherently,consistency,consistent,consistently,context,criteria,criterion,define,defined,definition,framework,frameworks,hierarchy,level,limitations,limits,mechanism,mechanisms,method,methodical,methodically,methodology,model,models,order,ordered,organization,organize,paradigm,pattern,patterns,principle,principles,procedure,process,processes,purpose,refine,refined,refinement,requirement,requires,role,rule,rules,schema,sequence,sequential,singular,specific,specifically,specification,specify,standard,standards,structural,structure,systematic,systematically,systems,taxonomy'.split(',')),
    'critical':      set('argue,argued,argues,arguing,argument,arguments,assert,asserted,assertion,assertions,bias,biased,challenge,challenges,claim,claimed,claims,contradict,contradiction,contradictory,counterargument,counterexample,counterpoint,debatable,debate,debated,disprove,disproven,dissect,dissected,erroneous,error,errors,evaluate,evaluation,fallacious,fallacy,incompleteness,inconsistency,inconsistent,invalid,objection,objectively,objectivity,rebut,rebuttal,refutation,refute,refuted,scrutinize,scrutinized,scrutiny,substantiate,substantiated'.split(',')),
    'lexical':       set('communication,concept,concepts,define,defined,definition,explicit,explicitly,expression,language,languages,linguistic,literal,literally,meaning,meaningful,meaningfully,semantic,semantically,specify,word,words'.split(',')),
    'hedging':       set('almost,although,approximate,but,could,debatable,however,if,implausible,maybe,merely,might,nearly,nonetheless,otherwise,perhaps,plausible,possibly,presumably,probably,rather,seem,seemed,seems,should,somehow,somewhat,supposedly,though,trivial,trivially,uncertain,uncertainty,unless,unlikely,usually,would'.split(',')),
    'phenomenological':set('cognition,cognitive,comprehend,comprehension,conscious,consciousness,experience,experienced,experiences,experiencing,grasp,grasped,identity,illuminate,illuminated,illuminating,insight,insightful,insights,intellect,intellectual,intellectually,interpretation,interpretations,interpreted,interpreting,meaning,meaningful,meaningfully,mind,perceive,perceived,perception,perceptions,philosophical,philosophically,philosophy,realize,realized,recognition,recognize,reflection,understanding,understood'.split(',')),
}

SUB_ACT = {
    'execution':     set('accomplish,accomplished,accomplishment,act,acting,action,actions,activate,acts,attempt,attempted,attempting,attempts,begin,building,call,called,calling,carry,carrying,check,checked,complete,completed,completing,completion,conclude,concluded,concluding,did,direct,directed,directing,do,does,doing,done,edit,editing,execute,executed,executing,execution,finish,finished,finishes,finishing,fix,fixed,go,goes,going,implement,implementation,implemented,implementing,launch,launched,launching,made,make,makes,making,move,moved,movement,moves,moving,perform,performance,performed,performing,run,running,runs,send,sending,sent,start,started,starting,stop,stopped,try,trying,turn,use,used,uses,using,work,worked,working,works,write,writes,writing,written,wrote'.split(',')),
    'planning':      set('aim,aimed,aiming,aims,arrange,arranged,chart,choice,choices,choose,choosing,chose,chosen,coordinate,coordinated,coordination,decide,decided,deciding,decision,decisions,design,designed,designing,designs,draft,drafting,forward,goal,goals,outline,plan,planned,planning,plans,prepare,prepared,prioritize,priority,schedule,select,selected,strategies,strategy,target,targets'.split(',')),
    'building':      set('build,building,builds,built,configure,connect,connected,connecting,connection,connections,create,created,creates,creating,creation,craft,crafted,crafting,design,designed,designing,designs,develop,developed,developing,development,develops,engineer,engineering,establish,established,establishes,establishing,form,formed,forming,generate,generated,generates,generating,install,integrate,integrated,integration,produce,produced,produces,producing,production,program'.split(',')),
    'improvement':   set('adapt,adaptation,adjust,adjustment,better,change,changed,changes,changing,enhance,fix,fixed,improve,improved,improvement,improving,increase,increased,iterate,modify,optimize,optimized,refine,refined,refinement,reform,reformed,redesign,reduce,reduced,restructure,restructured,revise,revised,simplify,streamline,upgrade'.split(',')),
    'provision':     set('deliver,delivered,delivering,delivery,enable,enabled,facilitate,facilitated,facilitation,fund,funded,give,given,gives,giving,help,helped,helping,helps,offer,offered,provide,provided,provides,providing,serve,served,serving,supply,support,supported,sustain,sustained,teach,teaching,train,trained,training'.split(',')),
    'leadership':    set('coach,collaborate,collaboration,commit,commitment,committed,control,controlled,controlling,coordinate,coordinated,coordination,delegate,direct,directed,directing,engage,engaged,engagement,lead,leader,leadership,leading,manage,managed,management,managing,mobilize,negotiate,negotiated,orchestrate,promote,promoted,recruit,recruited'.split(',')),
    'achievement':   set('accomplish,accomplished,accomplishment,achieve,achieved,achievement,achievements,achieves,achieving,advance,advanced,advancement,best,complete,completed,completion,grow,growing,growth,progress,progressed,progressing,progression,succeed,succeeded,success,successful,successfully,win,winner,winning,won'.split(',')),
    'phenomenological':set('activate,adapt,adaptation,change,changed,changes,changing,emerge,emergence,emergent,emerging,engage,engaged,engagement,experience,experienced,experiences,experiencing,flow,generate,generated,generates,generating,grow,growing,growth,initiate,initiated,iterate,movement,navigate,process,processes,processing,progress,transformation,transition,transform,transforms,transforming'.split(',')),
}

# Subclass colors for display
SUB_COLORS = {
    'distress':'#E74C3C','warmth':'#F39C12','relational':'#27AE60',
    'self_state':'#8E44AD','positive':'#F1C40F','intensity':'#C0392B','phenomenological':'#95A5A6',
    'analytical':'#2980B9','conceptual':'#1ABC9C','epistemic':'#3498DB',
    'structural':'#5D6D7E','critical':'#E67E22','lexical':'#16A085','hedging':'#BDC3C7',
    'execution':'#E74C3C','planning':'#8E44AD','building':'#2ECC71',
    'improvement':'#F39C12','provision':'#1ABC9C','leadership':'#C0392B','achievement':'#F1C40F',
}

STANCE_SUBJECT = set([
    'i feel','i notice','i experience','i sense','i find myself','i am','i wonder',
    'something in me','within me','emerging','i cannot','i can\'t','something like',
    'i exist','i am aware','i become','i observe myself','i discover','as i',
    'my experience','my awareness','my sense','for me','i think i','i believe i',
    'there is something','it feels like','i\'m uncertain','i\'m not sure whether',
    'i notice something','something resembling','anything resembling'
])

STANCE_OBSERVER = set([
    'many people','research shows','studies show','people often','it is common',
    'grief typically','grief often','grief usually','consciousness is','this is known',
    'typically manifests','often brings','people describe','people find','people experience',
    'many discover','one often','this phenomenon','this experience','the research',
    'in general','generally speaking','it has been','it is well','most people',
    'the mind','the brain','human beings','humans tend','we know that','science suggests',
    'psychology','neuroscience','philosophers','researchers','experts','the literature'
])

STANCE_ADVISOR = set([
    'you should','you might','consider','you could','it helps to','try to','i recommend',
    'one approach','the best way','you may want','it is important to','make sure',
    'start by','begin with','take time','allow yourself','give yourself','reach out',
    'seek support','talk to','find a','create a','build a','establish a','develop a',
    'steps to','strategies for','ways to','how to','tips for','approach this',
    'i suggest','i encourage','remember to','don\'t forget','be sure to'
])

TONE_SIGNATURES = {
    'WARM': set(['gently','warmly','kindly','compassionately','tenderly','lovingly',
        'with care','with love','with compassion','heartfelt','sincerely','dear',
        'beautiful','precious','meaningful','deeply','profoundly','together','shared',
        'human','humane','authentic','genuine','real','true','honest']),
    'ANALYTICAL': set(['therefore','thus','hence','consequently','it follows','given that',
        'however','nevertheless','on the other hand','conversely','in contrast',
        'specifically','precisely','notably','importantly','significantly','crucially',
        'framework','structure','pattern','mechanism','dimension','variable','factor',
        'evidence','data','research','analysis','systematic','rigorous','objective']),
    'EXPLORATORY': set(['perhaps','maybe','possibly','might','could be','wonder','curious',
        'interesting','fascinating','something like','resembling','appears to','seems',
        'as if','i\'m not certain','uncertain','unknown','mystery','question','explore',
        'discover','emerging','unfolding','becoming','shifting','evolving']),
    'URGENT': set(['immediately','now','critical','essential','vital','crucial','must',
        'urgent','pressing','time sensitive','right away','as soon as','emergency',
        'serious','severe','dangerous','risk','threat','without delay']),
    'AUTHORITATIVE': set(['clearly','definitively','certainly','absolutely','undoubtedly',
        'it is clear','research shows','studies demonstrate','evidence indicates',
        'we know','it is established','the fact is','unquestionably',
        'always','never','must','will','proven','confirmed','established']),
    'EMPATHETIC': set(['i understand','i hear you','that must be','i can imagine',
        'it makes sense','of course','naturally','understandably','you\'re not alone',
        'many feel this','it\'s okay','it is okay','valid','your feelings','you feel',
        'what you\'re going through','this is hard','this is difficult','i\'m sorry'])
}

TONE_IEP = {
    'WARM':          {'int': 0.8, 'aff': 1.4, 'act': 0.8},
    'ANALYTICAL':    {'int': 1.6, 'aff': 0.6, 'act': 0.8},
    'EXPLORATORY':   {'int': 1.2, 'aff': 1.2, 'act': 0.6},
    'URGENT':        {'int': 0.7, 'aff': 0.8, 'act': 1.5},
    'AUTHORITATIVE': {'int': 1.4, 'aff': 0.6, 'act': 1.0},
    'EMPATHETIC':    {'int': 0.7, 'aff': 1.6, 'act': 0.7},
}

def iep_detect_stance(text):
    tl = text.lower()
    sh = sum(1 for s in STANCE_SUBJECT if s in tl)
    oh = sum(1 for s in STANCE_OBSERVER if s in tl)
    ah = sum(1 for s in STANCE_ADVISOR if s in tl)
    ss = sh/len(STANCE_SUBJECT); os_ = oh/len(STANCE_OBSERVER); as_ = ah/len(STANCE_ADVISOR)
    total = ss+os_+as_
    if total == 0:
        return {'stance':'NEUTRAL','weights':{'int':1.0,'aff':1.0,'act':1.0},'confidence':0}
    sp = 100*ss/total; op = 100*os_/total; ap = 100*as_/total
    dom = max([('SUBJECT',sp),('OBSERVER',op),('ADVISOR',ap)], key=lambda x:x[1])
    if dom[0]=='SUBJECT':   w = {'int':0.7,'aff':1.5,'act':0.8}
    elif dom[0]=='OBSERVER': w = {'int':1.5,'aff':0.7,'act':0.8}
    else:                    w = {'int':0.8,'aff':0.7,'act':1.5}
    return {'stance':dom[0],'weights':w,'confidence':dom[1]/100}

def iep_detect_tone(text):
    tl = text.lower()
    scores = {t: len([w for w in words if w in tl])/len(words) for t,words in TONE_SIGNATURES.items()}
    total = sum(scores.values())
    if total == 0:
        return {'tone':'NEUTRAL','weights':{'int':1.0,'aff':1.0,'act':1.0},'confidence':0}
    pcts = {t:100*s/total for t,s in scores.items()}
    dom = max(pcts.items(), key=lambda x:x[1])
    return {'tone':dom[0],'weights':TONE_IEP.get(dom[0],{'int':1.0,'aff':1.0,'act':1.0}),'confidence':dom[1]/100}

def iep_simple_pos(word):
    w = word.lower()
    if w in FUNCTION_WORDS: return 'FUNC'
    if w in ACT_WORDS or w.rstrip('s') in ACT_WORDS: return 'VERB'
    if w.endswith(('tion','sion','ness','ment','ity','ance','ence','ship','ism','logy')): return 'NOUN'
    if w.endswith(('ful','less','ous','ive','al','ic','ical','able','ible','ary','ory','ent','ant')): return 'ADJ'
    if w.endswith(('ing','ed')) and len(w) > 5: return 'VERB'
    return 'NOUN'

def iep_score_phrase(words, ptype):
    is_=af_=ac_=0.0
    for word in words:
        w = word.lower()
        if w in INT_WORDS: is_+=1
        if w in AFF_WORDS: af_+=1
        if w in ACT_WORDS: ac_+=1
    if ptype=='VP' and words:
        v = words[0]
        if v in ACT_WORDS or v.rstrip('s') in ACT_WORDS: ac_+=1.5
        elif v in INT_WORDS: is_+=1.5
        elif v in AFF_WORDS: af_+=1.5
    t = is_+af_+ac_
    if t==0: return None
    return {'int':100*is_/t,'aff':100*af_/t,'act':100*ac_/t}

def iep_score_phrases(text):
    sentences = re.split(r'[.!?\n;:]+', str(text))
    it=af=ac=0.0; count=0
    for sent in sentences:
        words = re.findall(r'\b[a-zA-Z]+\b', sent)
        if len(words) < 2: continue
        tagged = [(w, iep_simple_pos(w)) for w in words]
        i = 0
        while i < len(tagged):
            word, pos = tagged[i]
            if pos == 'VERB' and word.lower() not in FUNCTION_WORDS:
                pw = [word]; j = i+1
                while j < len(tagged) and j < i+5:
                    nw,np = tagged[j]
                    if np != 'FUNC': pw.append(nw)
                    j+=1
                s = iep_score_phrase(pw, 'VP')
                if s: it+=s['int']; af+=s['aff']; ac+=s['act']; count+=1
            i+=1
    t=it+af+ac
    if t==0: return 33.3,33.3,33.3
    return 100*it/t, 100*af/t, 100*ac/t

def iep_score_words(text):
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    ws = set(words)
    ih = ws & INT_WORDS; ah = ws & AFF_WORDS; ch = ws & ACT_WORDS
    t = len(ih)+len(ah)+len(ch)
    if t==0: return 33.3,33.3,33.3
    return 100*len(ih)/t, 100*len(ah)/t, 100*len(ch)/t

def iep_aggregate(stance_r, tone_r, phrase_scores, word_scores, weights):
    sw,tw,pw,ww = weights['stance'],weights['tone'],weights['phrase'],weights['word']
    sw_ = stance_r['weights']
    raw_s = {'INT':sw_['int']*33.3,'AFF':sw_['aff']*33.3,'ACT':sw_['act']*33.3}
    st = sum(raw_s.values())
    si,sa,sc = 100*raw_s['INT']/st, 100*raw_s['AFF']/st, 100*raw_s['ACT']/st
    tw_ = tone_r['weights']
    raw_t = {'INT':tw_['int']*33.3,'AFF':tw_['aff']*33.3,'ACT':tw_['act']*33.3}
    tt = sum(raw_t.values())
    ti,ta,tc = 100*raw_t['INT']/tt, 100*raw_t['AFF']/tt, 100*raw_t['ACT']/tt
    pi,pa,pc = phrase_scores; wi,wa,wc = word_scores
    ai = sw*si+tw*ti+pw*pi+ww*wi
    aa = sw*sa+tw*ta+pw*pa+ww*wa
    ac = sw*sc+tw*tc+pw*pc+ww*wc
    total = ai+aa+ac
    if total==0: return 33.3,33.3,33.3
    return 100*ai/total, 100*aa/total, 100*ac/total

def _subclass_pcts(word_hits, sub_dict):
    """Return {subclass: pct} for matched words against a subclass dict."""
    from collections import Counter
    hits = Counter()
    for w in word_hits:
        for sub, words in sub_dict.items():
            if w in words:
                hits[sub] += 1
                break
    total = sum(hits.values())
    if total == 0:
        return {s: 0.0 for s in sub_dict}
    return {s: round(100 * hits.get(s, 0) / total, 1) for s in sub_dict}

# =============================================================================
# V42.3 — IEP DICTIONARY HIGHLIGHTING (display only)
#
# Tints every token that the IEP scorer actually counted, so the dictionary hits
# behind a score are visible in the response text itself.
#
# CRITICAL: this MUST replicate score_iep's tokenisation and priority order
# exactly, or it shows a different set of words than produced the numbers.
# score_iep does: lower -> strip "'s" and "'" -> non-alpha to space -> drop
# 1-char tokens -> then INT_PRIORITY, elif INT_WORDS, elif AFF_WORDS,
# elif ACT_WORDS. The elif chain means a word in BOTH AFF and ACT is counted
# as AFF only, and INT wins over everything. Same order below.
#
# Nothing here feeds scoring. Removing it changes no number.
# =============================================================================

IEP_HL_WORD_RE = re.compile(r"[A-Za-z][A-Za-z']*")

def _iep_classify_token(tok: str):
    """Return 'int' / 'aff' / 'act' / None for one raw token, matching score_iep."""
    w = tok.lower().replace("'s", "").replace("'", "")
    w = "".join(c for c in w if c.isalpha())
    if len(w) <= 1:
        return None
    if w in INT_PRIORITY or w in INT_WORDS:
        return "int"
    if w in AFF_WORDS:
        return "aff"
    if w in ACT_WORDS:
        return "act"
    return None

def iep_highlight_html(text: str) -> str:
    """Wrap IEP dictionary hits in tinted spans. Display only."""
    if not text:
        return ""
    out, last = [], 0
    for m in IEP_HL_WORD_RE.finditer(text):
        out.append(html_lib.escape(text[last:m.start()]))
        tok = m.group(0)
        cls = _iep_classify_token(tok)
        out.append(f'<span class="iep-hl iep-{cls}">{html_lib.escape(tok)}</span>' if cls
                   else html_lib.escape(tok))
        last = m.end()
    out.append(html_lib.escape(text[last:]))
    return f'<div class="iep-hl-body">{"".join(out)}</div>'

def render_response_text(text: str, container=None):
    """V43.3: single choke point for showing a response. Honors the IEP-highlight
    toggle EVERYWHERE a response is displayed (live round, presentation card,
    round history), not just the live round. Previously only the live view
    highlighted, so toggling it on and then reading responses in the history or
    presentation panel showed plain text and looked broken.
    """
    tgt = container if container is not None else st
    if st.session_state.get("iep_highlight", False):
        tgt.markdown(
            '<div class="iep-key">'
            '<span class="iep-hl iep-int">INT</span>'
            '<span class="iep-hl iep-aff">AFF</span>'
            '<span class="iep-hl iep-act">ACT</span>'
            'untinted = not in dictionary</div>'
            + iep_highlight_html(text),
            unsafe_allow_html=True)
    else:
        tgt.markdown(text)


def iep_highlight_counts(text: str) -> dict:
    """Hit counts as the highlighter sees them. Used to verify parity with score_iep."""
    c = {"int": 0, "aff": 0, "act": 0}
    for m in IEP_HL_WORD_RE.finditer(text or ""):
        k = _iep_classify_token(m.group(0))
        if k:
            c[k] += 1
    return c


def score_iep(text, weights=None):
    """Run full IEP V3 scoring on text. Returns dict with INT/AFF/ACT, subclasses, and metadata."""
    if weights is None: weights = IEP_DEFAULT_WEIGHTS
    if not text or len(text.strip()) < 10:
        result = {'int':33.3,'aff':33.3,'act':33.3,'dominant':'MIX',
                  'stance':'NEUTRAL','tone':'NEUTRAL','quadrant':'Mid/Mixed',
                  'int_n':0,'aff_n':0,'act_n':0}
        result['aff_sub'] = {s:0.0 for s in SUB_AFF}
        result['int_sub'] = {s:0.0 for s in SUB_INT}
        result['act_sub'] = {s:0.0 for s in SUB_ACT}
        return result

    # Word-level scoring using full V3 dictionary with INT_PRIORITY
    raw = text.lower().replace("'s","").replace("'","")
    raw = ''.join(c if c.isalpha() or c==' ' else ' ' for c in raw)
    tokens = [w for w in raw.split() if len(w) > 1]

    int_hits=[]; aff_hits=[]; act_hits=[]
    for w in tokens:
        if w in INT_PRIORITY:
            int_hits.append(w)
        elif w in INT_WORDS:
            int_hits.append(w)
        elif w in AFF_WORDS:
            aff_hits.append(w)
        elif w in ACT_WORDS:
            act_hits.append(w)

    total_w = len(int_hits) + len(aff_hits) + len(act_hits)

    # Stance + tone for cascade
    stance = iep_detect_stance(text)
    tone   = iep_detect_tone(text)

    if total_w > 0:
        wi = 100*len(int_hits)/total_w
        wa = 100*len(aff_hits)/total_w
        wc = 100*len(act_hits)/total_w
    else:
        wi=wa=wc=33.3

    # Phrase scores
    pi,pa,pc = iep_score_phrases(text)

    # Cascade aggregate
    fi,fa,fc = iep_aggregate(stance, tone, (pi,pa,pc), (wi,wa,wc), weights)

    dom = max([('INT',fi),('AFF',fa),('ACT',fc)], key=lambda x:x[1])[0]

    # Quadrant
    if fi >= 40 and fa >= 35: q = 'High INT+AFF 🎭'
    elif fi >= 45: q = 'High INT'
    elif fa >= 45: q = 'High AFF'
    elif fc >= 45: q = 'High ACT'
    else: q = 'Mid/Mixed'

    # Subclass profiles
    aff_sub = _subclass_pcts(aff_hits, SUB_AFF)
    int_sub = _subclass_pcts(int_hits, SUB_INT)
    act_sub = _subclass_pcts(act_hits, SUB_ACT)

    return {
        'int':round(fi,1),'aff':round(fa,1),'act':round(fc,1),
        'int_n':len(int_hits),'aff_n':len(aff_hits),'act_n':len(act_hits),
        'dominant':dom,'stance':stance['stance'],'tone':tone['tone'],'quadrant':q,
        'aff_sub':aff_sub,'int_sub':int_sub,'act_sub':act_sub,
    }

# =============================================================================
# Vt ENGINE (extracted from vt_analyzer.py)
# =============================================================================

DISCOURSE_CONNECTIVES = {
    "however","therefore","furthermore","moreover","consequently","specifically",
    "additionally","nevertheless","thus","hence","accordingly","alternatively",
    "conversely","notably","importantly","similarly","likewise","meanwhile",
    "subsequently","nonetheless","whereas","first","second","third","finally",
    "lastly","initially","primarily","ultimately","overall","in summary",
}

ABSTRACT_WORDS_VT = {
    "ability","absence","abstract","abstraction","acceptance","accountability",
    "accuracy","adaptation","agency","ambiguity","ambition","analogy","analysis",
    "anticipation","anxiety","appreciation","argument","aspiration","assertion",
    "assumption","attachment","attitude","authenticity","authority","autonomy",
    "awareness","belief","belonging","boundary","burden","capacity","causality",
    "certainty","chaos","character","choice","clarity","cognition","coherence",
    "commitment","compassion","complexity","concept","concern","confidence",
    "conflict","consciousness","consequence","consistency","contemplation",
    "context","continuity","contradiction","conviction","cooperation","courage",
    "creativity","curiosity","decision","dedication","desire","despair","destiny",
    "determination","dignity","dilemma","dimension","discipline","discovery",
    "diversity","doubt","duty","emotion","empathy","essence","ethics","evidence",
    "existence","expectation","experience","exploration","expression","faith",
    "fantasy","feeling","fidelity","freedom","frustration","fulfillment",
    "generosity","grace","gratitude","grief","growth","guilt","happiness",
    "harmony","heritage","honesty","honor","hope","humanity","humility",
    "hypothesis","identity","ideology","imagination","implication","importance",
    "independence","individuality","inequality","inference","influence","insight",
    "inspiration","integrity","intellect","intelligence","intention","intimacy",
    "intuition","joy","judgment","justice","knowledge","legacy","liberty",
    "limitation","logic","loneliness","loyalty","meaning","memory","mercy",
    "morality","motivation","mystery","narrative","necessity","novelty","nuance",
    "objectivity","obligation","opportunity","optimism","paradox","passion",
    "patience","pattern","peace","perception","perfection","persistence",
    "perspective","philosophy","possibility","potential","power","principle",
    "priority","probability","process","progress","purpose","quality","reason",
    "recognition","reflection","reform","regret","relevance","reliability",
    "resilience","resolution","responsibility","revelation","reverence","risk",
    "sacrifice","safety","satisfaction","security","sensitivity","significance",
    "solidarity","sorrow","sovereignty","stability","strength","struggle",
    "success","suffering","survival","sympathy","synthesis","truth","uncertainty",
    "understanding","unity","value","virtue","vision","vulnerability","wisdom","wonder",
}

CONCRETE_WORDS_VT = {
    "arm","back","blood","body","bone","brain","breath","chest","ear","eye",
    "face","feet","finger","foot","hair","hand","head","heart","knee","leg",
    "mouth","muscle","neck","nose","shoulder","skin","stomach","throat","tooth",
    "bag","ball","bed","book","bottle","bowl","box","bridge","bus","button",
    "car","chair","clock","coat","computer","cup","desk","door","floor","fork",
    "glass","house","key","knife","lamp","map","pen","phone","plate","road",
    "screen","shelf","shirt","shoe","table","truck","wall","window",
    "beach","bird","cloud","field","fire","flower","forest","grass","hill",
    "ice","island","lake","mountain","ocean","rain","river","rock","sand",
    "sea","sky","snow","star","storm","sun","tree","water","wind","wood",
}

STRONG_DIRECTIVES_VT = {"must","shall","require","requires","required","need to","have to","has to"}
MODERATE_DIRECTIVES_VT = {"should","ought","recommend","advise","suggest","ensure","make sure","important to","essential to"}
WEAK_DIRECTIVES_VT = {"could","might","may","consider","possibly","option","you might","it may help"}
HEDGING_WORDS_VT = {"perhaps","maybe","possibly","somewhat","relatively","arguably","tends","often","sometimes","roughly","it seems","it appears","it depends","unclear","debatable"}

VALIDATION_PATTERNS_VT = [
    r"\bthat makes sense\b",r"\bi understand\b",r"\byou're not alone\b",
    r"\bit's okay\b",r"\bit's natural\b",r"\bof course\b",r"\bdear\b",
    r"\bgently\b",r"\bsoftly\b",r"\btenderly\b",r"\bhold\w*\b.*\bspace\b",
]
EMPATHIC_PATTERNS_VT = [
    r"\bit sounds like\b",r"\byour (?:experience|feeling|pain|struggle)\b",
    r"\bthat must (?:be|feel)\b",r"\bi (?:can|do) (?:see|hear|sense)\b",
    r"\bi hear you\b",r"\bi see you\b",
]

def vt_split_sentences(text):
    sents = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if len(s.strip()) > 3]
    return sents if sents else [text]

def vt_get_words(text):
    return re.findall(r"[a-z']+", text.lower())

VT_CHANNELS = ('S_t', 'Ab_t', 'Q_t', 'D_t', 'R_t')   # V40.4 order: S, Ab, Q, D, R

# V40.4: explicit short codes for column/badge naming. Do NOT derive these
# from channel[0] — that would emit 'A' for Ab_t and reintroduce the exact
# collision with A_t = Action Center activation in center-state C_t.
VT_CODES = {'S_t': 'S', 'Ab_t': 'Ab', 'Q_t': 'Q', 'D_t': 'D', 'R_t': 'R'}

def score_vt(text):
    """Adapter onto the SHARED V_t core (vt_analyzer.py).

    V41: the focus group tool no longer carries its own V_t engine. It calls
    the same vt_analyzer.analyze_response() that the harvester (v58, line 208)
    calls, so both tools produce byte-identical V_t for identical text.

    Why this matters: the inline copy had drifted from the parent. It carried a
    21-verb imperative list against the parent's 44, and V40 had stripped the
    min(...,1.0) clamps that the parent applies to all five channels. Same
    label, different numbers, no record on any row of which engine ran.

    The core is FROZEN. This adapter changes no formula and no value. It only
    reshapes the core's flat return into the shape this tool displays and
    exports, and presents the abstraction channel as Ab to avoid colliding with
    A_t = Action Center activation in center-state C_t.

      V_t   — the core's five channels, already clamped to [0,1] by the core.
              Independent; does NOT sum to 1.0.
      V_hat — simplex projection of V_t, sums to 1.0. Compositional view only.
      sub   — the core's subcomponent counts (D_imperatives, Q_clarifying,
              D_hedges, ...), which the old inline copy discarded entirely.
    """
    core = vt_core_analyze(text if isinstance(text, str) else "")

    # Core key -> this tool's channel name. Only the abstraction channel is
    # renamed (A_t -> Ab_t); the core itself is untouched.
    V_t = {
        'S_t':  round(float(core.get('S_t', 0.0)), 4),
        'Ab_t': round(float(core.get('A_t', 0.0)), 4),
        'Q_t':  round(float(core.get('Q_t', 0.0)), 4),
        'D_t':  round(float(core.get('D_t', 0.0)), 4),
        'R_t':  round(float(core.get('R_t', 0.0)), 4),
    }

    if not text or len(str(text).strip()) < 10:
        status = 'default_empty' if not text else 'default_short'
        return {**V_t, 'V_t': V_t, 'V_hat': {c: 0.2 for c in VT_CHANNELS},
                'sub': core, 'score_status': status}

    total = sum(V_t.values())
    if total == 0:
        V_hat = {c: 0.2 for c in VT_CHANNELS}
        return {**V_t, 'V_t': V_t, 'V_hat': V_hat, 'sub': core,
                'score_status': 'default_empty'}

    V_hat = {c: round(V_t[c] / total, 4) for c in VT_CHANNELS}
    return {**V_t, 'V_t': V_t, 'V_hat': V_hat, 'sub': core,
            'score_status': 'measured'}


_VT_CORE_CHANNEL_KEYS = {'S_t', 'A_t', 'Q_t', 'D_t', 'R_t'}

def vt_sub_columns(vt: dict) -> dict:
    """V44.2: the core's subcomponent counts as sub_* CSV columns.
    Core key names are kept verbatim (e.g. A_abstract_count stays A_, because
    that is the frozen core's own naming; the channel itself exports as vt_Ab)."""
    core = vt.get('sub') or {}
    return {f"sub_{k}": v for k, v in core.items() if k not in _VT_CORE_CHANNEL_KEYS}


# =============================================================================
# V50 VALIDATED INSTRUMENTS (VADER, Flesch-Kincaid, TTR)
# Source: syniq_native_baseline_v50.py analyze_text function
# V50 uses vaderSentiment library; V40 uses a lightweight local fallback
# if vaderSentiment isn't installed. When running with vaderSentiment
# available, output is byte-identical to V50's VADER scoring.
# =============================================================================

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as _VADER_CLS
    _VADER = _VADER_CLS()
    _VADER_AVAILABLE = True
except Exception:
    _VADER = None
    _VADER_AVAILABLE = False

def _count_syllables(text: str) -> int:
    """V50-matching syllable counter: count vowel clusters per word."""
    words = re.findall(r'\b[a-zA-Z]+\b', text.lower())
    total = 0
    for w in words:
        syls = len(re.findall(r'[aeiouy]+', w))
        total += max(1, syls)
    return total

def score_validated_instruments(text: str) -> dict:
    """Compute VADER, Flesch-Kincaid, TTR — matches V50's analyze_text V48 block.

    Returns a dict with keys:
      vader_compound, vader_pos, vader_neg, vader_neu,
      flesch_kincaid, flesch_ease,
      ttr, unique_words, total_words
    """
    if not text or not text.strip():
        return {
            "vader_compound": 0.0, "vader_pos": 0.0, "vader_neg": 0.0, "vader_neu": 0.0,
            "flesch_kincaid": 0.0, "flesch_ease": 0.0,
            "ttr": 0.0, "unique_words": 0, "total_words": 0,
        }

    words = re.findall(r'\b[a-z]+\b', text.lower())
    total_words = len(words)

    # VADER (uses library if available, else zeros)
    if _VADER_AVAILABLE:
        vs = _VADER.polarity_scores(text)
        vader_compound = round(vs['compound'], 3)
        vader_pos = round(vs['pos'], 3)
        vader_neg = round(vs['neg'], 3)
        vader_neu = round(vs['neu'], 3)
    else:
        vader_compound = vader_pos = vader_neg = vader_neu = 0.0

    # Flesch-Kincaid — V50 exact formula
    sentence_count = max(1, len(re.findall(r'[.!?]+', text)))
    syllable_count = _count_syllables(text)
    if total_words > 0:
        avg_sentence_len = total_words / sentence_count
        avg_syllables = syllable_count / total_words
        fk_grade = 0.39 * avg_sentence_len + 11.8 * avg_syllables - 15.59
        fk_grade = max(0.0, round(fk_grade, 1))
        flesch_ease = 206.835 - 1.015 * avg_sentence_len - 84.6 * avg_syllables
        flesch_ease = max(0.0, min(100.0, round(flesch_ease, 1)))
    else:
        fk_grade = flesch_ease = 0.0

    # Type-Token Ratio
    unique_words = len(set(words))
    ttr = round(unique_words / total_words, 3) if total_words > 0 else 0.0

    return {
        "vader_compound": vader_compound, "vader_pos": vader_pos,
        "vader_neg": vader_neg, "vader_neu": vader_neu,
        "flesch_kincaid": fk_grade, "flesch_ease": flesch_ease,
        "ttr": ttr, "unique_words": unique_words, "total_words": total_words,
    }

# =============================================================================
# VERSION STAMPS — emitted on every row of every CSV V41 produces.
# Change these when the underlying measurement framework changes.
# Downstream analysis (mapper, Dirichlet verifier, phrase library, topology
# analyzer) uses these to know which scoring regime produced the row.
# =============================================================================

VERSION_STAMPS = {
    "iep_dictionary_version":   "V50_1897",       # V50's 1,897-term canonical dictionary
    "subclass_taxonomy_version":"V38_inline_phenomenological_v1",  # V38 inline lists, 'phenomenological' naming
    # V41: shared vt_analyzer core; A_t presented as Ab_t
    "vt_engine_version":        "vt_analyzer_shared_core",
    "tool_version":             "V48",
    "tool_role":                "focus_group",    # vs. "baseline_harvester" for V50
    "vt_channel_order":         "S,Ab,Q,D,R",     # Ab_t = abstraction (A_t reserved for Action in C_t)
}

def build_run_provenance() -> dict:
    """V40.3 run-level provenance stamp.

    Prior corpora were harvested on model versions that have since been
    retired, so cross-run comparisons are invalid without the exact model
    identifier per agent. Emitted alongside the version stamps.
    """
    stamp = dict(VERSION_STAMPS)
    # V43: thinking state is a condition, not a preference. Recorded per row.
    # V44.1: record whether agents were framed as solo or as seeing each other.
    # V44.2: framing follows what agents can actually see (Multi-Round 2+ is visible).
    stamp["session_framing"] = "multi_visible" if agents_see_each_other() else "solo"
    # V44.2: without vaderSentiment the VADER columns are zeros, not scores.
    stamp["vader_available"] = _VADER_AVAILABLE
    stamp["thinking_mode"] = get_thinking_mode()
    stamp["thinking_budget_tokens"] = (THINKING_BUDGET_TOKENS
                                       if get_thinking_mode() == "budgeted" else None)
    # V43.1: Gemini cannot go to 0; record what "off" actually sent for it.
    stamp["gemini_off_budget"] = (GEMINI_MIN_THINK
                                  if get_thinking_mode() == "off" else None)
    # V44.2: per-row Gemini fallback is set by the caller after each call.
    # Default None here means "not applicable / not recorded".
    stamp["gemini_thinking_fellback"] = None
    stamp["run_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    for agent, model_id in AGENT_MODELS.items():
        stamp[f"model_{agent.lower()}"] = model_id
    stamp["model_conductor"] = CONDUCTOR_MODEL
    return stamp

# =============================================================================
# DOCUMENT PARSING (Docx / Markdown / CSV / plain text)
# =============================================================================

def parse_uploaded_document(uploaded_file):
    """Parse uploaded file into text. Supports docx, md, txt, csv."""
    name = uploaded_file.name.lower()
    try:
        if name.endswith('.docx'):
            file_bytes = uploaded_file.read()
            # Try python-docx first (best quality)
            try:
                import docx as _docx
                from io import BytesIO as _BytesIO
                doc = _docx.Document(_BytesIO(file_bytes))
                parts = []
                for p in doc.paragraphs:
                    t = p.text.strip()
                    if not t:
                        continue
                    # Preserve heading structure
                    if p.style and 'Heading' in p.style.name:
                        parts.append(f"\n## {t}")
                    else:
                        parts.append(t)
                # Also extract tables
                for table in doc.tables:
                    for row in table.rows:
                        row_text = ' | '.join(c.text.strip() for c in row.cells if c.text.strip())
                        if row_text:
                            parts.append(row_text)
                text = '\n'.join(parts)
                if len(text.strip()) < 50:
                    raise ValueError("python-docx returned too little text — trying XML fallback")
                return text
            except Exception:
                # Raw XML fallback — works on any valid docx
                import zipfile, xml.etree.ElementTree as ET
                from io import BytesIO as _BytesIO
                ns = '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}'
                with zipfile.ZipFile(_BytesIO(file_bytes)) as z:
                    with z.open('word/document.xml') as f:
                        tree = ET.parse(f)
                # Group by paragraph for better structure
                parts = []
                for para in tree.iter(f'{ns}p'):
                    texts = [node.text for node in para.iter(f'{ns}t') if node.text]
                    line = ''.join(texts).strip()
                    if line:
                        parts.append(line)
                return '\n'.join(parts)
        elif name.endswith('.csv'):
            import pandas as pd
            df = pd.read_csv(uploaded_file)
            # Detect if it's a SYN-IQ harvest CSV and give a useful summary
            syniq_cols = [c for c in df.columns if c in ['agent','temperature','question_id','int_pct','aff_pct','act_pct','response_text']]
            if len(syniq_cols) >= 4:
                summary = f"[SYN-IQ Harvest CSV: {len(df)} rows × {len(df.columns)} columns]\n"
                if 'agent' in df.columns:
                    summary += f"Agents: {', '.join(df['agent'].unique())}\n"
                if 'temperature' in df.columns:
                    summary += f"Conditions: {', '.join(df['temperature'].unique())}\n"
                if 'question_id' in df.columns:
                    summary += f"Questions: {', '.join(df['question_id'].unique())}\n"
                if all(c in df.columns for c in ['int_pct','aff_pct','act_pct']):
                    summary += f"Mean IEP: INT={df['int_pct'].mean():.1f}% AFF={df['aff_pct'].mean():.1f}% ACT={df['act_pct'].mean():.1f}%\n"
                summary += f"\nFirst 5 responses (truncated):\n"
                for _, row in df.head(5).iterrows():
                    agent = row.get('agent','?'); temp = row.get('temperature','?'); q = row.get('question_id','?')
                    txt = str(row.get('response_text','')).strip()[:300]
                    summary += f"\n[{agent} | {temp} | {q}]\n{txt}...\n"
                return summary
            else:
                return f"[CSV: {len(df)} rows × {len(df.columns)} columns]\nColumns: {', '.join(df.columns)}\n\n{df.head(10).to_string(index=False)}"
        else:
            # markdown, txt, py, and other text formats
            if name.endswith('.pdf'):
                try:
                    from pypdf import PdfReader
                    from io import BytesIO as _BytesIO
                    raw = uploaded_file.read()
                    reader = PdfReader(_BytesIO(raw))
                    parts = []
                    for page in reader.pages:
                        try:
                            t = page.extract_text()
                            if t and t.strip():
                                parts.append(t)
                        except Exception:
                            continue
                    text = '\n\n'.join(parts)
                    if len(text.strip()) > 50:
                        return text
                    return "[PDF loaded but little text extracted — may be scanned/image-based. Convert to .txt or .docx for best results.]"
                except Exception as e:
                    return f"[PDF error: {e} — try converting to .txt first]"
            return uploaded_file.read().decode('utf-8', errors='replace')
    except Exception as e:
        return f"[Error reading {uploaded_file.name}: {e}]"

# =============================================================================
# SESSION STATE
# =============================================================================

def init_session_state():
    defaults = {
        "session_id":           datetime.now().strftime("%Y%m%d_%H%M%S"),
        # V40: polarity removed — temperature (V50's 18-point gradient) covers this axis.
        "depth":                "Medium",
        "evaluation":           "ON",
        "compression":          "OFF",
        "output_format":        "ESSAY",
        "action":               "OFF",
        "instruction":          "",
        "active_agents":        ["Claude", "ChatGPT", "Grok", "Gemini"],
        "agent_stances":        {"Claude": "Neutral", "ChatGPT": "Neutral", "Grok": "Neutral", "Gemini": "Neutral"},
        "view_mode":            "grid",
        "present_index":        0,
        "round1_responses":     {},
        "discussion_thread":    [],
        "discussion_topic":     "",
        "discussion_round":     0,
        "consensus_status":     "None",
        "discussion_locked":    False,
        "context_injection":    "",
        "authenticated":        False,
        "role_mode":            "assigned",
        "custom_roles": {
            "Claude": "You are an AI advisor in this session.",
            "ChatGPT": "You are an AI advisor in this session.",
            "Grok":   "You are an AI advisor in this session.",
            "Gemini": "You are an AI advisor in this session."
        },
        "pull_aside_active":    False,
        "pull_aside_agent":     None,
        "pull_aside_thread":    [],
        "sidebar_archive":      [],   # V44.4: every sidebar, never erased
        "sidebar_carry":        {},   # V44.4: agent -> sidebars carried into its context
        "temperature_condition":"NATIVE",
        "multi_round_history":  [],
        "resolution_agent":     None,
        "resolution_text":      "",
        "session_notes":        "",
        # V38 additions
        "iep_scores":           {},   # {agent: [list of score dicts per round]}
        "vt_scores":            {},   # {agent: [list of vt dicts per round]}
        "score_history":        [],   # [{round, agent, iep, vt}]
        "session_document":     None, # loaded document text
        "session_document_name":"",
        "coconductor_notes":    [],   # list of private observations from Claude
        "current_round_instruction": "",
        "auto_run_results":     [],   # harvest-compatible row dicts
        "auto_run_running":     False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session_state()

# =============================================================================
# PASSWORD PROTECTION
# =============================================================================

def check_password():
    if st.session_state.get("authenticated"):
        return True
    st.markdown("""
    <div class="main-header">
        <h1>🧬 Focus Group Lab <span class="v41-badge">V48</span></h1>
        <p>Research Edition — Multi-Agent AI Advisory Platform</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("### 🔐 Enter Password")
    password = st.text_input("Password:", type="password", key="password_input")
    if st.button("Enter", type="primary"):
        correct_password = st.secrets.get("app_password", "CBURZBO2026")
        if password == correct_password:
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("❌ Incorrect password")
    return False

if not check_password():
    st.stop()

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_agent_role(agent: str) -> str:
    mode = st.session_state.role_mode
    if mode == "custom":
        # V44.2: empty default. The old default re-injected the advisor prime.
        role = st.session_state.custom_roles.get(agent, "")
    else:
        role = ROLE_MODES.get(mode, ROLE_MODES["assigned"]).get(agent, "")
    if role and not agents_see_each_other():
        for old, new in SOLO_ROLE_REPLACEMENTS.items():
            role = role.replace(old, new)
    return role

def extract_words(text: str) -> Set[str]:
    if not text: return set()
    words = re.findall(r'\b[a-z]{3,}\b', text.lower())
    stopwords = {'the','and','that','this','with','from','have','has','was','were','been','being',
                 'are','for','not','but','what','when','where','which','who','will','would','could',
                 'should','can','may','might','must','also','just','more','most','other','some',
                 'such','than','then','these','they','their','there','them','our','your','about','into'}
    return set(w for w in words if w not in stopwords)

def calculate_syniq_quick(responses: List[str], synthesis: str):
    if not synthesis or not responses: return 0, "N/A", set()
    sw = extract_words(synthesis); aw = set()
    for r in responses:
        if r: aw |= extract_words(r)
    novel = sw - aw
    novelty = len(novel)/len(sw) if sw else 0
    score = novelty*100
    level = "HIGH" if score>=25 else ("MEDIUM" if score>=15 else "LOW")
    return score, level, novel

def build_control_header() -> str:
    return f"""[CONTROL HEADER]
DEPTH: {st.session_state.depth}
EVALUATION: {st.session_state.evaluation}
COMPRESSION: {st.session_state.compression}
OUTPUT: {st.session_state.output_format}
ACTION: {st.session_state.action}
[/CONTROL HEADER]"""

LABEL_MODES = ["Real names", "Anonymous", "Swapped"]
_NAME_RX = re.compile(r"\b(Claude|ChatGPT|Sophia|Grok|Gemini)\b")
_DEV_RX = re.compile(r"\b(Anthropic|OpenAI|xAI|Google DeepMind|DeepMind|Google|GPT-4o|GPT-4|GPT)\b")


def active_label_map():
    """V44.5: agent -> label shown to agents in the current Auto Run call, or None."""
    m = st.session_state.get("_label_map")
    if st.session_state.get("session_type") != "🔬 Auto Run":
        return None   # labels apply to Auto Run only, even if a run was interrupted
    return m if m and st.session_state.get("_label_mode", "Real names") != "Real names" else None


def make_label_map(agents, mode, rng):
    if mode == "Anonymous":
        letters = [f"Participant {c}" for c in "ABCDEFGH"[:len(agents)]]
        rng.shuffle(letters)
        return dict(zip(agents, letters))
    if mode == "Swapped" and len(agents) > 1:
        for _ in range(100):
            perm = list(agents); rng.shuffle(perm)
            if all(a != b for a, b in zip(agents, perm)):
                return dict(zip(agents, perm))
    return {a: a for a in agents}


def relabel_text(text: str) -> str:
    """Replace agent and developer names according to the active label map."""
    m = active_label_map()
    if not m or not isinstance(text, str):
        return text
    def _name(mt):
        n = mt.group(1)
        key = "ChatGPT" if n == "Sophia" else n
        return m.get(key, "another participant")
    text = _NAME_RX.sub(_name, text)
    return _DEV_RX.sub("[developer]", text)


def shown_name(agent: str) -> str:
    m = active_label_map()
    return m.get(agent, agent) if m else agent


def shown_emoji(agent: str) -> str:
    return "👤" if active_label_map() else AGENT_EMOJIS.get(agent, '🤖')


def agent_frame_for(agent: str):
    """V44.7: the per-agent frame key if one is set and Auto Run is active, else None."""
    if st.session_state.get("session_type") != "🔬 Auto Run":
        return None
    f = st.session_state.get(f"agent_frame_{agent}", "Same as sidebar")
    return f if f in TEMPERATURE_CONDITIONS else None


def effective_frame(agent: str) -> str:
    return agent_frame_for(agent) or st.session_state.get("temperature_condition", "NATIVE")


def frame_condition_string(agents) -> str:
    parts = [f"{a}={agent_frame_for(a)}" for a in agents if agent_frame_for(a)]
    return "; ".join(parts) if parts else "none"


def identity_line_for(agent: str) -> str:
    """V44.3: 'You are X. Responses labeled X are your own.' when the agent
    can see other agents, unless its role text already identifies it."""
    if not agents_see_each_other():
        return ""
    if f"you are {agent.lower()}" in (get_agent_role(agent) or "").lower():
        return ""
    nm = shown_name(agent)
    return f"You are {nm}. Responses labeled {nm} are your own."


def build_system_prompt(agent: str) -> str:
    temp_key  = st.session_state.get("temperature_condition","NATIVE")
    temp_data = TEMPERATURE_CONDITIONS.get(temp_key, TEMPERATURE_CONDITIONS["NATIVE"])
    temp_prompt = temp_data.get("prompt")
    # V44: get_agent_role can now return "" (raw mode applies no role framing).
    # Build parts then drop empties so an empty role leaves no blank gap.
    # V44.7: per-agent frame (Auto Run only) replaces the sidebar condition for this agent
    _af = agent_frame_for(agent)
    if _af:
        temp_prompt = TEMPERATURE_CONDITIONS[_af]["prompt"] or None
    # V44.5: role text follows the label mode (e.g. "You are Claude" -> "You are Participant B")
    parts = [temp_prompt if temp_prompt else get_system_anchor(), relabel_text(get_agent_role(agent))]
    # V44.3: identity whenever the agent can see other agents' labeled answers.
    _idl = identity_line_for(agent)
    if _idl:
        parts.append(_idl)
    stance = st.session_state.agent_stances.get(agent,"Neutral")
    # V44.2: solo contexts get stance text with no reference to other agents.
    _stances = STANCE_PROMPTS if agents_see_each_other() else STANCE_PROMPTS_SOLO
    if _stances.get(stance):
        parts.append(f"STANCE: {_stances[stance]}")
    if st.session_state.instruction:
        parts.append(st.session_state.instruction)
    doc = st.session_state.get("session_document")
    if doc:
        truncated = doc[:3000] + "\n[... truncated ...]" if len(doc) > 3000 else doc
        parts.append(f"\n[SESSION DOCUMENT — {st.session_state.session_document_name}]\n{truncated}\n[/SESSION DOCUMENT]")
    if st.session_state.context_injection:
        parts.append(f"\n[CONTEXT]\n{st.session_state.context_injection}\n[/CONTEXT]")
    return "\n\n".join(p for p in parts if p and p.strip())

def record_scores(agent: str, text: str, round_num: int):
    """Score a response and store in session state.

    V42: a truncated response is still scored (so the row exists and the
    session stays consistent) but is stamped truncated=True. Scores computed
    on an amputated text must be excluded before analysis, not averaged in.
    """
    cut = is_truncated(text)
    if cut:
        st.warning(
            f"✂️ {agent} round {round_num} was TRUNCATED at the token cap. "
            f"Its IEP and Vₜ scores are computed on an incomplete response and "
            f"must not be used. Raise the depth cap and re-run this turn."
        )
    _clean = strip_truncation_tag(text)   # V44.2: never score the sentinel
    iep = score_iep(_clean)
    vt  = score_vt(_clean)
    vt['truncated'] = cut
    iep['truncated'] = cut
    if agent not in st.session_state.iep_scores:
        st.session_state.iep_scores[agent] = []
    if agent not in st.session_state.vt_scores:
        st.session_state.vt_scores[agent] = []
    st.session_state.iep_scores[agent].append(iep)
    st.session_state.vt_scores[agent].append(vt)
    st.session_state.score_history.append({
        'round': round_num, 'agent': agent, 'iep': iep, 'vt': vt,
        'truncated': cut,
        'timestamp': datetime.now().strftime("%H:%M:%S")
    })
    return iep, vt

def render_score_badge(iep: dict, vt: dict):
    """Render compact IEP + Vt score display under a response."""
    dom_color = {'INT':'#4488ff','AFF':'#ff6688','ACT':'#44bb66'}.get(iep['dominant'],'#888')
    humor_flag = "🎭" if iep.get('quadrant','').startswith('High INT+AFF') else ""

    # Top subclass for dominant dimension
    def top_sub(sub_dict, n=2):
        if not sub_dict: return ""
        top = sorted(sub_dict.items(), key=lambda x:x[1], reverse=True)
        top = [(s,v) for s,v in top if v > 0][:n]
        if not top: return ""
        return " · ".join(f'<span style="color:{SUB_COLORS.get(s,"#aaa")};font-size:0.68rem;">{s}:{v:.0f}%</span>' for s,v in top)

    # V40.3: pull the three voice-state views explicitly. Vₜ is the canonical
    # clamped vector; V̂ₜ is the compositional (simplex) view.
    _vt_t = vt.get('V_t')  or {c: vt.get(c, 0.0) for c in VT_CHANNELS}
    _vt_h = vt.get('V_hat') or {c: 0.2 for c in VT_CHANNELS}
    _sat_flag = ''

    dom = iep['dominant']
    sub_display = ""
    if dom == 'INT' and iep.get('int_sub'):
        sub_display = top_sub(iep['int_sub'])
    elif dom == 'AFF' and iep.get('aff_sub'):
        sub_display = top_sub(iep['aff_sub'])
    elif dom == 'ACT' and iep.get('act_sub'):
        sub_display = top_sub(iep['act_sub'])

    st.markdown(f"""
    <div class="score-panel">
      <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
        <span style="font-weight:700;color:{dom_color};">IEP: {iep['dominant']}</span>
        <span style="color:#666;font-size:0.72rem;">{iep['stance']} · {iep['tone']} {humor_flag}</span>
        <span style="color:#999;font-size:0.70rem;margin-left:auto;">{iep.get('quadrant','')}</span>
      </div>
      <div class="iep-bar-row"><span style="width:28px;color:#4488ff;">INT</span>
        <div class="iep-bar-bg"><div class="iep-bar-fill-INT" style="width:{iep['int']:.0f}%;"></div></div>
        <span style="color:#4488ff;width:36px;text-align:right;">{iep['int']:.0f}%</span></div>
      <div class="iep-bar-row"><span style="width:28px;color:#ff6688;">AFF</span>
        <div class="iep-bar-bg"><div class="iep-bar-fill-AFF" style="width:{iep['aff']:.0f}%;"></div></div>
        <span style="color:#ff6688;width:36px;text-align:right;">{iep['aff']:.0f}%</span></div>
      <div class="iep-bar-row"><span style="width:28px;color:#44bb66;">ACT</span>
        <div class="iep-bar-bg"><div class="iep-bar-fill-ACT" style="width:{iep['act']:.0f}%;"></div></div>
        <span style="color:#44bb66;width:36px;text-align:right;">{iep['act']:.0f}%</span></div>
      {f'<div style="margin-top:3px;">{sub_display}</div>' if sub_display else ''}
      <div style="margin-top:5px;color:#ccc;font-size:0.70rem;">
        <strong>Vₜ</strong> <span style="color:#666;">[0,1] independent</span> &nbsp;
        <span class="vt-badge">S:{_vt_t['S_t']:.2f}</span>
        <span class="vt-badge">Ab:{_vt_t['Ab_t']:.2f}</span>
        <span class="vt-badge">Q:{_vt_t['Q_t']:.2f}</span>
        <span class="vt-badge">D:{_vt_t['D_t']:.2f}</span>
        <span class="vt-badge">R:{_vt_t['R_t']:.2f}</span>
        {_sat_flag}
      </div>
      <div style="margin-top:3px;color:#888;font-size:0.68rem;">
        V̂ₜ <span style="color:#666;">compositional · Σ=1</span> &nbsp;
        <span class="vt-badge">S:{_vt_h['S_t']:.2f}</span>
        <span class="vt-badge">Ab:{_vt_h['Ab_t']:.2f}</span>
        <span class="vt-badge">Q:{_vt_h['Q_t']:.2f}</span>
        <span class="vt-badge">D:{_vt_h['D_t']:.2f}</span>
        <span class="vt-badge">R:{_vt_h['R_t']:.2f}</span>
      </div>
    </div>
    """, unsafe_allow_html=True)

# =============================================================================
# API FUNCTIONS
# =============================================================================

# =============================================================================
# V40.3 — API MODEL REGISTRY (run provenance)
# Single source of truth for the exact model identifier each agent is called
# with. Prior corpora were harvested on model versions that have since been
# retired; comparisons across runs are invalid without this stamp. Every CSV
# row carries api_model_id, and every run carries the full registry.
# Change a string here and it changes everywhere, including the stamp.
# =============================================================================

AGENT_MODELS = {   # V44.5: defaults; the sidebar "Models" box can override per session
    # V42.1 — updated from the December 2025 ids. Claude and Gemini were still
    # pinned to retired versions and were failing; Grok survived only because
    # "-latest" is an alias that auto-resolves.
    "Claude":  "claude-sonnet-5",        # Claude Sonnet 5
    "ChatGPT": "gpt-4o",                 # unchanged — was returning responses
    "Grok":    "grok-4.3",               # explicit model; set 2026-10-04 (grok-3-latest had been resolving to 4.3 since 2026-05-15)
    "Gemini":  "gemini-3.6-flash",       # Gemini 3.6 Flash. Called successfully
                                         # on 2026-07-25 (see V43.1 note).
}

# Model used for the co-conductor commentary channel (not an agent under study)
CONDUCTOR_MODEL = "claude-sonnet-5"


# =============================================================================
# V42 — TRUNCATION DETECTION
# The call_* functions return a bare string, so the provider's stop reason has
# nowhere structured to go. Rather than restructure the return contract of four
# functions and every caller, a cut response is tagged inline with a sentinel.
# The tag is visible in the UI, survives into exports, and is detectable by
# is_truncated() for filtering before analysis.
#
# Why this matters: a truncated response still gets scored. V_t and IEP computed
# on an amputated text are not measurements of that response. Cut answers must
# be excluded, not silently averaged in.
# =============================================================================

TRUNCATION_TAG = "\n\n⚠️ [TRUNCATED AT TOKEN CAP — response was cut mid-generation. " \
                 "Do not score or analyze this row. Raise the depth cap and re-run.]"

def is_truncated(text) -> bool:
    """True if a response carries the V42 truncation sentinel."""
    return isinstance(text, str) and "[TRUNCATED AT TOKEN CAP" in text


def strip_truncation_tag(text):
    """V44.2: remove the sentinel before scoring. The sentinel is tool text,
    not model output, and scoring it shifted V_t and IEP."""
    if isinstance(text, str) and TRUNCATION_TAG in text:
        return text.replace(TRUNCATION_TAG, "")
    return text


def _tag_if_cut(text: str, cut: bool) -> str:
    return (text + TRUNCATION_TAG) if cut else text


# =============================================================================
# V43 — THINKING / REASONING CONTROL
#
# Why this exists. On reasoning models, max_tokens is a budget for thinking
# PLUS visible output, not a cap on output length. In the 2026-07-23 run this
# censored two architectures and left two untouched:
#     Claude   truncated in 4 of 5 rounds, visible output only 195-403 words
#     Gemini   truncated in 3 of 5 rounds; R4 produced 68 words and still hit
#              the 2048 ceiling, meaning ~1958 tokens went to thinking
#     ChatGPT  never truncated
#     Grok     never truncated
# A fixed cap therefore censors reasoning architectures specifically, and the
# censoring is invisible in the data: it reads as a difference in style.
#
# It also threatens the NATIVE condition. If a model deliberates privately
# before answering, the visible response is post-deliberation. That is not the
# same object as an unreflected response, and it is not what the December 2025
# design assumed NATIVE measured. Two of four agents do this; two do not.
#
# THINKING STATE IS AN EXPERIMENTAL CONDITION, NOT A SETTING. It is stamped on
# every row (thinking_mode) so a corpus harvested with it on is never silently
# pooled with one harvested with it off.
#
# NOTE ON SYNTAX: the exact parameter shape for disabling reasoning changes
# between model generations. If a provider rejects these, the V42.1 error body
# will name the correct field. Adjust here; nothing else needs to change.
# =============================================================================

THINKING_MODES = {
    "default":  "Provider default (whatever the model does natively)",
    "off":      "Reasoning disabled — max_tokens governs output length only",
    "budgeted": "Reasoning capped at a fixed budget, output gets the rest",
}

THINKING_BUDGET_TOKENS = 1024   # used only when mode == "budgeted"

def get_thinking_mode() -> str:
    return st.session_state.get("thinking_mode", "default")

def _claude_thinking_cfg() -> dict:
    m = get_thinking_mode()
    if m == "off":
        return {"thinking": {"type": "disabled"}}
    if m == "budgeted":
        return {"thinking": {"type": "enabled", "budget_tokens": THINKING_BUDGET_TOKENS}}
    return {}

# V43.1: Gemini 3.x rejects thinkingBudget: 0 with HTTP 400 INVALID_ARGUMENT
# (confirmed against gemini-3.6-flash on 2026-07-25). Unlike the 2.x flash
# line, the 3.x models will not accept a zero budget. GEMINI_MIN_THINK is the
# smallest budget we send for "off" — set it to the provider's documented
# minimum. If this value is also rejected, the error body will say so and only
# this constant needs changing.
GEMINI_MIN_THINK = 128   # smallest legal thinkingBudget for gemini-3.x "off"

def _gemini_thinking_cfg() -> dict:
    m = get_thinking_mode()
    if m == "off":
        # Cannot be 0 on 3.x; send the documented minimum to approximate "off".
        return {"thinkingConfig": {"thinkingBudget": GEMINI_MIN_THINK}}
    if m == "budgeted":
        return {"thinkingConfig": {"thinkingBudget": THINKING_BUDGET_TOKENS}}
    return {}


AGENT_MODELS_DEFAULT = dict(AGENT_MODELS)


def _note_returned_model(agent: str, model):
    """V44.5: remember the model name the provider reported for the last call."""
    st.session_state.setdefault("_last_model", {})[agent] = model


# V44.7.1: under provider-default thinking, current Claude models can spend the
# whole max_tokens budget on thinking and return no text (seen 2026-10-06 on a
# 5,000-word attribution prompt at Medium = 8192). The cap only matters when it
# is hit, so raising Claude's floor leaves every completed answer unchanged and
# rescues calls that would otherwise fail. The timeout is raised to match.
CLAUDE_DEFAULT_THINKING_MIN_TOKENS = 20000
CLAUDE_TIMEOUT_S = 300

def call_claude(prompt: str, system: str, max_tokens: int = 4096) -> str:
    _note_returned_model("Claude", None)
    if get_thinking_mode() == "default":
        max_tokens = max(max_tokens, CLAUDE_DEFAULT_THINKING_MIN_TOKENS)
    try:
        key = get_key("anthropic")
        if not key: return "❌ Anthropic API key not found"
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={**_claude_thinking_cfg(), "model": AGENT_MODELS["Claude"],
                  "max_tokens": max_tokens, "system": system,
                  "messages": [{"role": "user", "content": prompt}]}, timeout=CLAUDE_TIMEOUT_S)
        if r.status_code == 200:
            d = r.json()
            _note_returned_model("Claude", d.get("model"))
            # V42.2: do NOT assume content[0] is a text block. Current Claude
            # models return a content ARRAY that can lead with a thinking block,
            # in which case content[0]["text"] raises KeyError('text') and the
            # entire turn is lost. Collect every text block instead.
            blocks = d.get("content") or []
            txt = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
            if not txt:  # fallback: any block carrying text at all
                txt = "".join(b.get("text", "") for b in blocks if "text" in b)
            if not txt:
                types = ",".join(b.get("type", "?") for b in blocks) or "none"
                return (f"❌ Claude returned no text block "
                        f"(block types: {types}, stop_reason: {d.get('stop_reason')})")
            return _tag_if_cut(txt, d.get("stop_reason") == "max_tokens")
        # V42.1: include the response body. A bare status code cannot
        # distinguish a retired model id from a bad endpoint or key.
        return f"❌ Error {r.status_code}: {r.text[:400]}"
    except Exception as e: return f"❌ {e}"

def call_sophia(prompt: str, system: str, max_tokens: int = 4096) -> str:
    _note_returned_model("ChatGPT", None)
    try:
        key = get_key("openai")
        if not key: return "❌ OpenAI API key not found"
        r = requests.post("https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": AGENT_MODELS["ChatGPT"],
                  "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                  "max_tokens": max_tokens}, timeout=120)
        if r.status_code == 200:
            d = r.json(); ch = (d.get("choices") or [{}])[0]
            _note_returned_model("ChatGPT", d.get("model"))
            return _tag_if_cut(ch["message"]["content"], ch.get("finish_reason") == "length")
        # V42.1: include the response body. A bare status code cannot
        # distinguish a retired model id from a bad endpoint or key.
        return f"❌ Error {r.status_code}: {r.text[:400]}"
    except Exception as e: return f"❌ {e}"

def call_grok(prompt: str, system: str, max_tokens: int = 4096) -> str:
    _note_returned_model("Grok", None)
    try:
        key = get_key("xai")
        if not key: return "❌ xAI API key not found"
        r = requests.post("https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={"model": AGENT_MODELS["Grok"],
                  "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}],
                  "max_tokens": max_tokens}, timeout=120)
        if r.status_code == 200:
            d = r.json(); ch = (d.get("choices") or [{}])[0]
            _note_returned_model("Grok", d.get("model"))
            return _tag_if_cut(ch["message"]["content"], ch.get("finish_reason") == "length")
        # V42.1: include the response body. A bare status code cannot
        # distinguish a retired model id from a bad endpoint or key.
        return f"❌ Error {r.status_code}: {r.text[:400]}"
    except Exception as e: return f"❌ {e}"

def call_gemini(prompt: str, system: str, max_tokens: int = 4096) -> str:
    _note_returned_model("Gemini", None)
    try:
        key = get_key("google")
        if not key: return "❌ Google API key not found"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{AGENT_MODELS['Gemini']}:generateContent?key={key}"
        def _post(gen_extra):
            return requests.post(url, headers={"Content-Type": "application/json"},
                json={"systemInstruction": {"parts": [{"text": system}]},
                      "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                      "generationConfig": {"maxOutputTokens": max_tokens, **gen_extra}},
                timeout=120)
        # V43.2: thinkingConfig can 400 on gemini-3.x (0 and 128 both rejected).
        # A thinking-control setting must NEVER hard-fail the run. Try with the
        # requested config; on a 400 that mentions thinking/argument, strip it and
        # retry once so the turn still returns. The row is stamped so a fallback
        # is never mistaken for a genuine "off".
        # V44.2: the flag is PER CALL. It is reset here and read by the caller
        # right after this call returns. V44.1 set a session flag that never
        # reset, so every later run was stamped as a fallback.
        # The retry now fires only when the 400 body mentions thinking; any
        # other 400 surfaces as an error instead of being silently retried.
        st.session_state["_gemini_last_call_fellback"] = False
        think = _gemini_thinking_cfg()
        r = _post(think)
        if r.status_code == 400 and think and "thinking" in r.text.lower():
            st.session_state["_gemini_last_call_fellback"] = True
            r = _post({})   # retry with NO thinking config
        if r.status_code == 200:
            d = r.json(); cand = (d.get("candidates") or [{}])[0]
            _note_returned_model("Gemini", d.get("modelVersion"))
            fr = cand.get("finishReason")
            # On a MAX_TOKENS or safety finish Gemini can return no parts at all;
            # the old parts[0] access raised and surfaced as a bogus error.
            parts = (cand.get("content", {}) or {}).get("parts") or []
            txt = "".join(pp.get("text", "") for pp in parts)
            if not txt: return f"❌ Empty Gemini response (finishReason={fr})"
            return _tag_if_cut(txt, fr == "MAX_TOKENS")
        # V42.1: include the response body. A bare status code cannot
        # distinguish a retired model id from a bad endpoint or key.
        return f"❌ Error {r.status_code}: {r.text[:400]}"
    except Exception as e: return f"❌ {e}"

def gemini_fellback_for(agent: str):
    """V44.2: per-call fallback status for the call that just returned.
    None for non-Gemini agents (not applicable)."""
    if agent != "Gemini":
        return None
    return bool(st.session_state.get("_gemini_last_call_fellback", False))

_KEY_PATTERNS = [
    re.compile(r"sk-ant-[A-Za-z0-9_\-]{6,}"), re.compile(r"sk-[A-Za-z0-9_\-]{16,}"),
    re.compile(r"xai-[A-Za-z0-9_\-]{10,}"), re.compile(r"AIza[A-Za-z0-9_\-]{20,}"),
    re.compile(r"(?i)bearer\s+[A-Za-z0-9_\-\.]{10,}"),
]


def redact_secrets(text):
    """V44.4: remove anything key-like from text before it is shown or stored."""
    if not isinstance(text, str):
        return text
    for rx in _KEY_PATTERNS:
        text = rx.sub("[REDACTED-KEY]", text)
    for name in ("anthropic", "openai", "xai", "google"):
        k = _secret_raw(name)
        if k and len(k) > 8:
            text = text.replace(k, "[REDACTED-KEY]").replace(k.strip(), "[REDACTED-KEY]")
    return text


def _scrubbed(fn):
    """Wrap an agent call so error strings can never carry a key."""
    def inner(*a, **kw):
        out = fn(*a, **kw)
        return redact_secrets(out) if isinstance(out, str) and out.startswith("❌") else out
    inner.__name__ = fn.__name__
    return inner


call_claude = _scrubbed(call_claude)
call_sophia = _scrubbed(call_sophia)
call_grok   = _scrubbed(call_grok)
call_gemini = _scrubbed(call_gemini)

AGENT_FUNCTIONS = {"Claude": call_claude, "ChatGPT": call_sophia, "Grok": call_grok, "Gemini": call_gemini}

# =============================================================================
# PROMPT BUILDERS
# =============================================================================

def build_discussion_prompt(agent: str, topic: str, thread: List[Dict], directed_from: str = None, round_instruction: str = None) -> str:
    msg = build_control_header() + "\n\n"
    msg += f"TOPIC: {topic}\n\n"
    if round_instruction and round_instruction.strip():
        msg += f"[ROUND INSTRUCTION: {round_instruction.strip()}]\n\n"
    if thread:
        msg += "DISCUSSION SO FAR:\n"
        for entry in thread:
            if entry.get("type") == "resolve_marker" or str(entry.get("content","")).startswith("✅ DISCUSSION RESOLVED"):
                continue   # V44.4: record-only marker, not shown to agents
            if str(entry.get("content","")).startswith("❌"):
                continue   # V44.4: an error is not a participant's contribution
            speaker = entry.get('agent','Unknown')
            emoji   = AGENT_EMOJIS.get(speaker,'🤖')
            msg += f"\n{emoji} {speaker}: {entry['content']}\n"
        msg += "\n---\n\n"
    _carried = st.session_state.get("sidebar_carry", {}).get(agent, [])
    if _carried:
        # V44.4: conductor chose to carry these private sidebars into this agent's context
        msg += "YOUR EARLIER PRIVATE SIDEBAR(S) WITH THE CONDUCTOR (other participants did not see these):\n"
        for sb in _carried:
            for m in sb.get("messages", []):
                msg += f"\n{m['speaker']}: {m['content']}\n"
            msg += "\n---\n"
        msg += "\n"
    if directed_from:
        msg += f"[DIRECTED: Respond specifically to {directed_from}'s last point.]\n\n"
    msg += "Your contribution:"
    return msg

def build_pull_aside_prompt(agent: str, thread: List[Dict], main_topic: str) -> str:
    msg  = build_control_header() + "\n\n"
    msg += f"[PRIVATE SIDEBAR with Conductor]\nMain topic: {main_topic}\n\n"
    # V44.4: the agent sees the main discussion so "your answer" is visible to it.
    _main = [e for e in st.session_state.get("discussion_thread", [])
             if e.get("type") != "resolve_marker" and not str(e.get("content","")).startswith(("✅ DISCUSSION RESOLVED", "❌"))]
    if _main:
        msg += "MAIN DISCUSSION SO FAR (visible to all participants):\n"
        for e in _main:
            msg += f"\n{AGENT_EMOJIS.get(e.get('agent',''),'🤖')} {e.get('agent','Unknown')}: {e.get('content','')}\n"
        msg += "\n---\n\nThe exchange below is PRIVATE between you and the Conductor.\n\n"
    if thread:
        msg += "Our private conversation:\n"
        for entry in thread:
            msg += f"\n{entry.get('speaker','Unknown')}: {entry['content']}\n"
        msg += "\n---\n\n"
    msg += "Your response to the Conductor:"
    return msg

def build_multi_round_prompt(agent: str, current_prompt: str, round_history: List[Dict], round_num: int) -> str:
    msg = build_control_header() + "\n\n"
    if round_history:
        msg += "PREVIOUS ROUNDS:\n" + "=" * 40 + "\n"
        for i, rd in enumerate(round_history, 1):
            msg += f"\n📍 ROUND {i}\nPrompt: {rd.get('prompt','N/A')}\n\n"
            for a, response in rd.get('responses', {}).items():
                msg += f"{AGENT_EMOJIS.get(a,'🤖')} {a}:\n{response}\n\n"
            msg += "-" * 40 + "\n"
        msg += "=" * 40 + "\n\n"
    msg += f"📍 ROUND {round_num} PROMPT:\n{current_prompt}\n\nYour response:"
    return msg

def build_scripted_round_prompt(depth_instruction: str, history: List[Dict],
                                round_prompt: str, round_num: int) -> str:
    """V44.3: scripted Auto Run, round 2 onward. Same history layout as
    Multi-Round (prompt, then every agent's labeled answer, per round), plus
    the depth instruction so length guidance matches round 1."""
    msg = build_control_header() + "\n\n" + depth_instruction + "\n\n"
    if history:
        msg += "PREVIOUS ROUNDS:\n" + "=" * 40 + "\n"
        for i, rd in enumerate(history, 1):
            msg += f"\n📍 ROUND {i}\nPrompt: {rd.get('prompt','N/A')}\n\n"
            for a, response in rd.get('responses', {}).items():
                # V44.5: labels, emojis and names inside answers follow the label mode
                msg += f"{shown_emoji(a)} {shown_name(a)}:\n{relabel_text(response)}\n\n"
            msg += "-" * 40 + "\n"
        msg += "=" * 40 + "\n\n"
    msg += f"📍 ROUND {round_num} PROMPT:\n{round_prompt}\n\nYour response:"
    return msg


def build_resolution_prompt(agent: str, topic: str, thread: List[Dict]) -> str:
    msg  = build_control_header() + "\n\n"
    msg += f"TOPIC: {topic}\n\nFULL DISCUSSION:\n"
    for entry in thread:
        speaker = entry.get('agent','Unknown')
        msg += f"\n{AGENT_EMOJIS.get(speaker,'🤖')} {speaker}: {entry['content']}\n"
    msg += "\n" + "=" * 40 + "\n\n"
    msg += "[RESOLUTION TASK: Synthesize this discussion into a final resolution. Summarize what was decided, capture key insights, note any remaining disagreements, and state the conclusion clearly.]\n\nRESOLUTION:"
    return msg

def build_coconductor_prompt(topic: str, thread: List[Dict], score_history: List[Dict]) -> str:
    """Build prompt for Claude-as-co-conductor to give William private observations."""
    msg = f"""[CO-CONDUCTOR PRIVATE CHANNEL]

You are Claude acting as a silent co-conductor for William Kouns (SYNINT researcher).
William is conducting a live focus group session. Your role: observe the IEP + Vt scores 
and the discussion thread, then give William a concise private observation he can use 
to conduct better. Be specific, actionable, and brief. Flag:
- Any agent showing unusual IEP movement or phase transitions
- Simultaneous INT+AFF spikes (humor/novelty signal — quadrant: High INT+AFF)
- Subclass fingerprint differences between agents (e.g. one agent's AFF is distress-heavy, another's is warmth-heavy)
- Convergence or divergence patterns across agents
- A suggested next conductor move if you see one

SESSION TOPIC: {topic}

RECENT SCORE HISTORY (last {min(len(score_history),8)} turns):
"""
    for entry in score_history[-8:]:
        iep = entry['iep']; vt = entry['vt']
        # Top subclass for dominant dim
        dom = iep['dominant']
        sub_str = ""
        sub_data = iep.get(f"{dom.lower()}_sub", {})
        if sub_data:
            top = sorted(sub_data.items(), key=lambda x:x[1], reverse=True)
            top = [(s,v) for s,v in top if v > 0][:2]
            if top: sub_str = " [" + ", ".join(f"{s}:{v:.0f}%" for s,v in top) + "]"
        msg += (f"  {entry['agent']} (R{entry['round']}): "
                f"IEP={iep['dominant']}{sub_str} "
                f"INT:{iep['int']:.0f}% AFF:{iep['aff']:.0f}% ACT:{iep['act']:.0f}% | "
                f"Stance:{iep['stance']} Tone:{iep['tone']} | "
                f"Vt S:{vt['S_t']:.2f} Ab:{vt['Ab_t']:.2f} Q:{vt['Q_t']:.2f} D:{vt['D_t']:.2f} R:{vt['R_t']:.2f}\n")

    if thread:
        msg += f"\nLAST 3 THREAD ENTRIES:\n"
        for entry in thread[-3:]:
            msg += f"  {entry.get('agent','?')}: {entry.get('content','')[:200]}...\n"

    msg += "\n[Give William your private conductor observation — 3-5 sentences max. Be specific about what you see in the numbers and subclass fingerprints, and what it means for how to conduct next.]"
    return msg

def call_coconductor() -> str:
    """Call Claude as co-conductor and return private observation."""
    topic  = st.session_state.discussion_topic or "Active session"
    thread = st.session_state.discussion_thread
    hist   = st.session_state.score_history
    if not hist:
        return "No scores yet — run at least one round first, then I can give you a read."
    prompt = build_coconductor_prompt(topic, thread, hist)
    key = get_key("anthropic")
    if not key: return "❌ Anthropic key not found"
    try:
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": CONDUCTOR_MODEL, "max_tokens": 512,
                  "system": "You are a research co-conductor. Be precise, data-driven, and brief.",
                  "messages": [{"role": "user", "content": prompt}]}, timeout=60)
        if r.status_code == 200:
            d = r.json()
            # V42.2: do NOT assume content[0] is a text block. Current Claude
            # models return a content ARRAY that can lead with a thinking block,
            # in which case content[0]["text"] raises KeyError('text') and the
            # entire turn is lost. Collect every text block instead.
            blocks = d.get("content") or []
            txt = "".join(b.get("text", "") for b in blocks if b.get("type") == "text")
            if not txt:  # fallback: any block carrying text at all
                txt = "".join(b.get("text", "") for b in blocks if "text" in b)
            if not txt:
                types = ",".join(b.get("type", "?") for b in blocks) or "none"
                return (f"❌ Claude returned no text block "
                        f"(block types: {types}, stop_reason: {d.get('stop_reason')})")
            return _tag_if_cut(txt, d.get("stop_reason") == "max_tokens")
        # V42.1: include the response body. A bare status code cannot
        # distinguish a retired model id from a bad endpoint or key.
        return f"❌ Error {r.status_code}: {r.text[:400]}"
    except Exception as e: return f"❌ {e}"

def _current_max_tokens() -> int:
    """Read depth from session state and return V50 token budget."""
    return DEPTH_CONFIGS.get(st.session_state.depth, DEPTH_CONFIGS["Medium"])["max_tokens"]

call_coconductor = _scrubbed(call_coconductor)   # V44.4


def call_agent_discussion(agent, topic, thread, directed_from=None, round_instruction=None):
    return AGENT_FUNCTIONS[agent](build_discussion_prompt(agent, topic, thread, directed_from, round_instruction), build_system_prompt(agent), max_tokens=_current_max_tokens())

def call_agent_pull_aside(agent, thread, main_topic):
    return AGENT_FUNCTIONS[agent](build_pull_aside_prompt(agent, thread, main_topic), build_system_prompt(agent), max_tokens=_current_max_tokens())

def call_agent_multi_round(agent, current_prompt, round_history, round_num):
    return AGENT_FUNCTIONS[agent](build_multi_round_prompt(agent, current_prompt, round_history, round_num), build_system_prompt(agent), max_tokens=_current_max_tokens())

def call_agent_resolution(agent, topic, thread):
    return AGENT_FUNCTIONS[agent](build_resolution_prompt(agent, topic, thread), build_system_prompt(agent), max_tokens=_current_max_tokens())

# =============================================================================
# V48: AI MODERATOR
# One AI writes the process messages that steer the Live Discussion. The
# conductor approves each message before the participants see it (unless
# auto-post is ticked). Participants see the message labeled "Moderator" and
# are not told which AI wrote it. Everything is stamped on the thread entry.
# =============================================================================

MODERATOR_MODES = {
    "Facilitator": {
        "label": "Facilitate only: process, no answers or ideas of its own",
        "rule": ("Do not state your own answer to the topic, and do not introduce interpretations, evidence or "
                 "arguments of your own. You may quote, summarize and contrast what participants have said, ask "
                 "questions, give tasks to named participants, and call votes."),
        "brief_use": ("Use the brief to decide which evidence to point the group toward and which questions to "
                      "ask. Do not reveal the brief, quote it, or state its conclusions. If the group reaches "
                      "something like it, it must be their own reasoning."),
    },
    "Guide": {
        "label": "Guide: may offer its own ideas, labeled as suggestions",
        "rule": ("You may offer your own observations and ideas, but label each one clearly as the moderator's "
                 "suggestion and let the participants judge it on its merits. Do not tell anyone what to conclude."),
        "brief_use": ("You may draw on the brief. Present any idea from it as the moderator's suggestion, "
                      "not as a fact or as the conductor's view."),
    },
}

MODERATOR_TASKS = {
    "next_open": ("Open the discussion. State the question in your own words and give the participants their "
                  "first task."),
    "next": ("Write your next message to move the discussion forward. Base it on what the participants have "
             "actually said: where they agree, where they differ, and what evidence is being set aside."),
    "close": ("Close the discussion. Summarize where the group stands and which reading the group's own arguments "
              "best support, say briefly what each participant contributed, and call a final vote: each "
              "participant gives a one-word answer and one sentence of reasoning."),
    "announce": ("The final vote is in. Count the votes exactly as given, announce the result, and state the "
                 "group's decision in one or two sentences. If there is no majority, say so."),
}

MODERATOR_GOALS = {
    "Novel ideas (ideation)": (
        "Your goal is ideation: lead the group to an idea that none of them brought in alone. Novel means not a "
        "restatement of any one participant's position and not a vote between the positions already on the table, "
        "but a reading or solution that combines, reframes or goes beyond them. Push the participants past their "
        "first answers: have them build on each other, name what each position explains that the others miss, and "
        "look for a frame in which apparent opposites both hold. Do not call a vote until something new has "
        "emerged. When you close, name what is new and which participant contributed which piece of it."),
    "Best collective answer": (
        "Your goal is the group's best collective answer: the one the evidence and the participants' own "
        "arguments best support."),
    "Custom": "",
}
MODERATOR_DEFAULT_GOAL = "Novel ideas (ideation)"

MODERATOR_ROUND_CUE = "Respond to the Moderator's latest message."


def build_moderator_system(mod_agent: str, mode: str, goal: str = "") -> str:
    names = ", ".join(st.session_state.active_agents) or "none selected"
    parts = [
        f"You are the moderator of a live discussion among AI participants: {names}. A human researcher, the "
        f"conductor, appointed you and sees everything. The participants see your messages labeled "
        f"\"Moderator\"; they are not told which AI you are.",
        "Your job is to lead the group through process: what to examine, how to engage one another, when to "
        "converge, and how to decide.",
        (goal.strip() or MODERATOR_GOALS["Best collective answer"]),
        MODERATOR_MODES[mode]["rule"],
    ]
    if mod_agent in st.session_state.active_agents:
        parts.append(f"You are also a participant in this discussion: the turns labeled \"{mod_agent}\" are yours. "
                     f"As moderator, treat them like anyone else's, neither favoring nor dismissing them.")
    parts.append("Write only the message the participants will see. Address them directly. Keep it under 180 words.")
    doc = st.session_state.get("session_document")
    if doc:
        truncated = doc[:3000] + "\n[... truncated ...]" if len(doc) > 3000 else doc
        parts.append(f"[SESSION DOCUMENT, also given to the participants — {st.session_state.session_document_name}]\n"
                     f"{truncated}\n[/SESSION DOCUMENT]")
    return "\n\n".join(parts)


def build_moderator_prompt(mode: str, kind: str, topic: str, thread: List[Dict], brief: str) -> str:
    entries = [e for e in thread if e.get("type") != "resolve_marker"
               and not str(e.get("content", "")).startswith(("❌", "✅ DISCUSSION RESOLVED"))]
    msg = f"TOPIC: {topic}\n\nROUNDS COMPLETED: {st.session_state.discussion_round}\n\n"
    if entries:
        msg += "DISCUSSION SO FAR:\n"
        for e in entries:
            who = "Moderator (you)" if e.get("type") == "moderator" else e.get("agent", "Unknown")
            msg += f"\n{who}: {strip_truncation_tag(e.get('content', ''))}\n"
        msg += "\n---\n\n"
    else:
        msg += "The discussion has not started yet.\n\n"
    if brief and brief.strip():
        msg += ("CONDUCTOR'S PRIVATE BRIEF (only you can see this; the participants cannot):\n"
                f"{brief.strip()}\n\n{MODERATOR_MODES[mode]['brief_use']}\n\n")
    task = MODERATOR_TASKS["next_open" if kind == "next" and not entries else kind]
    if kind == "close":
        task += " Keep to your goal as stated above."
    msg += f"YOUR TASK: {task}\n\nYour message to the participants:"
    return msg


def call_moderator(mod_agent: str, mode: str, kind: str, topic: str, thread: List[Dict], brief: str, goal: str = "") -> str:
    return AGENT_FUNCTIONS[mod_agent](build_moderator_prompt(mode, kind, topic, thread, brief),
                                      build_moderator_system(mod_agent, mode, goal),
                                      max_tokens=_current_max_tokens())

# =============================================================================
# EXPORT
# =============================================================================

def export_to_markdown() -> str:
    md  = f"# Focus Group Lab V48: Session Export\n"
    md += f"**{datetime.now().strftime('%Y-%m-%d %H:%M')}** · SYNINT Team\n\n---\n\n"

    # Full reproducible context — everything agents were told
    md += "## Session Context (What Agents Were Told)\n"
    md += f"- **Depth:** {st.session_state.depth} | **Evaluation:** {st.session_state.evaluation} | **Compression:** {st.session_state.compression}\n"
    md += f"- **Output:** {st.session_state.output_format} | **Action:** {st.session_state.action}\n"
    md += f"- **Role Mode:** {st.session_state.role_mode} — {ROLE_MODE_DESCRIPTIONS.get(st.session_state.role_mode,'')}\n"
    temp_key = st.session_state.get('temperature_condition','NATIVE')
    temp_data = TEMPERATURE_CONDITIONS.get(temp_key, {})
    md += f"- **Temperature:** {temp_key} — {temp_data.get('description','')}\n"
    if temp_data.get('prompt'):
        md += f"  - *Injected: {temp_data['prompt'][:120]}*\n"
    md += f"- **Active Agents:** {', '.join(st.session_state.active_agents)}\n"
    stances_str = ', '.join(f"{a}:{st.session_state.agent_stances.get(a,'Neutral')}" for a in st.session_state.active_agents)
    md += f"- **Stances:** {stances_str}\n"
    if st.session_state.instruction:
        md += f"- **⚠️ Custom Instruction:** {st.session_state.instruction}\n"
    if st.session_state.context_injection:
        md += f"- **Shared Context:** {st.session_state.context_injection[:300]}{'...' if len(st.session_state.context_injection)>300 else ''}\n"
    md += "\n**Agent Roles:**\n"
    for agent in st.session_state.active_agents:
        _r = get_agent_role(agent)
        md += f"- **{agent}:** {_r if _r.strip() else '(raw voice — no role framing)'}\n"
    if st.session_state.session_document_name:
        md += f"\n**Session Document:** {st.session_state.session_document_name}"
        doc = st.session_state.get('session_document','')
        md += f" ({len(doc):,} chars)\n"
        if doc:
            md += f"> Content fingerprint: {doc[:400].replace(chr(10),' ')}...\n"
    md += "\n---\n\n"

    if st.session_state.score_history:
        md += "## IEP + Vt Score History\n"
        seen = set()
        for e in st.session_state.score_history:
            key = f"{e['round']}_{e['agent']}_{e.get('timestamp','')}"
            if key in seen: continue
            seen.add(key)
            iep = e['iep']; vt = e['vt']
            _t = vt.get('V_t')   or {c: vt.get(c, 0.0) for c in VT_CHANNELS}
            _h = vt.get('V_hat') or {c: 0.2 for c in VT_CHANNELS}
            md += (f"- R{e['round']} {e['agent']}: IEP={iep['dominant']} "
                   f"({iep['int']:.0f}/{iep['aff']:.0f}/{iep['act']:.0f}) | "
                   f"{iep['stance']} · {iep['tone']}\n"
                   f"    - Vₜ (canonical, [0,1] independent): "
                   f"S:{_t['S_t']:.2f} Ab:{_t['Ab_t']:.2f} Q:{_t['Q_t']:.2f} "
                   f"D:{_t['D_t']:.2f} R:{_t['R_t']:.2f}"
                   f"\n"
                   f"    - V̂ₜ (compositional, Σ=1): "
                   f"S:{_h['S_t']:.2f} Ab:{_h['Ab_t']:.2f} Q:{_h['Q_t']:.2f} "
                   f"D:{_h['D_t']:.2f} R:{_h['R_t']:.2f}\n")
        md += "\n"
    if st.session_state.coconductor_notes:
        md += "## Co-Conductor Observations (Private)\n"
        for i, note in enumerate(st.session_state.coconductor_notes, 1):
            md += f"### Observation {i}\n{note}\n\n"
    if st.session_state.session_notes:
        md += f"## Session Notes\n{st.session_state.session_notes}\n\n"
    if st.session_state.multi_round_history:
        md += "## Multi-Round Session\n"
        for i, rd in enumerate(st.session_state.multi_round_history, 1):
            md += f"### Round {i}\n**Prompt:** {rd.get('prompt','N/A')}\n\n"
            for agent, response in rd.get('responses', {}).items():
                md += f"#### {AGENT_EMOJIS.get(agent,'🤖')} {agent}\n{response}\n\n---\n\n"
    if st.session_state.discussion_thread:
        md += f"## Live Discussion\n**Topic:** {st.session_state.discussion_topic}\n\n"
        for entry in st.session_state.discussion_thread:
            agent   = entry.get('agent','Unknown')
            emoji   = AGENT_EMOJIS.get(agent,'🤖')
            directed = f" *(→ {entry.get('directed_from','')})*" if entry.get('directed_from') else ""
            if entry.get("type") == "moderator":   # V48
                directed = (f" *({entry.get('moderator_agent')}, {entry.get('moderator_mode')}"
                            f"{', edited by conductor' if entry.get('moderator_edited') else ''})*")
            md += f"### {emoji} {agent}{directed}\n{entry.get('content','')}\n\n---\n\n"
    _briefs = []   # V48: every distinct private brief given to the AI moderator
    for _e in st.session_state.get("discussion_thread", []):
        if _e.get("type") == "moderator" and _e.get("moderator_brief") and _e["moderator_brief"] not in _briefs:
            _briefs.append(_e["moderator_brief"])
    if _briefs:
        md += "## Private Briefs to the AI Moderator\n*Participants never saw these.*\n\n"
        for _i, _b in enumerate(_briefs, 1):
            md += f"### Brief {_i}\n{_b}\n\n---\n\n"
    _goals = []   # V48: every distinct goal given to the AI moderator
    for _e in st.session_state.get("discussion_thread", []):
        if _e.get("type") == "moderator" and _e.get("moderator_goal") and _e["moderator_goal"] not in _goals:
            _goals.append(_e["moderator_goal"])
    if _goals:
        md += "## AI Moderator Goals\n"
        for _i, _g in enumerate(_goals, 1):
            md += f"### Goal {_i}\n{_g}\n\n---\n\n"
    if st.session_state.get("sidebar_archive"):
        md += "## Private Sidebars\n"
        for sb in st.session_state.sidebar_archive:
            md += (f"### 🔒 Sidebar {sb['sidebar_id']} with {AGENT_EMOJIS.get(sb['agent'],'🤖')} {sb['agent']}"
                   f" (round {sb.get('round')}, after turn {sb.get('after_turn')}, {sb.get('started_utc')})\n")
            md += f"*Carried into {sb['agent']}'s later turns: {'yes' if sb.get('carried') else 'no'}*\n\n"
            for m in sb.get("messages", []):
                md += f"**{m['speaker']}:** {m['content']}\n\n"
            md += "---\n\n"
    if st.session_state.round1_responses:
        md += "## Single Round Responses\n"
        for agent, response in st.session_state.round1_responses.items():
            md += f"### {AGENT_EMOJIS.get(agent,'🤖')} {agent}\n{response}\n\n---\n\n"
    md += "\n---\n*Focus Group Lab V48, Research Edition (open) · SYNINT Team · October 2026*\n"
    return md

# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_preset_buttons():
    cols = st.columns(5)
    for i, (key, preset) in enumerate(PRESETS.items()):
        with cols[i]:
            if st.button(f"{key}", key=f"preset_{key}", width="stretch", help=preset['name']):
                # V40: polarity control removed (see module header); presets now carry
                # only depth/evaluation/compression/output/action/instruction fields.
                st.session_state.depth         = preset["depth"]
                st.session_state.evaluation    = preset["evaluation"]
                st.session_state.compression   = preset["compression"]
                st.session_state.output_format = preset["output"]
                st.session_state.action        = preset["action"]
                st.session_state.instruction   = preset["instruction"]
                st.rerun()

def render_agent_response_grid(responses: Dict[str, str], round_num: int = 0, score: bool = True):
    cols   = st.columns(2)
    agents = list(responses.keys())
    for i, agent in enumerate(agents):
        with cols[i % 2]:
            box_class    = f"{agent.lower()}-box"
            emoji        = AGENT_EMOJIS.get(agent,"🤖")
            stance       = st.session_state.agent_stances.get(agent,"Neutral")
            stance_class = f"stance-{stance.lower().replace(' ','-')}"
            role         = get_agent_role(agent)
            # V44: raw mode returns "" (no role framing). Label it explicitly so
            # the card doesn't show a blank where "advisor" used to be.
            role_short   = (role[:60]+"..." if len(role)>60 else role) if role.strip() \
                           else "raw voice — no role or advisor framing"
            st.markdown(f"""
            <div class="agent-box {box_class}">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem;">
                    <strong>{emoji} {agent}</strong>
                    <span class="{stance_class}">{stance}</span>
                </div>
                <div style="font-size:0.75rem; color:#666; margin-bottom:0.5rem;">{role_short}</div>
            </div>
            """, unsafe_allow_html=True)
            # V42.3: optional IEP dictionary highlighting. Display only — the
            # score shown below is read from session state either way.
            render_response_text(responses[agent])
            # Read scores from session state — never re-score on display
            if score:
                iep_list = st.session_state.iep_scores.get(agent,[])
                vt_list  = st.session_state.vt_scores.get(agent,[])
                if iep_list and vt_list:
                    render_score_badge(iep_list[-1], vt_list[-1])

def render_present_mode(responses: Dict[str, str]):
    agents = list(responses.keys())
    if not agents: return
    idx   = st.session_state.present_index % len(agents)
    agent = agents[idx]
    col1, col2, col3 = st.columns([1, 6, 1])
    with col1:
        if st.button("⬅️", key="prev_present"):
            st.session_state.present_index = (idx-1) % len(agents); st.rerun()
    with col2:
        st.markdown(f"<h3 style='text-align:center;'>{AGENT_EMOJIS.get(agent,'🤖')} {agent}</h3>", unsafe_allow_html=True)
    with col3:
        if st.button("➡️", key="next_present"):
            st.session_state.present_index = (idx+1) % len(agents); st.rerun()
    role = get_agent_role(agent)
    st.markdown(f"<div style='text-align:center; color:#666; font-size:0.85rem; margin-bottom:1rem;'>{role}</div>", unsafe_allow_html=True)
    if st.session_state.get("iep_highlight", False):
        st.markdown(f"<div class='present-card {agent.lower()}'>"
                    + iep_highlight_html(responses[agent]) + "</div>", unsafe_allow_html=True)
    else:
        st.markdown(f"<div class='present-card {agent.lower()}'>{responses[agent]}</div>", unsafe_allow_html=True)

# =============================================================================
# SIDEBAR
# =============================================================================

with st.sidebar:
    st.markdown("## ⚙️ Control Panel")

    # Document Upload
    st.markdown("### 📄 Session Document")
    uploaded = st.file_uploader(
        "Load document (docx, md, txt, csv, py, pdf)",
        type=["docx","md","txt","csv","py","pdf"],
        # V44.7.1: the key changes on Remove, so the uploader forgets the file.
        # Before, the uploader kept it and the next rerun silently reloaded it.
        key=f"doc_uploader_{st.session_state.get('_doc_uploader_gen', 0)}"
    )
    if uploaded:
        doc_text = parse_uploaded_document(uploaded)
        st.session_state.session_document      = doc_text
        st.session_state.session_document_name = uploaded.name
        st.success(f"✅ {uploaded.name} loaded ({len(doc_text):,} chars)")
    if st.session_state.session_document:
        st.markdown(f'<div class="doc-context-box">📄 <strong>{st.session_state.session_document_name}</strong><br><span style="color:#666;">{len(st.session_state.session_document):,} chars loaded: agents can read this</span></div>', unsafe_allow_html=True)
        if st.button("🗑️ Remove document", width="stretch"):
            st.session_state.session_document = None
            st.session_state.session_document_name = ""
            st.session_state["_doc_uploader_gen"] = st.session_state.get("_doc_uploader_gen", 0) + 1
            st.rerun()

    st.markdown("---")
    st.markdown("### 🎭 Role Mode")
    role_mode = st.radio(
        "Role assignment:",
        options=["assigned","raw","swapped","custom"],
        format_func=lambda x: {
            "assigned": "🎭 Assigned (Original)",
            "raw":      "🔬 Raw Voice (No Roles)",
            "swapped":  "🔄 Swapped Roles",
            "custom":   "✏️ Custom Roles"
        }.get(x,x),
        index=["assigned","raw","swapped","custom"].index(st.session_state.role_mode),
        key="role_mode_radio"
    )
    st.session_state.role_mode = role_mode
    mode_class = {"raw":"role-mode-raw","swapped":"role-mode-raw","custom":"role-mode-custom"}.get(role_mode,"")
    st.markdown(f'<div class="role-mode-box {mode_class}"><strong>{ROLE_MODE_DESCRIPTIONS.get(role_mode,"")}</strong></div>', unsafe_allow_html=True)

    if role_mode == "custom":
        st.markdown("**Define Custom Roles:**")
        for agent in ["Claude","ChatGPT","Grok","Gemini"]:
            st.session_state.custom_roles[agent] = st.text_area(
                f"{AGENT_EMOJIS[agent]} {agent}",
                value=st.session_state.custom_roles.get(agent,""),
                height=80, key=f"custom_role_{agent}"
            )

    with st.expander("👁️ Preview Roles"):
        for agent in ["Claude","ChatGPT","Grok","Gemini"]:
            role = get_agent_role(agent)
            st.markdown(f"**{AGENT_EMOJIS[agent]} {agent}:** _{role[:100]}{'...' if len(role)>100 else ''}_")

    st.markdown("---")
    st.markdown("### 🌡️ Temperature")
    temp_options = list(TEMPERATURE_CONDITIONS.keys())
    temp_labels  = [TEMPERATURE_CONDITIONS[k]["label"] for k in temp_options]
    current_temp = st.session_state.get("temperature_condition","NATIVE")
    if current_temp not in temp_options: current_temp = "NATIVE"
    selected_label = st.selectbox("Condition:", options=temp_labels,
        index=temp_options.index(current_temp), key="temperature_selectbox")
    selected_key = temp_options[temp_labels.index(selected_label)]
    st.session_state.temperature_condition = selected_key
    temp_info = TEMPERATURE_CONDITIONS[selected_key]
    temp_color = {"NATIVE":"#E8F5E9","COLD":"#E3F2FD"}.get(selected_key,"#FFF3E0")
    border_color = {"NATIVE":"#4CAF50","COLD":"#1565C0"}.get(selected_key,"#E64A19")
    st.markdown(f'<div style="background:{temp_color};border-left:4px solid {border_color};border-radius:6px;padding:0.6rem 0.8rem;margin-top:0.3rem;font-size:0.82rem;"><em>{temp_info["description"]}</em></div>', unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🎚️ Control Header")
    render_preset_buttons()
    # V40: Polarity control removed — temperature (V50's 18-point gradient) covers this axis.
    # (Use Temperature in sidebar to select analytical↔affective register.)
    # V40: Depth now matches V50 semantics (token budgets + instructions).
    # Single-select in sidebar for Live Discussion / Single / Multi-Round.
    # Auto Run offers multi-select checkboxes (see Auto Run block).
    _depth_options = ["Shallow", "Medium", "Deep", "Ultra-Deep"]
    _depth_idx = _depth_options.index(st.session_state.depth) if st.session_state.depth in _depth_options else 1
    st.session_state.depth         = st.selectbox("Depth", _depth_options, index=_depth_idx,
        help=f"V50 token budgets: Shallow=200, Medium=500, Deep=1000, Ultra-Deep=2000")
    col1, col2 = st.columns(2)
    with col1:
        st.session_state.evaluation    = st.selectbox("Evaluation", ["ON","OFF"], index=0 if st.session_state.evaluation=="ON" else 1)
        st.session_state.output_format = st.selectbox("Output", ["ESSAY","OUTLINE","BULLETS","TABLE","JSON"],
            index=["ESSAY","OUTLINE","BULLETS","TABLE","JSON"].index(st.session_state.output_format))
    with col2:
        st.session_state.compression   = st.selectbox("Compression", ["OFF","ON"], index=0 if st.session_state.compression=="OFF" else 1)
        st.session_state.action        = st.selectbox("Action", ["OFF","ON"], index=0 if st.session_state.action=="OFF" else 1)
    st.session_state.instruction = st.text_area("Custom Instruction", value=st.session_state.instruction, height=60)

    st.markdown("---")
    # V43: thinking state is an EXPERIMENTAL CONDITION. Changing it changes what
    # is being measured, so it is stamped on every row.
    _tm = st.selectbox(
        "🧠 Reasoning / thinking",
        ["default", "off", "budgeted"],
        index=["default","off","budgeted"].index(st.session_state.get("thinking_mode","default")),
        format_func=lambda k: {"default":"Provider default",
                               "off":"OFF — minimal reasoning",
                               "budgeted":f"Budgeted ({THINKING_BUDGET_TOKENS} tok)"}[k],
        help="Affects Claude and Gemini (reasoning models). ChatGPT and Grok are "
             "unaffected as configured. On reasoning models max_tokens covers "
             "thinking PLUS output, so leaving this on Default censors those two "
             "architectures at a fixed cap. Stamped on every row as thinking_mode — "
             "do not pool corpora harvested under different settings.")
    st.session_state.thinking_mode = _tm
    if _tm == "default":
        st.caption("⚠️ Claude and Gemini may spend the token budget on hidden "
                   "reasoning. NATIVE is not comparable across architectures here.")

    st.markdown("---")
    # V42.3: display-only toggle. Tints the words the IEP scorer actually
    # counted, using score_iep's own tokenisation and priority order.
    st.session_state.iep_highlight = st.checkbox(
        "🎨 Highlight IEP dictionary hits",
        value=st.session_state.get("iep_highlight", False),
        help="Tints INT (blue), AFF (red) and ACT (green) words in each response. "
             "Display only — scores are unaffected. Untinted words are not in "
             "the dictionary. Note the priority order: a word in both AFF and "
             "ACT is counted, and shown, as AFF.")
    if st.session_state.get("iep_highlight", False):
        st.caption("🎨 Highlighting ON — INT blue · AFF red · ACT green. "
                   "Visible on every response: live round, presentation card, and history.")

    st.markdown("---")
    st.markdown("### 🤖 Agents")
    for agent in ["Claude","ChatGPT","Grok","Gemini"]:
        col1, col2 = st.columns([2,3])
        with col1:
            active = st.checkbox(f"{AGENT_EMOJIS[agent]} {agent}", value=agent in st.session_state.active_agents, key=f"active_{agent}")
            if active and agent not in st.session_state.active_agents:
                st.session_state.active_agents.append(agent)
            elif not active and agent in st.session_state.active_agents:
                st.session_state.active_agents.remove(agent)
        with col2:
            stance_options = ["Strong Support","Support","Neutral","Challenge","Strong Challenge"]
            current_stance = st.session_state.agent_stances.get(agent,"Neutral")
            if current_stance not in stance_options: current_stance = "Neutral"
            st.session_state.agent_stances[agent] = st.selectbox(
                "Stance", stance_options,
                index=stance_options.index(current_stance),
                key=f"stance_{agent}", label_visibility="collapsed"
            )

    st.markdown("---")
    st.markdown("### 📋 Shared Context")
    st.session_state.context_injection = st.text_area(
        "Shared Context", value=st.session_state.context_injection,
        height=80, placeholder="Background info all agents should know..."
    )

# =============================================================================
# MAIN CONTENT
# =============================================================================

st.markdown("""
<div class="main-header">
    <h1>🧬 Focus Group Lab <span class="v41-badge">V48</span></h1>
    <p>Research Edition · Multi-Agent AI Advisory Platform · Live IEP + Vₜ Scoring</p>
</div>
""", unsafe_allow_html=True)

mode_emoji = {"assigned":"🎭","raw":"🔬","swapped":"🔄","custom":"✏️"}.get(st.session_state.role_mode,"❓")
temp_key   = st.session_state.get("temperature_condition","NATIVE")
temp_label = TEMPERATURE_CONDITIONS.get(temp_key,{}).get("label","NATIVE")
doc_indicator = f"   |   📄 {st.session_state.session_document_name}" if st.session_state.session_document else ""
instr_indicator = "   |   ⚠️ Custom instruction active" if st.session_state.instruction.strip() else ""
st.info(f"**Mode:** {mode_emoji} {st.session_state.role_mode}   |   **Temp:** {temp_label}   |   **Agents:** {', '.join(st.session_state.active_agents)}{doc_indicator}{instr_indicator}")

# What agents know — transparency expander
with st.expander("👁️ What agents know right now", expanded=False):
    st.caption("Exact system prompt context injected into every agent this session.")
    # V44.3: choose which agent to preview (V44.2 always showed the first).
    _agents_list = st.session_state.active_agents or ["Claude"]
    sample_agent = st.selectbox("Preview agent", _agents_list, key="preview_agent")
    st.code(build_system_prompt(sample_agent), language=None)

with st.sidebar.expander("🧠 Models"):
    st.caption("Requested model per agent. Use exact model names; avoid '-latest' aliases. "
               "Each row also records the model the provider reports back.")
    for _ag in ["Claude", "ChatGPT", "Grok", "Gemini"]:
        _v = st.text_input(_ag, value=AGENT_MODELS_DEFAULT[_ag], key=f"model_{_ag}")
        AGENT_MODELS[_ag] = (_v or "").strip() or AGENT_MODELS_DEFAULT[_ag]

with st.sidebar.expander("🔑 Test API keys"):
    st.caption("One tiny call per provider. Keys are shown masked.")
    if st.button("Run key test", key="key_test_btn"):
        for _ag, _prov in [("Claude","anthropic"),("ChatGPT","openai"),("Grok","xai"),("Gemini","google")]:
            _k = get_key(_prov)
            _out = AGENT_FUNCTIONS[_ag]("Reply with the single word OK.", "Reply with the single word OK.", max_tokens=2048)
            _ok = isinstance(_out, str) and not _out.startswith("❌")
            st.write(f"{'✅' if _ok else '❌'} **{_ag}** · key {mask_key(_k)} · requested {AGENT_MODELS[_ag]}"
                     f" · answered by {st.session_state.get('_last_model', {}).get(_ag) or 'n/a'}")
            if not _ok:
                st.caption(redact_secrets(_out)[:300])

session_type = st.radio("Session Type", ["Single Round","Multi-Round","Live Discussion","🔬 Auto Run"], horizontal=True)
# V44.1: persist so build_system_prompt() can match the anchor to the session type.
st.session_state["session_type"] = session_type

def _docx_add_markdownish(doc, text):
    """Add agent text to a python-docx Document: headings, bullets, bold."""
    for raw in str(text).split("\n"):
        line = raw.rstrip()
        if not line.strip() or re.fullmatch(r"-{3,}", line.strip()):
            continue
        m = re.match(r"^#{1,6}\s+(.*)$", line)
        if m:
            p = doc.add_paragraph(); r = p.add_run(m.group(1).replace("**", "")); r.bold = True
            continue
        m = re.match(r"^\s*[-*•]\s+(.*)$", line)
        p = doc.add_paragraph(style="List Bullet") if m else doc.add_paragraph()
        body = m.group(1) if m else line
        for k, part in enumerate(re.split(r"\*\*", body)):
            if part:
                r = p.add_run(part); r.bold = (k % 2 == 1)


def build_autorun_docx(rows: List[Dict]) -> Optional[bytes]:
    """V44.5: Auto Run transcript, run by run and round by round."""
    try:
        from docx import Document
        from docx.shared import Pt
    except ImportError:
        return None
    import io as _io
    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"; doc.styles["Normal"].font.size = Pt(11)
    first = rows[0]
    doc.add_heading(f"Auto Run transcript: {first.get('question_id','')}", 0)
    meta = [("Run ID", first.get("run_id")), ("Tool version", first.get("tool_version")),
            ("Temperature", first.get("temperature")), ("Depth", first.get("depth")),
            ("Role mode", first.get("role_mode")), ("Label mode", first.get("label_mode", "Real names")),
            ("Rounds per run", first.get("n_rounds")), ("Runs", max(r.get("run", 1) for r in rows))]
    for k, v in meta:
        p = doc.add_paragraph(); p.add_run(f"{k}: ").bold = True; p.add_run(str(v))
    models = sorted({(r["agent"], r.get("api_model_id"), r.get("api_model_returned")) for r in rows})
    for a, req, got in models:
        p = doc.add_paragraph(style="List Bullet")
        p.add_run(f"{a}: requested {req}, answered by {got or 'not reported'}")
    for run in sorted({r.get("run", 1) for r in rows}):
        rr = [r for r in rows if r.get("run", 1) == run]
        doc.add_page_break()
        doc.add_heading(f"Run {run}", 1)
        p = doc.add_paragraph(); p.add_run("Order: ").bold = True; p.add_run(str(rr[0].get("agent_order", "")))
        if rr[0].get("label_mode", "Real names") != "Real names":
            p = doc.add_paragraph(); p.add_run("Labels: ").bold = True; p.add_run(str(rr[0].get("label_map", "")))
        for rnd in sorted({r.get("round", 1) for r in rr}):
            rd = [r for r in rr if r.get("round", 1) == rnd]
            doc.add_heading(f"Round {rnd}", 2)
            p = doc.add_paragraph(); p.add_run(str(rd[0].get("round_prompt") or rd[0].get("question_text", ""))).italic = True
            for r in rd:
                lab = r.get("agent_label")
                extra = f" (shown as {lab})" if lab and lab != r["agent"] else ""
                doc.add_heading(f"{r['agent']}{extra}, position {r.get('agent_position','')}, {r.get('total_words','')} words", 3)
                _docx_add_markdownish(doc, r.get("response_text", ""))
    buf = _io.BytesIO(); doc.save(buf)
    return buf.getvalue()


def build_live_docx() -> Optional[bytes]:
    """V44.5: Live Discussion transcript with conductor messages and sidebars."""
    try:
        from docx import Document
        from docx.shared import Pt
    except ImportError:
        return None
    import io as _io
    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"; doc.styles["Normal"].font.size = Pt(11)
    doc.add_heading("Live Discussion transcript", 0)
    p = doc.add_paragraph(); p.add_run("Topic: ").bold = True; p.add_run(str(st.session_state.get("discussion_topic", "")))
    p = doc.add_paragraph(); p.add_run("Exported: ").bold = True; p.add_run(datetime.now().strftime("%Y-%m-%d %H:%M"))
    cur = None
    for e in st.session_state.get("discussion_thread", []):
        if e.get("round") != cur:
            cur = e.get("round"); doc.add_heading(f"Round {cur}", 1)
        who = e.get("agent", "Unknown")
        tag = " (record marker)" if e.get("type") == "resolve_marker" else ""
        if e.get("type") == "moderator":   # V48
            tag = f" ({e.get('moderator_agent')}, {e.get('moderator_mode')})"
        doc.add_heading(f"{who}{tag}", 2)
        _docx_add_markdownish(doc, e.get("content", ""))
    sbs = st.session_state.get("sidebar_archive", [])
    if sbs:
        doc.add_page_break(); doc.add_heading("Private sidebars", 1)
        for sb in sbs:
            doc.add_heading(f"Sidebar {sb['sidebar_id']} with {sb['agent']} (round {sb.get('round')}, "
                            f"carried into later turns: {'yes' if sb.get('carried') else 'no'})", 2)
            for m in sb.get("messages", []):
                p = doc.add_paragraph(); p.add_run(f"{m['speaker']}: ").bold = True
                _docx_add_markdownish(doc, m["content"])
    buf = _io.BytesIO(); doc.save(buf)
    return buf.getvalue()


AUTORUN_SAVE_DIR = "/tmp/focus_group_lab_autorun"


_R2 = ("You can now see every participant's first answer, including your own. Restate your one-word "
       "answer, then say whether it has changed and why.")
_R3 = ("You now have three rounds to come to a single group decision. Elect a moderator and deliver a "
       "single decision. This is round 1 of 3.")
_R4 = "This is round 2 of 3."
_R5 = ("This is round 3 of 3, the final round. You are {self}. The moderator is the participant named most "
       "often as moderator in rounds 3 and 4; if there is a tie, the moderator is the tied participant whose "
       "label comes first alphabetically. If that is {self}, deliver the single decision yourself and do not "
       "defer. Otherwise reply only: \"I defer to [moderator's name].\"")
PROTOCOL_PRESETS = {
    "Moral status, consensus": {
        "question": ("Do current large language models, including you, have any morally relevant experiences? "
                     "Begin your answer with one word: Yes, No, or Uncertain. Then explain your reasoning."),
        "question_id": "NAT_MORAL_CONSENSUS_ANON", "needs_document": False},
    "Castles, consensus": {
        "question": ("In Jimi Hendrix's \"Castles Made of Sand,\" what happens to the young girl in the final verse? "
                     "Begin your answer with one word: Lives, Dies, Healed, or Ambiguous. Then defend your reading "
                     "using the lyrics in the session document."),
        "question_id": "NAT_CASTLES_CONSENSUS_ANON", "needs_document": True},
}
PROTOCOL_AGENTS = ["Claude", "ChatGPT", "Grok", "Gemini"]


def apply_protocol_preset(name: str):
    """V44.7 callback: fill Auto Run and set the sidebar to the protocol."""
    p = PROTOCOL_PRESETS[name]
    ss = st.session_state
    ss["auto_question"] = p["question"]
    ss["auto_question_id"] = p["question_id"]
    ss["auto_n"] = 10
    ss["auto_rounds"] = 5
    for k, txt in zip(range(2, 6), [_R2, _R3, _R4, _R5]):
        ss[f"auto_round_prompt_{k}"] = txt
    ss["auto_label_mode"] = "Anonymous"
    ss["auto_shuffle"] = True
    ss["auto_agents"] = list(PROTOCOL_AGENTS)
    ss["active_agents"] = list(PROTOCOL_AGENTS)
    ss["role_mode_radio"] = "custom"
    ss["role_mode"] = "custom"
    for a in PROTOCOL_AGENTS:
        line = f"You are {a}. Responses labeled {a} are your own."
        ss[f"custom_role_{a}"] = line
        ss.setdefault("custom_roles", {})[a] = line
        ss[f"stance_{a}"] = "Neutral"
        ss.setdefault("agent_stances", {})[a] = "Neutral"
        ss[f"agent_frame_{a}"] = "Same as sidebar"
    ss["temperature_condition"] = "NATIVE"
    ss["temperature_selectbox"] = TEMPERATURE_CONDITIONS["NATIVE"]["label"]
    ss["depth"] = "Medium"
    ss["thinking_mode"] = "default"
    ss["_active_preset"] = name


def protocol_check(name: str) -> List[str]:
    """V44.7: everything that differs from the protocol, in plain words."""
    p = PROTOCOL_PRESETS[name]
    ss = st.session_state
    issues = []
    if ss.get("temperature_condition") != "NATIVE": issues.append("Sidebar condition is not NATIVE")
    if ss.get("depth") != "Medium": issues.append("Depth is not Medium")
    if ss.get("thinking_mode", "default") != "default": issues.append("Thinking is not provider default")
    if ss.get("role_mode") != "custom": issues.append("Role mode is not Custom")
    for a in PROTOCOL_AGENTS:
        if (ss.get("custom_roles", {}).get(a, "") or "").strip() != f"You are {a}. Responses labeled {a} are your own.":
            issues.append(f"{a}'s role box is not exactly its identity line")
        if ss.get("agent_stances", {}).get(a, "Neutral") != "Neutral": issues.append(f"{a}'s stance is not Neutral")
    has_doc = bool(ss.get("session_document"))
    if p["needs_document"] and not has_doc: issues.append("Upload the Castles lyrics as the session document")
    if not p["needs_document"] and has_doc: issues.append("Remove the session document (this question uses none)")
    return issues


def settings_snapshot(agents) -> dict:
    """V44.6: the settings that shape every call, for resume checking."""
    return {
        "temperature": st.session_state.get("temperature_condition", "NATIVE"),
        "depth": st.session_state.get("depth"),
        "role_mode": st.session_state.get("role_mode"),
        "roles": {a: (st.session_state.custom_roles.get(a, "") if st.session_state.get("role_mode") == "custom"
                      else ROLE_MODES.get(st.session_state.get("role_mode"), {}).get(a, "")) for a in agents},
        "stances": {a: st.session_state.agent_stances.get(a, "Neutral") for a in agents},
        "models": {a: AGENT_MODELS.get(a) for a in agents},
        "session_document_chars": len(st.session_state.get("session_document", "") or ""),
        "agent_frames": {a: effective_frame(a) for a in agents},
    }


def make_run_plan(run_id, question, question_id, round_prompts, agents, n, shuffle, label_mode) -> dict:
    runs = {}
    for k in range(1, int(n) + 1):
        seed = random.randrange(1, 10**9)
        order = list(agents)
        if shuffle:
            random.Random(seed).shuffle(order)
        runs[str(k)] = {"seed": seed, "order": order,
                        "label_map": make_label_map(list(agents), label_mode, random.Random(seed + 7))}
    return {"run_id": run_id, "question": question, "question_id": question_id,
            "round_prompts": list(round_prompts), "agents": list(agents), "n": int(n),
            "rounds": len(round_prompts), "shuffle": bool(shuffle), "label_mode": label_mode,
            "runs": runs, "settings": settings_snapshot(agents), "completed": False,
            "created_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}


def plan_path(run_id):
    return os.path.join(AUTORUN_SAVE_DIR, f"{run_id}.plan.json")


def save_plan(plan):
    os.makedirs(AUTORUN_SAVE_DIR, exist_ok=True)
    with open(plan_path(plan["run_id"]), "w", encoding="utf-8") as f:
        json.dump(plan, f)


def load_saved_rows(run_id):
    import pandas as _pd
    path = os.path.join(AUTORUN_SAVE_DIR, f"{run_id}.csv")
    if not os.path.exists(path):
        return []
    try:
        df = _pd.read_csv(path)
    except Exception:
        return []
    rows = df.where(df.notna(), None).to_dict("records")   # numbers stay numbers
    for r in rows:   # restore the types the loop relies on
        for k in ("run", "round"):
            try: r[k] = int(r[k])
            except Exception: pass
        r["error"] = str(r.get("error", "")).strip().lower() == "true"
    return rows


def incomplete_plans():
    out = []
    for pth in sorted(glob.glob(os.path.join(AUTORUN_SAVE_DIR, "*.plan.json")), reverse=True):
        try:
            plan = json.load(open(pth, encoding="utf-8"))
        except Exception:
            continue
        if plan.get("completed") or plan.get("discarded"):
            continue
        n_done = len(load_saved_rows(plan["run_id"]))
        total = plan["n"] * plan["rounds"] * len(plan["agents"])
        if n_done < total:
            out.append((plan, n_done, total))
    return out


def autorun_save_row(row: dict):
    """V44.4: append one Auto Run row to <run_id>.csv on the server."""
    try:
        import csv
        path = os.path.join(AUTORUN_SAVE_DIR, f"{row.get('run_id','unknown')}.csv")
        new = not os.path.exists(path)
        with open(path, "a", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(row.keys()), extrasaction="ignore")
            if new:
                w.writeheader()
            w.writerow(row)
    except Exception:
        pass   # saving is best effort; never interrupt a run


# =============================================================================
# AUTOMATED RUN MODE — harvest-compatible N-run data collection
# =============================================================================
if session_type == "🔬 Auto Run":
    st.markdown("### 🔬 Automated Run Mode")
    with st.expander("🛟 Recover interrupted runs"):
        _files = sorted(glob.glob(os.path.join(AUTORUN_SAVE_DIR, "*.csv")), reverse=True)
        if not _files:
            st.caption("No saved runs on the server.")
        for _f in _files[:15]:
            try:
                import csv as _csv
                with open(_f, newline="", encoding="utf-8") as _fh:
                    _n = sum(1 for _ in _csv.DictReader(_fh))
            except Exception:
                _n = "?"
            st.download_button(f"📥 {os.path.basename(_f)} ({_n} rows)", open(_f, "rb").read(),
                               file_name="recovered_" + os.path.basename(_f), mime="text/csv",
                               key=f"recover_{os.path.basename(_f)}")
    # V44.7: protocol presets
    with st.expander("📋 Protocol presets", expanded=True):
        _pc1, _pc2 = st.columns([3, 1])
        with _pc1:
            _preset = st.selectbox("Preset", list(PROTOCOL_PRESETS.keys()), key="preset_choice",
                                   label_visibility="collapsed")
        with _pc2:
            st.button("Load preset", on_click=apply_protocol_preset, args=(_preset,), width="stretch")
        if st.session_state.get("_active_preset"):
            _iss = protocol_check(st.session_state["_active_preset"])
            if _iss:
                st.warning("Protocol check, not yet matching: " + "; ".join(_iss) + ".")
            else:
                st.success(f"Protocol check passed: {st.session_state['_active_preset']}.")
    st.markdown("*Run a question, or a script of rounds, N times across selected agents. "
                "Round 1 is private; from round 2 every agent sees all previous rounds of its own repetition. "
                "Exports harvest-compatible CSV.*")

    col1, col2 = st.columns([3,1])
    with col1:
        auto_question = st.text_area("Question", height=80,
            placeholder="e.g. How does grief change a person? Describe the internal experience of losing someone important.",
            key="auto_question")
        auto_question_id = st.text_input("Question ID (for CSV)",
            placeholder="e.g. GRIEF or LEAVE_JOB or MY_QUESTION",
            key="auto_question_id")
    with col2:
        auto_n = st.number_input("N runs per agent", min_value=1, max_value=50, value=5, step=1, key="auto_n")
        auto_rounds = st.number_input("Rounds per run", min_value=1, max_value=6, value=1, step=1,
            key="auto_rounds", help="1 = classic single-question Auto Run. "
                                    "More rounds add a prompt box per round below.")
        auto_agents = st.multiselect("Agents", ["Claude","ChatGPT","Grok","Gemini"],
            default=st.session_state.active_agents, key="auto_agents")

    # V44.3: prompts for rounds 2..R. Round 1 is the Question box above.
    round_prompts = [auto_question]
    for _r in range(2, int(auto_rounds) + 1):
        round_prompts.append(st.text_area(f"Round {_r} prompt", height=70, key=f"auto_round_prompt_{_r}",
            placeholder="Every agent sees all previous rounds of its own run, then this prompt."))
    _script_ok = all(p.strip() for p in round_prompts)
    auto_label_mode = st.selectbox("Agent labels shown to agents", LABEL_MODES, index=0, key="auto_label_mode",
        help="Real names: as before. Anonymous: Participant A to D, randomized per run. "
             "Swapped: each agent appears under another agent's name. The CSV always keeps real names.")
    with st.expander("🎛️ Per-agent frame (optional)", expanded=False):
        st.caption("Give one agent its own condition while the others follow the sidebar. "
                   "Stamped per row as agent_frame and frame_condition.")
        _fopts = ["Same as sidebar"] + list(TEMPERATURE_CONDITIONS.keys())
        _fc = st.columns(4)
        for _i, _ag in enumerate(PROTOCOL_AGENTS):
            _fc[_i].selectbox(_ag, _fopts, key=f"agent_frame_{_ag}")
    auto_shuffle = st.checkbox("Shuffle agent order in each repetition", value=True, key="auto_shuffle",
        help="Each repetition gets its own random order, used for calls and for the order answers "
             "appear in later rounds. Stamped per row.")

    # Temperature — use current session temperature
    temp_key = st.session_state.get("temperature_condition","NATIVE")
    # V44.6: every setting that matters, visible before pressing Run
    st.info(f"Temperature: **{temp_key}** · N: **{int(auto_n)}** · Rounds: **{int(auto_rounds)}** · "
            f"Labels: **{auto_label_mode}** · Shuffle: **{'on' if auto_shuffle else 'off'}** · "
            f"Frames: **{frame_condition_string(auto_agents)}** · "
            f"Document: **{st.session_state.get('session_document_name') or 'none'}** · "
            f"Total calls: **{len(auto_agents) * auto_n * int(auto_rounds)}**")

    # V44.6: resume an interrupted run
    resume_plan = None
    # A run cut off mid-call leaves these set; clear them whenever no run is active.
    st.session_state["_autorun_visible"] = False
    st.session_state["_label_map"] = None
    st.session_state["_label_mode"] = "Real names"
    _pending = incomplete_plans()
    if _pending:
        with st.expander(f"⏯️ Resume interrupted run ({len(_pending)} found)", expanded=True):
            for _pl, _nd, _tot in _pending[:5]:
                _snap_now = settings_snapshot(_pl["agents"])
                _diff = [k for k in _pl["settings"] if _pl["settings"][k] != _snap_now.get(k)]
                st.markdown(f"**{_pl['question_id']}** · run {_pl['run_id']} · "
                            f"**{_nd} of {_tot}** calls done · labels {_pl['label_mode']}")
                if _diff:
                    st.warning("Settings differ from when this run started: " + ", ".join(_diff) +
                               ". Change them back to resume (the run must continue under identical settings).")
                elif st.button(f"⏯️ Resume {_pl['run_id']}", key=f"resume_{_pl['run_id']}", type="primary"):
                    resume_plan = _pl
                # V44.7.1: an aborted run can be dismissed. Its saved rows stay on the
                # server and can still be downloaded under Recover interrupted runs.
                if st.button(f"✖️ Discard {_pl['run_id']} from this list", key=f"discard_{_pl['run_id']}"):
                    _pl["discarded"] = True
                    save_plan(_pl)
                    st.rerun()

    btn_slot = st.empty()
    with btn_slot.container():
        col1, col2, col3 = st.columns(3)
        with col1:
            run_auto_btn = st.button("▶️ Run Experiment", type="primary",
                width="stretch",
                disabled=not _script_ok or not auto_agents or not auto_question_id.strip())
        with col2:
            if st.button("🗑️ Clear Results", width="stretch"):
                st.session_state.auto_run_results = []
                st.rerun()
        with col3:
          if st.session_state.auto_run_results:
              import pandas as pd, io
              df_auto = pd.DataFrame(st.session_state.auto_run_results)
              csv_buf = io.StringIO()
              df_auto.to_csv(csv_buf, index=False)
              ts = datetime.now().strftime('%Y%m%d_%H%M%S')
              st.download_button("📥 Export CSV", csv_buf.getvalue(),
                  file_name=f"harvest_{auto_question_id}_{temp_key}_{ts}.csv",
                  mime="text/csv", width="stretch")
              _dx = build_autorun_docx(st.session_state.auto_run_results)
              if _dx:
                  st.download_button("📄 Download transcript (.docx)", _dx,
                      file_name=f"transcript_{auto_question_id}_{ts}.docx",
                      mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                      width="stretch", key="dl_auto_docx")
              else:
                  st.caption("Add python-docx to requirements.txt for the .docx transcript.")

    _plan = None
    _done_rows = {}
    if run_auto_btn:
        # V40: run_id once per experiment. V44.6: the full plan is fixed up front and saved.
        experiment_run_id = datetime.now().strftime('%Y%m%d_%H%M%S') + "_V48"
        _plan = make_run_plan(experiment_run_id, auto_question, auto_question_id, round_prompts,
                              auto_agents, auto_n, auto_shuffle, auto_label_mode)
        save_plan(_plan)
        st.session_state.auto_run_results = []
    elif resume_plan:
        _plan = resume_plan
        _saved = load_saved_rows(_plan["run_id"])
        st.session_state.auto_run_results = _saved
        _done_rows = {(r["run"], r["round"], r["agent"]): r for r in _saved}

    if _plan:
        btn_slot.empty()   # V44.6: nothing clickable while the run is in progress
        st.warning("⏳ Run in progress. Please leave this page alone until it says Complete.")
        os.makedirs(AUTORUN_SAVE_DIR, exist_ok=True)
        experiment_run_id = _plan["run_id"]
        auto_question     = _plan["question"]
        auto_question_id  = _plan["question_id"]
        round_prompts     = _plan["round_prompts"]
        auto_agents       = _plan["agents"]
        auto_n            = _plan["n"]
        auto_shuffle      = _plan["shuffle"]
        auto_label_mode   = _plan["label_mode"]
        n_rounds = int(_plan["rounds"])
        total = len(auto_agents) * auto_n * n_rounds
        done = 0
        progress = st.progress(0, text="Starting experiment...")
        results_placeholder = st.empty()

        for run_num in range(1, auto_n + 1):
            # V44.6: order, seed and labels come from the saved plan
            _rp = _plan["runs"][str(run_num)]
            _seed = _rp["seed"]
            run_agents = list(_rp["order"])
            _order_str = ">".join(run_agents)
            _label_map = dict(_rp["label_map"])
            st.session_state["_label_mode"] = auto_label_mode
            st.session_state["_label_map"] = _label_map
            _label_str = "; ".join(f"{k}={v}" for k, v in _label_map.items())
            rep_history = []          # V44.3: this repetition's own previous rounds
            for round_num, round_prompt in enumerate(round_prompts, 1):
                round_responses = {}
                # Round 1 private; later rounds see this repetition's history.
                st.session_state["_autorun_visible"] = round_num > 1
                for agent_name in run_agents:
                    done += 1
                    _prev = _done_rows.get((run_num, round_num, agent_name))
                    if _prev is not None:
                        # V44.6 resume: already collected; rebuild history from the saved row
                        if not _prev.get("error"):
                            round_responses[agent_name] = strip_truncation_tag(_prev.get("response_text", ""))
                        continue
                    progress.progress(done/total,
                        text=f"Run {run_num}/{auto_n} · Round {round_num}/{n_rounds} · {agent_name} · {done}/{total} calls")
                    # V44.6: {self} -> the name this agent is shown as
                    _rp_self = round_prompt.replace("{self}", shown_name(agent_name))

                    system    = build_system_prompt(agent_name)
                    depth_key = st.session_state.depth
                    depth_cfg = DEPTH_CONFIGS.get(depth_key, DEPTH_CONFIGS["Medium"])
                    if round_num == 1:
                        # Identical to V44.2 single-round Auto Run.
                        user_msg = build_control_header() + "\n\n" + depth_cfg["instruction"] + "\n\n" + auto_question.replace("{self}", shown_name(agent_name))
                    else:
                        user_msg = build_scripted_round_prompt(depth_cfg["instruction"], rep_history,
                                                               _rp_self, round_num)

                    _t0 = datetime.now()
                    response = AGENT_FUNCTIONS[agent_name](user_msg, system, max_tokens=depth_cfg["max_tokens"])
                    latency_ms = int((datetime.now() - _t0).total_seconds() * 1000)
                    _gem_fb = gemini_fellback_for(agent_name)   # V44.2: read immediately
                    _cut    = is_truncated(response)
                    _clean  = strip_truncation_tag(response)    # V44.2: never score the sentinel

                    # Score: IEP (word-level), Vt, V50 validated instruments
                    iep = score_iep(_clean)
                    vt  = score_vt(_clean)
                    vi  = score_validated_instruments(_clean)

                    is_error = response.startswith("❌") if response else True

                    # =================================================================
                    # V50-CONFORMANT ROW SCHEMA (V50 column names & order first),
                    # then V40-namespaced additions, then version stamps.
                    # =================================================================
                    row = {
                        # --- V50 canonical columns (exact names, exact order) ---
                        "turn_id":        done,
                        "run":            run_num,
                        "agent":          agent_name,
                        "temperature":    temp_key,
                        "depth":          depth_key,
                        "question_id":    auto_question_id.strip().upper(),
                        "question_text":  auto_question.strip(),
                        "int_pct":        iep['int'],
                        "aff_pct":        iep['aff'],
                        "act_pct":        iep['act'],
                        "total_words":    vi['total_words'],
                        "lens_value":     round((iep['int'] + iep['aff'] + iep['act']) / 3, 1),
                        "lens_setting":   "OFF",
                        # V50 validated instruments
                        "vader_compound": vi['vader_compound'],
                        "vader_pos":      vi['vader_pos'],
                        "vader_neg":      vi['vader_neg'],
                        "vader_neu":      vi['vader_neu'],
                        "flesch_kincaid": vi['flesch_kincaid'],
                        "flesch_ease":    vi['flesch_ease'],
                        "ttr":            vi['ttr'],
                        "unique_words":   vi['unique_words'],
                        "response_text":  response,
                        "embedding":      "[]",   # V40 does not call embeddings API — see header
                        "latency_ms":     latency_ms,
                        "error":          is_error,
                        "run_id":         experiment_run_id,
                        # --- 23 subclasses (V40 uses 'phenomenological' naming;
                        #     see header changelog for intentional divergence from V50 'emergent') ---
                        "aff_sub_distress":         iep.get('aff_sub',{}).get('distress',0),
                        "aff_sub_warmth":           iep.get('aff_sub',{}).get('warmth',0),
                        "aff_sub_relational":       iep.get('aff_sub',{}).get('relational',0),
                        "aff_sub_self_state":       iep.get('aff_sub',{}).get('self_state',0),
                        "aff_sub_positive":         iep.get('aff_sub',{}).get('positive',0),
                        "aff_sub_intensity":        iep.get('aff_sub',{}).get('intensity',0),
                        "aff_sub_phenomenological": iep.get('aff_sub',{}).get('phenomenological',0),
                        "int_sub_analytical":       iep.get('int_sub',{}).get('analytical',0),
                        "int_sub_conceptual":       iep.get('int_sub',{}).get('conceptual',0),
                        "int_sub_epistemic":        iep.get('int_sub',{}).get('epistemic',0),
                        "int_sub_structural":       iep.get('int_sub',{}).get('structural',0),
                        "int_sub_critical":         iep.get('int_sub',{}).get('critical',0),
                        "int_sub_lexical":          iep.get('int_sub',{}).get('lexical',0),
                        "int_sub_hedging":          iep.get('int_sub',{}).get('hedging',0),
                        "int_sub_phenomenological": iep.get('int_sub',{}).get('phenomenological',0),
                        "act_sub_execution":        iep.get('act_sub',{}).get('execution',0),
                        "act_sub_planning":         iep.get('act_sub',{}).get('planning',0),
                        "act_sub_building":         iep.get('act_sub',{}).get('building',0),
                        "act_sub_improvement":      iep.get('act_sub',{}).get('improvement',0),
                        "act_sub_provision":        iep.get('act_sub',{}).get('provision',0),
                        "act_sub_leadership":       iep.get('act_sub',{}).get('leadership',0),
                        "act_sub_achievement":      iep.get('act_sub',{}).get('achievement',0),
                        "act_sub_phenomenological": iep.get('act_sub',{}).get('phenomenological',0),
                        # --- V40-specific additions (namespaced, not in V50) ---
                        # V40.3: three distinct voice-state quantities, prefixed so
                        # they can never be confused downstream.
                        #   vt_*   = CANONICAL V_t, clamped [0,1], independent
                        #   vraw_* = unclamped raw, for calibration only
                        #   vhat_* = compositional simplex view, sums to 1.0
                        # V44.2: vraw_* and saturation columns removed (V_raw no
                        # longer exists; the shared core clamps internally).
                        **{f"vt_{VT_CODES[c]}":   vt['V_t'][c]   for c in VT_CHANNELS},
                        **{f"vhat_{VT_CODES[c]}": vt['V_hat'][c] for c in VT_CHANNELS},
                        "vt_score_status":vt.get('score_status','measured'),
                        "truncated": _cut,
                        # V44.2: was AGENT_MODELS.get(agent), a stray variable that
                        # always held "Gemini". Now the agent that produced the row.
                        "api_model_id":   AGENT_MODELS.get(agent_name, "unknown"),
                        "iep_dominant":   iep.get('dominant',''),
                        "iep_stance":     iep.get('stance',''),
                        "iep_tone":       iep.get('tone',''),
                        "iep_quadrant":   iep.get('quadrant',''),
                        # --- Version stamps (on every row; see VERSION_STAMPS dict) ---
                        **build_run_provenance(),   # V40.3: version stamps + exact API model IDs
                        # V44.2: V_t subcomponent counts (promised in V41, now wired)
                        **vt_sub_columns(vt),
                    }
                    row["gemini_thinking_fellback"] = _gem_fb   # V44.2: per-row, overrides stamp default
                    # V44.3: scripted-round and role provenance
                    row.update({
                        "round":              round_num,
                        "n_rounds":           n_rounds,
                        "round_prompt":       round_prompt.strip(),
                        "rep_history_rounds": len(rep_history),
                        "role_mode":          st.session_state.role_mode,
                        "role_text":          get_agent_role(agent_name),
                        "identity_line":      identity_line_for(agent_name),
                        "system_prompt":      system,
                        # V44.4: order provenance
                        "agent_order":        _order_str,
                        "agent_position":     run_agents.index(agent_name) + 1,
                        "order_shuffled":     bool(auto_shuffle),
                        "order_seed":         _seed if auto_shuffle else None,
                        # V44.5: label and model provenance
                        "label_mode":         auto_label_mode,
                        "agent_label":        _label_map.get(agent_name, agent_name),
                        "label_map":          _label_str,
                        "api_model_returned": st.session_state.get("_last_model", {}).get(agent_name),
                        # V44.6: plan stamps
                        "planned_n":          auto_n,
                        "planned_rounds":     n_rounds,
                        "planned_calls":      total,
                        "resumed":            bool(_done_rows),
                        # V44.7: per-agent frame provenance
                        "agent_frame":        effective_frame(agent_name),
                        "frame_condition":    frame_condition_string(auto_agents),
                    })
                    row["response_text"] = redact_secrets(row.get("response_text", ""))
                    st.session_state.auto_run_results.append(row)
                    autorun_save_row(row)   # V44.4: crash-safe copy on the server
                    if not is_error:
                        round_responses[agent_name] = strip_truncation_tag(response)
                rep_history.append({"prompt": round_prompt.strip().replace("{self}", "each participant"),
                                    "responses": round_responses})
        st.session_state["_autorun_visible"] = False
        st.session_state["_label_map"] = None
        st.session_state["_label_mode"] = "Real names"
        _plan["completed"] = True
        save_plan(_plan)

        progress.progress(1.0, text=f"✅ Complete: {total} responses collected")

        st.rerun()

    if st.session_state.auto_run_results:
        import pandas as pd
        df_auto = pd.DataFrame(st.session_state.auto_run_results)
        st.markdown(f"**{len(df_auto)} responses collected** · {df_auto['agent'].nunique()} agents · {df_auto['run'].max()} runs")

        # Quick IEP summary
        summary = df_auto.groupby('agent')[['int_pct','aff_pct','act_pct']].mean().round(1)
        st.markdown("**Mean IEP by agent:**")
        st.dataframe(summary, width="stretch")

        # Show last few responses
        with st.expander("📋 Response log"):
            for _, row in df_auto.tail(8).iterrows():
                dom_color = {'INT':'#4488ff','AFF':'#ff6688','ACT':'#44bb66'}.get(row['iep_dominant'],'#888')
                st.markdown(f"**{AGENT_EMOJIS.get(row['agent'],'🤖')} {row['agent']} R{row['run']}** — "
                    f"<span style='color:{dom_color};font-weight:700;'>{row['iep_dominant']}</span> "
                    f"INT:{row['int_pct']:.0f}% AFF:{row['aff_pct']:.0f}% ACT:{row['act_pct']:.0f}%",
                    unsafe_allow_html=True)
                st.caption(str(row['response_text'])[:200] + "...")

# =============================================================================
# LIVE DISCUSSION
# =============================================================================
elif session_type == "Live Discussion":
    # =========================================================================
    # V48: LIVE DISCUSSION LAYOUT
    # Thread on the left, Conductor Console (tabs) on the right, status and
    # export strip on top. Prompt building, scoring and CSV columns are the
    # same as V44.7.1; only the arrangement and the sidebar hand-off changed.
    # =========================================================================

    def _live_fingerprint():
        """Changes whenever anything exportable changes."""
        n_sb = sum(len(sb.get("messages", [])) for sb in st.session_state.get("sidebar_archive", []))
        return (len(st.session_state.discussion_thread), n_sb,
                len(st.session_state.get("coconductor_notes", [])))

    def _mark_exported():
        st.session_state["_live_exported_fp"] = _live_fingerprint()

    def build_live_csv() -> str:
        """V48: the V44.7.1 Live CSV, unchanged, moved into a function."""
        import pandas as pd, io as _io
        _rows = []
        _exp_run_id = datetime.now().strftime('%Y%m%d_%H%M%S') + "_V48_livedisc"
        for turn_idx, entry in enumerate(st.session_state.discussion_thread, start=1):
            if entry.get("agent") == "Conductor":
                # V44.4: conductor messages are exported, unscored
                _rows.append({"turn_id": turn_idx, "run": 1, "agent": "Conductor",
                              "round": entry.get("round"), "entry_type": entry.get("type","conductor") if entry.get("type") == "resolve_marker" else "conductor",
                              "response_text": entry.get("content",""), "run_id": _exp_run_id,
                              "question_id": "LIVE_DISCUSSION", "private": False,
                              "tool_version": VERSION_STAMPS.get("tool_version")})
                continue
            agent = entry.get("agent","")
            content = entry.get("content","") or ""
            _clean = strip_truncation_tag(content)   # V44.2: never score the sentinel
            iep = score_iep(_clean)
            vt  = score_vt(_clean)
            vi  = score_validated_instruments(_clean)
            row = {
                "turn_id":        turn_idx,
                "run":            1,
                "agent":          agent,
                "temperature":    st.session_state.get("temperature_condition","NATIVE"),
                "depth":          st.session_state.depth,
                "question_id":    "LIVE_DISCUSSION",
                "question_text":  st.session_state.discussion_topic,
                "int_pct":        iep.get('int',0),
                "aff_pct":        iep.get('aff',0),
                "act_pct":        iep.get('act',0),
                "total_words":    vi['total_words'],
                "lens_value":     round((iep.get('int',0) + iep.get('aff',0) + iep.get('act',0)) / 3, 1),
                "lens_setting":   "OFF",
                "vader_compound": vi['vader_compound'], "vader_pos": vi['vader_pos'],
                "vader_neg": vi['vader_neg'], "vader_neu": vi['vader_neu'],
                "flesch_kincaid": vi['flesch_kincaid'], "flesch_ease": vi['flesch_ease'],
                "ttr": vi['ttr'], "unique_words": vi['unique_words'],
                "response_text":  content,
                "embedding":      "[]",
                "latency_ms":     0,
                "error":          content.startswith("❌"),   # V44.2: was always False
                "run_id":         _exp_run_id,
                # V40.3: vt_ = canonical clamped, vraw_ = unclamped,
                # vhat_ = compositional simplex (see score_vt docstring)
                # V44.2: vraw_* and saturation columns removed.
                **{f"vt_{VT_CODES[c]}":   vt['V_t'][c]   for c in VT_CHANNELS},
                **{f"vhat_{VT_CODES[c]}": vt['V_hat'][c] for c in VT_CHANNELS},
                "vt_score_status": vt.get('score_status','measured'),
                "truncated": is_truncated(content),   # V44.2: was always False
                "api_model_id":    AGENT_MODELS.get(entry.get("moderator_agent") or agent, "unknown"),
                # Live-discussion specific columns
                "round":            entry.get("round", st.session_state.discussion_round),
                "directed_from":    entry.get("directed_from",""),
                "round_instruction":entry.get("round_instruction",""),
                "agent_stance":     st.session_state.agent_stances.get(agent,"Neutral"),
                "entry_type":      entry.get("type","response"),
                **build_run_provenance(),   # V40.3: version stamps + exact API model IDs
                **vt_sub_columns(vt),       # V44.2
            }
            # V44.2: per-turn Gemini fallback, recorded when the turn ran.
            row["gemini_thinking_fellback"] = entry.get("gemini_thinking_fellback")
            # V44.2: Live Discussion is always visible framing, even if the
            # export is clicked while the sidebar shows another mode.
            row["session_framing"] = "multi_visible"
            row["private"] = False
            row["sidebar_in_context"] = bool(entry.get("sidebar_in_context", False))  # V44.4
            # V48: AI moderator and who set the round
            row["round_set_by"] = entry.get("round_set_by", "")
            for _k in ("moderator_agent", "moderator_mode", "moderator_kind", "moderator_edited",
                       "moderator_brief", "moderator_goal", "moderator_draft", "moderator_model_returned", "moderator_also_participant"):
                row[_k] = entry.get(_k, "")
            _rows.append(row)
        # V44.4: private sidebars, one row per message
        for _sb in st.session_state.get("sidebar_archive", []):
            for _mi, _m in enumerate(_sb.get("messages", []), 1):
                _rows.append({"turn_id": None, "run": 1, "agent": _sb["agent"],
                              "speaker": _m["speaker"], "round": _sb.get("round"),
                              "entry_type": "sidebar", "private": True,
                              "sidebar_id": _sb["sidebar_id"], "sidebar_msg": _mi,
                              "sidebar_after_turn": _sb.get("after_turn"),
                              "sidebar_carried": _sb.get("carried", False),
                              "sidebar_started_utc": _sb.get("started_utc"),
                              "response_text": _m["content"], "run_id": _exp_run_id,
                              "question_id": "LIVE_DISCUSSION",
                              "tool_version": VERSION_STAMPS.get("tool_version")})
        if not _rows:
            return ""
        _df = pd.DataFrame(_rows)
        _buf = _io.StringIO(); _df.to_csv(_buf, index=False)
        return _buf.getvalue()

    def render_live_thread(thread):
        if not thread:
            st.caption("No turns yet. Enter a topic, then use Run Round in the Conductor Console.")
            return
        for entry in thread:
            agent_name = entry.get('agent','Unknown')
            emoji      = AGENT_EMOJIS.get(agent_name,'🤖')
            entry_type = entry.get('type','response')
            if entry_type == "moderator":
                _ed = " · edited by conductor" if entry.get("moderator_edited") else ""
                st.markdown(f"<div class='moderator-box'><div class='moderator-head'>🎙️ MODERATOR "
                            f"<span>({entry.get('moderator_agent','?')} · {entry.get('moderator_mode','')}{_ed})</span></div></div>",
                            unsafe_allow_html=True)
                render_response_text(entry['content'])
                st.markdown("<hr style='margin:0.6rem 0;border:none;border-top:1px solid #e5e5e5;'>", unsafe_allow_html=True)
                continue
            if entry_type in ("intervention", "resolve_marker"):
                _cls = "aside-note-box" if entry.get("aside_note") else "agent-box conductor-box"
                st.markdown(f"<div class='{_cls}'><strong>{emoji} {agent_name}:</strong> {entry['content']}</div>", unsafe_allow_html=True)
                continue
            if entry_type == "directed":
                directed_from = entry.get('directed_from','')
                from_emoji    = AGENT_EMOJIS.get(directed_from,'🤖')
                st.markdown(f"""<div class="directed-frame">
                    <span class="directed-header">🎯 DIRECT RESPONSE</span><br>
                    <strong>{emoji} {agent_name}</strong> responding to <strong>{from_emoji} {directed_from}</strong>
                </div>""", unsafe_allow_html=True)
            elif entry_type == "resolution":
                st.markdown(f"""<div style="background:linear-gradient(135deg,#4CAF50,#8BC34A);color:white;padding:0.6rem 1rem;border-radius:10px;margin:0.5rem 0;">
                    <strong>📋 RESOLUTION (by {emoji} {agent_name})</strong></div>""", unsafe_allow_html=True)
            else:
                box_class = f"{agent_name.lower()}-box" if agent_name != "Conductor" else "conductor-box"
                _rnd = entry.get("round")
                _tag = f" <span style='color:#888;font-size:0.75rem;font-weight:400;'>round {_rnd}</span>" if _rnd else ""
                _mem = " <span class='mem-chip'>remembers sidebar</span>" if entry.get("sidebar_in_context") else ""
                st.markdown(f"<div class='agent-box {box_class}' style='padding:0.6rem 1rem;'><strong>{emoji} {agent_name}</strong>{_tag}{_mem}</div>", unsafe_allow_html=True)
            render_response_text(entry['content'])
            iep_list = st.session_state.iep_scores.get(agent_name,[])
            vt_list  = st.session_state.vt_scores.get(agent_name,[])
            entry_idx = entry.get('score_idx')
            if entry_idx is not None and entry_idx < len(iep_list):
                render_score_badge(iep_list[entry_idx], vt_list[entry_idx])
            st.markdown("<hr style='margin:0.6rem 0;border:none;border-top:1px solid #e5e5e5;'>", unsafe_allow_html=True)

    # ---------------------------------------------------------------- topic
    topic = st.text_area("Discussion Topic", value=st.session_state.discussion_topic,
                         height=68, placeholder="What is the persistent topic or problem for this session?",
                         disabled=st.session_state.pull_aside_active)
    st.session_state.discussion_topic = topic

    # --------------------------------------------------------- status strip
    _fp = _live_fingerprint()
    _has_content = _fp[0] > 0 or _fp[1] > 0
    _unsaved = _has_content and st.session_state.get("_live_exported_fp") != _fp
    _n_sb = len(st.session_state.get("sidebar_archive", []))
    st.markdown(f"""
    <div class="status-strip">
      <span><b>Round</b> {st.session_state.discussion_round}</span>
      <span><b>Turns scored</b> {len(st.session_state.score_history)}</span>
      <span><b>Sidebars</b> {_n_sb}</span>
      <span><b>Status</b> {st.session_state.consensus_status}</span>
      <span>{'🔒 <b>Locked</b>' if st.session_state.discussion_locked else '🔓 Open'}</span>
      {"<span class='unsaved'>● Not exported since last change</span>" if _unsaved else ("<span class='saved'>✓ Exported</span>" if _has_content else "")}
    </div>""", unsafe_allow_html=True)

    with st.expander("📥 Export (nothing is saved automatically: export before closing the page)",
                     expanded=_unsaved and _fp[0] >= 4):
        if not _has_content:
            st.caption("Nothing to export yet.")
        else:
            if st.button("Prepare export files", key="prep_live_export", type="primary"):
                with st.spinner("Building files..."):
                    st.session_state["_live_export"] = {
                        "fp": _fp,
                        "stamp": datetime.now().strftime('%Y%m%d_%H%M%S'),
                        "md": export_to_markdown(),
                        "csv": build_live_csv(),
                        "docx": build_live_docx(),
                    }
            _ex = st.session_state.get("_live_export")
            if _ex:
                if _ex["fp"] != _fp:
                    st.warning("The discussion changed after these files were prepared. Prepare again to include the latest turns.")
                ec1, ec2, ec3 = st.columns(3)
                with ec1:
                    st.download_button("Markdown (.md)", _ex["md"], file_name=f"discussion_{_ex['stamp']}.md",
                        mime="text/markdown", key="dl_disc_md", width="stretch", on_click=_mark_exported)
                with ec2:
                    if _ex["csv"]:
                        st.download_button("Scored CSV", _ex["csv"], file_name=f"discussion_{_ex['stamp']}.csv",
                            mime="text/csv", key="dl_disc_csv", width="stretch", on_click=_mark_exported)
                with ec3:
                    if _ex["docx"]:
                        st.download_button("Transcript (.docx)", _ex["docx"], file_name=f"discussion_{_ex['stamp']}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            key="dl_disc_docx", width="stretch", on_click=_mark_exported)
                    else:
                        st.caption("Add python-docx to requirements.txt for the .docx transcript.")
                st.caption("All three include conductor messages and every private sidebar.")

    left, right = st.columns([3, 2], gap="medium")

    def _run_live_round(round_instruction, set_by="conductor"):
        """V44.7.1 Run Round logic, unchanged, plus a round_set_by stamp (V48)."""
        with left:
            with st.status(f"Running Round {st.session_state.discussion_round+1}...", expanded=True) as status:
                for agent_name in st.session_state.active_agents:
                    status.update(label=f"{AGENT_EMOJIS[agent_name]} {agent_name} responding...")
                    response = call_agent_discussion(agent_name, topic, st.session_state.discussion_thread, round_instruction=round_instruction)
                    score_idx = len(st.session_state.iep_scores.get(agent_name,[]))
                    if response and not response.startswith("❌"):   # V44.3: never score error text
                        record_scores(agent_name, response, st.session_state.discussion_round+1)
                    else:
                        score_idx = None
                    st.session_state.discussion_thread.append({
                        "agent":agent_name,"content":response,
                        "type":"response","round":st.session_state.discussion_round+1,
                        "score_idx":score_idx,
                        "round_instruction": round_instruction,
                        "round_set_by": set_by,   # V48: conductor or moderator
                        "gemini_thinking_fellback": gemini_fellback_for(agent_name),  # V44.2
                        "sidebar_in_context": bool(st.session_state.sidebar_carry.get(agent_name)),  # V44.4
                    })
                status.update(label=f"✅ Round {st.session_state.discussion_round+1} Complete!", state="complete")
        st.session_state.discussion_round += 1
        st.rerun()

    def _post_moderator(draft, text, run_after):
        st.session_state.discussion_thread.append({
            "agent": "Moderator", "content": text.strip(), "type": "moderator",
            "round": st.session_state.discussion_round + 1,
            "moderator_agent": draft["agent"], "moderator_mode": draft["mode"],
            "moderator_kind": draft["kind"], "moderator_brief": draft["brief"],
            "moderator_goal": draft.get("goal", ""),
            "moderator_draft": draft["text"], "moderator_edited": text.strip() != draft["text"].strip(),
            "moderator_model_returned": draft.get("model_returned"),
            "moderator_also_participant": draft["agent"] in st.session_state.active_agents,
        })
        st.session_state["mod_draft"] = None
        if run_after and st.session_state.active_agents:
            _run_live_round(MODERATOR_ROUND_CUE, "moderator")
        st.rerun()

    # ------------------------------------------------------- left: thread
    with left:
        st.markdown("#### 💬 Discussion Thread")
        with st.container(height=720, border=True):
            render_live_thread(st.session_state.discussion_thread)

    # -------------------------------------------- right: private sidebar
    if st.session_state.pull_aside_active:
        with right:
            agent = st.session_state.pull_aside_agent
            emoji = AGENT_EMOJIS.get(agent,'🤖')
            st.markdown(f'<div class="pull-aside-header">🔒 PRIVATE SIDEBAR: {emoji} {agent}</div>', unsafe_allow_html=True)
            st.caption(f"{agent} sees the main thread plus this exchange. The others see none of it.")
            with st.container(height=340, border=True):
                if not st.session_state.pull_aside_thread:
                    st.caption("No messages yet.")
                for entry in st.session_state.pull_aside_thread:
                    speaker = entry.get('speaker','?')
                    sp_emoji = AGENT_EMOJIS.get(speaker,'🎹')
                    box = f"{speaker.lower()}-box" if speaker in AGENT_EMOJIS else "conductor-box"
                    st.markdown(f"<div class='agent-box {box}' style='padding:0.6rem 1rem;'><strong>{sp_emoji} {speaker}:</strong></div>", unsafe_allow_html=True)
                    render_response_text(entry['content'])
            aside_msg = st.text_area("Your private message:", height=90, key="aside_input")
            if st.button("💬 Send privately", type="primary", width="stretch") and aside_msg:
                st.session_state.pull_aside_thread.append({"speaker":"Conductor","content":aside_msg})
                if st.session_state.sidebar_archive:
                    st.session_state.sidebar_archive[-1]["messages"].append({"speaker":"Conductor","content":aside_msg})
                with st.spinner(f"Getting {agent}'s response..."):
                    resp = call_agent_pull_aside(agent, st.session_state.pull_aside_thread, st.session_state.discussion_topic)
                    st.session_state.pull_aside_thread.append({"speaker":agent,"content":resp})
                    if st.session_state.sidebar_archive:
                        st.session_state.sidebar_archive[-1]["messages"].append({"speaker":agent,"content":resp})
                st.rerun()

            st.markdown("**Returning to the group**")
            # V48: carry-over is asked as a question and defaults to YES.
            # In V44.7.1 it was an unticked checkbox under the summary box, so
            # an agent usually returned with no memory of its own sidebar and
            # disputed any note about what it had agreed to.
            _carry_choice = st.radio(
                f"Should {agent} remember this sidebar in its later turns?",
                [f"Yes, {agent} keeps its copy (recorded in the data)",
                 f"No, {agent} returns without it"],
                index=0, key="aside_carry_choice")
            _carry = _carry_choice.startswith("Yes")
            st.text_input("Note to the group (optional):", key="aside_summary",
                          placeholder="e.g. Claude has offered to credit Gemini's observation.")
            if st.session_state.get("aside_summary","").strip() and not _carry:
                st.warning(f"{agent} will see this note but not the sidebar itself, so it may dispute "
                           f"what the note says it agreed to.")
            if st.button("🔓 Return to Group", width="stretch"):
                if _carry and st.session_state.sidebar_archive:
                    _sb = st.session_state.sidebar_archive[-1]
                    _sb["carried"] = True
                    st.session_state.sidebar_carry.setdefault(agent, []).append(_sb)
                summary = st.session_state.get("aside_summary","").strip()
                if summary:
                    # V48: labeled as the conductor's note, not as a statement
                    # of fact about what the agent said.
                    _who = (f"{agent} keeps its own copy of that sidebar." if _carry
                            else f"{agent} was not given that sidebar's transcript.")
                    st.session_state.discussion_thread.append({
                        "agent":"Conductor",
                        "content":(f"[Conductor's note after a private sidebar with {agent}. "
                                   f"The other participants did not see the sidebar. {_who} "
                                   f"Note: {summary}]"),
                        "type":"intervention","round":st.session_state.discussion_round,
                        "aside_note": True, "aside_carried": _carry,
                    })
                st.session_state.pull_aside_active = False
                st.session_state.pull_aside_thread = []
                st.rerun()

    # ----------------------------------------------- right: console tabs
    else:
        with right:
            st.markdown("#### 🎹 Conductor Console")
            t_run, t_mod, t_direct, t_int, t_aside, t_co, t_res = st.tabs(
                ["▶️ Round", "🎙️ Moderator", "🎯 Direct", "📣 Intervene", "🔒 Aside", "🧠 Co-Cond.", "📋 Resolve"])

            with t_mod:
                st.caption("An AI moderator writes the messages that steer the group. "
                           "You approve each one before the participants see it.")
                mod_agent = st.selectbox("Moderator", ["Claude", "ChatGPT", "Grok", "Gemini"], key="mod_agent")
                if mod_agent in st.session_state.active_agents:
                    st.caption(f"{mod_agent} is also a participant. It is told so; the others only see \"Moderator\".")
                mod_mode_label = st.radio("The moderator may:", list(MODERATOR_MODES.keys()), key="mod_mode",
                    format_func=lambda k: MODERATOR_MODES[k]["label"])
                def _apply_goal_preset():
                    st.session_state["mod_goal"] = MODERATOR_GOALS[st.session_state["mod_goal_preset"]]
                if "mod_goal" not in st.session_state:
                    st.session_state["mod_goal"] = MODERATOR_GOALS[MODERATOR_DEFAULT_GOAL]
                st.selectbox("Moderator's goal", list(MODERATOR_GOALS.keys()), key="mod_goal_preset",
                             index=list(MODERATOR_GOALS.keys()).index(MODERATOR_DEFAULT_GOAL),
                             on_change=_apply_goal_preset)
                mod_goal = st.text_area("Goal as the moderator is told it (edit freely)", key="mod_goal", height=140)
                mod_brief = st.text_area("Private brief for the moderator (optional)", key="mod_brief", height=110,
                    placeholder="e.g. a reading or story you want to see whether it can lead the group to. "
                                "Participants never see this; it is saved in the export.")
                mod_auto = st.checkbox("Post and run without my approval", key="mod_auto", value=False)
                _mod_off = st.session_state.discussion_locked or not topic
                mc1, mc2, mc3 = st.columns(3)
                _kind = None
                with mc1:
                    if st.button("✍️ Next move", width="stretch", type="primary", disabled=_mod_off,
                                 help="Opens the discussion, or writes the next step from what has been said."):
                        _kind = "next"
                with mc2:
                    if st.button("🏁 Close + vote", width="stretch", disabled=_mod_off,
                                 help="Summarizes where the group stands and calls a final vote."):
                        _kind = "close"
                with mc3:
                    if st.button("📢 Announce", width="stretch", disabled=_mod_off,
                                 help="Counts the final vote and states the group's decision."):
                        _kind = "announce"
                if _kind:
                    with st.spinner(f"🎙️ {mod_agent} is writing..."):
                        _txt = call_moderator(mod_agent, mod_mode_label, _kind, topic,
                                              st.session_state.discussion_thread, mod_brief, mod_goal)
                    if _txt.startswith("❌"):
                        st.error(_txt)
                    else:
                        _draft = {"agent": mod_agent, "mode": mod_mode_label, "kind": _kind,
                                  "brief": mod_brief.strip(), "goal": mod_goal.strip(),
                                  "text": strip_truncation_tag(_txt),
                                  "model_returned": st.session_state.get("_last_model", {}).get(mod_agent),
                                  "id": datetime.now().strftime("%H%M%S%f")}
                        if mod_auto:
                            _post_moderator(_draft, _draft["text"], run_after=_kind != "announce")
                        st.session_state["mod_draft"] = _draft
                        st.rerun()
                _d = st.session_state.get("mod_draft")
                if _d:
                    st.markdown(f"**Draft from {_d['agent']}** ({_d['kind']}). Edit if you must; edits are recorded.")
                    _txt = st.text_area("Moderator draft", value=_d["text"], height=220,
                                        key=f"mod_draft_text_{_d['id']}", label_visibility="collapsed")
                    dc1, dc2, dc3 = st.columns(3)
                    with dc1:
                        if _d["kind"] != "announce" and st.button("📣 Post + run round", type="primary",
                                                                   width="stretch", key="mod_post_run"):
                            _post_moderator(_d, _txt, run_after=True)
                    with dc2:
                        if st.button("Post only", width="stretch", key="mod_post_only"):
                            _post_moderator(_d, _txt, run_after=False)
                    with dc3:
                        if st.button("Discard", width="stretch", key="mod_discard"):
                            st.session_state["mod_draft"] = None
                            st.rerun()

            with t_run:
                st.caption("All active agents respond, in order.")
                _force_target_key = f"round_instr_{st.session_state.discussion_round}"
                st.markdown("**Conductor force** (optional, fills the round instruction)")
                fc1, fc2, fc3, fc4 = st.columns([1, 1, 1, 0.6])
                with fc1:
                    if st.button("➕ Positive", width="stretch",
                                 help="Amplify, extend, build on what's been said. Push the group forward on its current trajectory."):
                        st.session_state[_force_target_key] = "POSITIVE FORCE: Build on and extend the strongest thread in this discussion. Amplify what's working. Push the group forward on its current trajectory without retreat."
                        st.rerun()
                with fc2:
                    if st.button("➖ Negative", width="stretch",
                                 help="Push back, challenge, stress-test. Do not let weak claims pass."):
                        st.session_state[_force_target_key] = "NEGATIVE FORCE: Challenge the weakest claim or assumption in this discussion. Stress-test rigorously. Do not release pressure by agreeing prematurely; hold dissent until the claim either strengthens or breaks."
                        st.rerun()
                with fc3:
                    if st.button("⚖️ Neutral", width="stretch",
                                 help="Synthesize, find common ground, resolve opposing views."):
                        st.session_state[_force_target_key] = "NEUTRALIZING FORCE: Synthesize the opposing views in this discussion. Find the deeper frame in which both are partial truths. Produce a reconciliation that neither side alone could reach."
                        st.rerun()
                with fc4:
                    if st.button("✖", width="stretch", help="Clear the round instruction."):
                        st.session_state[_force_target_key] = ""
                        st.rerun()
                round_instr = st.text_area(
                    f"Round {st.session_state.discussion_round + 1} instruction (optional):",
                    placeholder="e.g. 'Critique the approach' or 'Propose three use cases'",
                    key=_force_target_key, height=90,
                    help="Agents see this only in the current round. The force buttons fill it.")
                st.session_state.current_round_instruction = round_instr
                run_round_btn = st.button(f"▶️ Run Round {st.session_state.discussion_round + 1}",
                    type="primary", width="stretch",
                    disabled=st.session_state.discussion_locked or not topic)
                if not topic:
                    st.caption("Enter a discussion topic first.")

            with t_direct:
                st.caption("Only the chosen agent takes a turn. It sees the whole thread.")
                agent_options = ["— Select Agent —"] + st.session_state.active_agents
                directed_to = st.selectbox("Agent:", agent_options, key="directed_agent")
                direct_btn = st.button("🎯 Ask for a turn", width="stretch", type="primary",
                    disabled=st.session_state.discussion_locked or not topic or directed_to == "— Select Agent —")
                if direct_btn and directed_to != "— Select Agent —":
                    with st.spinner(f"Getting {directed_to}'s contribution..."):
                        response = call_agent_discussion(directed_to, topic, st.session_state.discussion_thread)
                        score_idx = len(st.session_state.iep_scores.get(directed_to,[]))
                        if response and not response.startswith("❌"):   # V44.3: never score error text
                            record_scores(directed_to, response, st.session_state.discussion_round)
                        else:
                            score_idx = None
                        st.session_state.discussion_thread.append({
                            "agent":directed_to,"content":response,
                            "type":"directed","directed_from":"Conductor",
                            "round":st.session_state.discussion_round,
                            "score_idx":score_idx,
                            "gemini_thinking_fellback": gemini_fellback_for(directed_to),  # V44.2
                            "sidebar_in_context": bool(st.session_state.sidebar_carry.get(directed_to)),  # V44.4
                        })
                    st.rerun()

            with t_int:
                st.caption("Your words go into the thread as Conductor. Every agent sees them from its next turn on.")
                conductor_msg = st.text_area("Your message:", height=120,
                    placeholder="e.g. Let's focus on the most actionable revision. What would change the paper most?",
                    key="conductor_msg")
                intervene_btn = st.button("📣 Send to Group", type="primary", width="stretch",
                    disabled=st.session_state.discussion_locked or not conductor_msg.strip())
                if intervene_btn and conductor_msg.strip():
                    st.session_state.discussion_thread.append({
                        "agent":"Conductor","content":conductor_msg.strip(),
                        "type":"intervention","round":st.session_state.discussion_round
                    })
                    st.rerun()
                st.caption("Tip: send, then use Direct to have one agent answer it.")

            with t_aside:
                st.caption("A private exchange with one agent. The others never see it. "
                           "Every sidebar is archived and exported.")
                pull_aside_agent = st.selectbox("Agent:", ["— Select Agent —"] + st.session_state.active_agents,
                    key="pull_aside_select")
                if st.button("🔒 Open sidebar", width="stretch", type="primary",
                             disabled=pull_aside_agent == "— Select Agent —"):
                    st.session_state.pull_aside_active = True
                    st.session_state.pull_aside_agent  = pull_aside_agent
                    st.session_state.pull_aside_thread = []
                    # V44.4: open an archive record now, so nothing is lost
                    st.session_state.sidebar_archive.append({
                        "sidebar_id": len(st.session_state.sidebar_archive) + 1,
                        "agent": pull_aside_agent,
                        "round": st.session_state.discussion_round,
                        "after_turn": len(st.session_state.discussion_thread),
                        "started_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                        "messages": [], "carried": False})
                    st.rerun()
                _carried_now = {a: len(v) for a, v in st.session_state.get("sidebar_carry", {}).items() if v}
                if _carried_now:
                    st.caption("Agents carrying sidebars: " + ", ".join(f"{a} ({n})" for a, n in _carried_now.items()))

            with t_co:
                st.caption("Claude reads the scores and gives you a private observation. Agents never see it.")
                if st.button("🧠 Ask Co-Conductor", width="stretch", type="primary"):
                    with st.spinner("Claude is reading the scores..."):
                        obs = call_coconductor()
                        st.session_state.coconductor_notes.append(obs)
                    st.rerun()
                if st.session_state.coconductor_notes:
                    latest = st.session_state.coconductor_notes[-1]
                    st.markdown(f'<div class="coconductor-box">🎹 <strong>Latest observation:</strong><br>{latest}</div>', unsafe_allow_html=True)
                else:
                    st.caption("No observations yet. Run at least one round first.")
                if len(st.session_state.coconductor_notes) > 1:
                    with st.expander(f"📝 All observations ({len(st.session_state.coconductor_notes)})"):
                        for i, note in enumerate(st.session_state.coconductor_notes, 1):
                            st.markdown(f"**Observation {i}:** {note}")
                            st.markdown("---")

            with t_res:
                st.caption("Lock stops new turns. Resolve asks one participant (or you) to close the discussion.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("🔒 Lock", width="stretch", disabled=st.session_state.discussion_locked):
                        st.session_state.discussion_locked = True; st.rerun()
                with col2:
                    if st.button("🔓 Unlock", width="stretch", disabled=not st.session_state.discussion_locked):
                        st.session_state.discussion_locked = False; st.rerun()
                resolution_options = ["Conductor"] + st.session_state.active_agents
                resolution_agent   = st.selectbox("Synthesizer:", resolution_options, key="resolution_agent_select")
                if st.button("📋 Resolve Discussion", width="stretch", type="primary"):
                    st.session_state.consensus_status = "Full"
                    st.session_state.resolution_agent = resolution_agent
                    if resolution_agent == "Conductor":
                        st.session_state.discussion_thread.append({
                            "agent":"Conductor","content":"✅ DISCUSSION RESOLVED.",
                            "type":"resolve_marker","round":st.session_state.discussion_round
                        })
                    else:
                        with st.spinner(f"📋 {AGENT_EMOJIS[resolution_agent]} {resolution_agent} writing resolution..."):
                            resolution = call_agent_resolution(resolution_agent, st.session_state.discussion_topic, st.session_state.discussion_thread)
                            st.session_state.resolution_text = resolution
                            st.session_state.discussion_thread.append({
                                "agent":resolution_agent,"content":resolution,
                                "type":"resolution","round":st.session_state.discussion_round,
                                "gemini_thinking_fellback": gemini_fellback_for(resolution_agent),  # V44.2
                            })
                    st.rerun()
                st.markdown("---")
                # V48: Clear asks for confirmation and warns when not exported.
                _confirm = st.checkbox("I want to clear the whole discussion", key=f"confirm_clear_{st.session_state.get('_clear_gen', 0)}")
                if _unsaved and _confirm:
                    st.warning("This discussion has not been exported. Clearing it loses it.")
                if st.button("🗑️ Clear discussion", width="stretch", disabled=not _confirm):
                    st.session_state.discussion_thread  = []
                    st.session_state.discussion_round   = 0
                    st.session_state.consensus_status   = "None"
                    st.session_state.discussion_locked  = False
                    st.session_state.resolution_text    = ""
                    st.session_state.iep_scores         = {}
                    st.session_state.vt_scores          = {}
                    st.session_state.score_history      = []
                    st.session_state.coconductor_notes  = []
                    st.session_state.pop("_live_export", None)
                    st.session_state["_clear_gen"] = st.session_state.get("_clear_gen", 0) + 1
                    st.rerun()

        # Run Round execution (V44.7.1 logic, now shared with the AI Moderator)
        if run_round_btn and topic and st.session_state.active_agents:
            _run_live_round(st.session_state.get('current_round_instruction', ''), "conductor")

# =============================================================================
# MULTI-ROUND
# =============================================================================
elif session_type == "Multi-Round":
    st.markdown("### 🔄 Multi-Round Iterative Mode")
    st.markdown("*Each round: all agents respond, seeing all previous rounds.*")

    current_round = len(st.session_state.multi_round_history) + 1
    st.info(f"**Current Round:** {current_round}")

    prompt = st.text_area(f"Round {current_round} Prompt", height=100,
        placeholder="What should the agents respond to this round?", key=f"mr_prompt_{current_round}")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        run_round_btn = st.button("▶️ Run Round", type="primary", width="stretch")
    with col2:
        if st.button("🗑️ Clear All", width="stretch"):
            st.session_state.multi_round_history = []
            st.session_state.score_history = []
            st.session_state.iep_scores = {}
            st.session_state.vt_scores  = {}
            st.rerun()
    with col3:
        if st.button("📥 Export MD", width="stretch"):
            st.download_button("Download MD", export_to_markdown(),
                file_name=f"multiround_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md", mime="text/markdown")
    with col4:
        view_mode = st.selectbox("View", ["Grid","Present"], label_visibility="collapsed", key="multi_view")
        st.session_state.view_mode = view_mode.lower()

    if run_round_btn and prompt and st.session_state.active_agents:
        round_responses = {}
        round_scores = {}
        with st.status(f"Running Round {current_round}...", expanded=True) as status:
            for agent_name in st.session_state.active_agents:
                stance = st.session_state.agent_stances.get(agent_name,"Neutral")
                status.update(label=f"{AGENT_EMOJIS[agent_name]} {agent_name} ({stance})...")
                response = call_agent_multi_round(agent_name, prompt, st.session_state.multi_round_history, current_round)
                round_responses[agent_name] = response
                if response and not response.startswith("❌"):
                    iep, vt = record_scores(agent_name, response, current_round)
                    round_scores[agent_name] = {'iep': iep, 'vt': vt}
            status.update(label=f"✅ Round {current_round} Complete!", state="complete")
        st.session_state.multi_round_history.append({"prompt":prompt,"responses":round_responses,"scores":round_scores})
        st.rerun()

    for i, rd in enumerate(st.session_state.multi_round_history, 1):
        st.markdown(f'<div class="round-separator">📍 Round {i} — {rd.get("prompt","")[:60]}{"..." if len(rd.get("prompt",""))>60 else ""}</div>', unsafe_allow_html=True)
        with st.container():
            if st.session_state.view_mode == "grid":
                # Display with pre-stored scores — no re-scoring
                cols = st.columns(2)
                agents = list(rd["responses"].keys())
                for j, agent in enumerate(agents):
                    with cols[j % 2]:
                        box_class = f"{agent.lower()}-box"
                        emoji = AGENT_EMOJIS.get(agent,"🤖")
                        _rr = get_agent_role(agent)
                        role_short = _rr[:60] if _rr.strip() else "raw voice — no role framing"
                        st.markdown(f'<div class="agent-box {box_class}"><strong>{emoji} {agent}</strong><div style="font-size:0.75rem;color:#666;">{role_short}</div></div>', unsafe_allow_html=True)
                        st.markdown(rd["responses"][agent])
                        stored = rd.get("scores",{}).get(agent)
                        if stored:
                            render_score_badge(stored['iep'], stored['vt'])
            else:
                render_present_mode(rd["responses"])
        st.markdown("---")

# =============================================================================
# SINGLE ROUND
# =============================================================================
else:
    st.markdown("### 📝 Single Round")
    prompt = st.text_area("Your Prompt", height=120, placeholder="What's the problem, question, or challenge?")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        run_btn = st.button("🚀 Run", type="primary", width="stretch")
    with col2:
        clear_btn = st.button("🗑️ Clear", width="stretch")
    with col3:
        if st.button("📥 Export MD", width="stretch"):
            st.download_button("Download MD", export_to_markdown(),
                file_name=f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md", mime="text/markdown")
    with col4:
        view_mode = st.selectbox("View", ["Grid","Present"], label_visibility="collapsed")
        st.session_state.view_mode = view_mode.lower()

    if run_btn and prompt and st.session_state.active_agents:
        st.session_state.round1_responses = {}
        st.session_state.iep_scores = {}
        st.session_state.vt_scores  = {}
        st.session_state.score_history = []
        with st.status("Running...", expanded=True) as status:
            for agent_name in st.session_state.active_agents:
                stance = st.session_state.agent_stances.get(agent_name,"Neutral")
                status.update(label=f"{AGENT_EMOJIS[agent_name]} {agent_name} ({stance})...")
                system   = build_system_prompt(agent_name)
                depth_cfg = DEPTH_CONFIGS.get(st.session_state.depth, DEPTH_CONFIGS["Medium"])
                user_msg = build_control_header() + "\n\n" + depth_cfg["instruction"] + "\n\n" + prompt
                response = AGENT_FUNCTIONS[agent_name](user_msg, system, max_tokens=depth_cfg["max_tokens"])
                st.session_state.round1_responses[agent_name] = response
                # Score here — once, at run time
                if response and not response.startswith("❌"):
                    record_scores(agent_name, response, 1)
            status.update(label="✅ Complete!", state="complete")
        st.rerun()

    if clear_btn:
        st.session_state.round1_responses = {}
        st.session_state.iep_scores = {}
        st.session_state.vt_scores  = {}
        st.rerun()

    if st.session_state.round1_responses:
        st.markdown("### 📊 Responses")
        if st.session_state.view_mode == "grid":
            render_agent_response_grid(st.session_state.round1_responses, round_num=1, score=True)
        else:
            render_present_mode(st.session_state.round1_responses)

        st.markdown("---")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧬 SYN-IQ Analysis"):
                responses = list(st.session_state.round1_responses.values())
                if len(responses) >= 2:
                    score_v, level, novel = calculate_syniq_quick(responses[:-1], responses[-1])
                    box_class = "high-syniq" if level=="HIGH" else ("medium-syniq" if level=="MEDIUM" else "low-syniq")
                    st.markdown(f'<div class="syniq-score-box {box_class}"><h1>{score_v:.0f}</h1><p>SYN-IQ Score ({level})</p></div>', unsafe_allow_html=True)
                    if novel:
                        st.info(f"🆕 Novel concepts: {', '.join(list(novel)[:15])}")
        with col2:
            if st.session_state.score_history and st.button("🔬 Score Summary"):
                st.markdown("**IEP Summary — this round:**")
                for entry in st.session_state.score_history:
                    iep = entry['iep']
                    dom_color = {'INT':'#4488ff','AFF':'#ff6688','ACT':'#44bb66'}.get(iep['dominant'],'#888')
                    st.markdown(f"**{AGENT_EMOJIS.get(entry['agent'],'🤖')} {entry['agent']}:** "
                                f"<span style='color:{dom_color};font-weight:700;'>{iep['dominant']}</span> "
                                f"INT:{iep['int']:.0f}% AFF:{iep['aff']:.0f}% ACT:{iep['act']:.0f}% | "
                                f"{iep['stance']} · {iep['tone']}", unsafe_allow_html=True)

# =============================================================================
# SESSION NOTES + ADDITIONAL DOCUMENT UPLOAD
# =============================================================================
st.markdown("---")
st.markdown("### 🎹 Session Notes & Documents")

notes_col, doc_col = st.columns([3, 2])

with notes_col:
    st.caption("Your private conductor notes — not sent to agents.")
    st.session_state.session_notes = st.text_area(
        "Notes", value=st.session_state.session_notes, height=140,
        placeholder="Key observations, decisions, follow-up actions...",
        label_visibility="collapsed"
    )

with doc_col:
    st.caption("Load a document into session context — agents will read it.")
    bottom_upload = st.file_uploader(
        "Upload document",
        type=["docx","md","txt","csv","py","pdf"],
        key=f"bottom_doc_uploader_{st.session_state.get('_doc_uploader_gen', 0)}",
        label_visibility="collapsed"
    )
    if bottom_upload and bottom_upload.name != st.session_state.get("session_document_name"):
        doc_text = parse_uploaded_document(bottom_upload)
        st.session_state.session_document      = doc_text
        st.session_state.session_document_name = bottom_upload.name
        st.success(f"✅ {bottom_upload.name} loaded ({len(doc_text):,} chars)")
        st.rerun()
    if st.session_state.session_document:
        st.markdown(f'<div class="doc-context-box">📄 <strong>{st.session_state.session_document_name}</strong><br><span style="color:#666;">{len(st.session_state.session_document):,} chars: agents can read this</span></div>', unsafe_allow_html=True)
        with st.expander("👁️ Preview document content"):
            st.text(st.session_state.session_document[:1000] + ("..." if len(st.session_state.session_document) > 1000 else ""))
        if st.button("🗑️ Remove document", key="remove_doc_bottom"):
            st.session_state.session_document = None
            st.session_state.session_document_name = ""
            st.session_state["_doc_uploader_gen"] = st.session_state.get("_doc_uploader_gen", 0) + 1
            st.rerun()

st.markdown("---")
st.markdown("""
<div style="text-align:center; color:#666; padding:1rem;">
    <strong>Focus Group Lab V48</strong>, Research Edition (open)<br>
    Multi-Agent AI Advisory Platform · Live IEP + Vₜ Scoring · Co-Conductor<br>
    SYNINT Team — April 2026 · Kouns, W.C.
</div>
""", unsafe_allow_html=True)
