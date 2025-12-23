import os
import tempfile
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory
from urllib.parse import urlparse, parse_qs, urljoin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_migrate import Migrate
from flask_wtf import CSRFProtect
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin

BASE_DIR = os.path.dirname(__file__)
# Prefer an explicit environment override for upload path (useful in production)
_static_upload = os.path.join(BASE_DIR, 'static', 'uploads')
UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER')

if not UPLOAD_FOLDER:
    # Try to use the repo's static/uploads for local/dev. If that's read-only
    # (serverless), fall back to the system temp directory which is writable.
    try:
        os.makedirs(_static_upload, exist_ok=True)
        UPLOAD_FOLDER = _static_upload
    except OSError:
        UPLOAD_FOLDER = os.path.join(tempfile.gettempdir(), 'riseup_uploads')
        try:
            os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        except Exception:
            # Best-effort only: if even /tmp can't be created, keep the path
            # and let file operations handle runtime errors instead of crashing
            # at import time.
            pass

app = Flask(__name__)
# Determine DB URI: prefer env var `DATABASE_URL` or `SQLALCHEMY_DATABASE_URI`.
# If none provided, attempt to use a writable sqlite file in the repo; if
# that's not writable (serverless), fall back to a tmp sqlite file, then
# to in-memory as a last resort.
db_uri = os.environ.get('DATABASE_URL') or os.environ.get('SQLALCHEMY_DATABASE_URI')
if not db_uri:
    candidate = os.path.join(BASE_DIR, 'riseup.db')
    try:
        # ensure we can create or open the file
        os.makedirs(os.path.dirname(candidate), exist_ok=True)
        with open(candidate, 'a'):
            pass
        db_uri = 'sqlite:///' + candidate
    except Exception:
        tmp_db = os.path.join(tempfile.gettempdir(), 'riseup.db')
        try:
            with open(tmp_db, 'a'):
                pass
            db_uri = 'sqlite:///' + tmp_db
        except Exception:
            db_uri = 'sqlite:///:memory:'

app.config['SQLALCHEMY_DATABASE_URI'] = db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'change-this-secret-in-production'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Import models which create the `db` instance, then initialize it with `app`.
import models
db = models.db
db.init_app(app)

migrate = Migrate(app, db)
csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Auto-initialize database tables when running in environments where
# migrations are not applied (serverless deployments). Controlled by
# `AUTO_INIT_DB` env var; set to '0' in production to disable.
if os.environ.get('AUTO_INIT_DB', '1') != '0':
    try:
        with app.app_context():
            db.create_all()
    except Exception as _e:
        app.logger.warning('AUTO_INIT_DB: failed to create tables: %s', _e)

from models import User, YouthProfile, Document, RecommendationLetter, Verification, FieldVisit, Opportunity, Application, Notification, YouTubeVideo
import smtplib
from email.message import EmailMessage

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


def is_safe_url(target):
    try:
        host_url = request.host_url
        ref_url = urlparse(host_url)
        test_url = urlparse(urljoin(host_url, target))
        return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc
    except Exception:
        return False

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/features')
def features():
    return render_template('features.html')


@app.route('/media')
def media():
    # Build a list of uploaded image URLs to display in the gallery
    uploads = []
    try:
        for fname in sorted(os.listdir(app.config['UPLOAD_FOLDER'])):
            if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg')):
                uploads.append(url_for('uploaded_file', filename=fname))
    except Exception:
        uploads = []
    # try DB-backed YouTube videos first
    main_video = None
    try:
        mv = YouTubeVideo.query.filter_by(is_main=True).first()
        if mv:
            main_video = {'id': mv.id, 'title': mv.title, 'description': mv.description, 'link': mv.link, 'youtube_id': mv.youtube_id, 'is_main': mv.is_main}
    except Exception:
        main_video = None

    # fallback: try to load from JSON file (legacy)
    if not main_video:
        yt_path = os.path.join(BASE_DIR, 'youtube_videos.json')
        try:
            import json
            with open(yt_path, 'r', encoding='utf-8') as f:
                vids = json.load(f)
            for v in vids:
                if v.get('is_main'):
                    main_video = v
                    break
        except Exception:
            main_video = None

    return render_template('media.html', uploads=uploads, main_video=main_video)


