# Keeping installations current

The portal and the portable skill have separate release lifecycles. A portal deployment changes the shared library UI immediately. Updating a skill replaces its managed files on that computer; an agent that already loaded instructions may need a new session to read them again. It does not import conversation histories or change an account, token, or publishing preference.

## Hosted or self-hosted skill

The updater remembers the HTTPS server selected at installation. A self-hosted installation keeps using that server, never artifacts.botto.is as an unsolicited fallback.

```sh
margen update --check
margen update --if-changed
margen update --auto enable
margen update --auto status
margen update --auto disable
```

If the command is not on PATH, use `python3 ~/.local/share/bottifact/library/scripts/update.py` with the same flags. Use `--destination PATH` for a custom installation.

Automatic updates are **opt-in**, per user, every six hours while the computer and user scheduler are available. macOS uses a LaunchAgent (also checks when loaded); Linux uses a systemd user timer with a short randomized delay. Windows uses a per-user Task Scheduler task while the user is signed in; it needs no administrator credentials. Native Windows credentials remain protected by DPAPI. No root privileges, cron edits, shell command evaluation, or publication token are needed. `status` reports whether the scheduler definition is installed, not whether a previous download succeeded. macOS logs live in `~/.local/state/bottifact/`; Linux logs are available through `journalctl --user` for the service shown by the timer definition.

A checksum check avoids downloading an unchanged ZIP. A per-destination lock prevents overlapping update processes. Changed packages pass the existing checksum, manifest, path, and atomic installation checks. The configured HTTPS server remains the trust source: SHA-256 detects corruption, but is not an independent publisher signature. Do not store personal changes inside the managed library; keep them in a project or a development checkout.

Local ZIP installations never silently enable network access. First choose a source explicitly, then enable the scheduler in a separate command:

```sh
margen update --server https://your-instance.example
margen update --auto enable
```

Git checkouts are not overwritten. Existing agent folders or links to a different library remain untouched. Other computers must install or enable the schedule themselves; one installation cannot configure unknown devices.

## Portal releases

Self-hosted operators deploy a reviewed release using [the upgrade procedure](self-hosting.md). Back up data and configuration, build or pull the selected image, restart the portal and worker, and verify health and permissions. Skill timers **do not redeploy the portal**, run migrations, or restart containers. Operators decide when to publish a new portable ZIP through their own `/downloads/` endpoints.
