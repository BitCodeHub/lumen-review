#!/usr/bin/env python3
"""
Lumen QC Review — Render-deployed frontend
Calls DGX review API via ngrok
"""
import os
import httpx
from fastapi import FastAPI, Response
from fastapi.responses import HTMLResponse, RedirectResponse
import uvicorn

app = FastAPI()

DGX_API = os.environ.get("DGX_REVIEW_API", "https://roofless-melina-alcoholically.ngrok-free.dev")
TOKEN = "lumen-review-2026"

HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Lumen QC Review</title>
<style>
*{margin:0;padding:0;box-sizing:border-box;-webkit-tap-highlight-color:transparent}
body{background:#0a0a0a;color:#fff;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;height:100dvh;display:flex;flex-direction:column;overflow:hidden}
#header{padding:14px 16px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #1a1a1a;flex-shrink:0}
#header h1{font-size:15px;font-weight:700;letter-spacing:0.3px}
.stats{display:flex;gap:12px}
.stat{text-align:center}
.stat .n{font-size:16px;font-weight:700}
.stat .l{font-size:10px;color:#555;text-transform:uppercase;letter-spacing:0.5px}
.stat.a .n{color:#22c55e}
.stat.r .n{color:#ef4444}
#counter{font-size:12px;color:#555;background:#111;padding:4px 10px;border-radius:20px}
#img-wrap{flex:1;display:flex;align-items:center;justify-content:center;overflow:hidden;padding:10px;position:relative}
#img-wrap img{max-width:100%;max-height:100%;object-fit:contain;border-radius:10px;display:block}
#reason{padding:10px 16px;font-size:12px;color:#f59e0b;text-align:center;background:rgba(245,158,11,0.08);border-top:1px solid rgba(245,158,11,0.15);flex-shrink:0;min-height:38px;display:flex;align-items:center;justify-content:center;gap:6px}
#reason::before{content:"⚠️";flex-shrink:0}
#btns{display:flex;gap:10px;padding:12px;flex-shrink:0}
#btn-r{flex:1;background:#ef4444;color:#fff;border:none;border-radius:14px;padding:20px;font-size:18px;font-weight:800;cursor:pointer;active:scale(0.95)}
#btn-a{flex:1;background:#22c55e;color:#fff;border:none;border-radius:14px;padding:20px;font-size:18px;font-weight:800;cursor:pointer}
#btn-r:active{transform:scale(0.95);background:#dc2626}
#btn-a:active{transform:scale(0.95);background:#16a34a}
#state{display:flex;align-items:center;justify-content:center;flex:1;flex-direction:column;gap:12px;padding:20px;text-align:center}
#state h2{font-size:22px}
#state p{color:#666;font-size:14px;line-height:1.5}
#refresh-btn{margin-top:12px;padding:10px 24px;background:#1a1a1a;color:#fff;border:1px solid #333;border-radius:10px;cursor:pointer;font-size:14px}
</style>
</head>
<body>
<div id="header">
  <h1>🎨 Lumen Review</h1>
  <div style="display:flex;align-items:center;gap:10px">
    <div class="stats">
      <div class="stat a"><div class="n" id="na">0</div><div class="l">ok</div></div>
      <div class="stat r"><div class="n" id="nr">0</div><div class="l">out</div></div>
    </div>
    <div id="counter">loading...</div>
  </div>
</div>
<div id="state"><h2>⏳</h2><p>Loading queue...</p></div>

<script>
const DGX = '';  // calls through Render proxy
let queue=[], idx=0, na=0, nr=0;

async function load(){
  try{
    const r = await fetch('/proxy/queue');
    queue = await r.json();
    idx=0; show();
  }catch(e){
    showState('❌','Failed to load queue.<br>'+e.message,'retry');
  }
}

function show(){
  const wrap = document.getElementById('img-wrap');
  const reason = document.getElementById('reason');
  const btns = document.getElementById('btns');
  const st = document.getElementById('state');
  if(!wrap){buildUI();}
  if(idx>=queue.length){
    document.getElementById('img-wrap').style.display='none';
    document.getElementById('reason').style.display='none';
    document.getElementById('btns').style.display='none';
    showState('🎉','All done!<br>'+na+' approved · '+nr+' rejected<br><span style="color:#555;font-size:12px">Pull to refresh for new images</span>','refresh');
    return;
  }
  const item=queue[idx];
  document.getElementById('counter').textContent=(queue.length-idx)+' left';
  document.getElementById('reason').textContent=item.reason||'QC flagged';
  document.getElementById('img-wrap').style.display='flex';
  document.getElementById('reason').style.display='flex';
  document.getElementById('btns').style.display='flex';
  document.getElementById('state').style.display='none';
  document.getElementById('img-wrap').innerHTML='<img src="/proxy/image/'+encodeURIComponent(item.filename)+'" alt="" />';
  document.getElementById('na').textContent=na;
  document.getElementById('nr').textContent=nr;
}

function buildUI(){
  const st=document.getElementById('state');
  st.insertAdjacentHTML('beforebegin',
    '<div id="img-wrap" style="flex:1;display:flex;align-items:center;justify-content:center;overflow:hidden;padding:10px"></div>'+
    '<div id="reason" style="padding:10px 16px;font-size:12px;color:#f59e0b;text-align:center;background:rgba(245,158,11,0.08);border-top:1px solid rgba(245,158,11,0.15);flex-shrink:0;min-height:38px;display:flex;align-items:center;justify-content:center;gap:6px"></div>'+
    '<div id="btns" style="display:flex;gap:10px;padding:12px;flex-shrink:0"><button id="btn-r" onclick="decide(\'reject\')" style="flex:1;background:#ef4444;color:#fff;border:none;border-radius:14px;padding:20px;font-size:18px;font-weight:800;cursor:pointer">✕ Reject</button><button id="btn-a" onclick="decide(\'approve\')" style="flex:1;background:#22c55e;color:#fff;border:none;border-radius:14px;padding:20px;font-size:18px;font-weight:800;cursor:pointer">✓ Approve</button></div>'
  );
}

function showState(icon,msg,btn){
  const st=document.getElementById('state');
  st.style.display='flex';
  st.innerHTML='<h2>'+icon+'</h2><p>'+msg+'</p>'+
    (btn==='refresh'?'<button id="refresh-btn" onclick="location.reload()">Check for more</button>':
     btn==='retry'?'<button id="refresh-btn" onclick="load()">Retry</button>':'');
}

async function decide(action){
  if(idx>=queue.length) return;
  const item=queue[idx]; idx++;
  if(action==='approve') na++; else nr++;
  show();
  fetch('/proxy/'+action+'/'+encodeURIComponent(item.filename),{method:'POST'}).catch(()=>{});
}

document.addEventListener('keydown',e=>{
  if(e.key==='ArrowRight'||e.key==='a'||e.key==='A') decide('approve');
  if(e.key==='ArrowLeft'||e.key==='r'||e.key==='R') decide('reject');
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
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.get(f"{DGX_API}/api/queue", params={"token": TOKEN})
        return Response(content=r.content, media_type="application/json")

@app.get("/proxy/image/{filename}")
async def proxy_image(filename: str):
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.get(f"{DGX_API}/api/image/{filename}", params={"token": TOKEN})
        ct = r.headers.get("content-type", "image/jpeg")
        return Response(content=r.content, media_type=ct)

@app.post("/proxy/approve/{filename}")
async def proxy_approve(filename: str):
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(f"{DGX_API}/api/approve/{filename}", params={"token": TOKEN})
        return Response(content=r.content, media_type="application/json")

@app.post("/proxy/reject/{filename}")
async def proxy_reject(filename: str):
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(f"{DGX_API}/api/reject/{filename}", params={"token": TOKEN})
        return Response(content=r.content, media_type="application/json")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
