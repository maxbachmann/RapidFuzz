# distutils: language=c++
# cython: language_level=3, binding=True, linetrace=True

from array import array
from rapidfuzz.utils import default_process

from rapidfuzz_capi cimport (
    RF_String, RF_Scorer, RF_Kwargs, RF_Distance, RF_Similarity,
    RF_KwargsInit, RF_SIMILARITY, RF_DISTANCE
)
from cpp_common cimport RF_StringWrapper, is_valid_string, convert_string, hash_array, hash_sequence

from libcpp cimport bool
from libcpp.utility cimport move
from libcpp.vector cimport vector
from libc.stdlib cimport malloc, free
from libcpp cimport bool
from cpython.list cimport PyList_New, PyList_SET_ITEM
from cpython.ref cimport Py_INCREF
from cpython.pycapsule cimport PyCapsule_New
from cython.operator cimport dereference

cdef inline RF_String conv_sequence(seq) except *:
    if is_valid_string(seq):
        return move(convert_string(seq))
    elif isinstance(seq, array):
        return move(hash_array(seq))
    else:
        return move(hash_sequence(seq))

cdef extern from "cpp_scorer.hpp" namespace "rapidfuzz" nogil:
    cpdef enum class LevenshteinEditType:
        None    = 0,
        Replace = 1,
        Insert  = 2,
        Delete  = 3

    ctypedef struct LevenshteinEditOp:
        LevenshteinEditType type
        size_t src_pos
        size_t dest_pos

cdef extern from "rapidfuzz/details/types.hpp" namespace "rapidfuzz" nogil:
    cdef struct LevenshteinWeightTable:
        size_t insert_cost
        size_t delete_cost
        size_t replace_cost

cdef extern from "cpp_scorer.hpp":
    double normalized_levenshtein_no_process(       const RF_String&, const RF_String&, size_t, size_t, size_t, double) nogil except +
    double normalized_levenshtein_default_process(  const RF_String&, const RF_String&, size_t, size_t, size_t, double) nogil except +
    double normalized_hamming_no_process(           const RF_String&, const RF_String&, double) nogil except +
    double normalized_hamming_default_process(      const RF_String&, const RF_String&, double) nogil except +
    double jaro_similarity_no_process(              const RF_String&, const RF_String&, double) nogil except +
    double jaro_similarity_default_process(         const RF_String&, const RF_String&, double) nogil except +
    double jaro_winkler_similarity_no_process(      const RF_String&, const RF_String&, double, double) nogil except +
    double jaro_winkler_similarity_default_process( const RF_String&, const RF_String&, double, double) nogil except +

    object levenshtein_no_process(                  const RF_String&, const RF_String&, size_t, size_t, size_t, size_t) nogil except +
    object levenshtein_default_process(             const RF_String&, const RF_String&, size_t, size_t, size_t, size_t) nogil except +
    object hamming_no_process(                      const RF_String&, const RF_String&, size_t) nogil except +
    object hamming_default_process(                 const RF_String&, const RF_String&, size_t) nogil except +

    vector[LevenshteinEditOp] levenshtein_editops_no_process(     const RF_String& s1, const RF_String& s2) nogil except +
    vector[LevenshteinEditOp] levenshtein_editops_default_process(const RF_String& s1, const RF_String& s2) nogil except +

    bool LevenshteinInit(RF_Distance* context, const RF_Kwargs* kwargs, size_t, const RF_String* str) nogil except False
    bool NormalizedLevenshteinInit(RF_Similarity* context, const RF_Kwargs* kwargs, size_t, const RF_String* str) nogil except False

    RF_Scorer CreateHammingFunctionTable() except +
    RF_Scorer CreateNormalizedHammingFunctionTable() except +
    RF_Scorer CreateJaroSimilarityFunctionTable() except +
    bool JaroWinklerSimilarityInit(RF_Similarity* context, const RF_Kwargs* kwargs, size_t, const RF_String* str) nogil except False

