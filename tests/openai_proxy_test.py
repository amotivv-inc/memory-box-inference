#!/usr/bin/env python3
"""
openai_proxy_test.py  –  Docker-friendly smoke-tests for *OpenAI Inference Proxy*

• Creates a throw-away organisation inside the running container
• Mints a JWT for that org
• Exercises users, API keys, responses (stream / non-stream), ratings, and
  common error paths through the public REST API.

Run:

    python openai_proxy_test.py \
        --api-url   http://localhost:8000 \
        --openai-key sk-test-key-123456789 \
        --docker    openai-proxy-api      # or whatever your service is called
"""
###############################################################################
#  Imports & constants
###############################################################################
import argparse, os, re, subprocess, sys, time, uuid
from dataclasses import dataclass
from datetime import datetime
from typing      import Dict, Optional

import requests
from requests.exceptions import RequestException

# Defaults (override with flags or env vars)
DEF_API_URL  = os.getenv("API_URL",        "http://localhost:8000")
DEF_ORG_NAME = os.getenv("TEST_ORG_NAME",  f"Test-Org-{int(time.time())}")
DEF_OAI_KEY  = os.getenv("TEST_OPENAI_KEY","sk-test-key-123456789")
DEF_MODEL    = os.getenv("TEST_MODEL",     "gpt-4o")
DEF_DOCKER   = os.getenv("OIP_DOCKER",     "openai-proxy-api")

USE_HELPERS = True               # always docker, per your note
STREAM_WAIT = 5                  # seconds to wait for first SSE chunk

# Colour helpers
GREEN, RED, YEL, BLU, RESET = "\033[92m", "\033[91m", "\033[93m", "\033[94m", "\033[0m"
h    = lambda m: print(f"\n{BLU}=== {m} ==={RESET}")
ok   = lambda m: print(f"{GREEN}✓ {m}{RESET}")
err  = lambda m: print(f"{RED}✗ {m}{RESET}")
info = lambda m: print(f"{YEL}ℹ {m}{RESET}")
die  = lambda m,c=1: (err(m), sys.exit(c))

UUID_RE = re.compile(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-"
                     r"[0-9a-fA-F]{4}-[0-9a-fA-F]{12}")
JWT_RE  = re.compile(r"eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+")

###############################################################################
#  Docker helper (list-style, to avoid quoting issues)
###############################################################################
def d_exec(container:str, *args:str) -> str:
    """Run a command inside the container and return stdout (text)."""
    try:
        out = subprocess.check_output(["docker", "exec", container, *args],
                                      text=True, stderr=subprocess.STDOUT)
        return out
    except subprocess.CalledProcessError as e:
        die(f"Docker exec failed:\n{e.output}")

def first_uuid(text:str) -> Optional[str]:
    m = UUID_RE.search(text); return m.group(0) if m else None
def first_jwt(text:str)  -> Optional[str]:
    m = JWT_RE.search(text);  return m.group(0) if m else None
def slug() -> str: return uuid.uuid4().hex[:8]

###############################################################################
@dataclass
class Ctx:
    api_url:   str
    org_name:  str
    openai_key:str
    model:     str
    docker:    str
    org_id:       Optional[str]=None
    jwt:          Optional[str]=None
    user1_id:     Optional[str]=None
    user2_id:     Optional[str]=None
    org_key_id:   Optional[str]=None
    user_key_id:  Optional[str]=None
    request_id:   Optional[str]=None
    response_id:  Optional[str]=None

    @property
    def hdr(self) -> Dict[str,str]:
        return {"Authorization": f"Bearer {self.jwt}"} if self.jwt else {}

###############################################################################
#  HTTP helpers
###############################################################################
def req(ctx:Ctx, method:str, path:str, **kw):
    url = f"{ctx.api_url.rstrip('/')}{path}"
    kw.setdefault("headers", {}).update(ctx.hdr)
    try:
        return requests.request(method, url, timeout=30, **kw)
    except RequestException as e:
        die(f"HTTP {method} {path}: {e}")

def jreq(ctx:Ctx, method:str, path:str, expect, **kw):
    r = req(ctx, method, path, **kw)
    okflag = r.status_code in expect if isinstance(expect,tuple) else r.status_code==expect
    return r, okflag

###############################################################################
#  Test steps
###############################################################################
def setup_org_jwt(ctx:Ctx):
    h("Org & JWT setup via helpers")

    # 1) create-org
    out = d_exec(ctx.docker, "python", "scripts/manage_api_keys.py",
                 "create-org", ctx.org_name)
    ctx.org_id = first_uuid(out) or die("Org UUID not found in helper output")
    ok(f"Org created → {ctx.org_id}")

    # 2) create-jwt
    out = d_exec(ctx.docker, "python", "scripts/create_jwt.py",
                 "--org-name", ctx.org_name, "--org-id", ctx.org_id)
    ctx.jwt = first_jwt(out) or die("JWT not found in helper output")
    ok("JWT minted")

