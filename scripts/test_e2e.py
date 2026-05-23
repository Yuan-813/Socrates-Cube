import httpx, json

payload = {"session_id": "e2e", "user_id": "test", "message": "1+1=?"}
with httpx.Client(timeout=60, verify=False) as client:
    resp = client.post(
        "http://localhost:8000/api/v1/chat/stream",
        json=payload,
        headers={"Accept": "text/event-stream"},
    )
    print("status:", resp.status_code)
    text = resp.text
    lines = [l for l in text.split("\n") if l.startswith("data:")]
    print("data lines:", len(lines))
    tokens = []
    for line in lines:
        evt = json.loads(line[5:].strip())
        if evt.get("event") == "token":
            tokens.append(evt.get("data", ""))
    print("answer:", "".join(tokens)[:200])