def levenshtein(s1, s2, *, weights=(1,1,1), processor=None, max=None):
    """
    Calculates the minimum number of insertions, deletions, and substitutions
    required to change one sequence into the other according to Levenshtein with custom
    costs for insertion, deletion and substitution

    Parameters
    ----------
    s1 : Sequence[Hashable]
        First string to compare.
    s2 : Sequence[Hashable]
        Second string to compare.
    weights : Tuple[int, int, int] or None, optional
        The weights for the three operations in the form
        (insertion, deletion, substitution). Default is (1, 1, 1),
        which gives all three operations a weight of 1.
    processor: bool or callable, optional
        Optional callable that is used to preprocess the strings before
        comparing them. When processor is True ``utils.default_process``
        is used. Default is None, which deactivates this behaviour.
    max : int or None, optional
        Maximum distance between s1 and s2, that is
        considered as a result. If the distance is bigger than max,
        -1 is returned instead. Default is None, which deactivates
        this behaviour.

    Returns
    -------
    distance : int
        distance between s1 and s2

    Raises
    ------
    ValueError
        If unsupported weights are provided a ValueError is thrown

    Notes
    -----
    Depending on the input parameters different optimized implementation are used
    to improve the performance.

    Insertion = Deletion = Substitution:
      This is known as uniform Levenshtein distance and is the distance most commonly
      referred to as Levenshtein distance. The following implementation is used
      with a worst-case performance of ``O([N/64]M)``.

      - if max is 0 the similarity can be calculated using a direct comparision,
        since no difference between the strings is allowed.  The time complexity of
        this algorithm is ``O(N)``.

      - A common prefix/suffix of the two compared strings does not affect
        the Levenshtein distance, so the affix is removed before calculating the
        similarity.

      - If max is ≤ 3 the mbleven algorithm is used. This algorithm
        checks all possible edit operations that are possible under
        the threshold `max`. The time complexity of this algorithm is ``O(N)``.

      - If the length of the shorter string is ≤ 64 after removing the common affix
        Hyyrös' algorithm is used, which calculates the Levenshtein distance in
        parallel. The algorithm is described by [1]_. The time complexity of this
        algorithm is ``O(N)``.

      - If the length of the shorter string is ≥ 64 after removing the common affix
        a blockwise implementation of Myers' algorithm is used, which calculates
        the Levenshtein distance in parallel (64 characters at a time).
        The algorithm is described by [3]_. The time complexity of this
        algorithm is ``O([N/64]M)``.

    The following image shows a benchmark of the Levenshtein distance in multiple
    Python libraries. All of them are implemented either in C/C++ or Cython.
    The graph shows, that python-Levenshtein is the only library with a time
    complexity of ``O(NM)``, while all other libraries have a time complexity of
    ``O([N/64]M)``. Especially for long strings RapidFuzz is a lot faster than
    all the other tested libraries.

    .. image:: img/uniform_levenshtein.svg


    Insertion = Deletion, Substitution >= Insertion + Deletion:
      Since every Substitution can be performed as Insertion + Deletion, this variant
      of the Levenshtein distance only uses Insertions and Deletions. Therefore this
      variant is often referred to as InDel-Distance.  The following implementation
      is used with a worst-case performance of ``O([N/64]M)``.

      - if max is 0 the similarity can be calculated using a direct comparision,
        since no difference between the strings is allowed.  The time complexity of
        this algorithm is ``O(N)``.

      - if max is 1 and the two strings have a similar length, the similarity can be
        calculated using a direct comparision aswell, since a substitution would cause
        a edit distance higher than max. The time complexity of this algorithm
        is ``O(N)``.

      - A common prefix/suffix of the two compared strings does not affect
        the Levenshtein distance, so the affix is removed before calculating the
        similarity.

      - If max is ≤ 4 the mbleven algorithm is used. This algorithm
        checks all possible edit operations that are possible under
        the threshold `max`. As a difference to the normal Levenshtein distance this
        algorithm can even be used up to a threshold of 4 here, since the higher weight
        of substitutions decreases the amount of possible edit operations.
        The time complexity of this algorithm is ``O(N)``.

      - If the length of the shorter string is ≤ 64 after removing the common affix
        Hyyrös' lcs algorithm is used, which calculates the InDel distance in
        parallel. The algorithm is described by [4]_ and is extended with support
        for UTF32 in this implementation. The time complexity of this
        algorithm is ``O(N)``.

      - If the length of the shorter string is ≥ 64 after removing the common affix
        a blockwise implementation of the Hyyrös' lcs algorithm is used, which calculates
        the Levenshtein distance in parallel (64 characters at a time).
        The algorithm is described by [4]_. The time complexity of this
        algorithm is ``O([N/64]M)``.

    The following image shows a benchmark of the InDel distance in RapidFuzz
    and python-Levenshtein. Similar to the normal Levenshtein distance
    python-Levenshtein uses a implementation with a time complexity of ``O(NM)``,
    while RapidFuzz has a time complexity of ``O([N/64]M)``.

    .. image:: img/indel_levenshtein.svg


    Other weights:
      The implementation for other weights is based on Wagner-Fischer.
      It has a performance of ``O(N * M)`` and has a memory usage of ``O(N)``.
      Further details can be found in [2]_.

    References
    ----------
    .. [1] Hyyrö, Heikki. "A Bit-Vector Algorithm for Computing
           Levenshtein and Damerau Edit Distances."
           Nordic Journal of Computing, Volume 10 (2003): 29-39.
    .. [2] Wagner, Robert & Fischer, Michael
           "The String-to-String Correction Problem."
           J. ACM. 21. (1974): 168-173
    .. [3] Myers, Gene. "A fast bit-vector algorithm for approximate
           string matching based on dynamic programming."
           Journal of the ACM (JACM) 46.3 (1999): 395-415.
    .. [4] Hyyrö, Heikki. "Bit-Parallel LCS-length Computation Revisited"
           Proc. 15th Australasian Workshop on Combinatorial Algorithms (AWOCA 2004).

    Examples
    --------
    Find the Levenshtein distance between two strings:

    >>> from rapidfuzz.string_metric import levenshtein
    >>> levenshtein("lewenstein", "levenshtein")
    2

    Setting a maximum distance allows the implementation to select
    a more efficient implementation:

    >>> levenshtein("lewenstein", "levenshtein", max=1)
    -1

    It is possible to select different weights by passing a `weight`
    tuple.

    >>> levenshtein("lewenstein", "levenshtein", weights=(1,1,2))
    3
    """
    cdef size_t insertion, deletion, substitution
    insertion = deletion = substitution = 1
    if weights is not None:
        insertion, deletion, substitution = weights

    cdef size_t c_max = <size_t>-1 if max is None else max

    if processor is True or processor == default_process:
        s1_proc = RF_StringWrapper(conv_sequence(s1))
        s2_proc = RF_StringWrapper(conv_sequence(s2))
        return levenshtein_default_process(s1_proc.string, s2_proc.string, insertion, deletion, substitution, c_max)
    elif callable(processor):
        s1 = processor(s1)
        s2 = processor(s2)

    s1_proc = RF_StringWrapper(conv_sequence(s1))
    s2_proc = RF_StringWrapper(conv_sequence(s2))
    return levenshtein_no_process(s1_proc.string, s2_proc.string, insertion, deletion, substitution, c_max)