def health(ctx:Ctx):
    h("Health checks")
    jreq(ctx,"GET","/health",200); ok("Public /health")
    r, okf = jreq(ctx,"GET","/v1/responses/health",200)
    ok("Auth /responses/health") if okf else err(f"Auth health {r.status_code}")

def users(ctx:Ctx):
    h("User CRUD")
    for email in (f"u1+{slug()}@ex.com", f"u2+{slug()}@ex.com"):
        r, okf = jreq(ctx,"POST","/v1/api/users",201,json={"user_id":email})
        if not okf: err(f"user create {email} {r.status_code}"); continue
        uid = r.json()["id"]
        (ctx.user1_id, ctx.user2_id)[ctx.user1_id is not None] or setattr(ctx,"user1_id" if ctx.user1_id is None else "user2_id", uid)
        ok(f"Created {email} → {uid}")
    r,_ = jreq(ctx,"GET","/v1/api/users",200)
    ok(f"List users ({len(r.json()['users'])})")

def keys(ctx:Ctx):
    h("API key CRUD")
    base = {"openai_api_key":ctx.openai_key,"name":"org-key","description":"test"}
    r,okf=jreq(ctx,"POST","/v1/api/keys",201,json=base); ctx.org_key_id=r.json().get("id") if okf else None
    ok("Org key made") if okf else err("Org key fail")
    usr = base|{"openai_api_key":ctx.openai_key+"-u","user_id":ctx.user1_id,"name":"user1-key"}
    r,okf=jreq(ctx,"POST","/v1/api/keys",201,json=usr); ctx.user_key_id=r.json().get("id") if okf else None
    ok("User key made") if okf else err("User key fail")
    r,_=jreq(ctx,"GET","/v1/api/keys",200); ok(f"List keys ({len(r.json()['api_keys'])})")

def resp_nonstream(ctx:Ctx):
    h("Non-stream response")
    pl={"model":ctx.model,"input":"Say hello","stream":False,"max_output_tokens":20,"temperature":0}
    hd=ctx.hdr|{"X-User-ID":ctx.user1_id,"X-Session-ID":"sess-"+slug()}
    r=requests.post(f"{ctx.api_url}/v1/responses",json=pl,headers=hd,timeout=30)
    if r.status_code==200:
        ok("Non-stream OK"); ctx.request_id=r.headers.get("x-request-id"); ctx.response_id=r.json().get("id")
    else: err(f"Non-stream {r.status_code} {r.text}")

def resp_stream(ctx:Ctx):
    h("Streaming response")
    pl={"model":ctx.model,"input":"Count 1-5","stream":True,"max_output_tokens":20,"temperature":0}
    hd=ctx.hdr|{"X-User-ID":ctx.user2_id,"Accept":"text/event-stream"}
    with requests.post(f"{ctx.api_url}/v1/responses",json=pl,headers=hd,
                       stream=True,timeout=30) as r:
        start=time.time(); chunk=False
        for line in r.iter_lines():
            if time.time()-start>STREAM_WAIT: break
            if line.startswith(b"data:"): chunk=True; break
        ok("Stream chunk received") if chunk else err("No SSE data")

def rating(ctx:Ctx):
    h("Rating")
    if not ctx.request_id: info("No request id"); return
    r,okf=jreq(ctx,"POST",f"/v1/responses/{ctx.request_id}/rate",200,
               json={"rating":1,"feedback":"great"})
    ok("Rating accepted") if okf else err(f"Rating fail {r.status_code}")

def errors(ctx:Ctx):
    h("Expected errors")
    r=requests.get(f"{ctx.api_url}/v1/api/users",
                   headers={"Authorization":"Bearer bad"})
    ok("Bad JWT rejected") if r.status_code==401 else err("Bad JWT not rejected")
    r=requests.post(f"{ctx.api_url}/v1/responses",
                    json={"model":ctx.model,"input":"hi"},headers=ctx.hdr)
    ok("Missing X-User-ID rejected") if r.status_code in (400,422) else err("Header miss fail")
    hd=ctx.hdr|{"X-User-ID":ctx.user1_id}
    r=requests.post(f"{ctx.api_url}/v1/responses",
                    json={"model":"no-such","input":"hi"},headers=hd)
    ok("Bad model rejected") if r.status_code in (400,422) else err("Bad model fail")

###############################################################################
#  Main
###############################################################################
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--api-url",   default=DEF_API_URL)
    p.add_argument("--org-name",  default=DEF_ORG_NAME)
    p.add_argument("--openai-key",default=DEF_OAI_KEY)
    p.add_argument("--model",     default=DEF_MODEL)
    p.add_argument("--docker",    default=DEF_DOCKER,
                   help="Container name (default: openai-proxy-api)")
    args=p.parse_args()

    ctx=Ctx(args.api_url,args.org_name,args.openai_key,args.model,args.docker)
    setup_org_jwt(ctx)
    health(ctx); users(ctx); keys(ctx)
    resp_nonstream(ctx); resp_stream(ctx); rating(ctx); errors(ctx)
    print(f"\n{GREEN}✔ All tests completed – {datetime.utcnow().isoformat()}Z{RESET}")

if __name__=="__main__":
    main()

