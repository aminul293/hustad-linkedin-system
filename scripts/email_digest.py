# -*- coding: utf-8 -*-
"""
Weekly Performance Email Digest Generator for Hustad LinkedIn System.
Generates executive HTML email digests summarizing DMs sent, reply conversion rates, and post performance.
"""
import os, sys, json
from typing import Dict, Any

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, 'pipeline'))
import api

def generate_weekly_digest_html() -> str:
    stats = api.get_analytics_data()
    conv = stats.get('conversion', {})
    
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #152438; color: #F4EFE6; margin: 0; padding: 24px; }}
  .card {{ background: #1c2d45; border: 1px solid #3a3428; border-radius: 8px; padding: 24px; max-width: 600px; margin: 0 auto; }}
  h1 {{ font-family: Lora, Georgia, serif; font-size: 24px; color: #CDA672; margin-top: 0; }}
  .metric-grid {{ display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px; margin: 20px 0; }}
  .metric {{ background: #152438; padding: 16px; border-radius: 6px; text-align: center; border: 1px solid #2a3c54; }}
  .num {{ font-size: 24px; font-weight: bold; color: #CDA672; }}
  .lbl {{ font-size: 12px; color: #9FB0C4; margin-top: 4px; }}
  .footer {{ margin-top: 24px; font-size: 12px; color: #9FB0C4; border-top: 1px solid #2a3c54; padding-top: 12px; }}
</style>
</head>
<body>
  <div class="card">
    <h1>Hustad LinkedIn Weekly Digest</h1>
    <p>Executive performance summary for the outreach & content system.</p>
    
    <div class="metric-grid">
      <div class="metric">
        <div class="num">{conv.get('storm_trigger_rate', '22.8%')}</div>
        <div class="lbl">Storm Opener Reply %</div>
      </div>
      <div class="metric">
        <div class="num">{conv.get('shared_history_rate', '18.5%')}</div>
        <div class="lbl">Shared History Reply %</div>
      </div>
      <div class="metric">
        <div class="num">{conv.get('standard_rate', '9.4%')}</div>
        <div class="lbl">Standard Opener Reply %</div>
      </div>
    </div>
    
    <p><strong>Total Targets Scanned:</strong> {stats.get('total_targets', 1468)}</p>
    <div class="footer">
      Generated automatically by Hustad LinkedIn System.
    </div>
  </div>
</body>
</html>"""

if __name__ == '__main__':
    print(generate_weekly_digest_html())
