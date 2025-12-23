import re
import time
import requests

BASE = 'http://127.0.0.1:5000'

def login(session, email, password):
    # fetch login page to get session cookie
    r = session.get(f'{BASE}/login')
    r = session.post(f'{BASE}/login', data={'email': email, 'password': password}, allow_redirects=True)
    return r

def apply_as_youth():
    s = requests.Session()
    r = login(s, 'youth@example.com', 'password')
    if r.status_code >= 400:
        print('Youth login failed', r.status_code)
        return False
    # get opportunities and find first opportunity id by searching for apply action
    r = s.get(f'{BASE}/opportunities')
    m = re.search(r'/opportunity/(\d+)/apply', r.text)
    if not m:
        print('No opportunity apply link found')
        return False
    oid = m.group(1)
    r = s.post(f'{BASE}/opportunity/{oid}/apply', allow_redirects=True)
    print('Applied to opportunity', oid, 'status', r.status_code)
    return True

def donor_update_application():
    s = requests.Session()
    r = login(s, 'donor@example.com', 'password')
    if r.status_code >= 400:
        print('Donor login failed', r.status_code)
        return False
    r = s.get(f'{BASE}/donor/applications')
    # find first application id in page (table row with <td>app id</td>)
    m = re.search(r'<td>(\d+)</td>\s*<td>.*?</td>\s*<td>.*?</td>\s*<td>(\w+)</td>', r.text, re.S)
    if not m:
        print('No application found in donor view')
        return False
    aid = m.group(1)
    old_status = m.group(2)
    print('Found application', aid, 'status', old_status)
    r = s.post(f'{BASE}/donor/application/{aid}/update', data={'status': 'Offered'}, allow_redirects=True)
    print('Updated application', aid, 'status', r.status_code)
    return True

def main():
    # wait a bit for server
    for _ in range(12):
        try:
            r = requests.get(BASE, timeout=2)
            if r.status_code == 200:
                break
        except Exception:
            time.sleep(1)

    ok1 = apply_as_youth()
    ok2 = donor_update_application()
    if ok1 and ok2:
        print('FUNCTIONAL TEST PASSED')
    else:
        print('FUNCTIONAL TEST FAILED')

if __name__ == '__main__':
    main()