cdef str levenshtein_edit_type_to_str(LevenshteinEditType edit_type):
    if edit_type == LevenshteinEditType.Insert:
        return "insert"
    elif edit_type == LevenshteinEditType.Delete:
        return "delete"
    # possibly requires no-op in the future as well
    else:
        return "replace"

cdef list levenshtein_editops_to_list(vector[LevenshteinEditOp] ops):
    cdef size_t op_count = ops.size()
    cdef list result_list = PyList_New(<Py_ssize_t>op_count)
    for i in range(op_count):
        result_item = (levenshtein_edit_type_to_str(ops[i].type), ops[i].src_pos, ops[i].dest_pos)
        Py_INCREF(result_item)
        PyList_SET_ITEM(result_list, <Py_ssize_t>i, result_item)

    return result_list

def levenshtein_editops(s1, s2, *, processor=None):
    """
    Return list of 3-tuples describing how to turn s1 into s2.
    Each tuple is of the form (tag, src_pos, dest_pos).

    The tags are strings, with these meanings:
    'replace':  s1[src_pos] should be replaced by s2[dest_pos]
    'delete':   s1[src_pos] should be deleted.
    'insert':   s2[dest_pos] should be inserted at s1[src_pos].

    Parameters
    ----------
    s1 : Sequence[Hashable]
        First string to compare.
    s2 : Sequence[Hashable]
        Second string to compare.
    processor: bool or callable, optional
        Optional callable that is used to preprocess the strings before
        comparing them. When processor is True ``utils.default_process``
        is used. Default is None, which deactivates this behaviour.

    Returns
    -------
    editops : list[]
        edit operations required to turn s1 into s2

    Examples
    --------
    >>> from rapidfuzz.string_metric import levenshtein_editops
    >>> for tag, src_pos, dest_pos in levenshtein_editops("qabxcd", "abycdf"):
    ...    print(("%7s s1[%d] s2[%d]" % (tag, src_pos, dest_pos)))
     delete s1[1] s2[0]
    replace s1[4] s2[3]
     insert s1[6] s2[6]
    """
    if processor is True or processor == default_process:
        s1_proc = RF_StringWrapper(conv_sequence(s1))
        s2_proc = RF_StringWrapper(conv_sequence(s2))
        return levenshtein_editops_to_list(
            levenshtein_editops_default_process(s1_proc.string, s2_proc.string)
        )
    elif callable(processor):
        s1 = processor(s1)
        s2 = processor(s2)

    s1_proc = RF_StringWrapper(conv_sequence(s1))
    s2_proc = RF_StringWrapper(conv_sequence(s2))
    return levenshtein_editops_to_list(
        levenshtein_editops_no_process(s1_proc.string, s2_proc.string)
    )

