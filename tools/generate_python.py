#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Max Bachmann
from __future__ import annotations

import subprocess
from pathlib import Path

import isort

format = """
# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Max Bachmann
from __future__ import annotations

import contextlib
import os

from rapidfuzz._feature_detector import AVX2, SSE2, supports

__all__ = [
    {exports}
]

_impl = os.environ.get("RAPIDFUZZ_IMPLEMENTATION")
if _impl == "cpp":
    imported = False
    if supports(AVX2):
        with contextlib.suppress(ImportError):
            from {module}_cpp_avx2 import {includes} # pyright: ignore[reportMissingImports]
            imported = True

    if not imported and supports(SSE2):
        with contextlib.suppress(ImportError):
            from {module}_cpp_sse2 import {includes} # pyright: ignore[reportMissingImports]
            imported = True

    if not imported:
        from {module}_cpp import {includes} # pyright: ignore[reportMissingImports]
elif _impl == "python":
    from {module}_py import {includes}
else:
    imported = False
    if supports(AVX2):
        with contextlib.suppress(ImportError):
            from {module}_cpp_avx2 import {includes} # pyright: ignore[reportMissingImports]
            imported = True

    if not imported and supports(SSE2):
        with contextlib.suppress(ImportError):
            from {module}_cpp_sse2 import {includes} # pyright: ignore[reportMissingImports]
            imported = True

    if not imported:
        with contextlib.suppress(ImportError):
            from {module}_cpp import {includes} # pyright: ignore[reportMissingImports]
            imported = True

    if not imported:
        from {module}_py import {includes}
"""


def generate(module, importModule, includes):
    segments = module.split(".")
    segments[-1] = segments[-1] + ".py"
    path = Path(__file__).parent.parent / "src"
    for segment in segments:
        path = path.joinpath(segment)

    print(f"generating {path}")
    if isinstance(includes, list):
        includesStr = ", ".join(includes)
        exportStr = ", ".join(f'"{x}"' for x in includes)
    else:
        includesStr = ", ".join(f"{k} as {v}" for k, v in includes.items())
        exportStr = ", ".join(f'"{x}"' for x in includes.values())

    formatted = format.format(module=importModule, includes=includesStr, exports=exportStr)

    config = isort.settings.Config(combine_as_imports=True)
    formatted = isort.code(formatted, config=config)

    with path.open("w", encoding="utf-8") as f:
        f.write(formatted)

    print(f"formatting {path} using ruff")
    subprocess.run(["ruff", "format", path], check=False)
    subprocess.run(["ruff", "check", path, "--fix"], check=False)


generate(
    "rapidfuzz.fuzz",
    "rapidfuzz.fuzz",
    [
        "ratio",
        "partial_ratio",
        "partial_ratio_alignment",
        "token_sort_ratio",
        "token_set_ratio",
        "token_ratio",
        "partial_token_sort_ratio",
        "partial_token_set_ratio",
        "partial_token_ratio",
        "WRatio",
        "QRatio",
    ],
)


generate(
    "rapidfuzz.process",
    "rapidfuzz.process",
    [
        "extract",
        "extractOne",
        "extract_iter",
        "cdist",
        "cpdist",
    ],
)

generate(
    "rapidfuzz.utils",
    "rapidfuzz.utils",
    [
        "default_process",
    ],
)

generate(
    "rapidfuzz.distance._initialize",
    "rapidfuzz.distance._initialize",
    [
        "Editop",
        "Editops",
        "Opcode",
        "Opcodes",
        "ScoreAlignment",
        "MatchingBlock",
    ],
)

generate(
    "rapidfuzz.distance.DamerauLevenshtein",
    "rapidfuzz.distance.metrics",
    {
        "damerau_levenshtein_distance": "distance",
        "damerau_levenshtein_similarity": "similarity",
        "damerau_levenshtein_normalized_distance": "normalized_distance",
        "damerau_levenshtein_normalized_similarity": "normalized_similarity",
    },
)

generate(
    "rapidfuzz.distance.Hamming",
    "rapidfuzz.distance.metrics",
    {
        "hamming_distance": "distance",
        "hamming_similarity": "similarity",
        "hamming_normalized_distance": "normalized_distance",
        "hamming_normalized_similarity": "normalized_similarity",
        "hamming_editops": "editops",
        "hamming_opcodes": "opcodes",
    },
)

generate(
    "rapidfuzz.distance.Indel",
    "rapidfuzz.distance.metrics",
    {
        "indel_distance": "distance",
        "indel_similarity": "similarity",
        "indel_normalized_distance": "normalized_distance",
        "indel_normalized_similarity": "normalized_similarity",
        "indel_editops": "editops",
        "indel_opcodes": "opcodes",
    },
)

generate(
    "rapidfuzz.distance.Jaro",
    "rapidfuzz.distance.metrics",
    {
        "jaro_distance": "distance",
        "jaro_similarity": "similarity",
        "jaro_normalized_distance": "normalized_distance",
        "jaro_normalized_similarity": "normalized_similarity",
    },
)

generate(
    "rapidfuzz.distance.JaroWinkler",
    "rapidfuzz.distance.metrics",
    {
        "jaro_winkler_distance": "distance",
        "jaro_winkler_similarity": "similarity",
        "jaro_winkler_normalized_distance": "normalized_distance",
        "jaro_winkler_normalized_similarity": "normalized_similarity",
    },
)

generate(
    "rapidfuzz.distance.LCSseq",
    "rapidfuzz.distance.metrics",
    {
        "lcs_seq_distance": "distance",
        "lcs_seq_similarity": "similarity",
        "lcs_seq_normalized_distance": "normalized_distance",
        "lcs_seq_normalized_similarity": "normalized_similarity",
        "lcs_seq_editops": "editops",
        "lcs_seq_opcodes": "opcodes",
    },
)

generate(
    "rapidfuzz.distance.Levenshtein",
    "rapidfuzz.distance.metrics",
    {
        "levenshtein_distance": "distance",
        "levenshtein_similarity": "similarity",
        "levenshtein_normalized_distance": "normalized_distance",
        "levenshtein_normalized_similarity": "normalized_similarity",
        "levenshtein_editops": "editops",
        "levenshtein_opcodes": "opcodes",
    },
)

generate(
    "rapidfuzz.distance.OSA",
    "rapidfuzz.distance.metrics",
    {
        "osa_distance": "distance",
        "osa_similarity": "similarity",
        "osa_normalized_distance": "normalized_distance",
        "osa_normalized_similarity": "normalized_similarity",
    },
)

generate(
    "rapidfuzz.distance.Postfix",
    "rapidfuzz.distance.metrics",
    {
        "postfix_distance": "distance",
        "postfix_similarity": "similarity",
        "postfix_normalized_distance": "normalized_distance",
        "postfix_normalized_similarity": "normalized_similarity",
    },
)

generate(
    "rapidfuzz.distance.Prefix",
    "rapidfuzz.distance.metrics",
    {
        "prefix_distance": "distance",
        "prefix_similarity": "similarity",
        "prefix_normalized_distance": "normalized_distance",
        "prefix_normalized_similarity": "normalized_similarity",
    },
)
