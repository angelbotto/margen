#!/usr/bin/env python3
"""Local adapter tests do not launch an agent or contact a server."""
import io, json, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import agent_connector as connector


class AdapterTests(unittest.TestCase):
    def test_fixed_commands_and_invalid_sessions(self):
        self.assertEqual(
            connector.command("Codex", "actual-session", "prompt"),
            ["codex", "exec", "resume", "actual-session", "prompt"],
        )
        self.assertEqual(
            connector.command("Claude", "", "prompt"), ["claude", "--print", "prompt"]
        )
        self.assertEqual(
            connector.command("Hermes", "actual-session", "prompt"),
            ["hermes", "--resume", "actual-session", "-z", "prompt"],
        )
        with self.assertRaises(ValueError):
            connector.command("Codex", "--dangerous", "prompt")

    def test_stdio_tool_failure_is_a_tool_result(self):
        requests = [
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {"protocolVersion": "2025-11-25"},
            },
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": "margen_assignment", "arguments": {"job": "a" * 32}},
            },
        ]
        output = io.StringIO()
        with patch.object(
            connector.sys,
            "stdin",
            io.StringIO("\n".join(json.dumps(r) for r in requests)),
        ), patch.object(connector.sys, "stdout", output), patch.object(
            connector, "api", side_effect=ValueError("Revoked")
        ):
            connector.mcp({})
        responses = [json.loads(line) for line in output.getvalue().splitlines()]
        self.assertEqual(len(responses[1]["result"]["tools"]), 3)
        self.assertTrue(responses[2]["result"]["isError"])

    def test_private_config_permissions(self):
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "config"
            connector.private(p, "{}")
            self.assertEqual(p.stat().st_mode & 0o777, 0o600)

    def test_http_identifies_the_connector_without_redirecting(self):
        with patch.object(connector.urllib.request, "build_opener") as factory:
            factory.return_value.open.return_value.__enter__.return_value = io.StringIO(
                "{}"
            )
            connector.api(
                {"server": "https://example.invalid", "token": "synthetic"},
                "/api/connector/pending",
            )
            request = factory.return_value.open.call_args.args[0]
            self.assertEqual(request.get_header("User-agent"), "Margen/1.0")
            self.assertEqual(request.get_header("Authorization"), "Bearer synthetic")

    def test_cancel_stops_local_process_before_delivery(self):
        import sys, subprocess

        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            key = "b" * 32
            state = root / key
            state.mkdir()
            (state / "context.json").write_text("{}")
            calls = []
            beats = 0
            processes = []

            def api(config, path, body=None):
                nonlocal beats
                calls.append((path, body))
                if path.endswith("/heartbeat"):
                    beats += 1
                    return {"continue": beats == 1, "revision": 2}
                if path.endswith("/report"):
                    return {"revision": 2}
                return {
                    "status": "received",
                    "revision": 1,
                    "packet": {"target": {"agent": "Codex"}},
                }

            popen = subprocess.Popen

            def launch(*args, **kwargs):
                process = popen(*args, **kwargs)
                processes.append(process)
                return process

            with patch.object(connector, "STATE", root), patch.object(
                connector, "api", side_effect=api
            ), patch.object(
                connector,
                "command",
                return_value=[sys.executable, "-c", "import time; time.sleep(60)"],
            ), patch.object(
                connector, "HEARTBEAT_INTERVAL", 0.03
            ), patch.object(
                connector.subprocess, "Popen", side_effect=launch
            ):
                with self.assertRaises(ValueError):
                    connector.run({}, key, root)
            self.assertIsNotNone(processes[0].poll())
            self.assertTrue(
                any(
                    path.endswith("/heartbeat") and body.get("stopped")
                    for path, body in calls
                )
            )
            self.assertFalse(any(path.endswith("/draft") for path, body in calls))


if __name__ == "__main__":
    unittest.main()
