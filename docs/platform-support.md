# Platform support

Artifact reading is browser-based. Local skill installation, the generator, publishing CLI and agent discovery are separate capabilities. Agent vendors' own OS requirements still apply; Margen does not install Claude, Codex or Hermes themselves.

| Environment | Bootstrap | Local command | Update scheduler |
| --- | --- | --- | --- |
| macOS | `install.sh` with Bash, curl, Python 3.10+ and OpenSSL | `margen` in `~/.local/bin` | Opt-in LaunchAgent |
| Linux | Same shell installer | Same launcher | Opt-in systemd user timer; manual update elsewhere |
| Windows native | `install.ps1` in PowerShell 5.1+; Python 3.10+ | `margen.cmd` in `$HOME\.local\bin` | Opt-in Task Scheduler, while the user is signed in |
| WSL | Linux installation **inside WSL** | Linux launcher | Depends on WSL's systemd configuration |

## Windows

Use [the installer page](https://artifacts.botto.is/install) and select Windows. In PowerShell:

```powershell
$installer = Join-Path $env:TEMP 'margen-install.ps1'
Invoke-WebRequest -UseBasicParsing https://artifacts.botto.is/install.ps1 -OutFile $installer
# Review the downloaded script. This bypass applies to this process, not machine policy.
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $installer
```

No Bash, WSL, OpenSSL, Developer Mode, administrator account or symlink privilege is required for this route. The installer discovers `py -3`, `python` or `python3`, checks the version and stops if Python is missing. Install Python from python.org, then reopen PowerShell. Enterprise execution policies can override the process policy; do not circumvent them. Use the reviewed Python installer directly if your organization permits it:

```powershell
Invoke-WebRequest -UseBasicParsing https://artifacts.botto.is/install.py -OutFile (Join-Path $env:TEMP 'margen-install.py')
py -3 -X utf8 (Join-Path $env:TEMP 'margen-install.py') --server https://artifacts.botto.is
```

The PowerShell bootstrap adds `$HOME\.local\bin` to the **user** PATH unless `-NoPath` is supplied. Reopen your terminal afterward; a child PowerShell process cannot change its parent's environment. For immediate use:

```powershell
& "$HOME\.local\bin\margen.cmd" status
& "$HOME\.local\bin\margen.cmd" connect --server https://artifacts.botto.is --email you@company.com
& "$HOME\.local\bin\margen.cmd" update
```

Credentials are protected with Windows DPAPI for the current OS user, and are not portable between user accounts. A copied or older plaintext credential must be reconnected. Tokens stay outside the skill and are never included in update packages. Native .NET verifies release signatures using the pinned RSA key; verification is not skipped when OpenSSL is absent.

Use `-Agents 'codex,hermes'` on the PowerShell installer, or `--agents codex,hermes` on the updater, to select integrations. Omit this option on subsequent updates to retain the saved selection.

Windows uses managed **copies** in `.agents/skills/margen`, `.claude/skills/margen` and `.hermes/skills/margen`. Updating the canonical library refreshes those copies and backs up previous managed directories. Independent skill folders are preserved. macOS/Linux keep directory symlinks. Custom destination updates should use `margen update`; `--no-links` deliberately leaves agent integrations untouched.

## Prompt portability

An agent should identify its shell and interpreter before running commands. Use `python3` on Unix and `py -3 -X utf8` (or a verified `python -X utf8`) on Windows. Quote paths with spaces. Use PowerShell `$env:TEMP` instead of `/tmp`, `$HOME` instead of `$env:HOME`, and the call operator `&` for a quoted executable path. Do not run Bash pipelines, `export`, Unix shebang launchers or backslash line continuations in PowerShell/CMD. A narrative prompt is portable; embedded terminal commands may not be.

Install inside the same environment as the agent. A Windows-native agent does not automatically load WSL's home directory; a WSL agent does not automatically load Windows user skills. Discovery in ChatGPT's website or another hosted agent is separate from a local filesystem installation.

Automated assignment execution with `margen-agent run` on native Windows requires an agent executable ending in `.exe`. Shell shims (`.cmd`, `.bat`, `.ps1`) are intentionally rejected so assignment text is never evaluated by a command shell. Agents installed through those shims can still use the skill interactively; use WSL for automated execution or open the assignment manually.

## Evidence boundary

The `portable-platforms` CI matrix exercises installation/update, generation/validation, managed integrations, commands with spaces/Unicode, signing/tamper rejection and credential storage on macOS, Ubuntu and Windows. Windows PowerShell syntax is parsed by Windows PowerShell itself. CI results establish the tested runtime paths, not compatibility with every agent release, enterprise policy, architecture or Linux distribution. Scheduler definitions are tested without installing background tasks on CI. Browser-only reading and the containerized Linux portal do not require a local skill.
