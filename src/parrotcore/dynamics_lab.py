from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse

from .embodiment import CreatureRegistry, ExpressionCompiler
from .kinematics import compute_creature_geometry
from .hardware import HardwareBaseline, load_hardware_baseline
from .physics import DynamicsSimulator
from .simulation import creature_effectiveness, metrics_dict

HTML = r'''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ParrotCore Dynamics Lab</title>
<style>:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#0a0d11;color:#eef3f7;font:14px/1.4 system-ui,sans-serif}header{padding:16px 20px;border-bottom:1px solid #29323c;background:#11161c;display:flex;justify-content:space-between;align-items:center}h1{margin:0;font-size:20px}small{color:#91a0ae}.layout{display:grid;grid-template-columns:minmax(0,1.55fr) minmax(340px,.8fr);gap:14px;padding:14px;max-width:1500px;margin:auto}.card{background:#141a21;border:1px solid #29323c;border-radius:14px;padding:13px}.viewer{padding:0;overflow:hidden;position:relative}canvas{display:block;width:100%;height:650px;background:radial-gradient(circle at 50% 38%,#222c37,#11161c 62%,#080a0d);touch-action:none}.overlay{position:absolute;top:12px;left:12px;background:#07090dbb;border:1px solid #303a45;border-radius:10px;padding:8px 10px}.right{display:flex;flex-direction:column;gap:12px}h2{font-size:14px;margin:0 0 9px}.row{display:flex;flex-wrap:wrap;gap:7px}button,select{font:inherit;border:1px solid #465360;border-radius:9px;background:#222a34;color:#fff;padding:8px 10px;cursor:pointer}.tele{display:grid;grid-template-columns:1fr 1fr;gap:7px}.meter{background:#0e141a;border:1px solid #26313a;border-radius:9px;padding:8px}.meter strong{display:block;font-size:18px}.meter span{font-size:11px;color:#96a5b4}.fault{color:#ffb5a7}.ok{color:#9be7b0}pre{white-space:pre-wrap;max-height:150px;overflow:auto;font-size:11px;color:#bdeac4}.warn{font-size:11px;color:#f3cb88}@media(max-width:900px){.layout{grid-template-columns:1fr}canvas{height:500px}}</style></head><body>
<header><div><h1>ParrotCore Dynamics Lab <small>v0.5.2</small></h1><small>Trajectory limits · safety-state telemetry · deliberate fault-injection validation</small></div><select id="species" onchange="selectSpecies(this.value)"></select></header>
<div class="layout"><div class="card viewer"><canvas id="view"></canvas><div class="overlay"><b id="label">Ready</b><div id="faultText" class="ok">faults: none</div><div id="safetyText" class="ok">safety: ready</div><small>Drag to orbit · wheel to zoom</small></div></div><div class="right">
<div class="card"><h2>Run semantic behavior</h2><div class="row"><button onclick="runIntent('greeting')">Greet</button><button onclick="runIntent('attend_left')">Left</button><button onclick="runIntent('attend_right')">Right</button><button onclick="runIntent('curious')">Curious</button><button onclick="runIntent('affirm')">Affirm</button><button onclick="runIntent('dance')">Dance</button><button onclick="runIntent('home')">Home</button></div></div>
<div class="card"><h2>Deliberate safety test</h2><div class="row"><button onclick="fault('clear')">Clear + Reset Safety</button><button onclick="fault('stall')">Stall yaw</button><button onclick="fault('proximity')">Object 4 cm</button><button onclick="fault('watchdog')">Lose watchdog</button><button onclick="fault('overtemp')">80 C</button><button onclick="fault('overcurrent')">All servos stall</button></div><div class="warn">These buttons intentionally create one simulated fault condition at a time. Active-frame counts are not independent fault counts. Clear + Reset Safety before returning to nominal operation.</div></div>
<div class="card"><h2>Live telemetry</h2><div class="tele"><div class="meter"><strong id="current">0 A</strong><span>servo rail current*</span></div><div class="meter"><strong id="power">0 W</strong><span>system power*</span></div><div class="meter"><strong id="temp">0 C</strong><span>max servo temp*</span></div><div class="meter"><strong id="tof">0 m</strong><span>ToF distance*</span></div><div class="meter"><strong id="stability">0 mm</strong><span>stability margin*</span></div><div class="meter"><strong id="duration">0 s</strong><span>planned segment time</span></div></div><div class="warn">*Parrot electrical endpoints use V1 manufacturer data; dynamic loads/thermal remain modeled. Owl/Raven remain conceptual.</div></div>
<div class="card"><h2>Runtime</h2><pre id="out">Ready.</pre></div></div></div>
<script>const canvas=document.getElementById('view'),ctx=canvas.getContext('2d');let dpr=devicePixelRatio||1,cam={yaw:-.55,pitch:.22,dist:.82},drag=null,geometry=null,token=0;
function resize(){let r=canvas.getBoundingClientRect();canvas.width=r.width*dpr;canvas.height=r.height*dpr;draw()}addEventListener('resize',resize);function project(v){let cy=Math.cos(cam.yaw),sy=Math.sin(cam.yaw),cp=Math.cos(cam.pitch),sp=Math.sin(cam.pitch);let x=cy*v[0]-sy*v[1],y=sy*v[0]+cy*v[1],z=v[2]-.16,y2=cp*y-sp*z,z2=sp*y+cp*z,f=cam.dist/(cam.dist+y2+.58);return [canvas.width/2+x*f*880*dpr,canvas.height*.57-z2*f*880*dpr,f]}const stroke={perch:'#a77b50',leg:'#9aa1a8',body:'#70b88a',neck:'#7fc69a',head:'#9cd5ad',beak:'#e1ae62',face:'#dce7ee',lid:'#75828e',wing:'#4b9e70',tail:'#3f8a64'};function draw(){if(!geometry)return;ctx.clearRect(0,0,canvas.width,canvas.height);let p=geometry.points,s=geometry.segments.map(q=>{let a=project(p[q[0]]),b=project(p[q[1]]);return {a,b,k:q[2],d:(a[2]+b[2])/2}}).sort((a,b)=>a.d-b.d);ctx.lineCap='round';for(let x of s){ctx.strokeStyle=stroke[x.k]||'#fff';ctx.lineWidth=(x.k==='body'||x.k==='wing'?10:x.k==='head'||x.k==='neck'?8:4)*dpr*x.d;ctx.beginPath();ctx.moveTo(x.a[0],x.a[1]);ctx.lineTo(x.b[0],x.b[1]);ctx.stroke()}for(let n of ['eye_l','eye_r'])if(p[n]){let q=project(p[n]);ctx.fillStyle='#111';ctx.beginPath();ctx.arc(q[0],q[1],5*dpr*q[2],0,Math.PI*2);ctx.fill()}}canvas.onpointerdown=e=>{drag=[e.clientX,e.clientY,cam.yaw,cam.pitch];canvas.setPointerCapture(e.pointerId)};canvas.onpointermove=e=>{if(!drag)return;cam.yaw=drag[2]+(e.clientX-drag[0])*.008;cam.pitch=Math.max(-1,Math.min(1,drag[3]+(e.clientY-drag[1])*.006));draw()};canvas.onpointerup=()=>drag=null;canvas.onwheel=e=>{e.preventDefault();cam.dist=Math.max(.35,Math.min(1.5,cam.dist+e.deltaY*.0006));draw()};async function api(path,method='GET',data=null){let o={method,headers:{'content-type':'application/json'}};if(data)o.body=JSON.stringify(data);let r=await fetch(path,o),j=await r.json();if(!r.ok)throw Error(j.error||r.status);return j}
function tele(t){current.textContent=t.rail_current_a.toFixed(2)+' A';power.textContent=t.system_power_w.toFixed(1)+' W';temp.textContent=t.max_servo_temp_c.toFixed(1)+' C';tof.textContent=t.tof_distance_m.toFixed(2)+' m';stability.textContent=(t.stability_margin_m*1000).toFixed(1)+' mm';let f=t.faults.join(', ')||'none';faultText.textContent='active condition: '+f;faultText.className=f==='none'?'ok':'fault';let state=t.safety_latched?('LATCHED / '+(t.safety_reason||'unknown')):(t.motion_inhibited?'motion inhibited':'ready');safetyText.textContent='safety: '+state+' | actuator power '+(t.actuator_power_enabled?'ON':'OFF');safetyText.className=(t.safety_latched||t.motion_inhibited)?'fault':'ok'}async function animate(frames,name){let mine=++token;label.textContent=name;for(let f of frames){if(mine!==token)return;geometry=f.geometry;tele(f.telemetry);draw();await new Promise(r=>setTimeout(r,f.dt_ms))}}
async function init(){let j=await api('/api/profiles');species.innerHTML=j.species.map(s=>`<option>${s}</option>`).join('');await selectSpecies(j.current);resize()}async function selectSpecies(s){let j=await api('/api/select','POST',{species:s});species.value=s;geometry=j.geometry;label.textContent=s.toUpperCase()+' / '+j.profile.role;draw();out.textContent=JSON.stringify(j.metrics,null,2)}async function runIntent(i){let j=await api('/api/run','POST',{intent:i});duration.textContent=j.duration_s.toFixed(2)+' s';out.textContent=JSON.stringify({intent:i,active_fault_injection:j.injection,frames:j.frames},null,2);await animate(j.animation,i)}async function fault(mode){let j=await api('/api/fault','POST',{mode});out.textContent=JSON.stringify(j,null,2)}init().catch(e=>out.textContent=e.stack);</script></body></html>'''


