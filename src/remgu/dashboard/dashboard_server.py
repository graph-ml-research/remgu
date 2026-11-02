# Copyright 2026 Mstislav Maslennikov
# SPDX-License-Identifier: Apache-2.0
"""Local-only live dashboard with SSE updates and safe text rendering."""
from __future__ import annotations
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading
import time
from typing import Any
from urllib.parse import urlparse


class DashboardServer:
    """Serve a small local dashboard; model execution remains outside the HTTP server."""

    def __init__(self, state: dict[str, Any] | None = None, *, host: str = "127.0.0.1", port: int = 0,
                 controller: Any | None = None, event_limit: int = 500) -> None:
        """Create a dashboard server bound to loopback by default."""
        if host not in {"127.0.0.1", "localhost"}:
            raise ValueError("dashboard server must bind to loopback by default")
        if event_limit < 1: raise ValueError("event_limit must be positive")
        self.host, self.port, self.controller = host, port, controller
        self.state = dict(state or {})
        self.events: list[dict[str, Any]] = []
        self.event_limit = event_limit
        self._condition = threading.Condition()
        self._state_revision = 0
        self._event_revision = 0
        self._httpd = None
        self._thread = None

    def update_state(self, values: dict[str, Any]) -> None:
        """Merge a new state snapshot and publish it to connected browsers."""
        with self._condition:
            self.state.update(values)
            self._state_revision += 1
            self._condition.notify_all()

    def publish_event(self, event: dict[str, Any]) -> None:
        """Append a structured event, keeping Probe diagnostics available separately."""
        record = dict(event)
        record.setdefault("timestamp", time.time())
        record.setdefault("type", "log")
        with self._condition:
            self.events.append(record)
            self.events = self.events[-self.event_limit:]
            self._event_revision += 1
            self._condition.notify_all()

    def snapshot(self) -> dict[str, Any]:
        """Return a copy of state, bounded SVG previews and recent diagnostic events."""
        with self._condition:
            state = dict(self.state)
            events = [dict(event) for event in self.events]
        config = state.get("config") if isinstance(state.get("config"), dict) else state
        param_types = config.get("param_types", {}) if isinstance(config.get("param_types", {}), dict) else {}
        parameter_specs = {name: dict(spec) for name, spec in
                           getattr(self.controller, "parameter_specs", {}).items()} if self.controller is not None else {}
        for name, category in param_types.items():
            if category not in {"hot", "structural", "view"}:
                continue
            if name in parameter_specs:
                parameter_specs[name]["category"] = category
            elif category in {"structural", "view"}:
                value = config.get(name)
                value_type = "int" if isinstance(value, int) and not isinstance(value, bool) else (
                    "float" if isinstance(value, float) else "bool" if isinstance(value, bool) else "str")
                parameter_specs[name] = {"category": category, "type": value_type,
                                          "value": value, "description": name}
        if self.controller is not None or parameter_specs:
            state["control_parameters"] = {name: {key: value for key, value in spec.items()
                                                   if key in {"type", "min", "max", "description", "category", "value", "step"}}
                                           for name, spec in parameter_specs.items()}
            state["control_commands"] = sorted(getattr(self.controller, "commands", {}).keys()) if self.controller is not None else []
        world_data = state.get("world")
        if isinstance(world_data, dict) and world_data.get("adjacency"):
            try:
                from remgu.simulation import GraphWorld
                from remgu.visualization import GraphRenderer
                world = GraphWorld({int(k): v for k, v in world_data["adjacency"].items()},
                                   {int(k): v for k, v in world_data["features"].items()},
                                   {int(k): v for k, v in world_data["communities"].items()},
                                   tuple(world_data["critical_bridge"]) if world_data.get("critical_bridge") else None)
                state["graph_svg"] = GraphRenderer().to_svg(world)
            except (KeyError, TypeError, ValueError):
                state["graph_preview_status"] = "unavailable"
        examples_key = "examples" if "examples" in state else "selected_examples"
        if isinstance(state.get(examples_key), list):
            from remgu.example.example_report_selector import ExampleReportSelector
            state[examples_key] = ExampleReportSelector(limit=100).select(state[examples_key])
            state["examples_page_size"] = 10
        # The SVG preview is enough for the browser; do not send a full graph adjacency back to the DOM.
        state.pop("world", None)
        if isinstance(state.get("metric_history"), dict):
            try:
                from remgu.visualization import MetricRenderer
                state["metric_history_svg"] = MetricRenderer().render(state["metric_history"])
            except (TypeError, ValueError):
                state["metric_history_svg"] = None
        if isinstance(state.get("graph_dot"), str): state["graph_dot"] = state["graph_dot"][:10000]
        dot = state.get("architecture_dot")
        if isinstance(dot, str):
            state["architecture_dot"] = dot[:10000]
            try:
                from remgu.visualization import DotSvgRenderer
                state["architecture_svg"] = DotSvgRenderer().render(dot)
            except ValueError:
                state["architecture_preview_status"] = "unsupported DOT subset"
        return {"state": state, "events": events}

    def start(self) -> str:
        """Start serving in a background thread and return the local URL."""
        if self._httpd is not None: raise RuntimeError("dashboard server is already running")
        owner = self

        class RequestHandler(BaseHTTPRequestHandler):
            """Handle a deliberately small set of safe dashboard endpoints."""
            def log_message(self, format: str, *args: Any) -> None:
                return

            def _send(self, status: int, content_type: str, body: bytes) -> None:
                self.send_response(status); self.send_header("Content-Type", content_type)
                self.send_header("Content-Length", str(len(body))); self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; connect-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline'")
                self.end_headers(); self.wfile.write(body)

            def do_GET(self) -> None:
                path = urlparse(self.path).path
                if path == "/":
                    self._send(200, "text/html; charset=utf-8", owner._page().encode("utf-8")); return
                if path == "/api/state":
                    self._send(200, "application/json; charset=utf-8", json.dumps(owner.snapshot(), ensure_ascii=False).encode()); return
                if path == "/events":
                    self.send_response(200); self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Cache-Control", "no-cache"); self.send_header("X-Content-Type-Options", "nosniff"); self.end_headers()
                    try:
                        self.wfile.write(b": connected\n\n"); self.wfile.flush()
                        previous = -1
                        for _ in range(600):
                            with owner._condition:
                                owner._condition.wait(timeout=1.0)
                                snapshot = owner.snapshot()
                            with owner._condition:
                                current = (owner._state_revision, owner._event_revision)
                            if current != previous:
                                payload = json.dumps(snapshot, ensure_ascii=False, default=str).replace("\n", "\\n")
                                self.wfile.write(f"data: {payload}\n\n".encode("utf-8")); self.wfile.flush(); previous = current
                    except (BrokenPipeError, ConnectionResetError, OSError):
                        return
                    return
                self._send(404, "text/plain; charset=utf-8", b"Not found")

            def do_POST(self) -> None:
                if urlparse(self.path).path != "/api/command":
                    self._send(404, "application/json", b'{"error":"not found"}'); return
                if owner.controller is None:
                    self._send(403, "application/json", b'{"error":"controls unavailable"}'); return
                try:
                    length = int(self.headers.get("Content-Length", "0"))
                    if length < 1 or length > 8192: raise ValueError("invalid request size")
                    payload = json.loads(self.rfile.read(length).decode("utf-8"))
                    if not isinstance(payload, dict): raise ValueError("request must be an object")
                    if payload.get("action") == "parameter":
                        result = owner.controller.apply_parameter(payload.get("name"), payload.get("value"))
                    else:
                        result = owner.controller.execute(payload.get("action", ""))
                    owner.publish_event({"type": "control", "message": "Control action recorded", "details": result})
                    body = json.dumps({"ok": True, "result": result}, ensure_ascii=False, default=str).encode()
                    self._send(200, "application/json; charset=utf-8", body)
                except (ValueError, TypeError, RuntimeError, json.JSONDecodeError) as exc:
                    body = json.dumps({"ok": False, "error": str(exc)}).encode()
                    self._send(400, "application/json; charset=utf-8", body)

        self._httpd = ThreadingHTTPServer((self.host, self.port), RequestHandler)
        self._httpd.daemon_threads = True
        self.port = self._httpd.server_address[1]
        self._thread = threading.Thread(target=self._httpd.serve_forever, name="remgu-dashboard", daemon=True)
        self._thread.start()
        return f"http://{self.host}:{self.port}/"

    def stop(self) -> None:
        """Stop the server and release its socket without affecting model execution."""
        if self._httpd is None: return
        self._httpd.shutdown(); self._httpd.server_close()
        if self._thread is not None: self._thread.join(timeout=3)
        self._httpd = None; self._thread = None

    def _page(self) -> str:
        """Return the HTML shell; dynamic text is assigned through textContent."""
        return r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>ReMgu live dashboard</title>
