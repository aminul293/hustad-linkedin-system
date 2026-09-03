# -*- coding: utf-8 -*-
"""
Test suite for Hybrid OpenAI AI Engine.

Validates:
1. OpenAI prompt formatting & error handling.
2. Graceful fallback when OPENAI_API_KEY is absent.
3. 12-rule QA linter compliance.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))

import copy_engine


class TestHybridAIEngine(unittest.TestCase):

    def test_llm_draft_fallback(self):
        # Without OPENAI_API_KEY, should return (None, 'No OPENAI_API_KEY configured')
        draft, status = copy_engine.generate_llm_draft("Katie", "Director", "Irvine Company")
        self.assertIsNone(draft)
        self.assertIn("No OPENAI_API_KEY", status)

    def test_qa_linter_validation(self):
        good_msg = (
            "Hi Katie,\n\n"
            "Holding 125 plus communities means your roofs cycle more than once under the same ownership.\n\n"
            "If it'd be useful, I'll send over a sample condition read from a recent acquisition?"
        )
        issues = copy_engine.qa(good_msg, company="Irvine Company")
        self.assertEqual(len(issues), 0, f"Expected PASS but got: {issues}")


if __name__ == '__main__':
    unittest.main()
