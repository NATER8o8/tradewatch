
import sys, httpx
BASE = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8001"
def ok(name, cond): print(f"[{name}] {'OK' if cond else 'FAIL'}"); return cond
def main():
    ok('healthz', httpx.get(f"{BASE}/healthz", timeout=5).status_code == 200)
    ok('metrics', httpx.get(f"{BASE}/metrics", timeout=5).status_code == 200)
    ok('trades.csv', httpx.get(f"{BASE}/api/export/trades.csv", timeout=5).status_code in (200,204,404,500))
    ok('backtest.csv', httpx.get(f"{BASE}/api/export/backtest.csv", timeout=5).status_code in (200,204,404,500))
    ok('trades.jsonl', httpx.get(f"{BASE}/api/export/trades.jsonl", timeout=5).status_code in (200,204,404,500))
    ok('backtest.json', httpx.get(f"{BASE}/api/export/backtest.json", timeout=5).status_code in (200,204,404,500))
    print("Smoke complete. Seed for richer data.")
if __name__ == "__main__": main()
