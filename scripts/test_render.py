import os
import sys

# Ensure project root is importable when the script is executed from scripts/
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import app

if __name__ == '__main__':
    # Render dashboard template inside test request context to catch template errors
    with app.test_request_context('/dashboard'):
        from flask import render_template
        html = render_template('dashboard.html')
        print('--- Rendered dashboard length:', len(html))
        # Optionally write to a temp file for inspection
        with open('tmp_dashboard_render.html', 'w', encoding='utf-8') as f:
            f.write(html)
        print('Wrote tmp_dashboard_render.html')
