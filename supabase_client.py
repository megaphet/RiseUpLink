import os
try:
    from supabase import create_client
except Exception:
    create_client = None

# Read config from env
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
_client = None
if SUPABASE_URL and SUPABASE_KEY and create_client:
    try:
        _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        _client = None


def _data_from_res(res):
    # Support older/newer supabase-py return shapes
    if res is None:
        return None
    if hasattr(res, 'data'):
        return res.data
    try:
        return res.get('data')
    except Exception:
        return None


# --- YouTube helpers ---
def get_main_youtube_video():
    if not _client:
        return None
    try:
        res = _client.table('you_tube_video').select('*').eq('is_main', True).limit(1).execute()
        data = _data_from_res(res)
        if data:
            return data[0]
    except Exception:
        return None
    return None


def list_youtube_videos(order_by='created_at', desc=True):
    if not _client:
        return []
    try:
        q = _client.table('you_tube_video').select('*')
        if order_by:
            # supabase-py uses order(column, desc=True) in some versions
            try:
                q = q.order(order_by, desc=bool(desc))
            except Exception:
                try:
                    q = q.order(order_by + ('.desc' if desc else '.asc'))
                except Exception:
                    pass
        res = q.execute()
        data = _data_from_res(res)
        return data or []
    except Exception:
        return []


def get_youtube_video(id):
    if not _client:
        return None
    try:
        res = _client.table('you_tube_video').select('*').eq('id', int(id)).limit(1).execute()
        data = _data_from_res(res)
        if data:
            return data[0]
    except Exception:
        return None
    return None


def add_youtube_video(payload: dict):
    if not _client:
        return None
    try:
        if payload.get('is_main'):
            # clear existing mains
            try:
                _client.table('you_tube_video').update({'is_main': False}).neq('id', 0).execute()
            except Exception:
                pass
        res = _client.table('you_tube_video').insert(payload).execute()
        data = _data_from_res(res)
        if data:
            return data[0]
    except Exception:
        return None
    return None


def update_youtube_video(id, updates: dict):
    if not _client:
        return False
    try:
        if updates.get('is_main'):
            try:
                _client.table('you_tube_video').update({'is_main': False}).neq('id', int(id)).execute()
            except Exception:
                pass
        _client.table('you_tube_video').update(updates).eq('id', int(id)).execute()
        return True
    except Exception:
        return False


def delete_youtube_video(id):
    if not _client:
        return False
    try:
        _client.table('you_tube_video').delete().eq('id', int(id)).execute()
        return True
    except Exception:
        return False


# --- User helpers ---
def get_user_by_email(email):
    if not _client:
        return None
    try:
        res = _client.table('user').select('*').eq('email', email).limit(1).execute()
        data = _data_from_res(res)
        if data:
            return data[0]
    except Exception:
        return None
    return None


def get_user_by_id(uid):
    if not _client:
        return None
    try:
        res = _client.table('user').select('*').eq('id', int(uid)).limit(1).execute()
        data = _data_from_res(res)
        if data:
            return data[0]
    except Exception:
        return None
    return None


def create_user(payload: dict):
    if not _client:
        return None
    try:
        res = _client.table('user').insert(payload).execute()
        data = _data_from_res(res)
        if data:
            return data[0]
    except Exception:
        return None
    return None


# --- Profile helpers ---
def get_profile_by_user_id(user_id):
    if not _client:
        return None
    try:
        res = _client.table('youth_profile').select('*').eq('user_id', int(user_id)).limit(1).execute()
        data = _data_from_res(res)
        if data:
            return data[0]
    except Exception:
        return None
    return None


def create_profile(payload: dict):
    if not _client:
        return None
    try:
        res = _client.table('youth_profile').insert(payload).execute()
        data = _data_from_res(res)
        if data:
            return data[0]
    except Exception:
        return None
    return None


# --- Document helpers ---
def list_documents_by_youth(youth_id, limit=100):
    if not _client:
        return []
    try:
        res = _client.table('document').select('*').eq('youth_id', int(youth_id)).limit(int(limit)).execute()
        return _data_from_res(res) or []
    except Exception:
        return []


def add_document(payload: dict):
    if not _client:
        return None
    try:
        res = _client.table('document').insert(payload).execute()
        data = _data_from_res(res)
        if data:
            return data[0]
    except Exception:
        return None
    return None


# --- Recommendation helpers ---
def list_recommendations_by_youth(youth_id, limit=100):
    if not _client:
        return []
    try:
        res = _client.table('recommendation_letter').select('*').eq('youth_id', int(youth_id)).limit(int(limit)).execute()
        return _data_from_res(res) or []
    except Exception:
        return []


def add_recommendation(payload: dict):
    if not _client:
        return None
    try:
        res = _client.table('recommendation_letter').insert(payload).execute()
        data = _data_from_res(res)
        if data:
            return data[0]
    except Exception:
        return None
    return None


# --- Opportunity helpers ---
def list_opportunities(limit=100):
    if not _client:
        return []
    try:
        res = _client.table('opportunity').select('*').limit(int(limit)).execute()
        return _data_from_res(res) or []
    except Exception:
        return []


def get_opportunity_by_id(opp_id):
    if not _client:
        return None
    try:
        res = _client.table('opportunity').select('*').eq('id', int(opp_id)).limit(1).execute()
        data = _data_from_res(res)
        if data:
            return data[0]
    except Exception:
        return None
    return None


def add_opportunity(payload: dict):
    if not _client:
        return None
    try:
        res = _client.table('opportunity').insert(payload).execute()
        data = _data_from_res(res)
        if data:
            return data[0]
    except Exception:
        return None
    return None


def update_opportunity(opp_id, updates: dict):
    if not _client:
        return False
    try:
        _client.table('opportunity').update(updates).eq('id', int(opp_id)).execute()
        return True
    except Exception:
        return False


# --- Application helpers ---
def add_application(payload: dict):
    if not _client:
        return None
    try:
        res = _client.table('application').insert(payload).execute()
        data = _data_from_res(res)
        if data:
            return data[0]
    except Exception:
        return None
    return None


def list_applications_by_youth(youth_id, limit=100):
    if not _client:
        return []
    try:
        res = _client.table('application').select('*').eq('youth_id', int(youth_id)).limit(int(limit)).execute()
        return _data_from_res(res) or []
    except Exception:
        return []


# --- Notification helpers ---
def create_notification(payload: dict):
    if not _client:
        return None
    try:
        res = _client.table('notification').insert(payload).execute()
        data = _data_from_res(res)
        if data:
            return data[0]
    except Exception:
        return None
    return None


def list_notifications_by_user(user_id, limit=50):
    if not _client:
        return []
    try:
        q = _client.table('notification').select('*').eq('user_id', int(user_id))
        try:
            q = q.order('created_at', desc=True)
        except Exception:
            pass
        if limit:
            q = q.limit(int(limit))
        res = q.execute()
        return _data_from_res(res) or []
    except Exception:
        return []


def mark_notification_read(nid):
    if not _client:
        return False
    try:
        _client.table('notification').update({'is_read': True}).eq('id', int(nid)).execute()
        return True
    except Exception:
        return False


# --- Verification helpers ---
def get_latest_verification_by_youth(youth_id):
    if not _client:
        return None
    try:
        res = _client.table('verification').select('*').eq('youth_id', int(youth_id)).order('started_at', desc=True).limit(1).execute()
        data = _data_from_res(res)
        if data:
            return data[0]
    except Exception:
        return None
    return None
