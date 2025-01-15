# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Max Bachmann
from __future__ import annotations

import contextlib
import os

from rapidfuzz._feature_detector import AVX2, SSE2, supports

__all__ = ["cdist", "cpdist", "extract", "extractOne", "extract_iter"]

_impl = os.environ.get("RAPIDFUZZ_IMPLEMENTATION")
if _impl == "cpp":
    imported = False
    if supports(AVX2):
        with contextlib.suppress(ImportError):
            from rapidfuzz.process_cpp_avx2 import (  # pyright: ignore[reportMissingImports]
                cdist,
                cpdist,
                extract,
                extract_iter,
                extractOne,
            )

            imported = True

    if not imported and supports(SSE2):
        with contextlib.suppress(ImportError):
            from rapidfuzz.process_cpp_sse2 import (  # pyright: ignore[reportMissingImports]
                cdist,
                cpdist,
                extract,
                extract_iter,
                extractOne,
            )

            imported = True

    if not imported:
        from rapidfuzz.process_cpp import (  # pyright: ignore[reportMissingImports]
            cdist,
            cpdist,
            extract,
            extract_iter,
            extractOne,
        )
elif _impl == "python":
    from rapidfuzz.process_py import cdist, cpdist, extract, extract_iter, extractOne
else:
    imported = False
    if supports(AVX2):
        with contextlib.suppress(ImportError):
            from rapidfuzz.process_cpp_avx2 import (  # pyright: ignore[reportMissingImports]
                cdist,
                cpdist,
                extract,
                extract_iter,
                extractOne,
            )

            imported = True

    if not imported and supports(SSE2):
        with contextlib.suppress(ImportError):
            from rapidfuzz.process_cpp_sse2 import (  # pyright: ignore[reportMissingImports]
                cdist,
                cpdist,
                extract,
                extract_iter,
                extractOne,
            )

            imported = True

    if not imported:
        with contextlib.suppress(ImportError):
            from rapidfuzz.process_cpp import (  # pyright: ignore[reportMissingImports]
                cdist,
                cpdist,
                extract,
                extract_iter,
                extractOne,
            )

            imported = True

    if not imported:
        from rapidfuzz.process_py import (
            cdist,
            cpdist,
            extract,
            extract_iter,
            extractOne,
        )
