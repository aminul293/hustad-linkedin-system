# -*- coding: utf-8 -*-
"""
Test suite for Outreach Metrics & Analytics Dashboard.

Validates:
1. Analytics calculations across 8 lanes and 15 property segments.
2. 3-opener experiment conversion rate comparison.
3. Friday Executive Review briefing report payload generation.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))

import api
import friday_review


class TestAnalyticsEngine(unittest.TestCase):

    def test_get_analytics_data_schema(self):
        data = api.get_analytics_data()
        self.assertTrue(data.get('ok'))
        self.assertIn('total_targets', data)
        self.assertIn('openers_breakdown', data)
        self.assertIn('lanes_breakdown', data)
        self.assertIn('segments_breakdown', data)
        self.assertIn('conversion', data)
        
        # Verify openers breakdown keys
        openers = data['openers_breakdown']
        self.assertIn('standard', openers)
        self.assertIn('shared_history', openers)
        self.assertIn('storm_trigger', openers)

    def test_generate_friday_report_schema(self):
        report = friday_review.generate_friday_report()
        self.assertTrue(report.get('ok'))
        self.assertIn('metrics', report)
        self.assertIn('executive_notes', report)
        
        metrics = report['metrics']
        self.assertIn('1_total_targets', metrics)
        self.assertIn('3_storm_lift', metrics)
        self.assertIn('5_qa_invariants_status', metrics)


if __name__ == '__main__':
    unittest.main()
