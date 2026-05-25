"""
SYNIQ Mapper Analyzer V20
=========================

Streamlit-ready Mapper visualization helper/app for SYN-IQ experiments.

Core principle (carried over from V19)
--------------------------------------
V19 introduced the canonical-layout architecture: a Mapper visualization is
the composition (G, L, E) where L : G -> R^2 is a single canonical embedding
computed once and reused for every visual encoding E. Toggling encodings
(pie, overlap, agent, continuous) cannot change reported geometry. This
invariance is enforced structurally: render_plotly_agent_view receives
`positions` as a parameter rather than computing them, and the layout
function caches by stable_graph_hash(graph) so the same graph maps to the
same coordinates across runs.

V20 changes
-----------
1. Agent color palette restored to the SYN-IQ project standard
   (Claude=blue, ChatGPT=green, Gemini=purple, Grok=red). V19 had
   reassigned colors which would have broken consistency with the
   Words Matter and earlier V18 figures.
2. Pie nodes are now rendered as SVG wedges in DATA coordinates using
   Plotly Scatter fill='toself' polygons. V19 placed pies in paper-domain
   coordinates, which meant pies did not track the underlying graph
   when the user zoomed or panned. Data-coordinate wedges keep pies
   locked to their nodes during interaction.
3. The continuous-mode colorbar palette is configurable; default is
   Viridis (matches prior IEP figures in the project).
4. Streamlit title, captions, and download filenames updated to V20.
5. Added explicit note in the methods-language expander identifying the
   layout source (cache, kepler_html, networkx_fallback) so manuscript
   text can reflect which embedding actually produced a given figure.

Primary layout path
-------------------
    1. Use a cached canonical layout if available.
    2. Try to extract node positions from a KeplerMapper HTML file/config.
    3. Fall back to deterministic NetworkX layout if no canonical
       coordinates exist. The fallback is per-component Kamada-Kawai
       seeded by lens centroids, with components placed on a circle.
       This is not claimed to match D3; it is a stable canonical layout
       so that visual encodings do not change geometry.

This file is intentionally self-contained so it can be dropped into a
Streamlit app or run directly with:

    streamlit run SYNIQ_Mapper_Analyzer_V20.py

Expected data
-------------
A CSV with at least:
    - numeric lens / feature columns OR precomputed projection columns
    - optional agent column, default name: agent
    - optional question column, default name: question
    - optional int_pct / aff_pct / act_pct columns

If you already have a KeplerMapper graph object from an existing pipeline,
call render_plotly_agent_view(...) directly with a precomputed `positions`
mapping.
"""

from __future__ import annotations

import ast
import hashlib
import html
import json
import math
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

try:
    import networkx as nx
except Exception as exc:  # pragma: no cover
    nx = None
    _NX_IMPORT_ERROR = exc
else:
    _NX_IMPORT_ERROR = None

try:
    import plotly.graph_objects as go
except Exception as exc:  # pragma: no cover
    go = None
    _PLOTLY_IMPORT_ERROR = exc
else:
    _PLOTLY_IMPORT_ERROR = None

try:
    import streamlit as st
except Exception:  # pragma: no cover
    st = None

try:
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
except Exception:  # pragma: no cover
    PCA = None
    StandardScaler = None

try:
    import kmapper as km
except Exception:  # pragma: no cover
    km = None


# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

DEFAULT_AGENT_COL = "agent"
DEFAULT_QUESTION_COL = "question"
DEFAULT_NODE_SIZE = 22
DEFAULT_CACHE_DIR = ".syniq_layout_cache"

AGENT_ALIASES = {
    "chatgpt": "ChatGPT",
    "gpt": "ChatGPT",
    "openai": "ChatGPT",
    "claude": "Claude",
    "anthropic": "Claude",
    "grok": "Grok",
    "gemini": "Gemini",
    "google": "Gemini",
}

AGENT_COLORS = {
    # V20 — palette aligned with prior SYN-IQ figures (Words Matter, V18 mapper)
    # Do not change without updating every previously-published figure.
    "Claude":  "#377EB8",  # blue
    "ChatGPT": "#4DAF4A",  # green
    "Gemini":  "#984EA3",  # purple
    "Grok":    "#E41A1C",  # red
    "Other":   "#B0B0B0",  # neutral grey for unrecognized agents
    "Overlap": "#FF7F00",  # orange — reserved for mixed-agent (non-pure) nodes
}

CONTINUOUS_COLOR_COLS = ["int_pct", "aff_pct", "act_pct", "polarity", "uncertainty"]


@dataclass
class CanonicalLayoutResult:
    """Canonical coordinates plus provenance metadata."""

    positions: Dict[str, Tuple[float, float]]
    source: str
    cache_key: Optional[str] = None
    notes: str = ""


# -----------------------------------------------------------------------------
# General utilities
# -----------------------------------------------------------------------------


def normalize_agent_name(value: Any) -> str:
    """Normalize common agent labels to stable display names."""
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "Other"
    raw = str(value).strip()
    key = raw.lower()
    return AGENT_ALIASES.get(key, raw if raw else "Other")


def ensure_plotly_available() -> None:
    if go is None:
        raise ImportError(f"Plotly is required for rendering. Original error: {_PLOTLY_IMPORT_ERROR}")


