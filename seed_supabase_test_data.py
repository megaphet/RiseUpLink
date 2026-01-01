from dotenv import load_dotenv
import os
load_dotenv()
import supabase_client
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

print('Supabase configured:', bool(os.environ.get('SUPABASE_URL')) and bool(os.environ.get('SUPABASE_KEY')))

# Create two users: youth@example.com and donor@example.com
pw_hash = generate_password_hash('password')

created = {}

u1 = supabase_client.get_user_by_email('youth@example.com')
if not u1:
    u1 = supabase_client.create_user({'email': 'youth@example.com', 'full_name': 'Test Youth', 'password_hash': pw_hash, 'role': 'youth'})
    print('Created youth user:', u1 and u1.get('id'))
else:
    print('Youth user exists:', u1.get('id'))
created['youth'] = u1

u2 = supabase_client.get_user_by_email('donor@example.com')
if not u2:
    u2 = supabase_client.create_user({'email': 'donor@example.com', 'full_name': 'Test Donor', 'password_hash': pw_hash, 'role': 'donor'})
    print('Created donor user:', u2 and u2.get('id'))
else:
    print('Donor user exists:', u2.get('id'))
created['donor'] = u2

# Create youth profile if missing
if u1:
    profile = supabase_client.get_profile_by_user_id(u1.get('id'))
    if not profile:
        profile = supabase_client.create_profile({'user_id': u1.get('id'), 'full_name': 'Test Youth', 'profile_completed': True, 'phone_number': '', 'preferred_contact': 'email'})
        print('Created youth profile:', profile and profile.get('id'))
    else:
        print('Youth profile exists:', profile.get('id'))
    created['profile'] = profile

# Add one opportunity
opp_list = supabase_client.list_opportunities(limit=10)
if not opp_list:
    opp = supabase_client.add_opportunity({'title': 'Test Opportunity', 'type': 'Internship', 'country': 'Testland', 'category_target': 'Education', 'description': 'Seeded test opportunity', 'posted_at': datetime.utcnow().isoformat(), 'deadline': (datetime.utcnow()+timedelta(days=30)).isoformat(), 'posted_by': u2.get('id') if u2 else None, 'is_active': True})
    print('Created opportunity:', opp and opp.get('id'))
    created['opportunity'] = opp
else:
    print('Opportunities already present:', len(opp_list))
    created['opportunity'] = opp_list[0]

# Add a main youtube video
mv = supabase_client.get_main_youtube_video()
if not mv:
    vid = supabase_client.add_youtube_video({'youtube_id': 'dQw4w9WgXcQ', 'title': 'Test Main', 'description': 'Seeded main video', 'link': 'https://youtu.be/dQw4w9WgXcQ', 'is_main': True, 'created_at': datetime.utcnow().isoformat()})
    print('Created main video:', vid and vid.get('id'))
    created['main_video'] = vid
else:
    print('Main video exists:', mv.get('id'))
    created['main_video'] = mv

print('Seeding complete. Summary:')
for k, v in created.items():
    print('-', k, '->', (v.get('id') if isinstance(v, dict) else v))