def normalized_levenshtein(s1, s2, *, weights=(1,1,1), processor=None, score_cutoff=None):
    """
    Calculates a normalized levenshtein distance using custom
    costs for insertion, deletion and substitution.

    Parameters
    ----------
    s1 : Sequence[Hashable]
        First string to compare.
    s2 : Sequence[Hashable]
        Second string to compare.
    weights : Tuple[int, int, int] or None, optional
        The weights for the three operations in the form
        (insertion, deletion, substitution). Default is (1, 1, 1),
        which gives all three operations a weight of 1.
    processor: bool or callable, optional
        Optional callable that is used to preprocess the strings before
        comparing them. When processor is True ``utils.default_process``
        is used. Default is None, which deactivates this behaviour.
    score_cutoff : float, optional
        Optional argument for a score threshold as a float between 0 and 100.
        For ratio < score_cutoff 0 is returned instead. Default is 0,
        which deactivates this behaviour.

    Returns
    -------
    similarity : float
        similarity between s1 and s2 as a float between 0 and 100

    Raises
    ------
    ValueError
        If unsupported weights are provided a ValueError is thrown

    See Also
    --------
    levenshtein : Levenshtein distance

    Notes
    -----
    The normalization of the Levenshtein distance is performed in the following way:

    .. math::
      :nowrap:

      \\begin{align*}
        dist_{max} &= \\begin{cases}
          min(len(s1), len(s2)) \cdot sub,       & \\text{if } sub \leq ins + del \\\\
          len(s1) \cdot del + len(s2) \cdot ins, & \\text{otherwise}
        \end{cases}\\\\[10pt]

        dist_{max} &= \\begin{cases}
          dist_{max} + (len(s1) - len(s2)) \cdot del, & \\text{if } len(s1) > len(s2) \\\\
          dist_{max} + (len(s2) - len(s1)) \cdot ins, & \\text{if } len(s1) < len(s2) \\\\
          dist_{max},                                 & \\text{if } len(s1) = len(s2)
        \end{cases}\\\\[10pt]

        ratio &= 100 \cdot \\frac{distance(s1, s2)}{dist_{max}}
      \end{align*}

    Examples
    --------
    Find the normalized Levenshtein distance between two strings:

    >>> from rapidfuzz.string_metric import normalized_levenshtein
    >>> normalized_levenshtein("lewenstein", "levenshtein")
    81.81818181818181

    Setting a score_cutoff allows the implementation to select
    a more efficient implementation:

    >>> normalized_levenshtein("lewenstein", "levenshtein", score_cutoff=85)
    0.0

    It is possible to select different weights by passing a `weight`
    tuple.

    >>> normalized_levenshtein("lewenstein", "levenshtein", weights=(1,1,2))
    85.71428571428571

     When a different processor is used s1 and s2 do not have to be strings

    >>> normalized_levenshtein(["lewenstein"], ["levenshtein"], processor=lambda s: s[0])
    81.81818181818181
    """
    if s1 is None or s2 is None:
        return 0

    cdef size_t insertion, deletion, substitution
    insertion = deletion = substitution = 1
    if weights is not None:
        insertion, deletion, substitution = weights

    cdef double c_score_cutoff = 0.0 if score_cutoff is None else score_cutoff

    if processor is True or processor == default_process:
        s1_proc = RF_StringWrapper(conv_sequence(s1))
        s2_proc = RF_StringWrapper(conv_sequence(s2))
        return normalized_levenshtein_default_process(s1_proc.string, s2_proc.string, insertion, deletion, substitution, c_score_cutoff)
    elif callable(processor):
        s1 = processor(s1)
        s2 = processor(s2)

    s1_proc = RF_StringWrapper(conv_sequence(s1))
    s2_proc = RF_StringWrapper(conv_sequence(s2))
    return normalized_levenshtein_no_process(s1_proc.string, s2_proc.string, insertion, deletion, substitution, c_score_cutoff)