@app.route('/admin/media', methods=['GET', 'POST'])
@login_required
def admin_media():
    if current_user.role != 'admin':
        flash('Admin only', 'danger')
        return redirect(url_for('dashboard'))
    # Simple file-backed metadata storage for media and youtube videos
    meta_path = os.path.join(BASE_DIR, 'media_meta.json')
    yt_path = os.path.join(BASE_DIR, 'youtube_videos.json')

    # Ensure metadata files exist
    try:
        if not os.path.exists(meta_path):
            with open(meta_path, 'w', encoding='utf-8') as f:
                f.write('{}')
        if not os.path.exists(yt_path):
            with open(yt_path, 'w', encoding='utf-8') as f:
                f.write('[]')
    except Exception:
        pass

    import json

    if request.method == 'POST':
        file = request.files.get('media')
        title = request.form.get('title', '')
        description = request.form.get('description', '')
        if file:
            filename = secure_filename(f"media_{int(datetime.utcnow().timestamp())}_{file.filename}")
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            # store metadata
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
            except Exception:
                meta = {}
            meta[filename] = {'title': title, 'description': description}
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)
            flash('Media uploaded', 'success')
            return redirect(url_for('admin_media'))

    # Build uploads list with metadata
    uploads = []
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
    except Exception:
        meta = {}

    try:
        for fname in sorted(os.listdir(app.config['UPLOAD_FOLDER'])):
            if fname.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.svg', '.mp4', '.mov')):
                item = {'filename': fname, 'title': meta.get(fname, {}).get('title', ''), 'description': meta.get(fname, {}).get('description', '')}
                uploads.append(item)
    except Exception:
        uploads = []

    # Load YouTube videos from DB (fall back to JSON)
    youtube_videos = []
    try:
        for yv in YouTubeVideo.query.order_by(YouTubeVideo.created_at.desc()).all():
            youtube_videos.append({'id': yv.id, 'title': yv.title, 'description': yv.description, 'link': yv.link, 'youtube_id': yv.youtube_id, 'is_main': yv.is_main})
        # fallback to legacy JSON if none in DB
        if not youtube_videos:
            try:
                with open(yt_path, 'r', encoding='utf-8') as f:
                    youtube_videos = json.load(f)
            except Exception:
                youtube_videos = []
    except Exception:
        youtube_videos = []

    return render_template('admin_media.html', uploads=uploads, youtube_videos=youtube_videos)


@app.route('/admin/media/update/<path:filename>', methods=['POST'])
@login_required
def admin_update_media(filename):
    if current_user.role != 'admin':
        flash('Admin only', 'danger')
        return redirect(url_for('dashboard'))
    title = request.form.get('title', '')
    description = request.form.get('description', '')
    meta_path = os.path.join(BASE_DIR, 'media_meta.json')
    import json
    try:
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
    except Exception:
        meta = {}
    meta[filename] = {'title': title, 'description': description}
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    flash('Media metadata updated', 'success')
    return redirect(url_for('admin_media'))


@app.route('/admin/video/update/<int:vid>', methods=['POST'])
@login_required
def admin_update_video(vid):
    if current_user.role != 'admin':
        flash('Admin only', 'danger')
        return redirect(url_for('dashboard'))
    title = request.form.get('title', '')
    description = request.form.get('description', '')
    link = request.form.get('link', '')
    # update DB-backed YouTubeVideo when present
    try:
        yv = YouTubeVideo.query.get(int(vid))
        if not yv:
            flash('Video not found', 'warning')
            return redirect(url_for('admin_media'))
        yv.title = title
        yv.description = description
        yv.link = link
        # update youtube_id when link changes
        try:
            yid = None
            parsed = urlparse(link)
            if parsed.hostname and 'youtu' in parsed.hostname:
                qs = parse_qs(parsed.query)
                if 'v' in qs:
                    yid = qs['v'][0]
                else:
                    parts = parsed.path.split('/')
                    if parts:
                        yid = parts[-1]
            yv.youtube_id = yid
        except Exception:
            pass
        db.session.commit()
        flash('Video updated', 'success')
    except Exception:
        flash('Failed to update video', 'warning')
    return redirect(url_for('admin_media'))


@app.route('/admin/video/delete/<int:vid>', methods=['POST'])
@login_required
def delete_video(vid):
    if current_user.role != 'admin':
        flash('Admin only', 'danger')
        return redirect(url_for('dashboard'))
    try:
        yv = YouTubeVideo.query.get_or_404(int(vid))
        db.session.delete(yv)
        db.session.commit()
        flash('Video deleted', 'success')
    except Exception:
        flash('Failed to delete video', 'warning')
    return redirect(url_for('admin_media'))


@app.route('/admin/video/add', methods=['POST'])
@login_required
def admin_add_video():
    if current_user.role != 'admin':
        flash('Admin only', 'danger')
        return redirect(url_for('dashboard'))
    title = request.form.get('title', '')
    description = request.form.get('description', '')
    link = request.form.get('link', '')
    # extract youtube id when possible
    yid = None
    try:
        parsed = urlparse(link)
        if parsed.hostname and 'youtu' in parsed.hostname:
            qs = parse_qs(parsed.query)
            if 'v' in qs:
                yid = qs['v'][0]
            else:
                parts = parsed.path.split('/')
                if parts:
                    yid = parts[-1]
    except Exception:
        yid = None

    # set is_main True if no main exists yet
    is_main = False
    try:
        if YouTubeVideo.query.filter_by(is_main=True).count() == 0:
            is_main = True
    except Exception:
        is_main = False

    try:
        if is_main:
            # ensure only one main
            for other in YouTubeVideo.query.filter_by(is_main=True).all():
                other.is_main = False
        yv = YouTubeVideo(youtube_id=yid, title=title, description=description, link=link, is_main=is_main)
        db.session.add(yv)
        db.session.commit()
        flash('YouTube video added', 'success')
    except Exception as e:
        app.logger.warning('Failed to add YouTube video: %s', e)
        flash('Failed to add video', 'danger')
    return redirect(url_for('admin_media'))


