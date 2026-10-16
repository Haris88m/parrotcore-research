from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

from .brain import ParrotBrain
from .models import Event, EventKind
from .reference import reference_joints
from .simulation import SimulationAssumptions, effectiveness, metrics_dict
from .skills._motions import MOTIONS


HTML = r'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ParrotCore 3D Studio</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#0d0f12;color:#eef2f5;font:14px/1.4 system-ui,sans-serif}
header{padding:18px 22px;border-bottom:1px solid #2a3038;background:#12161b;display:flex;justify-content:space-between;align-items:center}
h1{font-size:20px;margin:0}small{color:#8e9aa8}.layout{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(320px,.75fr);gap:14px;padding:14px;max-width:1500px;margin:auto}
.card{background:#15191f;border:1px solid #2a3038;border-radius:14px;padding:14px;overflow:hidden}.viewer{padding:0;position:relative;min-height:620px}
canvas{display:block;width:100%;height:620px;background:radial-gradient(circle at 50% 38%,#202833 0,#11161c 60%,#090b0e 100%);touch-action:none}
.overlay{position:absolute;left:14px;top:12px;background:#0b0e12bb;padding:9px 11px;border:1px solid #303943;border-radius:10px;backdrop-filter:blur(5px)}
.overlay b{display:block}.legend{font-size:12px;color:#aab5c1;margin-top:4px}.right{display:flex;flex-direction:column;gap:14px}h2{font-size:15px;margin:0 0 10px}.row{display:flex;flex-wrap:wrap;gap:7px}
button,input{font:inherit;border-radius:9px;border:1px solid #46505c;background:#222831;color:#f5f7fa;padding:9px 11px}button{cursor:pointer}button:hover{background:#2b333d}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:8px}.joint{background:#10141a;border:1px solid #272e36;border-radius:10px;padding:8px}.joint label{display:flex;justify-content:space-between;font-size:12px;color:#bcc6d0}.joint input{width:100%;padding:0;margin-top:7px}.value{font-variant-numeric:tabular-nums;color:#fff}
.metrics{display:grid;grid-template-columns:1fr 1fr;gap:7px}.metric{background:#10141a;border:1px solid #272e36;border-radius:10px;padding:8px}.metric strong{display:block;font-size:17px}.metric span{font-size:11px;color:#95a1ad}
pre{white-space:pre-wrap;color:#b6e8bf;font-size:11px;max-height:160px;overflow:auto}.badge{display:inline-block;border:1px solid #405064;border-radius:999px;padding:3px 8px;color:#a9c8ef;font-size:11px}
.warn{color:#ffd38c}.ok{color:#9de3ad}@media(max-width:900px){.layout{grid-template-columns:1fr}.viewer{min-height:480px}canvas{height:480px}.grid{grid-template-columns:1fr}}
</style></head><body>
<header><div><h1>ParrotCore 3D Studio <small>v0.3</small></h1><small>8-DOF digital twin / behavior simulation</small></div><span class="badge" id="simBadge">SIMULATION</span></header>
<div class="layout">
  <div class="card viewer"><canvas id="view"></canvas><div class="overlay"><b id="behavior">Home pose</b><div id="poseSummary" class="legend">Drag to orbit · wheel to zoom</div></div></div>
  <div class="right">
    <div class="card"><h2>Behavior</h2><div class="row">
      <button onclick="command('hello')">Greet</button><button onclick="command('look left')">Look left</button><button onclick="command('look right')">Look right</button><button onclick="command('blink')">Blink</button><button onclick="command('dance')">Dance</button><button onclick="home()">Home</button>
    </div><div class="row" style="margin-top:8px"><input id="phrase" style="flex:1" placeholder="Type an event phrase"><button onclick="command(phrase.value)">Send</button></div></div>
    <div class="card"><h2>Joint inspector</h2><div class="grid" id="joints"></div></div>
    <div class="card"><h2>Effective properties</h2><div class="metrics" id="metrics"></div><p class="legend warn">Power/mass values are engineering assumptions until the physical prototype is measured.</p></div>
    <div class="card"><h2>Teaching memory</h2><div class="row"><input id="trigger" placeholder="trigger"><input id="response" placeholder="response"><button onclick="teach()">Teach</button></div></div>
    <div class="card"><h2>Runtime state</h2><div class="row"><button onclick="status()">Refresh</button><button onclick="estop(true)">E-stop</button><button onclick="estop(false)">Reset E-stop</button></div><pre id="out">Ready.</pre></div>
  </div>
</div>
<script>
const canvas=document.getElementById('view'),ctx=canvas.getContext('2d');
let dpr=window.devicePixelRatio||1, cam={yaw:-0.55,pitch:0.22,dist:0.75},drag=null;
let joints={},pose={},motions={},activeAnim=0,simMetrics={};
function resize(){let r=canvas.getBoundingClientRect();canvas.width=Math.max(1,r.width*dpr);canvas.height=Math.max(1,r.height*dpr);draw()} window.addEventListener('resize',resize);
function Rz(v,a){a*=Math.PI/180;let c=Math.cos(a),s=Math.sin(a);return [v[0]*c-v[1]*s,v[0]*s+v[1]*c,v[2]]}
function Rx(v,a){a*=Math.PI/180;let c=Math.cos(a),s=Math.sin(a);return [v[0],v[1]*c-v[2]*s,v[1]*s+v[2]*c]}
function add(a,b){return [a[0]+b[0],a[1]+b[1],a[2]+b[2]]}
function body(v,lean){return add([0,0,.17],Rx(v,-lean))}
function geom(p){let yaw=+p.neck_yaw||0,pitch=+p.neck_pitch||0,beak=+p.beak||0,wl=+p.wing_left||0,wr=+p.wing_right||0,tail=+p.tail_pitch||0,lids=+p.eyelids||0,lean=+p.body_lean||0;
 let C=body([0,0,0],lean),top=body([0,.005,.105],lean),bot=body([0,0,-.095],lean),chest=body([0,.035,.025],lean),nb=body([0,.012,.11],lean);
 let nv=Rz(Rx([0,.018,.068],-pitch),-yaw),hc=add(nb,nv),fw=Rz(Rx([0,1,0],-pitch),-yaw),rt=Rz([1,0,0],-yaw),up=Rz(Rx([0,0,1],-pitch),-yaw);
 function hl(x,y,z){return [hc[0]+rt[0]*x+fw[0]*y+up[0]*z,hc[1]+rt[1]*x+fw[1]*y+up[1]*z,hc[2]+rt[2]*x+fw[2]*y+up[2]*z]}
 let bb=hl(0,.041,-.004),bt=hl(0,.078,-.004-.00045*beak),el=hl(-.023,.022,.016),er=hl(.023,.022,.016),ld=.00017*lids,ll=hl(-.023,.023,.025-ld),lr=hl(.023,.023,.025-ld);
 let wlh=body([-.064,0,.045],lean),wrh=body([.064,0,.045],lean); function wt(side,a){a*=Math.PI/180;return body([side*(.085+.075*Math.sin(a)),-.018,-.05+.105*Math.sin(a)],lean)}
 let wlt=wt(-1,wl),wrt=wt(1,wr),wlm=wlh.map((x,i)=>(x+wlt[i])/2),wrm=wrh.map((x,i)=>(x+wrt[i])/2),tb=body([0,-.055,-.035],lean),tt=add(tb,Rx(Rx([0,-.12,-.018],tail),-lean));
 let q={pl:[-.22,0,0],pr:[.22,0,0],fl:[-.032,0,.018],fr:[.032,0,.018],C,top,bot,chest,nb,hc,bb,bt,el,er,ll,lr,wlh,wrh,wlm,wrm,wlt,wrt,tb,tt};
 let seg=[['pl','pr','perch'],['fl','bot','leg'],['fr','bot','leg'],['bot','C','body'],['C','top','body'],['C','chest','body'],['top','nb','neck'],['nb','hc','neck'],['hc','bb','head'],['bb','bt','beak'],['hc','el','face'],['hc','er','face'],['el','ll','lid'],['er','lr','lid'],['wlh','wlm','wing'],['wlm','wlt','wing'],['wrh','wrm','wing'],['wrm','wrt','wing'],['tb','tt','tail']];return {q,seg}}
function project(v){let cy=Math.cos(cam.yaw),sy=Math.sin(cam.yaw),cp=Math.cos(cam.pitch),sp=Math.sin(cam.pitch);let x=cy*v[0]-sy*v[1],y=sy*v[0]+cy*v[1],z=v[2]-.16;let y2=cp*y-sp*z,z2=sp*y+cp*z;let f=cam.dist/(cam.dist+y2+.55);return [canvas.width/2+x*f*900*dpr,canvas.height*.55-z2*f*900*dpr,f]}
const styles={perch:['#b07b4f',9],leg:['#9a9a9a',4],body:['#62c08b',13],neck:['#70d49a',10],head:['#8ee3ae',9],beak:['#efb25d',8],face:['#dce7ef',3],lid:['#7c8b97',3],wing:['#4aa777',12],tail:['#39936a',10]};
function draw(){if(!canvas.width)return;ctx.clearRect(0,0,canvas.width,canvas.height);let g=geom(pose);let items=g.seg.map(s=>{let a=project(g.q[s[0]]),b=project(g.q[s[1]]);return {a,b,k:s[2],depth:(a[2]+b[2])/2}}).sort((a,b)=>a.depth-b.depth);ctx.lineCap='round';for(let it of items){let st=styles[it.k]||['#fff',3];ctx.strokeStyle=st[0];ctx.lineWidth=st[1]*dpr*it.depth;ctx.beginPath();ctx.moveTo(it.a[0],it.a[1]);ctx.lineTo(it.b[0],it.b[1]);ctx.stroke()}
 for(let n of ['el','er']){let p=project(g.q[n]);ctx.fillStyle='#111';ctx.beginPath();ctx.arc(p[0],p[1],5*dpr*p[2],0,Math.PI*2);ctx.fill()}
 document.getElementById('poseSummary').textContent=`yaw ${Math.round(pose.neck_yaw||0)}° · pitch ${Math.round(pose.neck_pitch||0)}° · wings ${Math.round(pose.wing_left||0)}/${Math.round(pose.wing_right||0)}°`}
canvas.onpointerdown=e=>{drag=[e.clientX,e.clientY,cam.yaw,cam.pitch];canvas.setPointerCapture(e.pointerId)};canvas.onpointermove=e=>{if(!drag)return;cam.yaw=drag[2]+(e.clientX-drag[0])*.008;cam.pitch=Math.max(-1.0,Math.min(1.0,drag[3]+(e.clientY-drag[1])*.006));draw()};canvas.onpointerup=()=>drag=null;canvas.onwheel=e=>{e.preventDefault();cam.dist=Math.max(.35,Math.min(1.4,cam.dist+e.deltaY*.0006));draw()};
function buildJointUI(){let root=document.getElementById('joints');root.innerHTML='';for(let [name,s] of Object.entries(joints)){let d=document.createElement('div');d.className='joint';d.innerHTML=`<label><span>${name}</span><span class="value" id="v_${name}">${s.home}</span></label><input id="j_${name}" type="range" min="${s.minimum}" max="${s.maximum}" step="1" value="${s.home}">`;root.appendChild(d);let inp=d.querySelector('input');inp.oninput=()=>{pose[name]=+inp.value;document.getElementById('v_'+name).textContent=inp.value;draw()}}}
function syncSliders(){for(let [n,v] of Object.entries(pose)){let e=document.getElementById('j_'+n);if(e){e.value=v;document.getElementById('v_'+n).textContent=Math.round(v)}}}
function smooth(t){return t*t*(3-2*t)}
async function animateFrames(frames,label){let token=++activeAnim;document.getElementById('behavior').textContent=label;for(let f of frames){if(token!==activeAnim)return;let start={...pose},target={...pose,...f.positions},dur=Math.max(.02,+f.duration_s||.25),t0=performance.now();await new Promise(resolve=>{function step(now){if(token!==activeAnim)return resolve();let t=Math.min(1,(now-t0)/(dur*1000)),u=smooth(t);for(let k of Object.keys(target))pose[k]=(start[k]||0)+(target[k]-(start[k]||0))*u;syncSliders();draw();if(t<1)requestAnimationFrame(step);else resolve()}requestAnimationFrame(step)})}}
function actionFrames(actions){let out=[];for(let a of actions){if(a.kind==='motion'&&motions[a.payload.name])out.push(...motions[a.payload.name]);if(a.kind==='pose')out.push({positions:a.payload.positions,duration_s:a.payload.duration_s||.25})}return out}
async function post(url,data){let r=await fetch(url,{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify(data)});return await r.json()}
async function command(v){if(!v)return;let r=await post('/api/event',{kind:'phrase',value:v});out.textContent=JSON.stringify(r,null,2);let fs=actionFrames(r.actions||[]);if(fs.length)animateFrames(fs,v);else document.getElementById('behavior').textContent=v}
function home(){++activeAnim;for(let [n,s] of Object.entries(joints))pose[n]=s.home;syncSliders();draw();document.getElementById('behavior').textContent='Home pose'}
async function teach(){let r=await post('/api/teach',{trigger:trigger.value,response:response.value});out.textContent=JSON.stringify(r,null,2)}
async function status(){let r=await fetch('/api/status').then(r=>r.json());out.textContent=JSON.stringify(r,null,2)}
async function estop(active){let r=await post('/api/estop',{active});out.textContent=JSON.stringify(r,null,2);simBadge.textContent=active?'E-STOP LATCHED':'SIMULATION'}
function renderMetrics(){let m=simMetrics, entries=[['8 DOF',m.degrees_of_freedom+' joints'],['Neck yaw',m.neck_yaw_span_deg+'°'],['Neck pitch',m.neck_pitch_span_deg+'°'],['Wing command',m.wing_span_command_deg+'°'],['Watchdog',m.watchdog_cutoff_s+' s'],['Typical motion',m.system_typical_motion_w.toFixed(1)+' W*'],['Peak budget',m.system_peak_w.toFixed(1)+' W*'],['Target size',Math.round(m.target_height_m*100)+' cm*']];let root=document.getElementById('metrics');root.innerHTML='';for(let [label,val] of entries){let d=document.createElement('div');d.className='metric';d.innerHTML=`<strong>${val}</strong><span>${label}</span>`;root.appendChild(d)}}
async function init(){let cfg=await fetch('/api/simulation').then(r=>r.json());joints=cfg.joints;motions=cfg.motions;simMetrics=cfg.metrics;for(let [n,s] of Object.entries(joints))pose[n]=s.home;buildJointUI();renderMetrics();resize();status()}init();
</script></body></html>'''


def _joint_payload() -> dict[str, dict[str, float]]:
    return {
        name: {"minimum": spec.minimum, "maximum": spec.maximum, "home": spec.home}
        for name, spec in reference_joints().items()
    }


def _motion_payload() -> dict[str, list[dict[str, object]]]:
    return {
        name: [{"positions": dict(frame.positions), "duration_s": frame.duration_s} for frame in frames]
        for name, frames in MOTIONS.items()
    }


def make_handler(brain: ParrotBrain):
    class Handler(BaseHTTPRequestHandler):
        def _json(self, payload, status=HTTPStatus.OK):
            raw = json.dumps(payload).encode("utf-8")
            self.send_response(status)
            self.send_header("content-type", "application/json")
            self.send_header("content-length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/":
                raw = HTML.encode("utf-8")
                self.send_response(200)
                self.send_header("content-type", "text/html; charset=utf-8")
                self.send_header("content-length", str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)
                return
            if path == "/api/status":
                self._json({"body": brain.body.status(), "learned": brain.memory.all()})
                return
            if path == "/api/simulation":
                self._json({
                    "joints": _joint_payload(),
                    "motions": _motion_payload(),
                    "metrics": metrics_dict(effectiveness(reference_joints(), SimulationAssumptions())),
                    "classification": "conceptual kinematic digital twin",
                })
                return
            self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

        def do_POST(self):
            path = urlparse(self.path).path
            try:
                n = int(self.headers.get("content-length", "0"))
                data = json.loads(self.rfile.read(n) or b"{}")
                if path == "/api/event":
                    event = Event(EventKind(data.get("kind", "phrase")), str(data["value"]))
                    actions = brain.emit(event)
                    self._json({"ok": True, "actions": [{"kind": a.kind, "payload": a.payload} for a in actions]})
                    return
                if path == "/api/teach":
                    brain.memory.teach(str(data["trigger"]), str(data["response"]))
                    self._json({"ok": True, "learned": brain.memory.all()})
                    return
                if path == "/api/estop":
                    active = bool(data.get("active", True))
                    if hasattr(brain.body, "estop"):
                        brain.body.estop(active)
                    elif active:
                        brain.body.safety.latch_estop()
                    else:
                        brain.body.safety.reset_estop()
                    self._json({"ok": True, "estop": active, "body": brain.body.status()})
                    return
                self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            except Exception as exc:
                self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

        def log_message(self, fmt, *args):
            return

    return Handler


def serve(brain: ParrotBrain, host: str = "127.0.0.1", port: int = 8765) -> None:
    server = HTTPServer((host, port), make_handler(brain))
    print(f"ParrotCore 3D Studio: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
