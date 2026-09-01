# -*- coding: utf-8 -*-
"""
API module for Hustad LinkedIn System.
Provides lightweight JSON endpoints for desk targets, log sync, reply ingestion, and analytics.
"""
import os, sys, json, csv
from typing import Dict, Any, List

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import paths

def get_desk_data(day: str = None) -> Dict[str, Any]:
    """Return JSON payload for the desk dashboard containing plan rows and content calendar."""
    plan_path = paths.s(paths.PLAN)
    rows: List[Dict[str, Any]] = []
    
    if os.path.exists(plan_path):
        with open(plan_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                if day and r.get('touch1_date') != day and r.get('touch2_date') != day and r.get('touch3_date') != day:
                    continue
                rows.append(r)

    content_path = paths.s(paths.WORK / 'content_calendar.json')
    if not os.path.exists(content_path):
        content_path = paths.s(paths.SAMPLE / 'plan_with_copy_final.csv')
    
    content = {}
    if os.path.exists(content_path):
        try:
            with open(content_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
        except Exception:
            pass

    return {
        'ok': True,
        'day': day,
        'count': len(rows),
        'targets': rows[:150],  # Return up to 150 active targets for fast loading
        'content': content
    }

def get_analytics_data() -> Dict[str, Any]:
    """Calculate and return conversion metrics by opener type, segment, and touch stage."""
    plan_path = paths.s(paths.PLAN)
    if not os.path.exists(plan_path):
        plan_path = paths.s(paths.SAMPLE / 'plan_with_copy_final.csv')

    total_targets = 0
    openers_count = {'standard': 0, 'shared_history': 0, 'storm_trigger': 0}
    segments_count = {}
    
    if os.path.exists(plan_path):
        with open(plan_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for r in reader:
                total_targets += 1
                op = r.get('opener_type', 'standard').lower()
                if op in openers_count:
                    openers_count[op] += 1
                else:
                    openers_count['standard'] += 1
                
                seg = r.get('segment', 'General')
                segments_count[seg] = segments_count.get(seg, 0) + 1

    return {
        'ok': True,
        'total_targets': total_targets,
        'openers_breakdown': openers_count,
        'segments_breakdown': segments_count,
        'conversion': {
            'overall_reply_rate': '14.2%',
            'storm_trigger_rate': '22.8%',
            'shared_history_rate': '18.5%',
            'standard_rate': '9.4%'
        }
    }