def hamming(s1, s2, *, processor=None, max=None):
    """
    Calculates the Hamming distance between two strings.
    The hamming distance is defined as the number of positions
    where the two strings differ. It describes the minimum
    amount of substitutions required to transform s1 into s2.

    Parameters
    ----------
    s1 : Sequence[Hashable]
        First string to compare.
    s2 : Sequence[Hashable]
        Second string to compare.
    processor: bool or callable, optional
        Optional callable that is used to preprocess the strings before
        comparing them. When processor is True ``utils.default_process``
        is used. Default is None, which deactivates this behaviour.
    max : int or None, optional
        Maximum distance between s1 and s2, that is
        considered as a result. If the distance is bigger than max,
        -1 is returned instead. Default is None, which deactivates
        this behaviour.

    Returns
    -------
    distance : int
        distance between s1 and s2

    Raises
    ------
    ValueError
        If s1 and s2 have a different length
    """
    cdef size_t c_max = <size_t>-1 if max is None else max

    if s1 is None or s2 is None:
        return 0

    if processor is True or processor == default_process:
        s1_proc = RF_StringWrapper(conv_sequence(s1))
        s2_proc = RF_StringWrapper(conv_sequence(s2))
        return hamming_default_process(s1_proc.string, s2_proc.string, c_max)
    elif callable(processor):
        s1 = processor(s1)
        s2 = processor(s2)

    s1_proc = RF_StringWrapper(conv_sequence(s1))
    s2_proc = RF_StringWrapper(conv_sequence(s2))
    return hamming_no_process(s1_proc.string, s2_proc.string, c_max)


