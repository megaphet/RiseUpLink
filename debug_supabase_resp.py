from dotenv import load_dotenv
import os
load_dotenv()
import supabase_client

print('Client object:', type(supabase_client._client))

try:
    res = supabase_client._client.table('opportunity').select('*').limit(1).execute()
    print('select resp type:', type(res))
    try:
        print('select repr:', repr(res)[:1000])
    except Exception:
        pass
    if hasattr(res, 'data'):
        print('has data attr; len:', len(res.data) if res.data else 0)
    else:
        try:
            print('get data:', res.get('data'))
        except Exception as e:
            print('res.get error:', e)
except Exception as e:
    print('select error:', e)

try:
    ins = supabase_client._client.table('opportunity').insert({'title':'dbg','posted_at':'now()'}).execute()
    print('insert resp type:', type(ins))
    try:
        print('insert repr:', repr(ins)[:1000])
    except Exception:
        pass
    if hasattr(ins, 'data'):
        print('insert data attr len:', len(ins.data) if ins.data else 0)
    else:
        try:
            print('insert get data:', ins.get('data'))
        except Exception as e:
            print('insert res.get error:', e)
except Exception as e:
    print('insert error:', e)
