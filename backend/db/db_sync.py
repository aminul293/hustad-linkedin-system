# -*- coding: utf-8 -*-
"""
Database Sync Engine for Hustad LinkedIn System.

Synchronizes send ticks, reply classifications, and content calendar status
to a Postgres / Supabase database or local SQLite backup store.
"""
import os
import sys
import json
import sqlite3
import urllib.request
import urllib.parse
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DB_PATH = os.path.join(ROOT, 'data', 'work', 'hustad_desk.db')

SUPABASE_URL = os.environ.get('SUPABASE_URL', '')
SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY', '')


def init_local_sqlite():
    """Ensure local SQLite fallback database tables exist."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute('''
        CREATE TABLE IF NOT EXISTS send_log (
            target_id TEXT NOT NULL,
            touch INTEGER NOT NULL,
            send_date TEXT,
            name TEXT,
            company TEXT,
            status TEXT DEFAULT 'pending',
            sent_at TEXT,
            opener TEXT,
            past_employer TEXT,
            note TEXT,
            updated_at TEXT,
            PRIMARY KEY (target_id, touch)
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS reply_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            target_id TEXT,
            full_name TEXT,
            company TEXT,
            url TEXT,
            category_id TEXT,
            category_name TEXT,
            message_text TEXT,
            status TEXT DEFAULT 'HALTED'
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS content_log (
            content_id TEXT PRIMARY KEY,
            done INTEGER DEFAULT 0,
            at TEXT,
            status TEXT,
            note TEXT,
            updated_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()


def sync_send_entry(entry):
    """
    Upsert target send entry to DB store.
    """
    if not entry or not entry.get('id') or not entry.get('touch'):
        return {'ok': False, 'error': 'Invalid entry payload'}

    target_id = entry['id']
    touch = int(entry['touch'])
    send_date = entry.get('date', '')
    name = entry.get('name', '')
    company = entry.get('company', '')
    done = bool(entry.get('done'))
    reply = bool(entry.get('reply'))
    
    status = 'sent' if done else ('replied' if reply else 'pending')
    sent_at = entry.get('at', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    opener = entry.get('opener', 'standard')
    past_employer = entry.get('pe', '')
    note = entry.get('note', '')
    updated_at = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # 1. Write to local SQLite
    init_local_sqlite()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO send_log (target_id, touch, send_date, name, company, status, sent_at, opener, past_employer, note, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(target_id, touch) DO UPDATE SET
            status = excluded.status,
            sent_at = excluded.sent_at,
            opener = excluded.opener,
            past_employer = excluded.past_employer,
            note = excluded.note,
            updated_at = excluded.updated_at
    ''', (target_id, touch, send_date, name, company, status, sent_at, opener, past_employer, note, updated_at))
    conn.commit()
    conn.close()

    # 2. Remote Supabase REST API sync if credentials set
    remote_synced = False
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/send_log"
            headers = {
                'apikey': SUPABASE_KEY,
                'Authorization': f'Bearer {SUPABASE_KEY}',
                'Content-Type': 'application/json',
                'Prefer': 'resolution=merge-duplicates'
            }
            data = json.dumps([{
                'target_id': target_id,
                'touch': touch,
                'send_date': send_date,
                'name': name,
                'company': company,
                'status': status,
                'sent_at': sent_at,
                'opener': opener,
                'past_employer': past_employer,
                'note': note
            }]).encode('utf-8')
            
            req = urllib.request.Request(url, data=data, headers=headers, method='POST')
            with urllib.request.urlopen(req) as resp:
                if resp.status in (200, 201):
                    remote_synced = True
        except Exception as e:
            pass

    return {
        'ok': True,
        'target_id': target_id,
        'touch': touch,
        'status': status,
        'sqlite_synced': True,
        'remote_synced': remote_synced
    }


def fetch_all_entries():
    """
    Fetch all send_log entries from DB store for merging with browser state.
    """
    init_local_sqlite()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute('SELECT * FROM send_log')
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    
    entries = {}
    for r in rows:
        key = f"{r['target_id']}|{r['touch']}"
        entries[key] = {
            'id': r['target_id'],
            'touch': r['touch'],
            'date': r['send_date'],
            'name': r['name'],
            'company': r['company'],
            'done': r['status'] == 'sent',
            'reply': 1 if r['status'] == 'replied' else 0,
            'at': r['sent_at'],
            'opener': r['opener'],
            'pe': r['past_employer'],
            'note': r['note']
        }
    return entries