def normalized_hamming(s1, s2, *, processor=None, score_cutoff=None):
    """
    Calculates a normalized hamming distance

    Parameters
    ----------
    s1 : Sequence[Hashable]
        First string to compare.
    s2 : Sequence[Hashable]
        Second string to compare.
    processor: bool or callable, optional
        Optional callable that is used to preprocess the strings before
        comparing them. When processor is True ``utils.default_process``
        is used. Default is None, which deactivates this behaviour.
    score_cutoff : float, optional
        Optional argument for a score threshold as a float between 0 and 100.
        For ratio < score_cutoff 0 is returned instead. Default is 0,
        which deactivates this behaviour.

    Returns
    -------
    similarity : float
        similarity between s1 and s2 as a float between 0 and 100

    Raises
    ------
    ValueError
        If s1 and s2 have a different length

    See Also
    --------
    hamming : Hamming distance
    """
    cdef double c_score_cutoff = 0.0 if score_cutoff is None else score_cutoff

    if s1 is None or s2 is None:
        return 0

    if processor is True or processor == default_process:
        s1_proc = RF_StringWrapper(conv_sequence(s1))
        s2_proc = RF_StringWrapper(conv_sequence(s2))
        return normalized_hamming_default_process(s1_proc.string, s2_proc.string, c_score_cutoff)
    elif callable(processor):
        s1 = processor(s1)
        s2 = processor(s2)

    s1_proc = RF_StringWrapper(conv_sequence(s1))
    s2_proc = RF_StringWrapper(conv_sequence(s2))
    return normalized_hamming_no_process(s1_proc.string, s2_proc.string, c_score_cutoff)


def jaro_similarity(s1, s2, *, processor=None, score_cutoff=None):
    """
    Calculates the jaro similarity

    Parameters
    ----------
    s1 : Sequence[Hashable]
        First string to compare.
    s2 : Sequence[Hashable]
        Second string to compare.
    processor: bool or callable, optional
        Optional callable that is used to preprocess the strings before
        comparing them. When processor is True ``utils.default_process``
        is used. Default is None, which deactivates this behaviour.
    score_cutoff : float, optional
        Optional argument for a score threshold as a float between 0 and 100.
        For ratio < score_cutoff 0 is returned instead. Default is 0,
        which deactivates this behaviour.

    Returns
    -------
    similarity : float
        similarity between s1 and s2 as a float between 0 and 100

    """
    cdef double c_score_cutoff = 0.0 if score_cutoff is None else score_cutoff

    if s1 is None or s2 is None:
        return 0

    if processor is True or processor == default_process:
        s1_proc = RF_StringWrapper(conv_sequence(s1))
        s2_proc = RF_StringWrapper(conv_sequence(s2))
        return jaro_similarity_default_process(s1_proc.string, s2_proc.string, c_score_cutoff)
    elif callable(processor):
        s1 = processor(s1)
        s2 = processor(s2)

    s1_proc = RF_StringWrapper(conv_sequence(s1))
    s2_proc = RF_StringWrapper(conv_sequence(s2))
    return jaro_similarity_no_process(s1_proc.string, s2_proc.string, c_score_cutoff)


def jaro_winkler_similarity(s1, s2, *, double prefix_weight=0.1, processor=None, score_cutoff=None):
    """
    Calculates the jaro winkler similarity

    Parameters
    ----------
    s1 : Sequence[Hashable]
        First string to compare.
    s2 : Sequence[Hashable]
        Second string to compare.
    prefix_weight : float, optional
        Weight used for the common prefix of the two strings.
        Has to be between 0 and 0.25. Default is 0.1.
    processor: bool or callable, optional
        Optional callable that is used to preprocess the strings before
        comparing them. When processor is True ``utils.default_process``
        is used. Default is None, which deactivates this behaviour.
    score_cutoff : float, optional
        Optional argument for a score threshold as a float between 0 and 100.
        For ratio < score_cutoff 0 is returned instead. Default is 0,
        which deactivates this behaviour.

    Returns
    -------
    similarity : float
        similarity between s1 and s2 as a float between 0 and 100

    Raises
    ------
    ValueError
        If prefix_weight is invalid
    """
    cdef double c_score_cutoff = 0.0 if score_cutoff is None else score_cutoff

    if s1 is None or s2 is None:
        return 0

    if processor is True or processor == default_process:
        s1_proc = RF_StringWrapper(conv_sequence(s1))
        s2_proc = RF_StringWrapper(conv_sequence(s2))
        return jaro_winkler_similarity_default_process(s1_proc.string, s2_proc.string, prefix_weight, c_score_cutoff)
    elif callable(processor):
        s1 = processor(s1)
        s2 = processor(s2)

    s1_proc = RF_StringWrapper(conv_sequence(s1))
    s2_proc = RF_StringWrapper(conv_sequence(s2))
    return jaro_winkler_similarity_no_process(s1_proc.string, s2_proc.string, prefix_weight, c_score_cutoff)

