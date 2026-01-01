import traceback
import time
from pathlib import Path

LOG = Path('debug.log')
try:
    from app import app, USE_SUPABASE
    LOG.write_text(f'Starting app; USE_SUPABASE={USE_SUPABASE}\n')
    try:
        app.run(host='127.0.0.1', port=5000, debug=False, use_reloader=False)
    except Exception as e:
        LOG.write_text(LOG.read_text() + 'Exception during app.run:\n' + traceback.format_exc())
except Exception as e:
    LOG.write_text('Failed importing app:\n' + traceback.format_exc())
