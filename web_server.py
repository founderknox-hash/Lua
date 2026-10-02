#!/usr/bin/env python3
"""
Small web front-end for the existing Luraph deobfuscator.

Run:
    python3 web_server.py

Then open:
    http://127.0.0.1:8080

The actual deobfuscation pipeline remains the project's existing Node/Python
implementation; this server only provides the browser UI and temporary-file
plumbing.
"""
import html
import os
import shutil
import subprocess
import tempfile
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from email.parser import BytesParser
from email.policy import default

ROOT = Path(__file__).resolve().parent
DEOB = ROOT / "deob.js"
MAX_UPLOAD = 15 * 1024 * 1024
PORT = int(os.environ.get("PORT", "8080"))

INDEX = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Luraph Deobfuscator Web</title>
<style>
:root{color-scheme:dark;font-family:Inter,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif}
*{box-sizing:border-box} body{margin:0;background:#0a0d12;color:#edf1f7}
.wrap{max-width:1100px;margin:0 auto;padding:32px 18px 50px}
h1{margin:0 0 8px;font-size:30px} .sub{color:#9aa5b5;margin-bottom:26px}
.card{background:#11161e;border:1px solid #252d38;border-radius:16px;padding:20px;margin:14px 0}
.drop{border:1px dashed #475467;border-radius:14px;padding:34px;text-align:center;background:#0d1219}
.drop.drag{border-color:#8aa4ff;background:#121a2a}
input[type=file]{display:none}.pick{display:inline-block;padding:11px 16px;border-radius:10px;background:#e8edf5;color:#10141b;font-weight:700;cursor:pointer}
.file{margin-top:14px;color:#aab4c3;font-size:14px}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:14px}
label{display:block;color:#aab4c3;font-size:13px;margin-bottom:7px}
select,input[type=number]{width:100%;padding:10px;border-radius:9px;border:1px solid #303948;background:#0b1017;color:#fff}
button{border:0;border-radius:10px;padding:12px 18px;background:#6d8cff;color:#fff;font-weight:800;cursor:pointer}
button:disabled{opacity:.5;cursor:not-allowed}
pre{white-space:pre-wrap;word-break:break-word;background:#090c11;border-radius:10px;padding:14px;min-height:100px;max-height:360px;overflow:auto}
.status{margin-top:12px;color:#aab4c3}.ok{color:#83e1a5}.err{color:#ff8f8f}
a.download{display:inline-block;margin-top:12px;color:#b9c7ff;text-decoration:none;font-weight:700}
.small{font-size:12px;color:#7f8a99;line-height:1.5}
@media(max-width:700px){.grid{grid-template-columns:1fr}.wrap{padding:22px 12px}}
</style>
</head>
<body>
<div class="wrap">
<h1>Luraph Deobfuscator</h1>
<div class="sub">Browser interface for the bundled deobfuscation engine.</div>

<div class="card">
<form id="form">
<div id="drop" class="drop">
<label for="file" class="pick">Choose .lua / .luau file</label>
<input id="file" name="file" type="file" accept=".lua,.luau,.txt">
<div id="filename" class="file">No file selected</div>
</div>

<div class="grid" style="margin-top:16px">
<div>
<label for="budget">Budget (seconds)</label>
<input id="budget" name="budget" type="number" value="120" min="1" max="3600">
</div>
<div>
<label for="maxRuns">Maximum runs</label>
<input id="maxRuns" name="maxRuns" type="number" value="12" min="1" max="50">
</div>
</div>

<div style="margin-top:16px;display:flex;gap:10px;flex-wrap:wrap">
<label style="display:flex;gap:8px;align-items:center"><input id="noDevirt" name="noDevirt" type="checkbox"> Trace only</label>
<label style="display:flex;gap:8px;align-items:center"><input id="strings" name="strings" type="checkbox"> Dump strings</label>
<label style="display:flex;gap:8px;align-items:center"><input id="noHooks" name="noHooks" type="checkbox"> Disable hooks</label>
</div>

<div style="margin-top:18px">
<button id="run" type="submit">Deobfuscate</button>
<div id="status" class="status"></div>
</div>
</form>
</div>

<div class="card">
<strong>Output</strong>
<pre id="output">// Your result will appear here.</pre>
<a id="download" class="download" hidden>Download result</a>
<div class="small" style="margin-top:10px">Files are processed on the server. For public deployment, add authentication, rate limits, and a job timeout.</div>
</div>
</div>

<script>
const file=document.getElementById('file'), drop=document.getElementById('drop');
const nameEl=document.getElementById('filename'), run=document.getElementById('run');
const status=document.getElementById('status'), output=document.getElementById('output');
const download=document.getElementById('download');

file.addEventListener('change',()=>nameEl.textContent=file.files[0]?.name||'No file selected');
['dragenter','dragover'].forEach(e=>drop.addEventListener(e,x=>{x.preventDefault();drop.classList.add('drag')}));
['dragleave','drop'].forEach(e=>drop.addEventListener(e,x=>{x.preventDefault();drop.classList.remove('drag')}));
drop.addEventListener('drop',e=>{if(e.dataTransfer.files.length){file.files=e.dataTransfer.files;nameEl.textContent=file.files[0].name}});

document.getElementById('form').addEventListener('submit',async e=>{
 e.preventDefault();
 if(!file.files[0]){status.textContent='Choose a Lua/Luau file first.';status.className='status err';return}
 run.disabled=true; download.hidden=true; output.textContent='';
 status.textContent='Processing…'; status.className='status';
 const fd=new FormData(e.target);
 try{
   const r=await fetch('/api/deobfuscate',{method:'POST',body:fd});
   const data=await r.json();
   if(!r.ok||!data.ok) throw new Error(data.error||'Deobfuscation failed');
   output.textContent=data.output;
   status.textContent='Completed.';
   status.className='status ok';
   const blob=new Blob([data.output],{type:'text/plain;charset=utf-8'});
   download.href=URL.createObjectURL(blob);
   download.download=data.filename||'deobfuscated.luau';
   download.hidden=false;
 }catch(err){
   status.textContent=err.message; status.className='status err';
   output.textContent='No output.';
 }finally{run.disabled=false}
});
</script>
</body>
</html>"""

class Handler(BaseHTTPRequestHandler):
    server_version = "LuraphWeb/1.0"

    def send_json(self, code, obj):
        import json
        data=json.dumps(obj).encode()
        self.send_response(code)
        self.send_header("Content-Type","application/json; charset=utf-8")
        self.send_header("Content-Length",str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        route = urlparse(self.path).path
        if route == "/health":
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", "2")
            self.end_headers()
            self.wfile.write(b"OK")
            return
        if route in ("/", "/index.html"):
            data=INDEX.encode()
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length",str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_error(404)

    def do_POST(self):
        if urlparse(self.path).path != "/api/deobfuscate":
            self.send_error(404); return
        if int(self.headers.get("Content-Length","0")) > MAX_UPLOAD:
            self.send_json(413, {"ok":False,"error":"File is too large."}); return

        ctype=self.headers.get("Content-Type","")
        if not ctype.startswith("multipart/form-data"):
            self.send_json(400, {"ok":False,"error":"Expected multipart/form-data."}); return

        tmp=None
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            header_block = (f"Content-Type: {ctype}\r\nMIME-Version: 1.0\r\n\r\n").encode()
            message = BytesParser(policy=default).parsebytes(header_block + body)
            item = next((part for part in message.iter_parts()
                         if part.get_content_disposition() == "form-data"
                         and part.get_param("name", header="content-disposition") == "file"), None)
            if item is None:
                raise ValueError("No input file supplied.")

            name = Path(item.get_filename() or "input.lua").name
            if Path(name).suffix.lower() not in (".lua",".luau",".txt"):
                raise ValueError("Only .lua, .luau, and .txt files are accepted.")

            tmp=Path(tempfile.mkdtemp(prefix="luraph_web_"))
            inp=tmp / name
            with inp.open("wb") as f:
                f.write(item.get_payload(decode=True) or b"")

            fields = {}
            for part in message.iter_parts():
                if part.get_content_disposition() == "form-data":
                    field_name = part.get_param("name", header="content-disposition")
                    if field_name and field_name != "file":
                        payload = part.get_payload(decode=True) or b""
                        fields[field_name] = payload.decode("utf-8", "replace")

            budget=max(1,min(int(fields.get("budget","120")),3600))
            max_runs=max(1,min(int(fields.get("maxRuns","12")),50))
            args=[os.environ.get("NODE_BIN","node"),str(DEOB),str(inp),
                  "--budget",str(budget),"--max-runs",str(max_runs),
                  "-o",str(tmp/"result.luau")]
            if fields.get("noDevirt") == "on": args.append("--no-devirt")
            if fields.get("strings") == "on": args.append("--strings")
            if fields.get("noHooks") == "on": args.append("--no-hooks")

            env=os.environ.copy()
            env["PYTHONPATH"]=str(ROOT/"core")+os.pathsep+env.get("PYTHONPATH","")

            proc=subprocess.run(args,cwd=ROOT,env=env,text=True,
                                stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                                timeout=budget*max_runs+120)

            result=tmp/"result.luau"
            if not result.exists():
                # The CLI normally creates an output beside the input if -o
                # is not usable; fall back to any generated .luau file.
                candidates=list(tmp.glob("*.deobf.luau"))+list(tmp.glob("*.luau"))
                candidates=[x for x in candidates if x.name!="result.luau"]
                if candidates: result=candidates[0]

            if not result.exists():
                raise RuntimeError("Engine produced no output.\n\n"+proc.stdout[-12000:])

            text=result.read_text(encoding="utf-8",errors="replace")
            self.send_json(200,{"ok":True,"output":text,
                                "filename":Path(name).stem+".deobf.luau",
                                "log":proc.stdout[-12000:]})
        except subprocess.TimeoutExpired:
            self.send_json(504,{"ok":False,"error":"Processing timed out."})
        except Exception as e:
            self.send_json(500,{"ok":False,"error":str(e)})
        finally:
            if tmp:
                shutil.rmtree(tmp,ignore_errors=True)

if __name__=="__main__":
    print(f"Luraph web UI: http://127.0.0.1:{PORT}")
    ThreadingHTTPServer(("0.0.0.0",PORT),Handler).serve_forever()
