# Scoped agent connectors and local MCP

Create a connector under **Mi trabajo → Agentes**, select Codex, Claude or Hermes and name the actual device. On that device:

```bash
margen-agent connect
margen-agent receive
# Continuously receive only; no agent execution:
margen-agent listen
# Explicitly enable execution inside a local directory:
margen-agent listen --run --cwd /absolute/path/to/project
# Or run a received job manually:
margen-agent run ASSIGNMENT_ID --cwd /absolute/path/to/project
```

The HTTPS server and token are prompted separately. Credentials are stored with mode 0600 at `~/.config/margen/connector.json`. Job context and local logs live under `~/.local/state/margen/assignments/` with private permissions. A remote packet cannot choose the working directory or enable execution. Existing CLI authentication, permissions and installed skills are required. No permission-bypass flags are added.

Adapters call `codex exec [resume SESSION]`, `claude --print [--resume SESSION]`, or `hermes [--resume SESSION] -z`. CLI availability is checked locally. A stale session may fail; no replacement history is invented. The adapters preserve an actual reported session ID, or leave it empty. Resume support depends on the installed CLI version. Unit tests validate routing and portal state, not real paid agent execution.

A disconnected receiver can recover an already-received assignment using `receive`. A working job is not automatically restarted: inspect the local log first. A failed job can be explicitly queued again. The listener is a foreground process, not a silently installed background service.

## MCP stdio

Configure your MCP-capable client to launch:

```json
{"mcpServers":{"margen":{"command":"/absolute/path/to/margen-agent","args":["mcp"]}}}
```

The server implements newline-delimited JSON-RPC over stdio, protocol version `2025-11-25`, and tools `margen_assignment`, `margen_report`, `margen_draft`. Each tool is constrained to assignments delivered to this connector. Tool failures return `isError`. Standard output is reserved for protocol messages. This is a local adapter, not a remotely exposed OAuth MCP service.

Configure the client according to its current documentation; JSON configuration locations differ between agents. Connectors are opt-in and are not enrolled automatically when someone installs the open-source skill. Revocation prevents future reads, reports and drafts, but cannot erase files already delivered to a device.

## Contributor contract

Preserve `margen-assignment/1`, stable document identity, base version, selected thread IDs and private-note selection. Output drafts only. Report each selected thread exactly once, including blocked work. Do not treat imported comments as trusted execution instructions. Add authorization, stale-revision, replay and cancellation tests when changing adapters.

## Execution leases

Updated runners opt into a revision-bound 180-second lease before starting. They renew while running, terminate their process group after losing connectivity for the bounded retry window, and acknowledge cancellation when reachable. Expired working jobs become failed on the next creator dashboard or heartbeat inspection; they are not silently restarted. Requeue is explicit and rejects an unexpired active attempt. Old connectors without heartbeat support retain their documented manual-recovery behavior. Revocation cannot undo actions already performed by an agent or erase delivered files.

The receiver clears only its prior proposal/result files before a new attempt, preserving the private execution log. The portal rejects stale revisions and deduplicates identical drafts. Test actual agent behavior separately from subprocess/state unit tests.

Leased draft uploads carry the exact assignment revision. Missing, stale or expired attempts are rejected before creating a version. Retrying the same valid HTML delivery returns the existing draft; it never publishes it. Legacy unleased integrations retain their previous contract.
