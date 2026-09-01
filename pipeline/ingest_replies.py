# -*- coding: utf-8 -*-
"""
Automated Reply Ingestion Engine for Hustad LinkedIn System.

Parses inbound LinkedIn notification emails or API webhooks, extracts sender details
and message body, matches against the master target roster, classifies the reply
into 1 of 22 categories (R1-R22), and automatically halts Touch 2 & Touch 3 follow-ups.
"""
import os
import sys
import re
import json
import csv
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import paths
import reply_engine

REPLY_LOG = paths.s(paths.WORK / 'reply_log.csv')


def parse_notification(raw_text):
    """
    Extract sender name, LinkedIn profile URL, and message body from an email notification or payload.
    """
    if isinstance(raw_text, dict):
        return {
            'name': raw_text.get('name', '').strip(),
            'url': raw_text.get('url', '').strip(),
            'text': raw_text.get('text', '').strip()
        }

    text = str(raw_text or '')
    
    # Extract LinkedIn URL
    url_m = re.search(r'https?://(?:www\.)?linkedin\.com/in/([a-zA-Z0-9_-]+)', text)
    profile_url = url_m.group(0) if url_m else ''

    # Extract Sender Name (e.g., "Joel Perez sent you a message" or "From: Joel Perez")
    name_m = re.search(r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s+(?:sent you a message|messaged you|commented)', text)
    if not name_m:
        name_m = re.search(r'From:\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)', text)
    sender_name = name_m.group(1) if name_m else ''

    # Extract Message Body Snippet
    body_m = re.search(r'["“]([^"”]+)["”]', text)
    msg_text = body_m.group(1).strip() if body_m else text.strip()

    return {
        'name': sender_name,
        'url': profile_url,
        'text': msg_text
    }


def classify_reply_category(msg_text):
    """
    Classify reply text against the 22 categories in reply_engine.REPLY_CATEGORIES.
    Returns the matching category dict or R14 default (general acknowledgment).
    """
    low = (msg_text or '').lower()

    best_match = None
    max_cues = 0

    for cat in reply_engine.REPLY_CATEGORIES:
        cues = [c.strip().lower() for c in cat.get('cues', '').split(',') if c.strip()]
        matched_count = sum(1 for c in cues if c in low)
        if matched_count > max_cues:
            max_cues = matched_count
            best_match = cat

    if not best_match:
        # Default fallback categorization based on sentiment indicators
        if any(w in low for w in ['no', 'stop', 'remove', 'not interested', 'pass']):
            best_match = next((c for c in reply_engine.REPLY_CATEGORIES if c['id'] == 'R13'), None)
        elif any(w in low for w in ['call', 'calendar', 'time', 'meet', 'talk']):
            best_match = next((c for c in reply_engine.REPLY_CATEGORIES if c['id'] == 'R2'), None)
        elif any(w in low for w in ['sure', 'send', 'yes', 'great', 'deck']):
            best_match = next((c for c in reply_engine.REPLY_CATEGORIES if c['id'] == 'R1'), None)
        else:
            best_match = next((c for c in reply_engine.REPLY_CATEGORIES if c['id'] == 'R14'), None)

    return best_match or reply_engine.REPLY_CATEGORIES[0]


def record_reply_and_halt(sender_url=None, sender_name=None, message_text='', category_id=None):
    """
    Match sender against master contacts / plan, update reply log, and halt Touch 2/3 follow-ups.
    """
    target_id = None
    company = None
    full_name = sender_name or ''
    matched_url = sender_url or ''

    plan_path = paths.s(paths.PLAN)
    master_path = paths.s(paths.MASTER)

    # 1. Match against master contacts or plan
    if os.path.exists(plan_path):
        import pandas as pd
        df = pd.read_csv(plan_path)
        
        # Match by URL first, then full name
        match = None
        if sender_url:
            clean_url = sender_url.lower().strip().rstrip('/')
            match = df[df['URL'].astype(str).str.lower().str.strip().str.rstrip('/') == clean_url]
        
        if (match is None or match.empty) and sender_name:
            match = df[df['full_name'].astype(str).str.lower() == sender_name.lower().strip()]
            
        if match is not None and not match.empty:
            row = match.iloc[0]
            target_id = row.get('target_id', '')
            full_name = row.get('full_name', full_name)
            company = row.get('Company', '')
            matched_url = row.get('URL', matched_url)

    # 2. Classify reply category
    category_info = None
    if category_id:
        category_info = next((c for c in reply_engine.REPLY_CATEGORIES if c['id'] == category_id), None)
    if not category_info:
        category_info = classify_reply_category(message_text)

    # 3. Append to reply_log.csv
    log_file = REPLY_LOG
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    
    file_exists = os.path.exists(log_file)
    with open(log_file, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(['timestamp', 'target_id', 'full_name', 'company', 'url', 'category_id', 'category_name', 'message_text', 'status'])
        writer.writerow([
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            target_id or 'UNKNOWN',
            full_name,
            company or '',
            matched_url,
            category_info['id'],
            category_info['category'],
            message_text,
            'HALTED'
        ])

    return {
        'ok': True,
        'target_id': target_id,
        'full_name': full_name,
        'company': company,
        'url': matched_url,
        'category': category_info['id'],
        'category_name': category_info['category'],
        'suggested_response': category_info['response'],
        'action': category_info['action'],
        'sequence_halted': True
    }


def ingest_reply(sender_email=None, sender_name=None, message_body='', sender_url=None):
    """
    Alias wrapper for record_reply_and_halt used by HTTP API endpoints.
    """
    parsed = parse_notification({
        'name': sender_name or '',
        'url': sender_url or '',
        'text': message_body or ''
    })
    return record_reply_and_halt(
        sender_url=parsed['url'],
        sender_name=parsed['name'],
        message_text=parsed['text']
    )


def get_ingested_replies():
    """
    Retrieve all ingested replies from reply_log.csv for the Desk UI.
    """
    if not os.path.exists(REPLY_LOG):
        return []
    
    replies = []
    with open(REPLY_LOG, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for r in reader:
            replies.append(r)
    return replies
