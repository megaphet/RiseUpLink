import urllib.request
try:
    with urllib.request.urlopen('http://127.0.0.1:5000/', timeout=5) as r:
        print('STATUS', r.status)
        print(r.read(500).decode('utf-8', errors='ignore'))
except Exception as e:
    print('ERR', e)
