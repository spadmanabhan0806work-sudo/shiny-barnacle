import sys
import scripts.ingest_urls as iu

def submit_batch_ext(client, api_base, urls):
    r = client.post(
        f"{api_base.rstrip('/')}/api/v1/calls/batch/from-urls",
        json={"urls": urls},
        timeout=1800.0,
    )
    if r.status_code >= 400:
        raise RuntimeError(f"Ingest failed ({r.status_code}): {r.text}")
    return r.json()

iu.submit_batch = submit_batch_ext
sys.argv = [
    "ingest_urls.py",
    r"C:\Users\natar\Downloads\recording_urls.txt",
    "--limit",
    "20",
    "--api-base",
    "http://127.0.0.1:8000",
]
raise SystemExit(iu.main())
