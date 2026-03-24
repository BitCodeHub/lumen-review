#!/usr/bin/env python3
"""Lumen QC Review — Render frontend, calls DGX review API"""
import os, httpx
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()
DGX_API = os.environ.get("DGX_REVIEW_API", "https://lumen-review.ngrok.app")
TOKEN = "lumen-review-2026"
HEADERS = {"X-Review-Token": TOKEN}

HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Lumen QC Review</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{background:#0a0a0a;color:#fff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;height:100dvh;display:flex;flex-direction:column;overflow:hidden}
#hdr{padding:12px 16px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1a1a1a;flex-shrink:0}
#hdr h1{font-size:15px;font-weight:700}
.stats{display:flex;gap:14px}
.stat .n{font-size:17px;font-weight:800;text-align:center}
.stat .l{font-size:10px;color:#555;text-transform:uppercase;text-align:center}
.stat.a .n{color:#22c55e}.stat.r .n{color:#ef4444}
#counter{font-size:12px;color:#666;background:#111;padding:3px 10px;border-radius:20px}
#img-wrap{flex:1;display:flex;align-items:center;justify-content:center;overflow:hidden;padding:10px}
#img-wrap img{max-width:100%;max-height:100%;object-fit:contain;border-radius:10px}
#reason{padding:8px 16px;font-size:12px;color:#f59e0b;text-align:center;background:rgba(245,158,11,0.07);border-top:1px solid rgba(245,158,11,0.12);flex-shrink:0;min-height:34px;display:flex;align-items:center;justify-content:center;gap:6px}
#btns{display:flex;gap:10px;padding:14px;flex-shrink:0}
.btn{flex:1;border:none;border-radius:14px;padding:20px;font-size:20px;font-weight:800;cursor:pointer;transition:transform .1s}
.btn:active{transform:scale(0.94)}
#st{display:flex;align-items:center;justify-content:center;flex:1;flex-direction:column;gap:12px;text-align:center;padding:20px}
#st h2{font-size:24px}#st p{color:#666;font-size:14px;line-height:1.6}
#rbtn{margin-top:8px;padding:10px 22px;background:#1a1a1a;color:#fff;border:1px solid #333;border-radius:10px;cursor:pointer;font-size:14px}
</style>
</head>
<body>
<div id="hdr">
  <h1>🎨 Lumen Review</h1>
  <div style="display:flex;align-items:center;gap:10px">
    <div class="stats">
      <div class="stat a"><div class="n" id="na">0</div><div class="l">ok</div></div>
      <div class="stat r"><div class="n" id="nr">0</div><div class="l">out</div></div>
    </div>
    <div id="counter">loading...</div>
  </div>
</div>
<div id="st"><h2>⏳</h2><p>Loading...</p></div>

<script>
let q=[], i=0, na=0, nr=0;

async function load(){
  try{
    const r=await fetch('/proxy/queue');
    const d=await r.json();
    q=d.images||d;
    i=0; show();
  }catch(e){setState('❌','Failed: '+e.message,'retry');}
}

function show(){
  if(i>=q.length){
    cleanup();
    setState('🎉','All done!<br>'+na+' approved · '+nr+' rejected<br><span style="color:#555;font-size:12px">Pull to refresh</span>','refresh');
    return;
  }
  const item=q[i];
  document.getElementById('counter').textContent=(q.length-i)+' left';
  document.getElementById('na').textContent=na;
  document.getElementById('nr').textContent=nr;
  ensureUI();
  document.getElementById('reason').textContent=item.reject_reason||item.reason||'QC flagged';
  document.getElementById('img-wrap').innerHTML=\'<img src="/proxy/image/\'+encodeURIComponent(item.filename)+\'" alt="" />\';
}

function ensureUI(){
  const st=document.getElementById('st');
  st.style.display='none';
  let iw=document.getElementById('img-wrap');
  if(!iw){
    st.insertAdjacentHTML(\'beforebegin\',
      \'<div id="img-wrap"></div>\'+
      \'<div id="reason"></div>\'+
      \'<div id="btns"><button class="btn" style="background:#ef4444" onclick="decide(\'reject\')">✕ Reject</button><button class="btn" style="background:#22c55e" onclick="decide(\'approve\')">✓ Approve</button></div>\'
    );
  }
}

function cleanup(){
  [\'img-wrap\',\'reason\',\'btns\'].forEach(id=>{const el=document.getElementById(id);if(el)el.remove()});
}

function setState(ic,msg,btn){
  cleanup();
  const st=document.getElementById(\'st\');
  st.style.display=\'flex\';
  st.innerHTML=\'<h2>\'+ic+\'</h2><p>\'+msg+\'</p>\'+
    (btn===\'refresh\'?\'<button id="rbtn" onclick="location.reload()">Check for more</button>\':
     btn===\'retry\'?\'<button id="rbtn" onclick="load()">Retry</button>\':\'\'
  );
}

async function decide(action){
  if(i>=q.length)return;
  const item=q[i]; i++;
  if(action===\'approve\')na++;else nr++;
  show();
  fetch(\'/proxy/\'+action+\'/\'+encodeURIComponent(item.filename),{method:\'POST\'}).catch(()=>{});
}

document.addEventListener(\'keydown\',e=>{
  if(e.key===\'ArrowRight\'||e.key===\'a\'||e.key===\'A\')decide(\'approve\');
  if(e.key===\'ArrowLeft\'||e.key===\'r\'||e.key===\'R\')decide(\'reject\');
});
load();
</script>
</body>
</html>
'''

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTML

@app.get("/proxy/queue")
async def proxy_queue():
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(f"{DGX_API}/queue", headers=HEADERS)
        return Response(content=r.content, media_type="application/json")

@app.get("/proxy/image/{filename}")
async def proxy_image(filename: str):
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.get(f"{DGX_API}/image/{filename}", headers=HEADERS)
        return Response(content=r.content, media_type=r.headers.get("content-type","image/jpeg"))

@app.post("/proxy/approve/{filename}")
async def proxy_approve(filename: str):
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f"{DGX_API}/approve/{filename}", headers=HEADERS)
        return Response(content=r.content, media_type="application/json")

@app.post("/proxy/reject/{filename}")
async def proxy_reject(filename: str):
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(f"{DGX_API}/reject/{filename}", headers=HEADERS)
        return Response(content=r.content, media_type="application/json")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
