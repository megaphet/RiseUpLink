from dotenv import load_dotenv
import os
load_dotenv()
import supabase_client

print('SUPABASE_URL present:', bool(os.environ.get('SUPABASE_URL')))
print('SUPABASE_KEY present:', bool(os.environ.get('SUPABASE_KEY')))

try:
    ops = supabase_client.list_opportunities(limit=3)
    print('Opportunities (count):', len(ops) if ops is not None else 'client not configured')
except Exception as e:
    print('Opportunities error:', e)

try:
    mv = supabase_client.get_main_youtube_video()
    print('Main video:', bool(mv))
except Exception as e:
    print('Main video error:', e)
