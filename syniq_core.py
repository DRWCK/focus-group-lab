"""
syniq_core.py — Stable import facade for the SYN-IQ unified measurement core
=============================================================================

This is a thin re-export shim. The actual canonical core lives in
`syniq_core_v1_1_0.py` (or whatever the latest versioned core is).

Every analyzer in the SYN-IQ stack imports from `syniq_core` (no version
suffix) so the import path stays stable across core upgrades:

    from syniq_core import INT_WORDS, AFF_WORDS, ACT_WORDS
    from syniq_core import score_iep, score_all, VERSION_STAMPS

When a new core ships (e.g. syniq_core_v1_2_0.py), point the import below
at the new module. No analyzer code needs to change.

Drift-protection rail: if the underlying versioned core file is missing,
this raises a clear ImportError naming the file you need to ship — much
more diagnostic than a generic "no module named syniq_core" deep inside
an analyzer.
"""

try:
    from syniq_core_v1_1_0 import *  # noqa: F401,F403
    from syniq_core_v1_1_0 import (
        CORE_VERSION,
        VERSION_STAMPS,
        INT_WORDS, AFF_WORDS, ACT_WORDS,
        SUB_INT, SUB_AFF, SUB_ACT,
        CAM_CONCRETE, CAM_ABSTRACT, CAM_METAPHORICAL,
        IEP_DEFAULT_WEIGHTS,
        score_iep, score_vt, score_cam,
        score_validated_instruments, score_all,
        flatten_scores,
    )
except ImportError as e:
    raise ImportError(
        "syniq_core shim failed: cannot import syniq_core_v1_1_0. "
        "Ensure syniq_core_v1_1_0.py is on the Python path alongside "
        "this shim. Original error: " + str(e)
    ) from e

# Sanity assertion — fast-fail if the core is missing key exports
assert isinstance(INT_WORDS, set) and len(INT_WORDS) > 500, \
    "syniq_core: INT_WORDS missing or too small — core file may be corrupt"
assert isinstance(AFF_WORDS, set) and len(AFF_WORDS) > 500, \
    "syniq_core: AFF_WORDS missing or too small — core file may be corrupt"
assert isinstance(ACT_WORDS, set) and len(ACT_WORDS) > 500, \
    "syniq_core: ACT_WORDS missing or too small — core file may be corrupt"
