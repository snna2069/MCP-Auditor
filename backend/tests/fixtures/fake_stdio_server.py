"""A minimal fake MCP stdio server used only by tests.

Reads JSON-RPC requests line-by-line from stdin and writes line-delimited
JSON-RPC responses to stdout, implementing just enough of the MCP handshake
(``initialize`` -> ``notifications/initialized`` -> ``tools/list``) to
exercise StdioMCPClient without a real MCP server.

Behavior is driven by the ``FAKE_MCP_SCENARIO`` environment variable (a JSON
object), so tests can exercise different scenarios without new scripts:

- ``tools``: list of raw MCP Tool dicts to return from tools/list.
- ``exit_after_init``: if true, exit immediately after responding to
  ``initialize`` (simulates a crashing server).
- ``delay_seconds``: sleep this long before responding to ``initialize``
  (simulates a hung/slow server, for timeout tests).
"""

import json
import os
import sys
import time


def main() -> None:
    scenario = json.loads(os.environ.get("FAKE_MCP_SCENARIO", "{}"))
    tools = scenario.get("tools", [])
    delay = scenario.get("delay_seconds", 0)
    exit_after_init = scenario.get("exit_after_init", False)

    for raw_line in sys.stdin:
        line = raw_line.strip()
        if not line:
            continue
        message = json.loads(line)
        method = message.get("method")

        if method == "initialize":
            if delay:
                time.sleep(delay)
            response = {
                "jsonrpc": "2.0",
                "id": message["id"],
                "result": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {"tools": {}},
                    "serverInfo": {"name": "fake-server", "version": "1.0.0"},
                },
            }
            print(json.dumps(response), flush=True)
            if exit_after_init:
                return
        elif method == "notifications/initialized":
            continue  # notifications get no response
        elif method == "tools/list":
            response = {"jsonrpc": "2.0", "id": message["id"], "result": {"tools": tools}}
            print(json.dumps(response), flush=True)
        else:
            error = {
                "jsonrpc": "2.0",
                "id": message.get("id"),
                "error": {"code": -32601, "message": f"Unknown method {method}"},
            }
            print(json.dumps(error), flush=True)


if __name__ == "__main__":
    main()