def _geometry(profile, pose):
    g=compute_creature_geometry(profile,pose)
    return {"points":{k:list(v) for k,v in g.points.items()},"segments":[list(x) for x in g.segments]}


def _profile(profile):
    return {"species":profile.species,"role":profile.role,"joints":list(profile.joints),"expressions":sorted(profile.expressions)}


class DynamicsSession:
    def __init__(self, registry: CreatureRegistry, hardware: HardwareBaseline | None = None):
        self.registry=registry; self.hardware=hardware; self.species="parrot" if "parrot" in registry.species() else registry.species()[0]; self._reset()
    def _reset(self):
        self.profile=self.registry.get(self.species)
        selected_hardware = self.hardware if self.species == "parrot" else None
        self.sim=DynamicsSimulator(self.profile,sample_hz=20,hardware=selected_hardware)
        self.pose=dict(self.profile.home_pose)
    def select(self,species): self.species=species; self._reset()
    def set_fault(self,mode):
        self.sim.injection.clear()
        if mode=="clear":
            self.sim.reset_safety()
            return
        if mode=="stall":
            yaw="head_yaw" if "head_yaw" in self.profile.joints else "neck_yaw"; self.sim.injection.stalled_joints.add(yaw)
        elif mode=="proximity": self.sim.injection.forced_tof_distance_m=.04
        elif mode=="watchdog": self.sim.injection.watchdog_lost=True
        elif mode=="overtemp": self.sim.injection.forced_temperature_c=80
        elif mode=="overcurrent": self.sim.injection.stalled_joints.update(self.profile.joints)
        else: raise ValueError(f"unknown fault mode {mode}")


