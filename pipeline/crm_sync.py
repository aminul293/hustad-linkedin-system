# -*- coding: utf-8 -*-
"""
CRM Sync Bridge for Hustad LinkedIn System.
Formats active outreach targets and engagement history for CRM synchronization (HubSpot, Salesforce, Pipedrive).
"""
import os, sys, csv
from typing import Dict, Any, List

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import paths

def export_crm_payload() -> Dict[str, Any]:
    """Export formatted contact records with outreach status for CRM integration."""
    plan_path = paths.s(paths.PLAN_FINAL)
    if not os.path.exists(plan_path):
        plan_path = paths.s(paths.SAMPLE_PLAN)

    records: List[Dict[str, Any]] = []
    if os.path.exists(plan_path):
        with open(plan_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                records.append({
                    'contact_id': r.get('url_key'),
                    'first_name': r.get('first_name'),
                    'last_name': r.get('last_name'),
                    'title': r.get('title'),
                    'company': r.get('company'),
                    'segment': r.get('segment'),
                    'tier': r.get('tier'),
                    'linkedin_url': r.get('url_key'),
                    'touch1_date': r.get('touch1_date'),
                    'touch2_date': r.get('touch2_date'),
                    'touch3_date': r.get('touch3_date'),
                    'opener_type': r.get('opener_type', 'standard'),
                    'replied': r.get('replied', 'false') == 'true'
                })

    return {
        'ok': True,
        'count': len(records),
        'contacts': records
    }
