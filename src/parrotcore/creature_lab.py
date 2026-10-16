from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .embodiment import CreatureRegistry
from .kinematics import compute_creature_geometry
from .memory import MemoryStore
from .models import Event, EventKind
from .runtime import simulated_runtime
from .simulation import creature_effectiveness, interpolate_motion, metrics_dict


HTML = r'''<!doctype html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>ParrotCore Creature Lab</title>
<style>
:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#0b0e12;color:#eef2f5;font:14px/1.4 system-ui,sans-serif}
header{padding:16px 20px;border-bottom:1px solid #29313a;background:#11161c;display:flex;justify-content:space-between;gap:15px;align-items:center}h1{font-size:20px;margin:0}small{color:#8e9baa}.layout{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(340px,.8fr);gap:14px;padding:14px;max-width:1500px;margin:auto}.card{background:#141920;border:1px solid #29313a;border-radius:14px;padding:13px}.viewer{padding:0;overflow:hidden;position:relative}canvas{display:block;width:100%;height:650px;background:radial-gradient(circle at 50% 38%,#222b36 0,#11161d 60%,#090b0e 100%);touch-action:none}.overlay{position:absolute;top:12px;left:12px;background:#07090dbb;border:1px solid #313a45;border-radius:10px;padding:8px 10px}.right{display:flex;flex-direction:column;gap:12px}h2{font-size:14px;margin:0 0 9px}.row{display:flex;flex-wrap:wrap;gap:7px}button,select,input{font:inherit;border:1px solid #46515e;border-radius:9px;background:#222a33;color:#f5f7fa;padding:8px 10px}button{cursor:pointer}.joint{display:grid;grid-template-columns:110px 1fr 48px;align-items:center;gap:6px;padding:5px 0}.joint input{padding:0;width:100%}.metrics{display:grid;grid-template-columns:1fr 1fr;gap:7px}.metric{background:#0f141a;border:1px solid #262f38;border-radius:9px;padding:8px}.metric strong{display:block;font-size:16px}.metric span{font-size:11px;color:#99a6b3}.caps{display:flex;gap:5px;flex-wrap:wrap}.tag{border:1px solid #3b4a59;border-radius:999px;padding:3px 7px;font-size:11px;color:#bed3e7}pre{max-height:150px;overflow:auto;white-space:pre-wrap;color:#bcecc4;font-size:11px}.warn{font-size:11px;color:#f4ce8e}@media(max-width:900px){.layout{grid-template-columns:1fr}canvas{height:500px}}
</style></head><body>
<header><div><h1>ParrotCore Creature Lab <small>v0.4</small></h1><small>One semantic brain · interchangeable embodiments</small></div><select id="species" onchange="selectSpecies(this.value)"></select></header>
<div class="layout"><div class="card viewer"><canvas id="view"></canvas><div class="overlay"><b id="role">Loading…</b><div><small>Drag to orbit · wheel to zoom</small></div></div></div><div class="right">
<div class="card"><h2>Semantic behavior</h2><div class="row"><button onclick="eventPhrase('hello')">Greet</button><button onclick="eventPhrase('look left')">Attend left</button><button onclick="eventPhrase('look right')">Attend right</button><button onclick="eventPhrase('curious')">Curious</button><button onclick="eventPhrase('yes')">Affirm</button><button onclick="eventPhrase('blink')">Blink</button><button onclick="eventPhrase('dance')">Dance</button><button onclick="eventPhrase('home')">Home</button></div><div class="row" style="margin-top:8px"><input id="phrase" style="flex:1" placeholder="phrase"><button onclick="eventPhrase(phrase.value)">Send</button></div></div>
<div class="card"><h2>Creature capabilities</h2><div id="caps" class="caps"></div></div>
<div class="card"><h2>Joint inspector</h2><div id="joints"></div></div>
<div class="card"><h2>Effective properties</h2><div class="metrics" id="metrics"></div><div class="warn">Power, mass and height are simulation assumptions until measured on physical prototypes.</div></div>
<div class="card"><h2>Teaching memory</h2><div class="row"><input id="trigger" placeholder="trigger"><input id="response" placeholder="response"><button onclick="teach()">Teach</button></div></div>
<div class="card"><h2>Safety / runtime</h2><div class="row"><button onclick="estop(true)">E-stop</button><button onclick="estop(false)">Reset</button><button onclick="status()">Status</button></div><pre id="out">Ready.</pre></div>
</div></div>
<script>
const canvas=document.getElementById('view'),ctx=canvas.getContext('2d');let dpr=devicePixelRatio||1,cam={yaw:-.55,pitch:.22,dist:.82},drag=null,profile=null,pose={},geometry=null,animToken=0;
function resize(){let r=canvas.getBoundingClientRect();canvas.width=r.width*dpr;canvas.height=r.height*dpr;draw()}addEventListener('resize',resize);
function project(v){let cy=Math.cos(cam.yaw),sy=Math.sin(cam.yaw),cp=Math.cos(cam.pitch),sp=Math.sin(cam.pitch);let x=cy*v[0]-sy*v[1],y=sy*v[0]+cy*v[1],z=v[2]-.16,y2=cp*y-sp*z,z2=sp*y+cp*z,f=cam.dist/(cam.dist+y2+.58);return [canvas.width/2+x*f*880*dpr,canvas.height*.57-z2*f*880*dpr,f]}
const stroke={perch:'#a77b50',leg:'#9aa1a8',body:'#70b88a',neck:'#7fc69a',head:'#9cd5ad',beak:'#e1ae62',face:'#dce7ee',lid:'#75828e',wing:'#4b9e70',tail:'#3f8a64'};
function draw(){if(!geometry)return;ctx.clearRect(0,0,canvas.width,canvas.height);let pts=geometry.points;let seg=geometry.segments.map(s=>{let a=project(pts[s[0]]),b=project(pts[s[1]]);return {a,b,k:s[2],d:(a[2]+b[2])/2}}).sort((a,b)=>a.d-b.d);ctx.lineCap='round';for(let s of seg){ctx.strokeStyle=stroke[s.k]||'#fff';ctx.lineWidth=(s.k==='body'||s.k==='wing'?10:s.k==='head'||s.k==='neck'?8:4)*dpr*s.d;ctx.beginPath();ctx.moveTo(s.a[0],s.a[1]);ctx.lineTo(s.b[0],s.b[1]);ctx.stroke()}for(let n of ['eye_l','eye_r'])if(pts[n]){let p=project(pts[n]);ctx.fillStyle='#101215';ctx.beginPath();ctx.arc(p[0],p[1],5*dpr*p[2],0,Math.PI*2);ctx.fill()}}
canvas.onpointerdown=e=>{drag=[e.clientX,e.clientY,cam.yaw,cam.pitch];canvas.setPointerCapture(e.pointerId)};canvas.onpointermove=e=>{if(!drag)return;cam.yaw=drag[2]+(e.clientX-drag[0])*.008;cam.pitch=Math.max(-1,Math.min(1,drag[3]+(e.clientY-drag[1])*.006));draw()};canvas.onpointerup=()=>drag=null;canvas.onwheel=e=>{e.preventDefault();cam.dist=Math.max(.35,Math.min(1.5,cam.dist+e.deltaY*.0006));draw()};
async function api(path,method='GET',data=null){let opt={method,headers:{'content-type':'application/json'}};if(data)opt.body=JSON.stringify(data);let r=await fetch(path,opt),j=await r.json();if(!r.ok)throw Error(j.error||r.status);return j}
function buildJoints(){let root=document.getElementById('joints');root.innerHTML='';for(let [name,s] of Object.entries(profile.joints)){let d=document.createElement('div');d.className='joint';d.innerHTML=`<span>${name}</span><input type="range" min="${s.minimum}" max="${s.maximum}" step="1" value="${pose[name]}"><span id="v_${name}">${Math.round(pose[name])}</span>`;let inp=d.querySelector('input');inp.oninput=async()=>{pose[name]=+inp.value;document.getElementById('v_'+name).textContent=Math.round(pose[name]);let j=await api('/api/geometry','POST',{pose});geometry=j.geometry;draw()};root.appendChild(d)}}
function syncJoints(){for(let [n,v] of Object.entries(pose)){let rows=[...document.querySelectorAll('.joint')];let row=rows.find(x=>x.firstChild.textContent===n);if(row){row.querySelector('input').value=v;document.getElementById('v_'+n).textContent=Math.round(v)}}}
function buildMetrics(m){let wanted=[['degrees_of_freedom','DOF'],['expression_count','Expressions'],['yaw_span_deg','Yaw span °'],['pitch_span_deg','Pitch span °'],['system_typical_motion_w','Typical W*'],['system_peak_w','Peak W*'],['estimated_mass_kg','Mass kg*'],['target_height_m','Height m*']];metrics.innerHTML=wanted.map(([k,l])=>`<div class="metric"><strong>${typeof m[k]==='number'?Math.round(m[k]*100)/100:m[k]}</strong><span>${l}</span></div>`).join('')}
async function init(){let j=await api('/api/profiles');species.innerHTML=j.species.map(s=>`<option>${s}</option>`).join('');await selectSpecies(j.current)}
async function selectSpecies(s){animToken++;let j=await api('/api/select','POST',{species:s});profile=j.profile;pose={...j.pose};geometry=j.geometry;species.value=s;role.textContent=`${s.toUpperCase()} — ${profile.role}`;caps.innerHTML=profile.capabilities.map(c=>`<span class="tag">${c}</span>`).join('');buildJoints();buildMetrics(j.metrics);draw();out.textContent=`Selected ${s}. Semantic intents stay the same; joint expression changed.`}
async function eventPhrase(value){if(!value)return;let j=await api('/api/event','POST',{value});out.textContent=JSON.stringify(j.actions,null,2);await animate(j.animation);pose={...j.pose};syncJoints()}
async function animate(frames){let token=++animToken;for(let f of frames){if(token!==animToken)return;geometry=f.geometry;pose=f.pose;syncJoints();draw();await new Promise(r=>setTimeout(r,Math.max(15,f.dt_ms)))} }
async function teach(){let j=await api('/api/teach','POST',{trigger:trigger.value,response:response.value});out.textContent=JSON.stringify(j.learned,null,2)}
async function estop(active){let j=await api('/api/estop','POST',{active});out.textContent=JSON.stringify(j,null,2)}
async function status(){out.textContent=JSON.stringify(await api('/api/status'),null,2)}
init().then(resize).catch(e=>out.textContent=e.stack);
</script></body></html>'''


