#!/usr/bin/env python3
"""A fake Responses endpoint on 127.0.0.1 for tests that drive the real Codex CLI.

No model is called and no credentials are read or accepted. Each request is answered with the
next step of a script; the last step repeats. A step is ("call", <shell command>) for one
exec_command tool call, or ("answer", <text>) for a final assistant message.
Load it with importlib (the file name is not a module name), then use start(script).
"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import threading


def handler(script):
    lock = threading.Lock()
    served = [0]

    class FakeResponses(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_GET(self):
            self.send_response(404)
            self.end_headers()

        def _event(self, obj):
            self.wfile.write(("event: %s\ndata: %s\n\n" % (obj["type"], json.dumps(obj))).encode())
            self.wfile.flush()

        def do_POST(self):
            self.rfile.read(int(self.headers.get("content-length", 0)))
            with lock:
                index = served[0]
                served[0] += 1
            kind, value = script[min(index, len(script) - 1)]
            self.send_response(200)
            self.send_header("content-type", "text/event-stream")
            self.end_headers()
            response = "resp_fake_%d" % index
            self._event({"type": "response.created", "response": {"id": response}})
            if kind == "call":
                item = {"type": "function_call", "id": "fc_%d" % index, "call_id": "call_%d" % index,
                        "name": "exec_command", "arguments": json.dumps({"cmd": value, "yield_time_ms": 30000})}
            else:
                item = {"type": "message", "role": "assistant", "id": "msg_%d" % index,
                        "content": [{"type": "output_text", "text": value}]}
            self._event({"type": "response.output_item.done", "item": item})
            self._event({"type": "response.completed", "response": {"id": response, "usage": {
                "input_tokens": 1, "input_tokens_details": {"cached_tokens": 0}, "output_tokens": 1,
                "output_tokens_details": {"reasoning_tokens": 0}, "total_tokens": 2}}})

    return FakeResponses


def start(script):
    """Serve the script on a free port; returns the server (stop it with shutdown() and server_close())."""
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler(script))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def provider_args(server):
    """Codex -c options that route the model to this server instead of OpenAI."""
    port = server.server_address[1]
    return ["-c", 'model_providers.fk={name="fk",base_url="http://127.0.0.1:%d/v1",wire_api="responses"}' % port,
            "-c", 'model_provider="fk"', "-m", "fake-model"]
