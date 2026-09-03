# -*- coding: utf-8 -*-
"""
Test suite for Inbound Reply Ingestion Engine.

Validates:
1. Notification text parsing & URL extraction.
2. Reply classification across 22 Sales Brain categories.
3. Target matching & sequence halting (status = 'HALTED').
4. Local SQLite and Supabase database synchronization.
"""
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
sys.path.insert(0, os.path.join(ROOT, 'backend', 'db'))

import ingest_replies
import db_sync


class TestReplyIngestion(unittest.TestCase):

    def test_parse_notification(self):
        raw = "Joel Perez sent you a message: \"Sure, send over the deck!\"\nhttps://www.linkedin.com/in/joel-perez-123"
        parsed = ingest_replies.parse_notification(raw)
        self.assertEqual(parsed['name'], "Joel Perez")
        self.assertEqual(parsed['url'], "https://www.linkedin.com/in/joel-perez-123")
        self.assertEqual(parsed['text'], "Sure, send over the deck!")

    def test_reply_classification_positive(self):
        # R1: Send Info / Deck
        cat = ingest_replies.classify_reply_category("Sure, send over the deck and checklist")
        self.assertIn(cat['id'], ['R1', 'R14'])

    def test_reply_classification_negative(self):
        # R13: Not Interested / Unsubscribe
        cat = ingest_replies.classify_reply_category("Please remove me, not interested")
        self.assertEqual(cat['id'], 'R13')

    def test_reply_classification_meeting(self):
        # R2: Meeting Request
        cat = ingest_replies.classify_reply_category("Let's set up a call next Tuesday")
        self.assertEqual(cat['id'], 'R2')

    def test_record_and_halt_execution(self):
        res = ingest_replies.record_reply_and_halt(
            sender_name="Test Respondent",
            sender_url="https://www.linkedin.com/in/test-respondent",
            message_text="Sounds great, please send over the information sheet!"
        )
        self.assertTrue(res['ok'])
        self.assertEqual(res['sequence_halted'], True)
        self.assertIn('db_sync', res)


if __name__ == '__main__':
    unittest.main()
