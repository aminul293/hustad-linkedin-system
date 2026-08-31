# -*- coding: utf-8 -*-
"""
Automated reply ingestion module for Hustad LinkedIn System.
Parses inbound reply payloads (Outlook Graph API / Webhook), matches to target records,
sets replied status, and halts downstream touch 2 / touch 3 messages automatically.
"""
import os, sys, json, csv
from typing import Dict, Any, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import paths

def ingest_reply(sender_email: str = "", sender_name: str = "", message_body: str = "") -> Dict[str, Any]:
    """
    Match an inbound message to a target in master_contacts / plan_with_copy_final,
    mark them as replied, and halt future touches.
    """
    plan_path = paths.s(paths.PLAN_FINAL)
    if not os.path.exists(plan_path):
        return {'ok': False, 'message': 'No active plan file found'}

    matched_target = None
    rows = []
    
    with open(plan_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for r in reader:
            # Check match by name or email or profile
            full_name = f"{r.get('first_name', '')} {r.get('last_name', '')}".strip()
            if (sender_name and sender_name.lower() in full_name.lower()) or \
               (sender_email and sender_email.lower() == r.get('email', '').lower()):
                r['replied'] = 'true'
                matched_target = r
            rows.append(r)

    if matched_target:
        # Write back updated rows to halt sequence
        with open(plan_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
            
        return {
            'ok': True,
            'matched': True,
            'target_id': matched_target.get('url_key'),
            'target_name': f"{matched_target.get('first_name')} {matched_target.get('last_name')}",
            'company': matched_target.get('company'),
            'status': 'Sequence halted successfully'
        }

    return {
        'ok': True,
        'matched': False,
        'message': 'No matching target found for sender'
    }
