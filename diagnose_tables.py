#!/usr/bin/env python3
"""
Diagnose what's in each Supabase table
"""
from dotenv import load_dotenv
import os
load_dotenv()

from supabase import create_client

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL or SUPABASE_KEY not set")
    exit(1)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

tables = [
    'user',
    'youth_profile',
    'opportunity',
    'application',
    'document',
    'recommendation_letter',
    'field_visit',
    'verification',
    'notification',
    'you_tube_video'
]

for table_name in tables:
    try:
        res = client.table(table_name).select('*').limit(1).execute()
        data = res.data if hasattr(res, 'data') else res.get('data', [])
        count_res = client.table(table_name).select('*', count='exact').execute()
        count = count_res.count if hasattr(count_res, 'count') else 'unknown'
        print(f"{table_name:25} | Count: {count:5} | Sample: {data}")
    except Exception as e:
        print(f"{table_name:25} | ERROR: {str(e)[:60]}")
