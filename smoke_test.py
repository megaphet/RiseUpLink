import time
import urllib.request

URLS = ['http://127.0.0.1:5000/', 'http://127.0.0.1:5000/opportunities', 'http://127.0.0.1:5000/login']

def try_get(url, timeout=5):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return resp.status, resp.read(200).decode('utf-8', errors='ignore')
    except Exception as e:
        return None, str(e)

def main():
    # wait for server to start
    for _ in range(12):
        status, body = try_get(URLS[0], timeout=2)
        if status:
            break
        time.sleep(1)

    results = {}
    for u in URLS:
        status, body = try_get(u, timeout=3)
        results[u] = (status, body[:200])

    print('SMOKE TEST RESULTS')
    for u, (s, b) in results.items():
        print(f"{u} -> {s}")
    # exit with non-zero if any endpoint failed
    ok = all(s and 200 <= s < 400 for s, _ in results.values())
    if not ok:
        raise SystemExit(2)

if __name__ == '__main__':
    main()
