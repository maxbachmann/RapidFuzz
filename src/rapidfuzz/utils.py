# SPDX-License-Identifier: MIT
# Copyright (C) 2025 Max Bachmann
from __future__ import annotations

import contextlib
import os

from rapidfuzz._feature_detector import AVX2, SSE2, supports

__all__ = ["default_process"]

_impl = os.environ.get("RAPIDFUZZ_IMPLEMENTATION")
if _impl == "cpp":
    imported = False
    if supports(AVX2):
        with contextlib.suppress(ImportError):
            from rapidfuzz.utils_cpp_avx2 import (
                default_process,  # pyright: ignore[reportMissingImports]
            )

            imported = True

    if not imported and supports(SSE2):
        with contextlib.suppress(ImportError):
            from rapidfuzz.utils_cpp_sse2 import (
                default_process,  # pyright: ignore[reportMissingImports]
            )

            imported = True

    if not imported:
        from rapidfuzz.utils_cpp import (
            default_process,  # pyright: ignore[reportMissingImports]
        )
elif _impl == "python":
    from rapidfuzz.utils_py import default_process
else:
    imported = False
    if supports(AVX2):
        with contextlib.suppress(ImportError):
            from rapidfuzz.utils_cpp_avx2 import (
                default_process,  # pyright: ignore[reportMissingImports]
            )

            imported = True

    if not imported and supports(SSE2):
        with contextlib.suppress(ImportError):
            from rapidfuzz.utils_cpp_sse2 import (
                default_process,  # pyright: ignore[reportMissingImports]
            )

            imported = True

    if not imported:
        with contextlib.suppress(ImportError):
            from rapidfuzz.utils_cpp import (
                default_process,  # pyright: ignore[reportMissingImports]
            )

            imported = True

    if not imported:
        from rapidfuzz.utils_py import default_process