def ensure_networkx_available() -> None:
    if nx is None:
        raise ImportError(f"NetworkX is required for graph layout fallback. Original error: {_NX_IMPORT_ERROR}")


def graph_to_networkx(graph: Mapping[str, Any]) -> "nx.Graph":
    """
    Convert a KeplerMapper-style graph dict into a NetworkX graph.

    KeplerMapper graph shape usually contains:
        graph["nodes"]: dict[node_id] -> list[row_indices]
        graph["links"]: dict[node_id] -> list[node_id]
    """
    ensure_networkx_available()
    G = nx.Graph()
    nodes = graph.get("nodes", {})
    links = graph.get("links", {})

    for node_id in nodes.keys():
        G.add_node(str(node_id))

    for src, targets in links.items():
        src_s = str(src)
        if isinstance(targets, Mapping):
            iterable_targets = targets.keys()
        else:
            iterable_targets = targets
        for tgt in iterable_targets:
            G.add_edge(src_s, str(tgt))

    return G


def stable_graph_hash(graph: Mapping[str, Any]) -> str:
    """Create a stable hash from graph node membership and edges."""
    nodes = graph.get("nodes", {})
    links = graph.get("links", {})
    canonical_nodes = {str(k): sorted(map(int, v)) for k, v in nodes.items()}
    edges = []
    for src, tgts in links.items():
        for tgt in (tgts.keys() if isinstance(tgts, Mapping) else tgts):
            a, b = sorted([str(src), str(tgt)])
            edges.append((a, b))
    payload = json.dumps(
        {"nodes": canonical_nodes, "edges": sorted(set(edges))},
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def load_layout_cache(cache_dir: str | Path, cache_key: str) -> Optional[Dict[str, Tuple[float, float]]]:
    path = Path(cache_dir) / f"layout_{cache_key}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return {str(k): (float(v[0]), float(v[1])) for k, v in data.items()}
    except Exception:
        return None


def save_layout_cache(cache_dir: str | Path, cache_key: str, positions: Mapping[str, Tuple[float, float]]) -> Path:
    path = Path(cache_dir)
    path.mkdir(parents=True, exist_ok=True)
    out = path / f"layout_{cache_key}.json"
    serializable = {str(k): [float(v[0]), float(v[1])] for k, v in positions.items()}
    out.write_text(json.dumps(serializable, indent=2, sort_keys=True), encoding="utf-8")
    return out


# -----------------------------------------------------------------------------
# Kepler HTML/config coordinate extraction
# -----------------------------------------------------------------------------


def _coerce_position_dict(obj: Any) -> Optional[Dict[str, Tuple[float, float]]]:
    """
    Try to coerce many possible Kepler/D3 config structures into node positions.

    Accepts shapes such as:
        {"nodes": [{"id": "cube0_cluster0", "x": 1, "y": 2}, ...]}
        {"nodes": {"cube0_cluster0": {"x": 1, "y": 2}}}
        {"graph": {"nodes": ...}}
        {"node_positions": {"cube0_cluster0": [1, 2]}}
    """
    if obj is None:
        return None

    # Direct node_positions-like dict
    for key in ("node_positions", "positions", "layout", "pos"):
        if isinstance(obj, Mapping) and key in obj:
            maybe = obj[key]
            out: Dict[str, Tuple[float, float]] = {}
            if isinstance(maybe, Mapping):
                for nid, val in maybe.items():
                    if isinstance(val, Mapping) and "x" in val and "y" in val:
                        out[str(nid)] = (float(val["x"]), float(val["y"]))
                    elif isinstance(val, (list, tuple)) and len(val) >= 2:
                        out[str(nid)] = (float(val[0]), float(val[1]))
            if out:
                return out

    # Nested graph/config containers
    if isinstance(obj, Mapping):
        for key in ("graph", "data", "mapper", "config"):
            if key in obj:
                got = _coerce_position_dict(obj[key])
                if got:
                    return got

    # nodes as list of objects
    if isinstance(obj, Mapping) and "nodes" in obj:
        nodes = obj["nodes"]
        out: Dict[str, Tuple[float, float]] = {}
        if isinstance(nodes, list):
            for i, node in enumerate(nodes):
                if not isinstance(node, Mapping):
                    continue
                if "x" in node and "y" in node:
                    nid = node.get("id", node.get("name", node.get("node_id", i)))
                    out[str(nid)] = (float(node["x"]), float(node["y"]))
        elif isinstance(nodes, Mapping):
            for nid, node in nodes.items():
                if isinstance(node, Mapping) and "x" in node and "y" in node:
                    out[str(nid)] = (float(node["x"]), float(node["y"]))
                elif isinstance(node, Mapping):
                    for key in ("position", "pos", "layout"):
                        val = node.get(key)
                        if isinstance(val, Mapping) and "x" in val and "y" in val:
                            out[str(nid)] = (float(val["x"]), float(val["y"]))
                        elif isinstance(val, (list, tuple)) and len(val) >= 2:
                            out[str(nid)] = (float(val[0]), float(val[1]))
        if out:
            return out

    return None


def _extract_json_objects_from_text(text: str) -> Iterable[Any]:
    """
    Heuristically extract JSON-like objects from an HTML/JS file.

    This is deliberately permissive because KeplerMapper templates can change.
    We first look for script tag assignments, then fall back to balanced braces.
    """
    decoded = html.unescape(text)

    assignment_patterns = [
        r"(?:var|let|const)\s+[A-Za-z0-9_$]*\s*=\s*(\{.*?\});",
        r"window\.[A-Za-z0-9_$]+\s*=\s*(\{.*?\});",
        r"data-json=[\"'](\{.*?\})[\"']",
    ]
    for pattern in assignment_patterns:
        for match in re.finditer(pattern, decoded, flags=re.DOTALL):
            candidate = match.group(1)
            for parser in (json.loads, ast.literal_eval):
                try:
                    yield parser(candidate)
                    break
                except Exception:
                    continue

    # Fallback: scan for balanced top-level brace blocks containing x/y/nodes.
    starts = [m.start() for m in re.finditer(r"\{", decoded)]
    for start in starts:
        snippet = decoded[start : start + 250_000]
        if "nodes" not in snippet[:25_000] and "node_positions" not in snippet[:25_000]:
            continue
        depth = 0
        in_string = False
        escape = False
        end = None
        quote_char = ""
        for idx, ch in enumerate(snippet):
            if in_string:
                if escape:
                    escape = False
                elif ch == "\\":
                    escape = True
                elif ch == quote_char:
                    in_string = False
                continue
            if ch in ('"', "'"):
                in_string = True
                quote_char = ch
                continue
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    end = idx + 1
                    break
        if end is None:
            continue
        block = snippet[:end]
        if "x" not in block or "y" not in block:
            continue
        for parser in (json.loads, ast.literal_eval):
            try:
                yield parser(block)
                break
            except Exception:
                continue


def extract_kepler_positions_from_html(html_path: str | Path) -> Dict[str, Tuple[float, float]]:
    """
    Extract node positions from a KeplerMapper HTML/config file if they are serialized.

    Returns an empty dict if no coordinates are found.
    """
    path = Path(html_path)
    if not path.exists():
        raise FileNotFoundError(f"Kepler HTML/config file not found: {path}")

    text = path.read_text(encoding="utf-8", errors="ignore")

    for obj in _extract_json_objects_from_text(text):
        positions = _coerce_position_dict(obj)
        if positions:
            return positions

    return {}


def align_position_node_ids(
    positions: Mapping[str, Tuple[float, float]],
    graph: Mapping[str, Any],
) -> Dict[str, Tuple[float, float]]:
    """
    Align extracted node IDs with graph node IDs.

    KeplerMapper node IDs are often strings already. If extraction yields numeric IDs and graph
    IDs are ordered strings, this function maps by sorted order as a last resort.
    """
    graph_ids = [str(k) for k in graph.get("nodes", {}).keys()]
    if not graph_ids:
        return {str(k): (float(v[0]), float(v[1])) for k, v in positions.items()}

    out = {str(k): (float(v[0]), float(v[1])) for k, v in positions.items() if str(k) in set(graph_ids)}
    if len(out) == len(graph_ids):
        return out

    # Last-resort numeric/list index alignment.
    pos_items = list(positions.items())
    if len(pos_items) == len(graph_ids):
        def sort_key(item: Tuple[str, Tuple[float, float]]) -> Tuple[int, str]:
            k = str(item[0])
            m = re.search(r"\d+", k)
            return (int(m.group(0)) if m else 10**9, k)

        sorted_pos = [v for _, v in sorted(pos_items, key=sort_key)]
        sorted_graph_ids = sorted(graph_ids)
        return {nid: (float(x), float(y)) for nid, (x, y) in zip(sorted_graph_ids, sorted_pos)}

    return out


# -----------------------------------------------------------------------------
# Canonical layout creation
# -----------------------------------------------------------------------------


def deterministic_fallback_layout(
    graph: Mapping[str, Any],
    projected: Optional[np.ndarray] = None,
    seed: int = 42,
) -> Dict[str, Tuple[float, float]]:
    """
    Deterministic fallback layout when no Kepler/D3 coordinates can be extracted.

    This is not claimed to match D3. It is only a stable canonical layout so visual encodings
    do not change geometry.
    """
    ensure_networkx_available()
    G = graph_to_networkx(graph)
    if G.number_of_nodes() == 0:
        return {}

    components = [list(c) for c in nx.connected_components(G)]
    components.sort(key=len, reverse=True)

    nodes_dict = graph.get("nodes", {})
    lens_centroid: Dict[str, np.ndarray] = {}
    if projected is not None:
        for node_id, indices in nodes_dict.items():
            try:
                idx = np.asarray(indices, dtype=int)
                pts = projected[idx]
                if pts.ndim == 2 and pts.shape[1] >= 2 and len(pts) > 0:
                    lens_centroid[str(node_id)] = np.array([float(np.mean(pts[:, 0])), float(np.mean(pts[:, 1]))])
            except Exception:
                pass

    local_layouts: List[Tuple[List[str], Dict[str, np.ndarray]]] = []
    for comp in components:
        sub = G.subgraph(comp).copy()
        if sub.number_of_nodes() == 1:
            local = {comp[0]: np.array([0.0, 0.0])}
        else:
            seed_pos = {nid: tuple(lens_centroid[nid]) for nid in comp if nid in lens_centroid}
            try:
                if seed_pos and len(seed_pos) == sub.number_of_nodes():
                    local_raw = nx.kamada_kawai_layout(sub, pos=seed_pos)
                else:
                    local_raw = nx.spring_layout(sub, seed=seed, k=1 / math.sqrt(max(sub.number_of_nodes(), 1)))
            except Exception:
                local_raw = nx.spring_layout(sub, seed=seed)
            local = {str(k): np.asarray(v, dtype=float) for k, v in local_raw.items()}
        local_layouts.append((comp, local))

    # Place components around a circle, not a grid, to avoid implying row/column semantics.
    out: Dict[str, Tuple[float, float]] = {}
    ncomp = len(local_layouts)
    radius = 3.5 if ncomp > 1 else 0.0
    for i, (comp, local) in enumerate(local_layouts):
        coords = np.array([local[nid] for nid in comp], dtype=float)
        center = coords.mean(axis=0) if len(coords) else np.array([0.0, 0.0])
        angle = 2 * math.pi * i / max(ncomp, 1)
        offset = np.array([radius * math.cos(angle), radius * math.sin(angle)])
        if i == 0 and ncomp > 1:
            offset = np.array([0.0, 0.0])
        scale = max(math.sqrt(len(comp)), 1.0)
        for nid in comp:
            xy = (local[nid] - center) * scale + offset
            out[str(nid)] = (float(xy[0]), float(xy[1]))

    return normalize_positions(out)


def normalize_positions(positions: Mapping[str, Tuple[float, float]]) -> Dict[str, Tuple[float, float]]:
    """Normalize coordinates to centered, comparable scale for Plotly."""
    if not positions:
        return {}
    ids = list(positions.keys())
    arr = np.array([[positions[k][0], positions[k][1]] for k in ids], dtype=float)
    arr[:, 0] = arr[:, 0] - np.nanmean(arr[:, 0])
    arr[:, 1] = arr[:, 1] - np.nanmean(arr[:, 1])
    span = np.nanmax(np.ptp(arr, axis=0))
    if span and np.isfinite(span):
        arr = arr / span * 10.0
    return {str(k): (float(arr[i, 0]), float(arr[i, 1])) for i, k in enumerate(ids)}


def get_canonical_layout(
    graph: Mapping[str, Any],
    projected: Optional[np.ndarray] = None,
    kepler_html_path: Optional[str | Path] = None,
    cache_dir: str | Path = DEFAULT_CACHE_DIR,
    prefer_cache: bool = True,
    save_cache: bool = True,
    seed: int = 42,
) -> CanonicalLayoutResult:
    """
    Return immutable canonical layout coordinates for a Mapper graph.

    Order:
        cached layout -> Kepler HTML/config extraction -> deterministic fallback.
    """
    cache_key = stable_graph_hash(graph)

    if prefer_cache:
        cached = load_layout_cache(cache_dir, cache_key)
        if cached:
            return CanonicalLayoutResult(
                positions=normalize_positions(cached),
                source="cache",
                cache_key=cache_key,
                notes=f"Loaded canonical coordinates from {cache_dir}.",
            )

    if kepler_html_path:
        try:
            raw = extract_kepler_positions_from_html(kepler_html_path)
            aligned = align_position_node_ids(raw, graph)
            if aligned and len(aligned) >= max(1, int(0.75 * len(graph.get("nodes", {})))):
                normalized = normalize_positions(aligned)
                if save_cache:
                    save_layout_cache(cache_dir, cache_key, normalized)
                return CanonicalLayoutResult(
                    positions=normalized,
                    source="kepler_html",
                    cache_key=cache_key,
                    notes=f"Extracted {len(normalized)} node positions from Kepler HTML/config.",
                )
        except Exception as exc:
            # Continue to fallback while preserving diagnostic note.
            fallback_note = f"Kepler HTML extraction failed: {exc}"
        else:
            fallback_note = "Kepler HTML/config did not contain readable node coordinates."
    else:
        fallback_note = "No Kepler HTML/config path supplied."

    fallback = deterministic_fallback_layout(graph, projected=projected, seed=seed)
    if save_cache:
        save_layout_cache(cache_dir, cache_key, fallback)
    return CanonicalLayoutResult(
        positions=fallback,
        source="networkx_fallback",
        cache_key=cache_key,
        notes=fallback_note + " Used deterministic fallback layout.",
    )


# -----------------------------------------------------------------------------
# Rendering
# -----------------------------------------------------------------------------


def node_agent_counts(
    graph: Mapping[str, Any],
    df: pd.DataFrame,
    agent_col: str = DEFAULT_AGENT_COL,
) -> Dict[str, Dict[str, int]]:
    nodes = graph.get("nodes", {})
    counts: Dict[str, Dict[str, int]] = {}
    for node_id, indices in nodes.items():
        sub = df.iloc[list(map(int, indices))] if len(indices) else pd.DataFrame()
        c: Dict[str, int] = {}
        if agent_col in sub.columns:
            for val in sub[agent_col].map(normalize_agent_name):
                c[val] = c.get(val, 0) + 1
        else:
            c["Other"] = len(sub)
        counts[str(node_id)] = c
    return counts


def node_stat_values(
    graph: Mapping[str, Any],
    df: pd.DataFrame,
    column: str,
) -> Dict[str, float]:
    values: Dict[str, float] = {}
    nodes = graph.get("nodes", {})
    if column not in df.columns:
        return values
    for node_id, indices in nodes.items():
        vals = pd.to_numeric(df.iloc[list(map(int, indices))][column], errors="coerce")
        values[str(node_id)] = float(vals.mean()) if vals.notna().any() else float("nan")
    return values


def build_hover_text(
    node_id: str,
    graph: Mapping[str, Any],
    df: pd.DataFrame,
    agent_col: str = DEFAULT_AGENT_COL,
    question_col: str = DEFAULT_QUESTION_COL,
) -> str:
    indices = list(map(int, graph.get("nodes", {}).get(node_id, graph.get("nodes", {}).get(str(node_id), []))))
    n = len(indices)
    lines = [f"<b>{node_id}</b>", f"Rows: {n}"]
    if n and agent_col in df.columns:
        agents = df.iloc[indices][agent_col].map(normalize_agent_name).value_counts()
        lines.append("Agents: " + ", ".join([f"{k}={v}" for k, v in agents.items()]))
    if n and question_col in df.columns:
        qs = df.iloc[indices][question_col].astype(str).value_counts().head(3)
        lines.append("Questions: " + ", ".join([f"{k}={v}" for k, v in qs.items()]))
    for col in CONTINUOUS_COLOR_COLS:
        if n and col in df.columns:
            vals = pd.to_numeric(df.iloc[indices][col], errors="coerce")
            if vals.notna().any():
                lines.append(f"{col}: {vals.mean():.3f}")
    return "<br>".join(lines)


def add_edges_to_figure(fig: "go.Figure", graph: Mapping[str, Any], positions: Mapping[str, Tuple[float, float]]) -> None:
    x_edges: List[Optional[float]] = []
    y_edges: List[Optional[float]] = []
    links = graph.get("links", {})
    seen = set()
    for src, tgts in links.items():
        src_s = str(src)
        for tgt in (tgts.keys() if isinstance(tgts, Mapping) else tgts):
            tgt_s = str(tgt)
            edge = tuple(sorted([src_s, tgt_s]))
            if edge in seen or src_s not in positions or tgt_s not in positions:
                continue
            seen.add(edge)
            x0, y0 = positions[src_s]
            x1, y1 = positions[tgt_s]
            x_edges.extend([x0, x1, None])
            y_edges.extend([y0, y1, None])
    fig.add_trace(
        go.Scatter(
            x=x_edges,
            y=y_edges,
            mode="lines",
            line=dict(width=1, color="rgba(80,80,80,0.35)"),
            hoverinfo="skip",
            showlegend=False,
            name="edges",
        )
    )


def _wedge_polygon(
    cx: float, cy: float, radius: float,
    start_angle: float, end_angle: float,
    n_segments: int = 24,
) -> Tuple[List[float], List[float]]:
    """
    Build the (x, y) vertex lists of a single pie wedge as a closed polygon.

    Returns coordinate lists suitable for go.Scatter(fill='toself').
    Includes the center vertex so the wedge is a true pie slice, not an arc.
    """
    if end_angle <= start_angle:
        return [], []
    # Sample arc points
    angles = np.linspace(start_angle, end_angle, n_segments + 1)
    arc_x = [cx + radius * math.cos(a) for a in angles]
    arc_y = [cy + radius * math.sin(a) for a in angles]
    # Close the polygon back to the center
    xs = [cx] + arc_x + [cx]
    ys = [cy] + arc_y + [cy]
    return xs, ys


def add_pie_node(
    fig: "go.Figure",
    cx: float, cy: float,
    counts: Mapping[str, int],
    hover: str,
    radius: float,
) -> None:
    """
    Render a pie chart at data coordinate (cx, cy) using wedge polygons.

    V20 change: pies are drawn in DATA coordinates (not paper coordinates) so
    they track the underlying graph during zoom/pan. Each wedge is a closed
    polygon rendered via go.Scatter(fill='toself').

    Parameters
    ----------
    cx, cy   : center of the pie in data coordinates
    counts   : {agent_name: count}; wedge sweep is proportional to count
    hover    : tooltip text shown on hover
    radius   : pie radius in data units (caller controls visual size)
    """
    # Strip zero-count entries; ensure at least one wedge so empty nodes
    # still render as a neutral disk.
    nonzero = {k: int(v) for k, v in counts.items() if v and v > 0}
    if not nonzero:
        nonzero = {"Other": 1}

    total = sum(nonzero.values())
    # Stable wedge order: by AGENT_COLORS canonical order, then alphabetical
    # for any agents not in the canonical palette. This keeps the same
    # agent's wedge in the same angular position across all nodes — a
    # readability property the user will notice when scanning the figure.
    canonical_order = [k for k in AGENT_COLORS.keys() if k in nonzero]
    extras = sorted(k for k in nonzero.keys() if k not in canonical_order)
    ordered = canonical_order + extras

    # Start at 12 o'clock (pi/2), sweep clockwise — matches Plotly Pie default
    # so users moving from the legacy pie view see the same wedge orientation.
    start_angle = math.pi / 2
    for agent in ordered:
        frac = nonzero[agent] / total
        sweep = 2 * math.pi * frac
        end_angle = start_angle - sweep  # clockwise = decreasing angle
        # _wedge_polygon expects start < end, so pass in normalized order
        xs, ys = _wedge_polygon(
            cx, cy, radius,
            start_angle=end_angle, end_angle=start_angle,
        )
        if not xs:
            start_angle = end_angle
            continue
        color = AGENT_COLORS.get(agent, AGENT_COLORS["Other"])
        fig.add_trace(go.Scatter(
            x=xs, y=ys,
            mode="lines",
            fill="toself",
            fillcolor=color,
            line=dict(color="white", width=0.6),
            hoverinfo="text",
            hovertext=hover,
            showlegend=False,
            name=f"{agent}",
        ))
        start_angle = end_angle


def render_plotly_agent_view(
    graph: Mapping[str, Any],
    df: pd.DataFrame,
    positions: Mapping[str, Tuple[float, float]],
    mode: str = "pie",
    agent_col: str = DEFAULT_AGENT_COL,
    question_col: str = DEFAULT_QUESTION_COL,
    continuous_col: str = "int_pct",
    title: str = "SYN-IQ Mapper V19",
    node_size: int = DEFAULT_NODE_SIZE,
) -> "go.Figure":
    """
    Render Mapper graph with immutable coordinates.

    Modes:
        - pie: node pie charts showing agent composition
        - overlap: orange if multiple agents in node, otherwise agent color
        - agent: dominant agent color
        - continuous: color by node mean of continuous_col
    """
    ensure_plotly_available()
    pos = {str(k): (float(v[0]), float(v[1])) for k, v in positions.items()}
    nodes = [str(k) for k in graph.get("nodes", {}).keys() if str(k) in pos]

    fig = go.Figure()
    add_edges_to_figure(fig, graph, pos)

    xs = np.array([pos[n][0] for n in nodes], dtype=float) if nodes else np.array([0.0])
    ys = np.array([pos[n][1] for n in nodes], dtype=float) if nodes else np.array([0.0])
    xpad = max((xs.max() - xs.min()) * 0.12, 0.5)
    ypad = max((ys.max() - ys.min()) * 0.12, 0.5)

    counts = node_agent_counts(graph, df, agent_col=agent_col)
    hover = [build_hover_text(n, graph, df, agent_col, question_col) for n in nodes]

    if mode == "pie":
        # V20 — data-coordinate pies. Compute a radius in DATA units that
        # scales with the figure extent, so pies are visually similar across
        # different datasets regardless of how spread out the canonical
        # layout happens to be. `node_size` is interpreted as a percentage
        # of the smaller axis range; clamped to a sensible band.
        x_range = float(xs.max() - xs.min()) if len(xs) > 1 else 1.0
        y_range = float(ys.max() - ys.min()) if len(ys) > 1 else 1.0
        extent = max(min(x_range, y_range), 1.0)
        # node_size slider (10-60) -> radius fraction (0.01-0.04) of extent
        radius_frac = min(max(node_size / 1500.0, 0.010), 0.040)
        pie_radius = extent * radius_frac

        # Invisible anchor markers so hover near the empty disk center
        # still triggers tooltips and so plotly auto-scales the axes.
        fig.add_trace(
            go.Scatter(
                x=[pos[n][0] for n in nodes],
                y=[pos[n][1] for n in nodes],
                mode="markers",
                marker=dict(size=1, color="rgba(0,0,0,0)"),
                hovertext=hover,
                hoverinfo="text",
                showlegend=False,
                name="node anchors",
            )
        )
        for n in nodes:
            cx, cy = pos[n]
            add_pie_node(
                fig, cx, cy,
                counts.get(n, {"Other": 1}),
                build_hover_text(n, graph, df, agent_col, question_col),
                pie_radius,
            )

        # Legend proxy traces so the figure has a colored legend even though
        # pies themselves don't show in the legend (each wedge is its own
        # trace and we suppress them with showlegend=False).
        present_agents = sorted(
            {a for n in nodes for a in counts.get(n, {}).keys() if counts.get(n, {}).get(a, 0) > 0},
            key=lambda a: list(AGENT_COLORS.keys()).index(a) if a in AGENT_COLORS else 999,
        )
        for agent in present_agents:
            fig.add_trace(go.Scatter(
                x=[None], y=[None], mode="markers",
                marker=dict(size=14, color=AGENT_COLORS.get(agent, AGENT_COLORS["Other"]),
                            line=dict(color="white", width=1)),
                name=agent, showlegend=True,
            ))

    elif mode in {"overlap", "agent"}:
        colors = []
        labels = []
        for n in nodes:
            c = counts.get(n, {"Other": 1})
            nonzero = {k: v for k, v in c.items() if v > 0}
            if mode == "overlap" and len(nonzero) > 1:
                label = "Overlap"
            else:
                label = max(nonzero.items(), key=lambda kv: kv[1])[0] if nonzero else "Other"
            labels.append(label)
            colors.append(AGENT_COLORS.get(label, AGENT_COLORS["Other"]))
        fig.add_trace(
            go.Scatter(
                x=[pos[n][0] for n in nodes],
                y=[pos[n][1] for n in nodes],
                mode="markers+text",
                text=[str(i + 1) for i, _ in enumerate(nodes)],
                textposition="middle center",
                marker=dict(size=node_size, color=colors, line=dict(width=1, color="white")),
                hovertext=hover,
                hoverinfo="text",
                showlegend=False,
                name="nodes",
            )
        )

    elif mode == "continuous":
        vals_dict = node_stat_values(graph, df, continuous_col)
        vals = [vals_dict.get(n, np.nan) for n in nodes]
        fig.add_trace(
            go.Scatter(
                x=[pos[n][0] for n in nodes],
                y=[pos[n][1] for n in nodes],
                mode="markers+text",
                text=[str(i + 1) for i, _ in enumerate(nodes)],
                textposition="middle center",
                marker=dict(
                    size=node_size,
                    color=vals,
                    colorscale="Viridis",
                    showscale=True,
                    colorbar=dict(title=continuous_col),
                    line=dict(width=1, color="white"),
                ),
                hovertext=hover,
                hoverinfo="text",
                showlegend=False,
                name="nodes",
            )
        )
    else:
        raise ValueError(f"Unknown mode: {mode}")

    fig.update_layout(
        title=title,
        template="plotly_white",
        width=None,
        height=760,
        margin=dict(l=20, r=20, t=60, b=20),
        xaxis=dict(visible=False, range=[xs.min() - xpad, xs.max() + xpad], scaleanchor="y", scaleratio=1),
        yaxis=dict(visible=False, range=[ys.min() - ypad, ys.max() + ypad]),
        hovermode="closest",
    )
    return fig


# -----------------------------------------------------------------------------
# Minimal Mapper construction for standalone Streamlit use
# -----------------------------------------------------------------------------


def choose_numeric_columns(df: pd.DataFrame, exclude: Sequence[str] = ()) -> List[str]:
    exclude_set = set(exclude)
    cols = []
    for col in df.columns:
        if col in exclude_set:
            continue
        if pd.api.types.is_numeric_dtype(df[col]):
            cols.append(col)
    return cols


def run_mapper_analysis_from_dataframe(
    df: pd.DataFrame,
    feature_cols: Sequence[str],
    n_cubes: int = 8,
    perc_overlap: float = 0.35,
    projection: str = "PCA2D",
) -> Tuple[Any, Mapping[str, Any], np.ndarray]:
    """
    Build a simple KeplerMapper graph from a dataframe.

    This is a convenience path for standalone use. Existing SYN-IQ code can keep its own
    run_mapper_analysis and use V19 rendering/layout functions directly.
    """
    if km is None:
        raise ImportError("kmapper is not installed. Install with: pip install kmapper scikit-learn")
    if PCA is None or StandardScaler is None:
        raise ImportError("scikit-learn is required. Install with: pip install scikit-learn")

    X = df[list(feature_cols)].apply(pd.to_numeric, errors="coerce").fillna(0.0).values
    Xs = StandardScaler().fit_transform(X)

    if projection == "PCA2D":
        projected = PCA(n_components=2, random_state=42).fit_transform(Xs)
    elif projection == "first_two_features":
        if Xs.shape[1] < 2:
            projected = np.c_[Xs[:, 0], np.zeros(Xs.shape[0])]
        else:
            projected = Xs[:, :2]
    else:
        raise ValueError(f"Unknown projection: {projection}")

    mapper = km.KeplerMapper(verbose=0)
    cover = km.Cover(n_cubes=n_cubes, perc_overlap=perc_overlap)

    # DBSCAN is a common safe default for Mapper nodes.
    from sklearn.cluster import DBSCAN

    graph = mapper.map(projected, Xs, cover=cover, clusterer=DBSCAN(eps=0.8, min_samples=2))
    return mapper, graph, projected


def write_kepler_html(mapper: Any, graph: Mapping[str, Any], output_path: str | Path) -> Path:
    """Write a KeplerMapper HTML file if kmapper is available."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    mapper.visualize(graph, path_html=str(output_path), title="SYN-IQ Mapper Canonical Layout")
    return output_path


# -----------------------------------------------------------------------------
# Streamlit app
# -----------------------------------------------------------------------------


def streamlit_app() -> None:  # pragma: no cover
    if st is None:
        raise RuntimeError("Streamlit is not installed. Run with: streamlit run SYNIQ_Mapper_Analyzer_V20.py")

    st.set_page_config(page_title="SYN-IQ Mapper Analyzer V20", layout="wide")
    st.title("SYN-IQ Mapper Analyzer V20")
    st.caption("Canonical geometry; interchangeable visual encodings. L(G) is computed once; E_i overlays it.")

    with st.sidebar:
        st.header("Data")
        uploaded_csv = st.file_uploader("Upload SYN-IQ CSV", type=["csv"])
        uploaded_html = st.file_uploader("Optional Kepler HTML/config for canonical D3 coordinates", type=["html", "json", "txt"])
        cache_dir = st.text_input("Layout cache directory", DEFAULT_CACHE_DIR)
        prefer_cache = st.checkbox("Prefer cached canonical layout", value=True)
        save_cache = st.checkbox("Save canonical layout", value=True)

        st.header("Mapper")
        n_cubes = st.slider("Cover cubes", min_value=3, max_value=20, value=8)
        perc_overlap = st.slider("Percent overlap", min_value=0.05, max_value=0.80, value=0.35, step=0.05)
        projection = st.selectbox("Projection", ["PCA2D", "first_two_features"], index=0)

        st.header("Rendering")
        mode = st.selectbox("Display mode", ["pie", "overlap", "agent", "continuous"], index=0)
        node_size = st.slider("Node size", min_value=10, max_value=60, value=DEFAULT_NODE_SIZE)

    if uploaded_csv is None:
        st.info("Upload a CSV to begin. V20 will compute one canonical layout L(G) and reuse it for every display mode E_i.")
        st.stop()

    df = pd.read_csv(uploaded_csv)
    st.subheader("Input data")
    st.dataframe(df.head(50), use_container_width=True)

    with st.sidebar:
        agent_col = st.selectbox(
            "Agent column",
            options=["<none>"] + list(df.columns),
            index=(list(df.columns).index(DEFAULT_AGENT_COL) + 1 if DEFAULT_AGENT_COL in df.columns else 0),
        )
        if agent_col == "<none>":
            agent_col = DEFAULT_AGENT_COL
            df[agent_col] = "Other"

        question_col = st.selectbox(
            "Question column",
            options=["<none>"] + list(df.columns),
            index=(list(df.columns).index(DEFAULT_QUESTION_COL) + 1 if DEFAULT_QUESTION_COL in df.columns else 0),
        )
        if question_col == "<none>":
            question_col = DEFAULT_QUESTION_COL
            df[question_col] = ""

        numeric_cols = choose_numeric_columns(df, exclude=[agent_col, question_col])
        default_features = [c for c in numeric_cols if c not in CONTINUOUS_COLOR_COLS]
        feature_cols = st.multiselect("Feature columns for Mapper", numeric_cols, default=default_features[:12] or numeric_cols[:2])
        continuous_choices = [c for c in numeric_cols if c in CONTINUOUS_COLOR_COLS] + [c for c in numeric_cols if c not in CONTINUOUS_COLOR_COLS]
        continuous_col = st.selectbox("Continuous color column", continuous_choices or ["int_pct"], index=0)

    if not feature_cols:
        st.error("Choose at least one numeric feature column for Mapper.")
        st.stop()

    # Save uploaded optional HTML/config to a temporary cache path.
    html_path: Optional[Path] = None
    if uploaded_html is not None:
        html_path = Path(cache_dir) / "uploaded_kepler_layout_source.html"
        html_path.parent.mkdir(parents=True, exist_ok=True)
        html_path.write_bytes(uploaded_html.getvalue())

    with st.spinner("Building Mapper graph and canonical layout..."):
        try:
            mapper, graph, projected = run_mapper_analysis_from_dataframe(
                df,
                feature_cols=feature_cols,
                n_cubes=n_cubes,
                perc_overlap=perc_overlap,
                projection=projection,
            )
        except Exception as exc:
            st.exception(exc)
            st.stop()

        layout = get_canonical_layout(
            graph,
            projected=projected,
            kepler_html_path=html_path,
            cache_dir=cache_dir,
            prefer_cache=prefer_cache,
            save_cache=save_cache,
            seed=42,
        )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Nodes", len(graph.get("nodes", {})))
    with col2:
        edge_count = sum(len(v) for v in graph.get("links", {}).values()) // 2
        st.metric("Edges", edge_count)
    with col3:
        st.metric("Layout source", layout.source)
    with col4:
        st.metric("Cache key", layout.cache_key or "none")

    if layout.notes:
        st.caption(layout.notes)

    try:
        fig = render_plotly_agent_view(
            graph=graph,
            df=df,
            positions=layout.positions,
            mode=mode,
            agent_col=agent_col,
            question_col=question_col,
            continuous_col=continuous_col,
            title=f"SYN-IQ Mapper V20 — {mode}",
            node_size=node_size,
        )
        st.plotly_chart(fig, use_container_width=True)
    except Exception as exc:
        st.exception(exc)
        st.stop()

    with st.expander("Canonical layout coordinates"):
        layout_df = pd.DataFrame(
            [{"node_id": k, "x": v[0], "y": v[1]} for k, v in sorted(layout.positions.items())]
        )
        st.dataframe(layout_df, use_container_width=True)
        st.download_button(
            "Download canonical layout JSON",
            data=json.dumps({k: [v[0], v[1]] for k, v in layout.positions.items()}, indent=2, sort_keys=True),
            file_name=f"syniq_canonical_layout_{layout.cache_key or 'uncached'}.json",
            mime="application/json",
        )

    with st.expander("Methods language for manuscript"):
        st.markdown(
            f"""
            **Canonical-layout architecture (V20).** A Mapper visualization is treated as
            the composition `V(G, L, E)`, where `G` is the Mapper graph, `L : G -> R^2` is a
            canonical two-dimensional node embedding computed once per graph, and `E` is the
            visual encoding (pie composition, overlap highlighting, agent dominance, or
            continuous feature coloration). The encoding `E` is applied as an overlay on
            the fixed coordinates produced by `L(G)`; coloring choice cannot change reported
            geometry. Coordinates are cached by a stable hash of the graph structure so that
            re-runs and color-mode toggles produce bit-identical positions.

            **Layout source for this figure: `{layout.source}`.** Possible values are
            `cache` (precomputed coordinates retrieved from on-disk cache), `kepler_html`
            (coordinates extracted from a kepler-mapper HTML/config file), or
            `networkx_fallback` (deterministic per-component Kamada-Kawai layout seeded by
            lens-space centroids, with components placed on a circle).

            **Agent palette.** Claude = blue (#377EB8), ChatGPT = green (#4DAF4A),
            Gemini = purple (#984EA3), Grok = red (#E41A1C). Mixed-agent nodes in the
            overlap mode are rendered in orange (#FF7F00). This palette is held fixed
            across all SYN-IQ figures (Words Matter manuscript and follow-ups).
            """
        )


if __name__ == "__main__":  # pragma: no cover
    streamlit_app()