def _profile_payload(profile):
    return {
        "name": profile.name,
        "species": profile.species,
        "morphology": profile.morphology,
        "role": profile.role,
        "capabilities": sorted(profile.capabilities),
        "joints": {
            n: {"minimum": s.minimum, "maximum": s.maximum, "home": s.home, "max_speed": s.max_speed}
            for n, s in profile.joints.items()
        },
        "expressions": sorted(profile.expressions),
    }


def _geometry_payload(profile, pose):
    g = compute_creature_geometry(profile, pose)
    return {
        "species": g.species,
        "points": {k: list(v) for k, v in g.points.items()},
        "segments": [list(x) for x in g.segments],
    }


class CreatureSession:
    def __init__(self, registry: CreatureRegistry, memory: MemoryStore):
        self.registry = registry
        self.memory = memory
        self.species = "parrot" if "parrot" in registry.species() else registry.species()[0]
        self.brain = simulated_runtime(registry.get(self.species), memory)

    @property
    def profile(self):
        return self.registry.get(self.species)

    def select(self, species: str):
        self.species = species
        self.brain = simulated_runtime(self.registry.get(species), self.memory)


def make_handler(session: CreatureSession):
    class Handler(BaseHTTPRequestHandler):
        def _json(self, data, status=HTTPStatus.OK):
            raw = json.dumps(data).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers(); self.wfile.write(raw)

        def _read(self):
            n = int(self.headers.get("content-length", "0"))
            return json.loads(self.rfile.read(n) or b"{}")

        def do_GET(self):
            path = urlparse(self.path).path
            if path == "/":
                raw = HTML.encode("utf-8")
                self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(raw))); self.end_headers(); self.wfile.write(raw); return
            if path == "/api/profiles":
                self._json({"species": session.registry.species(), "current": session.species}); return
            if path == "/api/status":
                self._json({"species": session.species, "body": session.brain.body.status(), "learned": session.memory.all()}); return
            self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)

        def do_POST(self):
            path = urlparse(self.path).path
            try:
                data = self._read()
                if path == "/api/select":
                    session.select(str(data["species"]))
                    p = session.profile; pose = dict(session.brain.body.positions)
                    self._json({"profile": _profile_payload(p), "pose": pose, "geometry": _geometry_payload(p, pose), "metrics": metrics_dict(creature_effectiveness(p))}); return
                if path == "/api/geometry":
                    pose = {k: float(v) for k, v in data.get("pose", {}).items()}
                    # Safety validation without executing the pose.
                    session.brain.body.safety.check_motion(pose)
                    self._json({"geometry": _geometry_payload(session.profile, pose)}); return
                if path == "/api/event":
                    start = dict(session.brain.body.positions); before = len(session.brain.body.trace)
                    actions = session.brain.emit(Event(EventKind.PHRASE, str(data["value"])))
                    new_frames = session.brain.body.trace[before:]
                    poses = interpolate_motion(new_frames, start, fps=18)
                    animation = []
                    for pose in poses[1:]:
                        animation.append({"pose": pose, "geometry": _geometry_payload(session.profile, pose), "dt_ms": 1000/18})
                    self._json({"ok": True, "actions": [{"kind": a.kind, "payload": a.payload} for a in actions], "animation": animation, "pose": dict(session.brain.body.positions)}); return
                if path == "/api/teach":
                    session.memory.teach(str(data["trigger"]), str(data["response"]))
                    self._json({"ok": True, "learned": session.memory.all()}); return
                if path == "/api/estop":
                    active = bool(data.get("active", True))
                    if active: session.brain.body.safety.latch_estop()
                    else: session.brain.body.safety.reset_estop()
                    self._json({"ok": True, "estop": active, "body": session.brain.body.status()}); return
                self._json({"error": "not found"}, HTTPStatus.NOT_FOUND)
            except Exception as exc:
                self._json({"error": str(exc)}, HTTPStatus.BAD_REQUEST)

        def log_message(self, fmt, *args):
            return
    return Handler


def serve(registry_dir: str | Path, host: str = "127.0.0.1", port: int = 8770, memory_path: str = ":memory:") -> None:
    registry = CreatureRegistry.from_directory(registry_dir)
    session = CreatureSession(registry, MemoryStore(memory_path))
    server = HTTPServer((host, port), make_handler(session))
    print(f"ParrotCore Creature Lab: http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
