# SPDX-License-Identifier: MIT
# Copyright (C) 2022 Max Bachmann
"""
The Levenshtein (edit) distance is a string metric to measure the
difference between two strings/sequences s1 and s2.
It's defined as the minimum number of insertions, deletions or
substitutions required to transform s1 into s2.
"""

from rapidfuzz._utils import default_distance_attribute as _dist_attr
from rapidfuzz._utils import default_normalized_distance_attribute as _norm_dist_attr
from rapidfuzz._utils import default_normalized_similarity_attribute as _norm_sim_attr
from rapidfuzz._utils import default_similarity_attribute as _sim_attr
from rapidfuzz._utils import fallback_import as _fallback_import

_mod = "rapidfuzz.distance.Levenshtein"
distance = _fallback_import(_mod, "distance")
similarity = _fallback_import(_mod, "similarity")
normalized_distance = _fallback_import(_mod, "normalized_distance")
normalized_similarity = _fallback_import(_mod, "normalized_similarity")
editops = _fallback_import(_mod, "editops")
opcodes = _fallback_import(_mod, "opcodes")

distance._RF_ScorerPy = _dist_attr
similarity._RF_ScorerPy = _sim_attr
normalized_distance._RF_ScorerPy = _norm_dist_attr
normalized_similarity._RF_ScorerPy = _norm_sim_attr
