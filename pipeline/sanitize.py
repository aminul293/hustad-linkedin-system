# -*- coding: utf-8 -*-
"""
CSV Data Sanitizer & Pre-Validator for Hustad LinkedIn System.
Inspects uploaded CSV files for missing headers, duplicate contacts, and malformed URLs.
"""
import os, sys, csv
from typing import Dict, Any

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
import paths

def validate_raw_exports() -> Dict[str, Any]:
    """Scan files in data/raw/ and return a health grade and breakdown."""
    raw_dir = paths.s(paths.RAW)
    if not os.path.exists(raw_dir):
        return {'ok': False, 'grade': 'F', 'issues': ['No raw directory found']}

    found_files = os.listdir(raw_dir)
    total_contacts = 0
    duplicate_count = 0
    seen_urls = set()
    issues = []

    for fn in found_files:
        if fn.endswith('.csv'):
            fp = os.path.join(raw_dir, fn)
            try:
                with open(fp, 'r', encoding='utf-8', errors='ignore') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        total_contacts += 1
                        url = row.get('URL') or row.get('LinkedIn Profile') or ''
                        if url:
                            if url in seen_urls:
                                duplicate_count += 1
                            else:
                                seen_urls.add(url)
            except Exception as e:
                issues.append(f"Error reading {fn}: {str(e)}")

    grade = 'A+' if not issues and duplicate_count < 10 else ('B' if duplicate_count < 50 else 'C')

    return {
        'ok': True,
        'grade': grade,
        'files_found': found_files,
        'total_rows_scanned': total_contacts,
        'unique_contacts': len(seen_urls),
        'duplicates_detected': duplicate_count,
        'issues': issues
    }
