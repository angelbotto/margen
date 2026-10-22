# Install, connect and update

## Start with the hosted service

To use the existing service, follow [Use artifacts.botto.is](hosted-service.md). Install the skill from that origin, sign in, create a personal agent token and connect it. **No `.env`, Docker or server setup is needed.**

To run an independent server, use [Self-hosting](self-hosting.md). The local-only path below remains available without any account.

## Local-only skill

Requirements: Python 3.10+ and a modern browser. No Python packages, Node, account or environment variables are needed for HTML generation.

```bash
git clone https://github.com/angelbotto/margen.git
cd margen
python3 scripts/package.py
python3 scripts/update.py --package dist/bottifact-portable.zip
```

The adjacent `.sha256` is required. The updater verifies the archive checksum and extraction paths, then the installer verifies the per-file manifest. The shared library is installed under `~/.local/share/bottifact/library`, with links under `~/.agents/skills`, `~/.claude/skills` and `~/.hermes/skills`. It preserves independent directories or links pointing elsewhere instead of overwriting them. Read its output to see whether a conflicting installation was kept.

`~/.local/bin/margen` is the managed CLI launcher; `bottifact` remains a compatibility alias. Put `~/.local/bin` on `PATH` if your shell does not already include it. Restart/reload each agent's skill discovery. The skill uses the Agent Skills format, but discovery and permitted tool execution depend on the host agent/version. A filesystem installer cannot install a skill into the ChatGPT website.

For a custom destination without agent links or launcher changes:

```bash
python3 scripts/update.py --package dist/bottifact-portable.zip \
  --destination /tmp/bottifact-library --no-links
```

## Your own server

Run your portal following [self-hosting](self-hosting.md). Its `/install` page serves installation instructions and downloads from that origin:

```bash
curl -fsSL https://artifacts.example.com/install.sh -o /tmp/bottifact-install.sh
# Review the downloaded script.
bash /tmp/bottifact-install.sh
margen connect --server https://artifacts.example.com
```

Create a token in the authenticated portal and paste it at the CLI's masked prompt. Do not place it in an artifact, shell argument, screenshot or shared skill. Personal connection settings live outside the skill, under `~/.config/bottifact/`.

## Update

Portal-installed library: `margen update` uses the configured server. To deliberately change servers, use `margen update --server https://another.example.com`.

Local ZIP installation: update the source checkout, rebuild the package and repeat `scripts/update.py --package ...`. This installation remains independent rather than silently switching to botto.is. The installer keeps a backup of the previous managed library. Review failures before retrying; never bypass checksum validation to make an update succeed.

## Design and imported documents

The portable package carries the same recipes, registry, theme tokens, fonts and component runtime used by the generator. [The design contract](design-contract.md) explains what an update changes, which format-specific behaviors it preserves, and how to upload your own HTML without applying the library design.

## Common problems

| Problem | Action |
| --- | --- |
| Agent cannot find the skill | Check installer output and the agent's skill directory; reload discovery |
| `margen` command not found | Add `~/.local/bin` to PATH or run the library's Python scripts directly |
| Existing skill was preserved | Inspect that directory before moving it; the installer does not overwrite unrelated work |
| No account in a fresh portal | Bootstrap the configured admin, then configure Google/email |
| No shared comments in an HTML file | Publish through a connected portal; local HTML comments are local storage |
| React package cannot be found on npm | Use workspace or packed tarballs; registry publication has not happened |

The [self-hosting environment table](self-hosting.md#configuration-reference) is for the optional portal, not the standalone skill.