def make_handler(session: DynamicsSession):
    class H(BaseHTTPRequestHandler):
        def _json(self,data,status=200):
            raw=json.dumps(data).encode();self.send_response(status);self.send_header("Content-Type","application/json");self.send_header("Content-Length",str(len(raw)));self.end_headers();self.wfile.write(raw)
        def _read(self):
            n=int(self.headers.get("content-length","0"));return json.loads(self.rfile.read(n) or b"{}")
        def do_GET(self):
            p=urlparse(self.path).path
            if p=="/":
                raw=HTML.encode();self.send_response(200);self.send_header("Content-Type","text/html; charset=utf-8");self.send_header("Content-Length",str(len(raw)));self.end_headers();self.wfile.write(raw);return
            if p=="/api/profiles": self._json({"species":session.registry.species(),"current":session.species});return
            self._json({"error":"not found"},404)
        def do_POST(self):
            p=urlparse(self.path).path
            try:
                d=self._read()
                if p=="/api/select":
                    session.select(str(d["species"]));selected_hardware=session.hardware if session.species=="parrot" else None;self._json({"profile":_profile(session.profile),"geometry":_geometry(session.profile,session.pose),"metrics":metrics_dict(creature_effectiveness(session.profile,hardware=selected_hardware)),"hardware_grounded":bool(selected_hardware)});return
                if p=="/api/fault":
                    session.set_fault(str(d.get("mode","clear")));self._json({"ok":True,"injection":session.sim.injection.active_labels()});return
                if p=="/api/run":
                    intent=str(d["intent"]);animation=[];duration=0.0
                    for frame in ExpressionCompiler(session.profile).compile(intent).frames:
                        run=session.sim.run(session.pose,frame.positions,frame.duration_s);duration+=run.trajectory.duration_s
                        for t in run.telemetry[1:]: animation.append({"telemetry":t.as_dict(),"geometry":_geometry(session.profile,t.positions),"dt_ms":50})
                        session.pose=dict(run.telemetry[-1].positions)
                    self._json({"ok":True,"intent":intent,"frames":len(animation),"duration_s":duration,"animation":animation,"injection":session.sim.injection.active_labels()});return
                self._json({"error":"not found"},404)
            except Exception as exc:self._json({"error":str(exc)},HTTPStatus.BAD_REQUEST)
        def log_message(self,fmt,*args):return
    return H


def serve(registry_dir: str|Path,host="127.0.0.1",port=8780):
    registry_dir=Path(registry_dir)
    root=registry_dir.resolve().parent
    component=root/"hardware"/"v1_component_baseline.toml"
    actuator_map=root/"hardware"/"v1_actuator_map.toml"
    hardware=load_hardware_baseline(component,actuator_map) if component.exists() and actuator_map.exists() else None
    session=DynamicsSession(CreatureRegistry.from_directory(registry_dir),hardware=hardware);server=HTTPServer((host,port),make_handler(session));print(f"ParrotCore Dynamics Lab: http://{host}:{port}")
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
