#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import pytest

from rapidfuzz import process, fuzz, utils

scorers = [
    fuzz.ratio,
    fuzz.partial_ratio,
    fuzz.token_sort_ratio,
    fuzz.token_set_ratio,
    fuzz.token_ratio,
    fuzz.partial_token_sort_ratio,
    fuzz.partial_token_set_ratio,
    fuzz.partial_token_ratio,
    fuzz.WRatio,
    fuzz.QRatio
]

class RatioTest(unittest.TestCase):
    s1 = "new york mets"
    s1a = "new york mets"
    s2 = "new YORK mets"
    s3 = "the wonderful new york mets"
    s4 = "new york mets vs atlanta braves"
    s5 = "atlanta braves vs new york mets"
    s6 = "new york mets - atlanta braves"

    def testNoProcessor(self):
        self.assertEqual(fuzz.ratio(self.s1, self.s1a), 100)
        self.assertNotEqual(fuzz.ratio(self.s1, self.s2), 100)

    def testPartialRatio(self):
        self.assertEqual(fuzz.partial_ratio(self.s1, self.s3), 100)

    def testTokenSortRatio(self):
        self.assertEqual(fuzz.token_sort_ratio(self.s1, self.s1a), 100)

    def testPartialTokenSortRatio(self):
        self.assertEqual(fuzz.partial_token_sort_ratio(self.s1, self.s1a), 100)
        self.assertEqual(fuzz.partial_token_sort_ratio(self.s4, self.s5), 100)

    def testTokenSetRatio(self):
        self.assertEqual(fuzz.token_set_ratio(self.s4, self.s5),100)

    def testPartialTokenSetRatio(self):
        self.assertEqual(fuzz.partial_token_set_ratio(self.s4, self.s5),100)

    def testQuickRatioEqual(self):
        self.assertEqual(fuzz.QRatio(self.s1, self.s1a), 100)

    def testQuickRatioCaseInsensitive(self):
        self.assertEqual(fuzz.QRatio(self.s1, self.s2), 100)

    def testQuickRatioNotEqual(self):
        self.assertNotEqual(fuzz.QRatio(self.s1, self.s3), 100)

    def testWRatioEqual(self):
        self.assertEqual(fuzz.WRatio(self.s1, self.s1a), 100)

    def testWRatioCaseInsensitive(self):
        self.assertEqual(fuzz.WRatio(self.s1, self.s2), 100)

    def testWRatioPartialMatch(self):
        # a partial match is scaled by .9
        self.assertEqual(fuzz.WRatio(self.s1, self.s3), 90)

    def testWRatioMisorderedMatch(self):
        # misordered full matches are scaled by .95
        self.assertEqual(fuzz.WRatio(self.s4, self.s5), 95)

    def testWRatioUnicode(self):
        self.assertEqual(fuzz.WRatio(self.s1, self.s1a), 100)

    def testQRatioUnicode(self):
        self.assertEqual(fuzz.WRatio(self.s1, self.s1a), 100)


@pytest.mark.parametrize("scorer", scorers)
def test_empty_string(scorer):
    """
    when both strings are empty this is a perfect match
    """
    assert scorer("", "") == 100


@pytest.mark.parametrize("scorer", scorers)
def test_none_string(scorer):
    """
    when None is passed to a scorer the result should always be 0
    """
    assert scorer("test", None) == 0
    assert scorer(None, "test") == 0

@pytest.mark.parametrize("scorer", scorers)
def test_simple_unicode_tests(scorer):
    """
    some very simple tests using unicode with scorers
    to catch relatively obvious implementation errors
    """
    s1 = u"ÁÄ"
    s2 = "ABCD"
    assert scorer(s1, s2) == 0
    assert scorer(s1, s1) == 100


@pytest.mark.parametrize("processor", [True, utils.default_process, lambda s: utils.default_process(s)])
@pytest.mark.parametrize("scorer", scorers)
def test_scorer_case_insensitive(processor, scorer):
    """
    each scorer should be able to preprocess strings properly
    """
    assert scorer(RatioTest.s1, RatioTest.s2, processor=processor) == 100


@pytest.mark.parametrize("processor", [False, None, lambda s: s])
def test_ratio_case_censitive(processor):
    assert fuzz.ratio(RatioTest.s1, RatioTest.s2, processor=processor) != 100


@pytest.mark.parametrize("scorer", scorers)
def test_custom_processor(scorer):
    """
    Any scorer should accept any type as s1 and s2, as long as it is a string
    after preprocessing.
    """
    s1 = ["chicago cubs vs new york mets", "CitiField", "2011-05-11", "8pm"]
    s2 = ["chicago cubs vs new york mets", "CitiFields", "2012-05-11", "9pm"]
    s3 = ["different string", "CitiFields", "2012-05-11", "9pm"]
    assert scorer(s1, s2, processor=lambda event: event[0]) == 100
    assert scorer(s2, s3, processor=lambda event: event[0]) != 100


@pytest.mark.parametrize("scorer", scorers)
def test_help(scorer):
    """
    test that all help texts can be printed without throwing an exception,
    since they are implemented in C++ aswell
    """
    help(scorer)

if __name__ == '__main__':
    unittest.main()