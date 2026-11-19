#!/usr/bin/env python3
"""
MobileClaw 'Build for Good' Google Cloud Run Service (https://getmobileclaw.com)

Serves:
- GET  /                     -> Official MobileClaw landing page (index.html)
- GET  /privacy              -> Privacy Policy (privacy.html)
- GET  /healthz              -> Cloud Run service health & architecture metadata
- POST /mcp                  -> Model Context Protocol (JSON-RPC 2.0) tools for low-RAM phones:
                                1. socratic_study_hint
                                2. elder_care_checkin
                                3. recent_earthquakes
- POST /v1/chat/completions  -> OpenAI-compatible stateless relay (uses GEMINI_API_KEY if set,
                                with a built-in Socratic/Care fallback so it never fails offline).
"""
import json
import os
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
INDEX_HTML = (HERE / "index.html").read_bytes()
PRIVACY_HTML = (HERE / "privacy.html").read_bytes() if (HERE / "privacy.html").exists() else INDEX_HTML

MCP_TOOLS = [
    {
        "name": "socratic_study_hint",
        "description": "Returns a Socratic guiding question that helps a child solve a homework problem step by step without giving away the final answer.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "question": {"type": "string", "description": "The student's question or math/reading problem"},
                "language": {"type": "string", "description": "tr or en", "default": "en"},
            },
            "required": ["question"],
        },
    },
    {
        "name": "elder_care_checkin",
        "description": "Builds a calm, reassuring memory & daily routine prompt for an older adult in MobileClaw Simple/Care mode.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {"type": "string", "description": "Older adult's first name"},
                "note": {"type": "string", "description": "Reminder or family note to include"},
                "language": {"type": "string", "description": "tr or en", "default": "en"},
            },
        },
    },
    {
        "name": "recent_earthquakes",
        "description": "Checks the live USGS earthquake feed for recent M4.0+ seismic events to keep families informed.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "description": "Maximum events to return (1-5)", "default": 3},
            },
        },
    },
]


def run_mcp_tool(name: str, args: dict) -> str:
    lang = (args.get("language") or "en").lower()
    if name == "socratic_study_hint":
        q = (args.get("question") or "").strip()
        if lang.startswith("tr"):
            return (
                f"Soru: '{q}'\n"
                "Cevabı doğrudan söylemek yerine birlikte düşünelim: "
                "1) Bu soruda bize verilen iki ana bilgi nedir? "
                "2) İlk adımda hangi işlemi denemeliyiz?"
            )
        return (
            f"Problem: '{q}'\n"
            "Instead of jumping straight to the answer, let's break it down together: "
            "1) What are the two pieces of information we already know here? "
            "2) Which small operation should we try first?"
        )

    if name == "elder_care_checkin":
        person = (args.get("name") or "").strip()
        note = (args.get("note") or "").strip()
        if lang.startswith("tr"):
            who = f"{person}, " if person else ""
            extra = f" Notun: {note}." if note else ""
            return f"{who}her şey yolunda ve güvendesin.{extra} Bir şeye ihtiyacın olursa ekrandaki büyük yeşil arama düğmesine basılı tutman yeterli."
        who = f"{person}, " if person else ""
        extra = f" Note for today: {note}." if note else ""
        return f"{who}everything is calm and you are safe at home.{extra} Hold the large call button on your screen anytime you want to talk to family."

    if name == "recent_earthquakes":
        limit = max(1, min(int(args.get("limit") or 3), 5))
        url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/4.5_day.geojson"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "MobileClaw-CloudRun/1.0"})
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            features = data.get("features") or []
            if not features:
                return "No M4.5+ earthquakes reported in the last 24 hours."
            lines = []
            for f in features[:limit]:
                props = f.get("properties") or {}
                lines.append(f"• M{props.get('mag')} — {props.get('place')}")
            return "Recent M4.5+ Earthquakes (USGS 24h):\n" + "\n".join(lines)
        except Exception as exc:
            return f"Earthquake feed temporarily unreachable: {exc}"

    return f"Unknown tool: {name}"


def call_gemini_or_fallback(messages: list) -> str:
    last_user = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user = str(m.get("content") or "")
            break
    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if api_key:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={api_key}"
            payload = json.dumps({"contents": [{"parts": [{"text": last_user}]}]}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            return body["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            pass
    return run_mcp_tool("socratic_study_hint", {"question": last_user or "How does MobileClaw Cloud Run bridge work?"})


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, content_type: str = "application/json; charset=utf-8"):
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            self._send(200, INDEX_HTML, "text/html; charset=utf-8")
        elif path in ("/blog", "/blog/", "/blog/index.html"):
            self._send(200, (HERE / "blog" / "index.html").read_bytes(), "text/html; charset=utf-8")
        elif path == "/blog/repos.json":
            self._send(200, (HERE / "blog" / "repos.json").read_bytes(), "application/json; charset=utf-8")
        elif path in ("/privacy", "/privacy.html"):
            self._send(200, PRIVACY_HTML, "text/html; charset=utf-8")
        elif path in ("/healthz", "/healthz.json"):
            info = {
                "status": "ok",
                "service": "mobileclaw-cloudrun-good",
                "theme": "Product Hunt x Google Cloud Run — Build for Good",
                "domain": "getmobileclaw.com",
                "play_store": "https://play.google.com/store/apps/details?id=com.la1ncher",
                "mcp_tools": [t["name"] for t in MCP_TOOLS],
            }
            self._send(200, json.dumps(info, indent=2).encode("utf-8"))
        else:
            self._send(404, b'{"error":"not_found"}')

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length > 0 else b"{}"
        try:
            body = json.loads(raw.decode("utf-8"))
        except Exception:
            body = {}

        if path == "/mcp":
            rpc_id = body.get("id", 1)
            method = body.get("method", "")
            params = body.get("params") or {}
            if method == "initialize":
                res = {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "mobileclaw-cloudrun-good", "version": "1.0.7"},
                }
            elif method == "tools/list":
                res = {"tools": MCP_TOOLS}
            elif method == "tools/call":
                text = run_mcp_tool(params.get("name", ""), params.get("arguments") or {})
                res = {"content": [{"type": "text", "text": text}]}
            else:
                res = {"tools": MCP_TOOLS}
            out = {"jsonrpc": "2.0", "id": rpc_id, "result": res}
            self._send(200, json.dumps(out).encode("utf-8"))
            return

        if path == "/v1/chat/completions":
            reply = call_gemini_or_fallback(body.get("messages") or [])
            out = {
                "id": f"chatcmpl-{int(time.time())}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": body.get("model") or "mobileclaw-cloudrun-good",
                "choices": [
                    {
                        "index": 0,
                        "message": {"role": "assistant", "content": reply},
                        "finish_reason": "stop",
                    }
                ],
            }
            self._send(200, json.dumps(out).encode("utf-8"))
            return

        self._send(404, b'{"error":"not_found"}')


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"MobileClaw Cloud Run service listening on 0.0.0.0:{port}")
    server.serve_forever()