@app.route('/admin/video/mark_main/<int:vid>', methods=['POST'])
@login_required
def admin_mark_main(vid):
    if current_user.role != 'admin':
        flash('Admin only', 'danger')
        return redirect(url_for('dashboard'))
    try:
        # clear existing main flags
        for v in YouTubeVideo.query.filter_by(is_main=True).all():
            v.is_main = False
        yv = YouTubeVideo.query.get_or_404(int(vid))
        yv.is_main = True
        db.session.commit()
        flash('Main video updated', 'success')
    except Exception as e:
        app.logger.warning('Failed to mark main video: %s', e)
        flash('Video not found', 'warning')
    return redirect(url_for('admin_media'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        full_name = request.form['full_name']
        phone_number = request.form.get('phone_number', '')
        whatsapp_number = request.form.get('whatsapp_number', '')
        password = request.form['password']
        role = request.form['role']
        preferred_contact = request.form.get('preferred_contact', 'email')
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect(url_for('register', next=request.args.get('next')))
        user = User(
            email=email, 
            full_name=full_name, 
            phone_number=phone_number if phone_number else None,
            whatsapp_number=whatsapp_number if whatsapp_number else None,
            preferred_contact=preferred_contact,
            role=role
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful. Please log in.', 'success')
        next_url = request.args.get('next') or request.form.get('next')
        if next_url:
            return redirect(url_for('login', next=next_url))
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in', 'success')
            # Prefer explicit `next` value if present and safe
            next_url = request.form.get('next') or request.args.get('next')
            if next_url and is_safe_url(next_url):
                return redirect(next_url)
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')


@app.route('/login_prompt')
def login_prompt():
    # Simple prompt page asking user to login or register; preserves `next`
    next_url = request.args.get('next') or ''
    return render_template('login_prompt.html', next=next_url)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('index'))

@app.route('/dashboard')
@login_required
def dashboard():
    role = current_user.role
    if role == 'youth':
        profile = YouthProfile.query.filter_by(user_id=current_user.id).first()
        applications = []
        if profile:
            applications = Application.query.filter_by(youth_id=profile.id).all()
        # recent opportunities and notifications for youth
        recent_opps = Opportunity.query.filter_by(is_active=True).order_by(Opportunity.posted_at.desc()).limit(5).all()
        unread_notifications = []
        try:
            unread_notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).limit(10).all()
        except Exception:
            # Notification table may not exist yet (migrations not run)
            pass
        return render_template('dashboard_youth.html', profile=profile, applications=applications, recent_opps=recent_opps, notifications=unread_notifications)
    elif role == 'donor':
        opportunities = Opportunity.query.filter_by(posted_by=current_user.id).all()
        return render_template('dashboard_donor.html', opportunities=opportunities)
    elif role == 'admin':
        verifs = Verification.query.order_by(Verification.started_at.desc()).all()
        return render_template('dashboard_admin.html', verifications=verifs)
    elif role == 'field':
        pending = Verification.query.filter_by(status='PendingField').all()
        return render_template('dashboard_field.html', verifications=pending)
    else:
        flash('Unknown role', 'warning')
        return redirect(url_for('index'))

@app.route('/profile/create', methods=['GET', 'POST'])
@login_required
def create_profile():
    if current_user.role != 'youth':
        flash('Only youth can create profiles', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        category = request.form['category']
        country = request.form['country']
        community = request.form['community']
        whatsapp_number = request.form.get('whatsapp_number', '')
        preferred_feedback = request.form.get('preferred_feedback', 'email')
        profile = YouthProfile(
            user_id=current_user.id, 
            category=category, 
            country=country, 
            community=community,
            whatsapp_number=whatsapp_number if whatsapp_number else None,
            preferred_feedback=preferred_feedback,
            profile_completed=True
        )
        db.session.add(profile)
        db.session.commit()
        try:
            from notifications import create_in_app_notification
            create_in_app_notification(current_user.id, 'Profile created', 'Your youth profile was created successfully.')
        except Exception:
            pass
        flash('Profile created', 'success')
        return redirect(url_for('dashboard'))
    return render_template('create_profile.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/notifications')
@login_required
def list_notifications():
    notes = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.created_at.desc()).all()
    return render_template('notifications.html', notifications=notes)


@app.route('/notifications/mark_read/<int:nid>', methods=['POST'])
@login_required
def mark_notification_read(nid):
    n = Notification.query.get_or_404(nid)
    if n.user_id != current_user.id:
        flash('Not authorized', 'danger')
        return redirect(url_for('list_notifications'))
    n.is_read = True
    db.session.commit()
    return redirect(url_for('list_notifications'))


@app.route('/admin/media/delete/<path:filename>', methods=['POST'])
@login_required
def delete_media(filename):
    if current_user.role != 'admin':
        flash('Admin only', 'danger')
        return redirect(url_for('dashboard'))
    safe_name = secure_filename(filename)
    path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
    if os.path.exists(path):
        try:
            os.remove(path)
            flash('Media deleted', 'success')
        except Exception as e:
            app.logger.warning('Failed to delete file: %s', e)
            flash('Failed to delete file', 'danger')
    else:
        flash('File not found', 'warning')
    return redirect(url_for('admin_media'))


@app.route('/assets/images/<path:filename>')
def assets_images(filename):
    # Serve image assets stored under templates/assets/images without moving them
    assets_dir = os.path.join(BASE_DIR, 'templates', 'assets', 'images')
    return send_from_directory(assets_dir, filename)

@app.route('/documents/upload', methods=['GET', 'POST'])
@login_required
def upload_documents():
    if current_user.role != 'youth':
        flash('Only youth can upload documents', 'danger')
        return redirect(url_for('dashboard'))
    profile = YouthProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        flash('Create profile first', 'warning')
        return redirect(url_for('create_profile'))
    if request.method == 'POST':
        file = request.files.get('document')
        dtype = request.form.get('doc_type')
        if file:
            filename = f"{current_user.id}_{int(datetime.utcnow().timestamp())}_{file.filename}"
            path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(path)
            doc = Document(youth_id=profile.id, type=dtype, file_url=filename, uploaded_at=datetime.utcnow(), validated=False)
            db.session.add(doc)
            db.session.commit()
            try:
                from notifications import create_in_app_notification
                create_in_app_notification(current_user.id, 'Document uploaded', f'Your document "{filename}" was uploaded and is awaiting validation.', link=url_for('upload_documents'))
            except Exception:
                pass
            flash('Document uploaded', 'success')
            return redirect(url_for('upload_documents'))
    docs = Document.query.filter_by(youth_id=profile.id).all()
    recs = RecommendationLetter.query.filter_by(youth_id=profile.id).all()
    return render_template('upload_documents.html', docs=docs, recs=recs)

@app.route('/recommendation/upload', methods=['POST'])
@login_required
def upload_recommendation():
    if current_user.role != 'youth':
        flash('Only youth can upload recommendation letters', 'danger')
        return redirect(url_for('dashboard'))
    profile = YouthProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        flash('Create profile first', 'warning')
        return redirect(url_for('create_profile'))
    file = request.files.get('recommendation')
    issuer = request.form.get('issuer')
    issuer_role = request.form.get('issuer_role')
    contact = request.form.get('contact')
    if file:
        filename = f"{current_user.id}_rec_{int(datetime.utcnow().timestamp())}_{file.filename}"
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(path)
        rec = RecommendationLetter(youth_id=profile.id, issuer_name=issuer, issuer_role=issuer_role, contact_info=contact, file_url=filename, uploaded_at=datetime.utcnow(), validated=False)
        db.session.add(rec)
        db.session.commit()
        try:
            from notifications import create_in_app_notification
            create_in_app_notification(current_user.id, 'Recommendation uploaded', f'Recommendation from {issuer} uploaded and awaiting review.', link=url_for('upload_documents'))
        except Exception:
            pass
        flash('Recommendation uploaded', 'success')
    return redirect(url_for('upload_documents'))

@app.route('/verification/submit', methods=['POST'])
@login_required
def submit_verification():
    if current_user.role != 'youth':
        flash('Only youth can submit for verification', 'danger')
        return redirect(url_for('dashboard'))
    profile = YouthProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        flash('Create profile first', 'warning')
        return redirect(url_for('create_profile'))
    # create verification
    v = Verification(youth_id=profile.id, status='Pending', started_at=datetime.utcnow())
    db.session.add(v)
    db.session.commit()
    flash('Submitted for verification', 'success')
    return redirect(url_for('dashboard'))

@app.route('/admin/verifications')
@login_required
def admin_verifications():
    if current_user.role != 'admin':
        flash('Admin only', 'danger')
        return redirect(url_for('dashboard'))
    verifs = Verification.query.order_by(Verification.started_at.desc()).all()
    return render_template('admin_verifications.html', verifications=verifs)

@app.route('/admin/verify/<int:vid>/<action>', methods=['POST'])
@login_required
def admin_verify(vid, action):
    if current_user.role != 'admin':
        flash('Admin only', 'danger')
        return redirect(url_for('dashboard'))
    v = Verification.query.get_or_404(vid)
    if action == 'approve':
        v.status = 'PendingField'
        v.decided_at = datetime.utcnow()
        v.decided_by = current_user.id
    else:
        v.status = 'Rejected'
        v.decided_at = datetime.utcnow()
        v.decided_by = current_user.id
    db.session.commit()
    flash('Verification updated', 'success')
    # notify the youth about verification status change
    try:
        from notifications import create_in_app_notification
        youth_user = v.youth.user
        if youth_user:
            create_in_app_notification(youth_user.id, 'Verification status updated', f'Your verification status is now: {v.status}', link=url_for('dashboard'))
    except Exception:
        pass
    return redirect(url_for('admin_verifications'))

@app.route('/field/visit/<int:vid>', methods=['GET', 'POST'])
@login_required
def field_visit(vid):
    if current_user.role != 'field':
        flash('Field agents only', 'danger')
        return redirect(url_for('dashboard'))
    v = Verification.query.get_or_404(vid)
    if request.method == 'POST':
        findings = request.form.get('findings')
        passed = request.form.get('passed') == 'yes'
        fv = FieldVisit(verification_id=v.id, scheduled_at=datetime.utcnow(), location=request.form.get('location'), findings=findings, verified_identity=passed, completed_at=datetime.utcnow())
        db.session.add(fv)
        if passed:
            v.status = 'Verified'
        else:
            v.status = 'Rejected'
        v.decided_at = datetime.utcnow()
        v.decided_by = current_user.id
        db.session.commit()
        flash('Field visit recorded', 'success')
        return redirect(url_for('dashboard'))
    return render_template('field_visit.html', verification=v)

@app.route('/opportunities')
def list_opportunities():
    # Support simple search/filter for opportunities (type, country, category)
    otype = request.args.get('type')
    country = request.args.get('country')
    category = request.args.get('category')
    q = Opportunity.query.filter_by(is_active=True)
    if otype:
        q = q.filter(Opportunity.type.ilike(f"%{otype}%"))
    if country:
        q = q.filter(Opportunity.country.ilike(f"%{country}%"))
    if category:
        q = q.filter(Opportunity.category_target.ilike(f"%{category}%"))
    opportunities = q.all()
    # If the viewer is a youth, build a map of their applications by opportunity id
    applications_map = {}
    if current_user.is_authenticated and getattr(current_user, 'role', None) == 'youth':
        try:
            profile = YouthProfile.query.filter_by(user_id=current_user.id).first()
            if profile:
                apps = Application.query.filter_by(youth_id=profile.id).all()
                applications_map = {a.opportunity_id: a for a in apps}
        except Exception:
            applications_map = {}

    return render_template('opportunities.html', opportunities=opportunities, applications_map=applications_map)

@app.route('/opportunity/post', methods=['GET', 'POST'])
@login_required
def post_opportunity():
    if current_user.role != 'donor':
        flash('Only donors can post opportunities', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        title = request.form.get('title')
        otype = request.form.get('type')
        country = request.form.get('country')
        category = request.form.get('category')
        deadline = request.form.get('deadline')
        desc = request.form.get('description')
        opp = Opportunity(title=title, type=otype, country=country, category_target=category, description=desc, posted_at=datetime.utcnow(), deadline=deadline, posted_by=current_user.id, is_active=True)
        db.session.add(opp)
        db.session.commit()
        flash('Opportunity posted', 'success')
        return redirect(url_for('dashboard'))
    return render_template('post_opportunity.html')

@app.route('/opportunity/<int:oid>/apply', methods=['POST'])
@login_required
def apply_opportunity(oid):
    if current_user.role != 'youth':
        flash('Only youth can apply', 'danger')
        return redirect(url_for('list_opportunities'))
    profile = YouthProfile.query.filter_by(user_id=current_user.id).first()
    if not profile:
        flash('Complete profile first', 'warning')
        return redirect(url_for('create_profile'))
    # Eligibility rules (revised):
    # - Verified OR
    # - PendingField (waiting for field visit) OR
    # - Profile completed AND at least one validated document
    v = Verification.query.filter_by(youth_id=profile.id).order_by(Verification.started_at.desc()).first()
    eligible = False
    if v and v.status in ('Verified', 'PendingField'):
        eligible = True
    else:
        try:
            validated_docs = Document.query.filter_by(youth_id=profile.id, validated=True).count()
        except Exception:
            validated_docs = 0
        if profile.profile_completed and validated_docs > 0:
            eligible = True

    if not eligible:
        flash('You must have a Verified profile (or PendingField) or a completed profile with at least one validated document to apply. Submit for verification if needed.', 'warning')
        return redirect(url_for('dashboard'))

    appn = Application(opportunity_id=oid, youth_id=profile.id, submitted_at=datetime.utcnow(), status='Submitted')
    db.session.add(appn)
    db.session.commit()
    try:
        from notifications import create_in_app_notification
        create_in_app_notification(current_user.id, 'Application submitted', f'Your application for "{opp.title if (opp:=Opportunity.query.get(oid)) else oid}" was submitted.', link=url_for('dashboard'))
    except Exception:
        pass
    flash('Application submitted', 'success')
    return redirect(url_for('dashboard'))


@app.route('/donor/search_youth', methods=['GET'])
@login_required
def donor_search_youth():
    if current_user.role != 'donor':
        flash('Donors only', 'danger')
        return redirect(url_for('dashboard'))
    category = request.args.get('category')
    country = request.args.get('country')
    community = request.args.get('community')
    # find youth with verified verification records
    q = YouthProfile.query.join(Verification, isouter=True).filter(Verification.status == 'Verified')
    if category:
        q = q.filter(YouthProfile.category.ilike(f"%{category}%"))
    if country:
        q = q.filter(YouthProfile.country.ilike(f"%{country}%"))
    if community:
        q = q.filter(YouthProfile.community.ilike(f"%{community}%"))
    results = q.all()
    return render_template('search_youth.html', results=results)


@app.route('/donor/applications')
@login_required
def donor_applications():
    if current_user.role != 'donor':
        flash('Donors only', 'danger')
        return redirect(url_for('dashboard'))
    opportunities = Opportunity.query.filter_by(posted_by=current_user.id).all()
    return render_template('donor_applications.html', opportunities=opportunities)


@app.route('/donor/opportunity/<int:oid>/edit', methods=['GET', 'POST'])
@login_required
def edit_opportunity(oid):
    if current_user.role != 'donor':
        flash('Donors only', 'danger')
        return redirect(url_for('dashboard'))
    opp = Opportunity.query.get_or_404(oid)
    if opp.posted_by != current_user.id:
        flash('Cannot edit other donors\' opportunities', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        opp.title = request.form.get('title')
        opp.type = request.form.get('type')
        opp.country = request.form.get('country')
        opp.category_target = request.form.get('category')
        opp.deadline = request.form.get('deadline')
        opp.description = request.form.get('description')
        db.session.commit()
        flash('Opportunity updated', 'success')
        return redirect(url_for('donor_applications'))
    return render_template('edit_opportunity.html', opportunity=opp)


@app.route('/donor/opportunity/<int:oid>/delete', methods=['POST'])
@login_required
def delete_opportunity(oid):
    if current_user.role != 'donor':
        flash('Donors only', 'danger')
        return redirect(url_for('dashboard'))
    opp = Opportunity.query.get_or_404(oid)
    if opp.posted_by != current_user.id:
        flash('Cannot delete other donors\' opportunities', 'danger')
        return redirect(url_for('dashboard'))
    opp.is_active = False
    db.session.commit()
    flash('Opportunity deactivated', 'success')
    return redirect(url_for('donor_applications'))


@app.route('/donor/application/<int:aid>/update', methods=['POST'])
@login_required
def donor_update_application(aid):
    if current_user.role != 'donor':
        flash('Donors only', 'danger')
        return redirect(url_for('dashboard'))
    app_obj = Application.query.get_or_404(aid)
    new_status = request.form.get('status')
    if new_status in ['UnderReview', 'Offered', 'NotSelected', 'Withdrawn']:
        app_obj.status = new_status
        db.session.commit()
        flash('Application status updated', 'success')
        # Notify the youth by email and WhatsApp if available
        try:
            from notifications import notify_applicant
            youth_user = app_obj.youth.user
            if youth_user:
                notify_applicant(youth_user, app_obj.opportunity.title, new_status)
        except Exception as e:
            app.logger.warning('Failed to send notification: %s', e)
        # also create in-app notification for the youth
        try:
            from notifications import create_in_app_notification
            youth_user = app_obj.youth.user
            if youth_user:
                create_in_app_notification(youth_user.id, 'Application status updated', f'Your application for "{app_obj.opportunity.title}" is now: {new_status}', link=url_for('donor_applications'))
        except Exception:
            pass
    else:
        flash('Invalid status', 'danger')
    return redirect(url_for('donor_applications'))


@app.route('/admin/recommendations')
@login_required
def admin_recommendations():
    if current_user.role not in ['admin', 'donor']:
        flash('Admins and donors only', 'danger')
        return redirect(url_for('dashboard'))
    
    # For admins: show all recommendations
    # For donors: show only recommendations from youth who applied to their opportunities
    if current_user.role == 'admin':
        recs = RecommendationLetter.query.order_by(RecommendationLetter.uploaded_at.desc()).all()
    else:  # donor
        # Get all opportunities posted by this donor
        donor_opps = Opportunity.query.filter_by(posted_by=current_user.id).all()
        donor_opp_ids = [opp.id for opp in donor_opps]
        
        # Get all applications to these opportunities
        applications = Application.query.filter(Application.opportunity_id.in_(donor_opp_ids)).all()
        youth_ids = [app.youth_id for app in applications]
        
        # Get recommendations from these youth
        recs = RecommendationLetter.query.filter(RecommendationLetter.youth_id.in_(youth_ids)).order_by(RecommendationLetter.uploaded_at.desc()).all()
    
    return render_template('admin_recommendations.html', recommendations=recs)


@app.route('/admin/recommendation/<int:rid>/verify', methods=['POST'])
@login_required
def verify_recommendation(rid):
    if current_user.role not in ['admin', 'donor']:
        flash('Admins and donors only', 'danger')
        return redirect(url_for('dashboard'))
    
    rec = RecommendationLetter.query.get_or_404(rid)
    
    # For donors: verify they can only approve recommendations from their applicants
    if current_user.role == 'donor':
        # Get the youth who submitted this recommendation
        youth = rec.youth
        
        # Check if any applications to this donor's opportunities came from this youth
        donor_opps = Opportunity.query.filter_by(posted_by=current_user.id).all()
        donor_opp_ids = [opp.id for opp in donor_opps]
        
        has_application = Application.query.filter(
            Application.opportunity_id.in_(donor_opp_ids),
            Application.youth_id == youth.id
        ).first()
        
        if not has_application:
            flash('You can only verify recommendations from youth who applied to your opportunities', 'danger')
            return redirect(url_for('admin_recommendations'))
    
    action = request.form.get('action')
    notes = request.form.get('notes', '')
    if action in ['approve', 'reject']:
        rec.validated = (action == 'approve')
        rec.verified_at = datetime.utcnow()
        rec.verified_by = current_user.id
        rec.verification_notes = notes
        # Process per-document validation flags submitted from the form
        try:
            for d in rec.youth.documents:
                field_name = f"doc_validated_{d.id}"
                # Checkbox will be present in form if checked
                if request.form.get(field_name):
                    d.validated = True
                else:
                    # Only change if explicitly present as 'on' or absent; leave untouched otherwise
                    # For safety, if the form didn't include the checkbox at all, we don't modify the flag
                    # However, in our template we always render the checkbox for each document, so absence => unchecked
                    d.validated = False
            db.session.commit()
            # notify the youth that recommendation verification changed
            try:
                from notifications import create_in_app_notification
                youth_user = rec.youth.user
                if youth_user:
                    create_in_app_notification(youth_user.id, 'Recommendation verification', f'Your recommendation was {"approved" if rec.validated else "rejected"}.', link=url_for('admin_recommendations'))
            except Exception:
                pass
        except Exception as e:
            app.logger.warning('Failed to update document validation flags: %s', e)
            # still commit the recommendation state
            db.session.commit()
        flash(f'Recommendation {action}d', 'success')
    else:
        flash('Invalid action', 'danger')
    return redirect(url_for('admin_recommendations'))


@app.route('/admin/reports')
@login_required
def admin_reports():
    total_youth = YouthProfile.query.count()
    total_verified = Verification.query.filter_by(status='Verified').count()
    total_pending = Verification.query.filter(Verification.status.in_(['Pending', 'PendingField'])).count()
    total_opps = Opportunity.query.count()
    total_apps = Application.query.count()
    return render_template('admin_reports.html', total_youth=total_youth, total_verified=total_verified, total_pending=total_pending, total_opps=total_opps, total_apps=total_apps)


@app.route('/admin/manage_users', methods=['GET', 'POST'])
@login_required
def admin_manage_users():
    if current_user.role != 'admin':
        flash('Admin only', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        # simple user role update / delete
        action = request.form.get('action')
        uid = request.form.get('user_id')
        user = User.query.get(uid)
        if not user:
            flash('User not found', 'warning')
            return redirect(url_for('admin_manage_users'))
        if action == 'delete':
            try:
                db.session.delete(user)
                db.session.commit()
                flash('User deleted', 'success')
            except Exception as e:
                app.logger.warning('Failed to delete user: %s', e)
                flash('Failed to delete user', 'danger')
        elif action == 'update_role':
            new_role = request.form.get('role')
            user.role = new_role
            db.session.commit()
            flash('User role updated', 'success')
        return redirect(url_for('admin_manage_users'))
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin_manage_users.html', users=users)


@app.route('/admin/contacts', methods=['GET', 'POST'])
@login_required
def admin_contacts():
    if current_user.role != 'admin':
        flash('Admin only', 'danger')
        return redirect(url_for('dashboard'))
    # store simple support contact in a JSON file
    cfg_path = os.path.join(BASE_DIR, 'support_contact.json')
    import json
    if request.method == 'POST':
        email = request.form.get('support_email')
        phone = request.form.get('support_phone')
        cfg = {'email': email, 'phone': phone}
        with open(cfg_path, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
        flash('Support contact updated', 'success')
        return redirect(url_for('admin_contacts'))
    try:
        with open(cfg_path, 'r', encoding='utf-8') as f:
            cfg = json.load(f)
    except Exception:
        cfg = {'email': '', 'phone': ''}
    return render_template('admin_contacts.html', support=cfg)


@app.route('/admin/features', methods=['GET', 'POST'])
@login_required
def admin_features():
    if current_user.role != 'admin':
        flash('Admin only', 'danger')
        return redirect(url_for('dashboard'))
    feats_path = os.path.join(BASE_DIR, 'features.json')
    import json
    if request.method == 'POST':
        # Collect feature toggles as boolean flags
        features = {
            'enable_media_gallery': bool(request.form.get('enable_media_gallery')),
            'enable_recommendations': bool(request.form.get('enable_recommendations')),
            'enable_verifications': bool(request.form.get('enable_verifications'))
        }
        with open(feats_path, 'w', encoding='utf-8') as f:
            json.dump(features, f, ensure_ascii=False, indent=2)
        flash('Features updated', 'success')
        return redirect(url_for('admin_features'))
    try:
        with open(feats_path, 'r', encoding='utf-8') as f:
            features = json.load(f)
    except Exception:
        features = {'enable_media_gallery': True, 'enable_recommendations': True, 'enable_verifications': True}
    return render_template('admin_features.html', features=features)


@app.route('/admin/opportunities', methods=['GET', 'POST'])
@login_required
def admin_opportunities():
    if current_user.role != 'admin':
        flash('Admin only', 'danger')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        action = request.form.get('action')
        oid = request.form.get('opportunity_id')
        opp = Opportunity.query.get(oid)
        if not opp:
            flash('Opportunity not found', 'warning')
            return redirect(url_for('admin_opportunities'))
        if action == 'deactivate':
            opp.is_active = False
            db.session.commit()
            flash('Opportunity deactivated', 'success')
        elif action == 'activate':
            opp.is_active = True
            db.session.commit()
            flash('Opportunity activated', 'success')
        return redirect(url_for('admin_opportunities'))
    opps = Opportunity.query.order_by(Opportunity.posted_at.desc()).all()
    return render_template('admin_opportunities.html', opportunities=opps)


@app.route('/profile/settings', methods=['GET', 'POST'])
@login_required
def profile_settings():
    """Update contact information and preferences for any user"""
    if request.method == 'POST':
        current_user.phone_number = request.form.get('phone_number', current_user.phone_number)
        current_user.whatsapp_number = request.form.get('whatsapp_number', current_user.whatsapp_number)
        current_user.preferred_contact = request.form.get('preferred_contact', 'email')
        
        # For youth, also update YouthProfile preferences
        if current_user.role == 'youth' and current_user.youth_profile:
            current_user.youth_profile.whatsapp_number = request.form.get('whatsapp_number', current_user.youth_profile.whatsapp_number)
            current_user.youth_profile.preferred_feedback = request.form.get('preferred_feedback', 'email')
        
        db.session.commit()
        flash('Contact information updated successfully', 'success')
        return redirect(url_for('profile_settings'))
    
    return render_template('profile_settings.html')


@app.route('/contact')
def contact():
    """Public contact page for admin/support information"""
    admin_user = User.query.filter_by(role='admin').first()
    return render_template('contact.html', admin_user=admin_user)


def send_email(to_addr: str, subject: str, body: str):
    """Best-effort email sender. Uses SMTP settings from app.config if present.
    If no SMTP configured, logs the message to the application logger.
    """
    mail_server = app.config.get('MAIL_SERVER')
    if not mail_server:
        app.logger.info('EMAIL (console) -> To: %s Subject: %s\n%s', to_addr, subject, body)
        return
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = app.config.get('MAIL_FROM', 'noreply@riseuplink.local')
    msg['To'] = to_addr
    msg.set_content(body)
    try:
        port = app.config.get('MAIL_PORT', 587)
        use_tls = app.config.get('MAIL_USE_TLS', True)
        username = app.config.get('MAIL_USERNAME')
        password = app.config.get('MAIL_PASSWORD')
        if use_tls:
            server = smtplib.SMTP(mail_server, port, timeout=10)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(mail_server, port, timeout=10)
        if username and password:
            server.login(username, password)
        server.send_message(msg)
        server.quit()
        app.logger.info('Email sent to %s', to_addr)


# Global exception logger: record full tracebacks to the application logs
# so we can inspect errors in serverless logs without exposing internals
@app.errorhandler(Exception)
def handle_uncaught_exception(e):
    try:
        app.logger.exception('Unhandled exception during request: %s', e)
    except Exception:
        pass
    return "Internal Server Error", 500
    except Exception as exc:
        app.logger.warning('Failed to send email to %s: %s', to_addr, exc)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # One-time migration: import legacy youtube_videos.json into DB if table empty
        try:
            if YouTubeVideo.query.count() == 0:
                yt_path = os.path.join(BASE_DIR, 'youtube_videos.json')
                import json
                try:
                    with open(yt_path, 'r', encoding='utf-8') as f:
                        vids = json.load(f)
                    for v in vids:
                        try:
                            yid = v.get('youtube_id')
                            yv = YouTubeVideo(youtube_id=yid, title=v.get('title'), description=v.get('description'), link=v.get('link'), is_main=bool(v.get('is_main')))
                            db.session.add(yv)
                        except Exception:
                            continue
                    db.session.commit()
                    app.logger.info('Imported legacy YouTube videos into DB')
                except Exception:
                    pass
        except Exception:
            pass
    app.run(host='172.20.19.137', port=5000, debug=True)

"""if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)"""