<style>
body{font:16px/1.5 system-ui,sans-serif;max-width:1100px;margin:1rem auto;padding:0 1rem;color:#172033}header{position:sticky;top:0;background:white;border:1px solid #d6dbe4;border-radius:8px;padding:.8rem;z-index:2}nav{display:flex;gap:.5rem;flex-wrap:wrap;margin:1rem 0}button{padding:.45rem .7rem;margin:.15rem}section{margin:1rem 0;padding:1rem;border:1px solid #d6dbe4;border-radius:8px}pre{white-space:pre-wrap;overflow-wrap:anywhere} .hidden{display:none}table{border-collapse:collapse;width:100%}td,th{text-align:left;padding:.4rem;border-bottom:1px solid #ddd}svg,img{max-width:100%;height:auto}.resource-strip{display:flex;gap:1rem;flex-wrap:wrap}.resource{border:1px solid #ddd;padding:.4rem .7rem;border-radius:6px}details{margin:.6rem 0}label{display:inline-flex;gap:.4rem;align-items:center;margin:.3rem}input[type=range]{min-width:180px}
</style></head><body><header><strong>ReMgu Live View</strong><span id="status" style="margin-left:1rem">Connecting…</span><div class="resource-strip"><span class="resource">Main metric: <b id="main-metric">—</b></span><span class="resource">RAM: <b id="ram">—</b></span><span class="resource">CPU: <b id="cpu">—</b></span><span class="resource">GPU: <b id="gpu">—</b></span><span class="resource">VRAM: <b id="vram">—</b></span></div></header>
<nav><button data-tab="charts">Графики</button><button data-tab="model">Модель / данные</button><button data-tab="parameters">Параметры</button><button data-tab="logs">Логи</button></nav>
<section id="charts"><h2>Графики</h2><img id="metric-chart" alt="Live metric history" hidden><details><summary>Дополнительная диагностика</summary><pre id="state"></pre></details></section>
<section id="model" class="hidden"><h2>Модель и данные</h2><details open><summary>Граф</summary><img id="graph-image" alt="Graph preview"><pre id="graph-text"></pre></details><details><summary>Архитектура модели</summary><img id="architecture-image" alt="Model architecture preview"><pre id="architecture-text"></pre></details><h3>Отобранные примеры</h3><label>Фильтр <input id="example-filter" type="search" placeholder="Фильтр по тексту"></label><div id="examples-table"></div><button id="examples-prev">Назад</button><span id="examples-page-status"></span><button id="examples-next">Вперёд</button></section>
<section id="parameters" class="hidden"><h2>Параметры</h2><div id="controls"></div><p id="parameter-status" aria-live="polite"></p></section><section id="logs" class="hidden"><h2>Логи и события</h2><details open><summary>События</summary><div id="events"></div></details><details><summary>Probe and model health / диагностика</summary><div id="probe-events"></div></details></section>
<script>
const stateNode=document.getElementById('state'),probeNode=document.getElementById('probe-events'),eventsNode=document.getElementById('events'),controlsNode=document.getElementById('controls');let exampleRows=[],examplePage=0;const pageSize=10;
async function sendControl(payload){const response=await fetch('/api/command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});const result=await response.json();if(!response.ok)throw new Error(result.error||'control rejected');return result}
function setText(id,value){document.getElementById(id).textContent=value===null||value===undefined?'—':String(value)}
function renderExamples(){const target=document.getElementById('examples-table');target.replaceChildren();const query=document.getElementById('example-filter').value.toLowerCase();const filtered=exampleRows.filter(row=>JSON.stringify(row).toLowerCase().includes(query));const pages=Math.max(1,Math.ceil(filtered.length/pageSize));examplePage=Math.min(examplePage,pages-1);const table=document.createElement('table'),head=document.createElement('thead'),hr=document.createElement('tr');const cols=Array.from(new Set(filtered.slice(0,1).flatMap(row=>Object.keys(row))));for(const col of cols){const th=document.createElement('th');th.textContent=col;hr.appendChild(th)}head.appendChild(hr);table.appendChild(head);const body=document.createElement('tbody');for(const row of filtered.slice(examplePage*pageSize,(examplePage+1)*pageSize)){const tr=document.createElement('tr');for(const col of cols){const td=document.createElement('td');const value=row[col];td.textContent=typeof value==='object'&&value!==null?JSON.stringify(value):String(value??'');tr.appendChild(td)}body.appendChild(tr)}table.appendChild(body);target.appendChild(table);setText('examples-page-status',`Page ${examplePage+1} / ${pages} (${filtered.length} examples)`);document.getElementById('examples-prev').disabled=examplePage===0;document.getElementById('examples-next').disabled=examplePage+1>=pages}
function buildControls(state){controlsNode.replaceChildren();const params=state.control_parameters||{},commands=state.control_commands||[];for(const [name,spec] of Object.entries(params)){const category=spec.category||'hot';const wrapper=document.createElement('div');const label=document.createElement('label');label.textContent=(spec.description||name)+' ';let input;
if(category==='hot'){input=document.createElement('input');input.type='range';input.name=name;input.min=spec.min??0;input.max=spec.max??1;input.step=spec.step??(spec.type==='int'?1:'any');input.value=spec.value??spec.min??0;const valueLabel=document.createElement('output');valueLabel.textContent=input.value;input.addEventListener('input',()=>valueLabel.textContent=input.value);label.append(input,valueLabel);const button=document.createElement('button');button.textContent='Apply';button.addEventListener('click',async()=>{const value=spec.type==='int'?Number.parseInt(input.value,10):Number(input.value);try{await sendControl({action:'parameter',name,value});setText('parameter-status','Параметр применён: '+name)}catch(error){setText('parameter-status',error.message)}});wrapper.append(label,button)}else if(category==='structural'){input=document.createElement('input');input.type=spec.type==='int'||spec.type==='float'?'number':'text';input.value=spec.value??'';label.appendChild(input);const warning=document.createElement('span');warning.textContent='Требуется перезапуск; изменение здесь не применяется.';wrapper.append(label,warning)}else{input=document.createElement('input');input.type='text';input.value=spec.value??'';label.appendChild(input);input.addEventListener('input',()=>{document.getElementById('example-filter').value=input.value;examplePage=0;renderExamples()});wrapper.appendChild(label)}controlsNode.appendChild(wrapper)}for(const command of commands){if(!['pause','resume','stop','checkpoint'].includes(command))continue;const button=document.createElement('button');button.textContent=command;button.addEventListener('click',async()=>{try{await sendControl({action:command});setText('parameter-status','Command accepted: '+command)}catch(error){setText('parameter-status',error.message)}});controlsNode.appendChild(button)}}
function setImage(id,svg){const node=document.getElementById(id);if(svg){node.src='data:image/svg+xml;charset=utf-8,'+encodeURIComponent(svg);node.hidden=false}else{node.removeAttribute('src');node.hidden=true}}
function render(data){const s=data.state||{};setText('status','Connected; state refreshed');stateNode.textContent=JSON.stringify(s,null,2);const resources=s.live_resources||s.resource_usage||{};setText('main-metric',s.main_metric_value??(s.metrics?JSON.stringify(s.metrics):null));setText('ram',resources.ram_bytes_process==null?null:(resources.ram_bytes_process/1048576).toFixed(1)+' MB');setText('cpu',resources.cpu_percent_process==null?null:resources.cpu_percent_process+'%');setText('gpu',resources.gpu_utilization_percent==null?null:resources.gpu_utilization_percent+'%');setText('vram',resources.vram_bytes_device_used==null?null:(resources.vram_bytes_device_used/1048576).toFixed(1)+' MB');buildControls(s);setImage('metric-chart',s.metric_history_svg);setImage('graph-image',s.graph_svg);setImage('architecture-image',s.architecture_svg);document.getElementById('graph-text').textContent=s.graph_dot||s.graph_preview_status||'Graph data unavailable';document.getElementById('architecture-text').textContent=s.architecture_dot||s.architecture_preview_status||'Architecture data unavailable';exampleRows=s.examples||s.selected_examples||[];examplePage=0;renderExamples();probeNode.replaceChildren();eventsNode.replaceChildren();for(const item of (data.events||[])){const row=document.createElement('pre');row.textContent=JSON.stringify(item,null,2);(String(item.type||'').toLowerCase().includes('probe')||String(item.category||'').toLowerCase()==='probe'?probeNode:eventsNode).appendChild(row)}}
document.getElementById('example-filter').addEventListener('input',()=>{examplePage=0;renderExamples()});document.getElementById('examples-prev').addEventListener('click',()=>{examplePage=Math.max(0,examplePage-1);renderExamples()});document.getElementById('examples-next').addEventListener('click',()=>{examplePage++;renderExamples()});for(const button of document.querySelectorAll('[data-tab]'))button.addEventListener('click',()=>{for(const section of document.querySelectorAll('body>section'))section.classList.toggle('hidden',section.id!==button.dataset.tab)});fetch('/api/state').then(r=>r.json()).then(render).catch(()=>setText('status','State unavailable'));const source=new EventSource('/events');source.onmessage=e=>{try{render(JSON.parse(e.data))}catch(_){}};source.onerror=()=>setText('status','Connection interrupted; retrying…');
</script></body></html>'''
