# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Max Bachmann
from __future__ import annotations

import contextlib
import os

from rapidfuzz._feature_detector import AVX2, SSE2, supports

__all__ = [
    "QRatio",
    "WRatio",
    "partial_ratio",
    "partial_ratio_alignment",
    "partial_token_ratio",
    "partial_token_set_ratio",
    "partial_token_sort_ratio",
    "ratio",
    "token_ratio",
    "token_set_ratio",
    "token_sort_ratio",
]

_impl = os.environ.get("RAPIDFUZZ_IMPLEMENTATION")
if _impl == "cpp":
    imported = False
    if supports(AVX2):
        with contextlib.suppress(ImportError):
            from rapidfuzz.fuzz_cpp_avx2 import (  # pyright: ignore[reportMissingImports]
                QRatio,
                WRatio,
                partial_ratio,
                partial_ratio_alignment,
                partial_token_ratio,
                partial_token_set_ratio,
                partial_token_sort_ratio,
                ratio,
                token_ratio,
                token_set_ratio,
                token_sort_ratio,
            )

            imported = True

    if not imported and supports(SSE2):
        with contextlib.suppress(ImportError):
            from rapidfuzz.fuzz_cpp_sse2 import (  # pyright: ignore[reportMissingImports]
                QRatio,
                WRatio,
                partial_ratio,
                partial_ratio_alignment,
                partial_token_ratio,
                partial_token_set_ratio,
                partial_token_sort_ratio,
                ratio,
                token_ratio,
                token_set_ratio,
                token_sort_ratio,
            )

            imported = True

    if not imported:
        from rapidfuzz.fuzz_cpp import (  # pyright: ignore[reportMissingImports]
            QRatio,
            WRatio,
            partial_ratio,
            partial_ratio_alignment,
            partial_token_ratio,
            partial_token_set_ratio,
            partial_token_sort_ratio,
            ratio,
            token_ratio,
            token_set_ratio,
            token_sort_ratio,
        )
elif _impl == "python":
    from rapidfuzz.fuzz_py import (
        QRatio,
        WRatio,
        partial_ratio,
        partial_ratio_alignment,
        partial_token_ratio,
        partial_token_set_ratio,
        partial_token_sort_ratio,
        ratio,
        token_ratio,
        token_set_ratio,
        token_sort_ratio,
    )
else:
    imported = False
    if supports(AVX2):
        with contextlib.suppress(ImportError):
            from rapidfuzz.fuzz_cpp_avx2 import (  # pyright: ignore[reportMissingImports]
                QRatio,
                WRatio,
                partial_ratio,
                partial_ratio_alignment,
                partial_token_ratio,
                partial_token_set_ratio,
                partial_token_sort_ratio,
                ratio,
                token_ratio,
                token_set_ratio,
                token_sort_ratio,
            )

            imported = True

    if not imported and supports(SSE2):
        with contextlib.suppress(ImportError):
            from rapidfuzz.fuzz_cpp_sse2 import (  # pyright: ignore[reportMissingImports]
                QRatio,
                WRatio,
                partial_ratio,
                partial_ratio_alignment,
                partial_token_ratio,
                partial_token_set_ratio,
                partial_token_sort_ratio,
                ratio,
                token_ratio,
                token_set_ratio,
                token_sort_ratio,
            )

            imported = True

    if not imported:
        with contextlib.suppress(ImportError):
            from rapidfuzz.fuzz_cpp import (  # pyright: ignore[reportMissingImports]
                QRatio,
                WRatio,
                partial_ratio,
                partial_ratio_alignment,
                partial_token_ratio,
                partial_token_set_ratio,
                partial_token_sort_ratio,
                ratio,
                token_ratio,
                token_set_ratio,
                token_sort_ratio,
            )

            imported = True

    if not imported:
        from rapidfuzz.fuzz_py import (
            QRatio,
            WRatio,
            partial_ratio,
            partial_ratio_alignment,
            partial_token_ratio,
            partial_token_set_ratio,
            partial_token_sort_ratio,
            ratio,
            token_ratio,
            token_set_ratio,
            token_sort_ratio,
        )
