#!/usr/bin/env python3
"""Get or create a Veracode application profile by exact name (REST Applications API, HMAC).

  usage: veracode_app_profile.py get  NAME
         veracode_app_profile.py ensure NAME [--criticality VERY_HIGH|HIGH|MEDIUM|LOW|VERY_LOW]
                                            [--description TEXT] [--repo-url URL] [--team TEAM ...]
Prints one JSON line: {"name", "guid", "id", "created": bool, "policy": ...}.
Credentials from the environment: VERACODE_API_KEY_ID, VERACODE_API_KEY_SECRET (HMAC pair; never OAuth).
Region from VERACODE_REGION (com|eu|us-fed) or guessed from the key id prefix. Standard library only.
Never prints credential values. `ensure` is the only call that writes, and only when no exact match exists.
Verified live 2026-11-11 (US commercial tenant): GET /appsec/v1/applications?name= is a partial,
case-insensitive match (re-filtered here); POST /appsec/v1/applications returns 200/201 with the new guid.
"""
import argparse, hashlib, hmac, json, os, secrets, sys, time, urllib.error, urllib.parse, urllib.request

HOSTS = {"com": "api.veracode.com", "eu": "api.veracode.eu", "us-fed": "api.veracode.us"}

def region():
    r = os.environ.get("VERACODE_REGION")
    if r in HOSTS: return r
    p = os.environ.get("VERACODE_API_KEY_ID", "")[:8]
    return "eu" if p.startswith("vera01e") else "us-fed" if p.startswith("vera01f") else "com"

def hmac_header(host, path_and_query, method):
    api_id = os.environ["VERACODE_API_KEY_ID"].split("-")[-1].lower()
    key = bytes.fromhex(os.environ["VERACODE_API_KEY_SECRET"])
    data = f"id={api_id}&host={host.lower()}&url={path_and_query}&method={method.upper()}"
    nonce = secrets.token_bytes(16); ts = str(int(time.time() * 1000))
    k1 = hmac.new(key, nonce, hashlib.sha256).digest()
    k2 = hmac.new(k1, ts.encode(), hashlib.sha256).digest()
    k3 = hmac.new(k2, b"vcode_request_version_1", hashlib.sha256).digest()
    sig = hmac.new(k3, data.encode(), hashlib.sha256).hexdigest()
    return f"VERACODE-HMAC-SHA-256 id={api_id},ts={ts},nonce={nonce.hex()},sig={sig}"

def call(method, path, body=None):
    host = HOSTS[region()]
    req = urllib.request.Request(f"https://{host}{path}", data=body, method=method)
    req.add_header("Authorization", hmac_header(host, path, method))
    req.add_header("Accept", "application/json"); req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        raw = e.read()
        try: return e.code, json.loads(raw)
        except Exception: return e.code, {"raw": raw[:300].decode(errors="replace")}

def summarize(app, created=False):
    prof = app["profile"]
    return {"name": prof["name"], "guid": app["guid"], "id": app.get("id"), "created": created,
            "business_criticality": prof.get("business_criticality"),
            "policy": [(p.get("name"), p.get("policy_compliance_status")) for p in (prof.get("policies") or [])],
            "teams": [t.get("team_name") for t in (prof.get("teams") or [])]}

def find(name):
    page = 0
    while True:
        q = urllib.parse.urlencode({"name": name, "size": 100, "page": page})
        st, j = call("GET", f"/appsec/v1/applications?{q}")
        if st != 200: raise SystemExit(f"GET applications failed: HTTP {st} {j}")
        for a in j.get("_embedded", {}).get("applications", []):   # empty collections omit _embedded
            if a["profile"]["name"] == name: return a
        if page >= j.get("page", {}).get("total_pages", 1) - 1: return None
        page += 1

def main():
    ap = argparse.ArgumentParser(); sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("get"); g.add_argument("name")
    e = sub.add_parser("ensure"); e.add_argument("name")
    e.add_argument("--criticality", default="MEDIUM"); e.add_argument("--description", default="")
    e.add_argument("--repo-url", default=""); e.add_argument("--team", action="append", default=[])
    a = ap.parse_args()
    for k in ("VERACODE_API_KEY_ID", "VERACODE_API_KEY_SECRET"):
        if not os.environ.get(k): raise SystemExit(f"{k} not set in the environment")
    app = find(a.name)
    if app or a.cmd == "get":
        print(json.dumps(summarize(app)) if app else json.dumps({"name": a.name, "guid": None})); return
    profile = {"name": a.name, "business_criticality": a.criticality}
    if a.description: profile["description"] = a.description
    if a.repo_url: profile["git_repo_url"] = a.repo_url
    if a.team: profile["teams"] = [{"team_name": t} for t in a.team]
    st, j = call("POST", "/appsec/v1/applications", json.dumps({"profile": profile}).encode())
    if st not in (200, 201): raise SystemExit(f"POST applications failed: HTTP {st} {j}")
    print(json.dumps(summarize(j, created=True)))

if __name__ == "__main__": main()