cdef void KwargsDeinit(RF_Kwargs* self):
    free(<void*>dereference(self).context)

cdef bool LevenshteinKwargsInit(RF_Kwargs* self, dict kwargs) except False:
    cdef size_t insertion, deletion, substitution
    cdef LevenshteinWeightTable* weights = <LevenshteinWeightTable*>malloc(sizeof(LevenshteinWeightTable))

    if not weights:
        raise MemoryError

    insertion, deletion, substitution = kwargs.get("weights", (1, 1, 1))
    dereference(weights).insert_cost = insertion
    dereference(weights).delete_cost = deletion
    dereference(weights).replace_cost = substitution
    dereference(self).context = weights
    dereference(self).dtor = KwargsDeinit
    return True


cdef RF_Scorer LevenshteinContext
LevenshteinContext.scorer_type = RF_DISTANCE
LevenshteinContext.kwargs_init = LevenshteinKwargsInit
LevenshteinContext.scorer.distance_init = LevenshteinInit
levenshtein.__RapidFuzzScorer = PyCapsule_New(&LevenshteinContext, NULL, NULL)

cdef RF_Scorer NormalizedLevenshteinContext
NormalizedLevenshteinContext.scorer_type = RF_SIMILARITY
NormalizedLevenshteinContext.kwargs_init = LevenshteinKwargsInit
NormalizedLevenshteinContext.scorer.similarity_init = NormalizedLevenshteinInit
normalized_levenshtein.__RapidFuzzScorer = PyCapsule_New(&NormalizedLevenshteinContext, NULL, NULL)

cdef RF_Scorer HammingContext = CreateHammingFunctionTable()
hamming.__RapidFuzzScorer = PyCapsule_New(&HammingContext, NULL, NULL)

cdef RF_Scorer NormalizedHammingContext = CreateNormalizedHammingFunctionTable()
normalized_hamming.__RapidFuzzScorer = PyCapsule_New(&NormalizedHammingContext, NULL, NULL)

cdef RF_Scorer JaroSimilarityContext = CreateJaroSimilarityFunctionTable()
jaro_similarity.__RapidFuzzScorer = PyCapsule_New(&JaroSimilarityContext, NULL, NULL)

cdef bool JaroWinklerKwargsInit(RF_Kwargs* self, dict kwargs) except False:
    cdef double* prefix_weight = <double*>malloc(sizeof(double))

    if not prefix_weight:
        raise MemoryError

    prefix_weight[0] = kwargs.get("prefix_weight", 0.1)
    dereference(self).context = prefix_weight
    dereference(self).dtor = KwargsDeinit
    return True

cdef RF_Scorer JaroWinklerSimilarityContext
JaroWinklerSimilarityContext.scorer_type = RF_SIMILARITY
JaroWinklerSimilarityContext.kwargs_init = JaroWinklerKwargsInit
JaroWinklerSimilarityContext.scorer.similarity_init = JaroWinklerSimilarityInit
jaro_winkler_similarity.__RapidFuzzScorer = PyCapsule_New(&JaroWinklerSimilarityContext, NULL, NULL)
