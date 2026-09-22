# Use artifacts.botto.is

Use the existing Margen service without operating a server. This guide covers the hosted path only. [Self-hosting](self-hosting.md) has its own guide; [local-only installation](installation.md#local-only-skill) remains available without an account.

## What you need

- A browser and an account you can sign in with at [artifacts.botto.is](https://artifacts.botto.is).
- For agent creation/publication: macOS or Linux, Bash/curl and Python 3.10+. The installer checks Python and explains how to install it if missing.
- Claude Code, Codex or Hermes, if you want that agent to use the skill.

You do **not** configure Docker, a NAS, DNS, `.env`, Google OAuth credentials or an email provider. Those are service-operator responsibilities. Installing the open-source skill does not give anyone your account or access to your private documents.

## 1. Sign in

Open [the portal](https://artifacts.botto.is) and sign in through an available method shown on its login screen. Your personal library is associated with the authenticated account. An empty library on a new account is expected; installing the skill does not import local files or another account's documents.

Readers need only the shared artifact link. Public/unlisted reading and authenticated review follow the artifact's access rules; receiving a link is not permission to edit it. A private artifact needs an appropriate grant. The browser upload flow is also available without installing an agent skill.

## 2. Install the skill

```bash
curl -fsSL https://artifacts.botto.is/install.sh -o /tmp/bottifact-install.sh
# Inspect the script, then run it.
bash /tmp/bottifact-install.sh
```

The installer downloads a checksum-verified package, keeps a shared library in `~/.local/share/bottifact/library`, and creates links for Claude Code, Codex and Hermes. Existing independent skill directories are preserved; read the output if there is a conflict. The CLI launcher is `~/.local/bin/margen`.

If your shell cannot find it, add the directory for the current shell:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Add the equivalent line to your own shell profile if you want it to persist. Reload the agent's skill discovery or start a new session and ask it to use **Margen**. This terminal installer configures local agents; it does not install anything into the ChatGPT website.

## 3. Connect your account

In the signed-in portal, open **Conectar un agente** and create a personal token with a recognizable label, for example the agent and device. Then run:

```bash
margen connect --server https://artifacts.botto.is --email you@company.com
margen status
```

Paste the token only into the masked CLI prompt. Do not place it in a prompt, command argument, repository or screenshot. `status` reports your account, server and publication preference without displaying the token. Connection settings remain under `~/.config/bottifact/`, outside the shared skill.

An agent token is a credential for your account. Create and manage connections deliberately. The current token implementation is not a project-scoped, expiring OAuth delegation system.

## 4. Create and publish

Ask your agent to use Margen, describe the audience and decision, and ask for a validated HTML artifact. Publishing is separate from generating a local file. Explicitly ask it to publish, or opt into the persistent preference:

```bash
margen preferences --publish-on-create yes
```

You can disable that preference with `no`. It does not grant public visibility. A direct publication looks like:

```bash
margen publish --file /path/to/brief.html --title 'Decision brief' \
  --visibility private --agent codex --session SESSION_ID --device DEVICE_LABEL
```

Use real source metadata. Omit unknown session IDs; the CLI may infer a real session from supported environment variables when unambiguous. Keep the document ID stable across revisions. A later publication of that document normally creates a draft version so the shared link can keep showing the previously published version until review is complete.

Open the returned link and manage sharing in the portal. `private`, `unlisted` and `public` express different audiences. A hidden listing is not the same as access control. Administrators operate the instance and can access its artifacts; private visibility is not end-to-end encryption against the service operator.

For a whole team, use [domain sharing](domain-sharing.md) instead of entering every email. [The team trial](team-trial.md) provides a first exercise and a reusable prompt for Claude Code, Codex or Hermes.

## 5. Collect review and return to work

```bash
margen comments --artifact-id ARTIFACT_ID --open --kind all
margen feedback --artifact-id ARTIFACT_ID --output /tmp/bottifact-feedback
```

The export preserves available artifact/version/anchor and source-session context. Open the intended agent session and ask it to read the bundle. Missing or ambiguous origins require `--agent` and `--session`. It does not automatically message the agent, edit conversation histories or resolve threads. See [feedback and sessions](feedback-and-sessions.md).

## Update or choose another instance

```bash
margen update
```

Updates use the server recorded by the installer. If you later self-host, install/update from that new server and connect a token issued by that instance. Server selection for downloads and authentication are separate settings: updating code does not silently move your account or documents. Moving artifacts, reviews and identities between instances requires an explicit migration; simply changing the URL is not a data migration.

## Troubleshooting

| Symptom | Check |
| --- | --- |
| Command not found | PATH and `~/.local/bin/margen` |
| Skill not discovered | Installer output, agent skill directory and discovery reload |
| Library empty | Signed-in account, actual publication and artifact permissions |
| Email code missing | Available alternate sign-in method and service support; users do not need to create an email server |
| Publish fails with authentication error | `margen status`, chosen server and a valid personal token |
| Local HTML comments are absent from the portal | Browser-local comments are not automatically uploaded; use the review import/export workflow |
| Feedback has no source session | Supply the actual target explicitly; no session transcript was imported |
| A revision is not visible to readers | Check whether it is still a draft and release it after review |

For service access problems, use the support contact offered by the service or the repository maintainer. Do not post tokens, private titles, source-session IDs or screenshots of confidential documents in public issues.

## Account ownership and team installations

Each operating-system user installs the library in their own home directory. Claude, Codex and Hermes can share that library; people must not share `~/.config/bottifact/portal.json` or personal tokens. The public installer and portable ZIP contain no account credentials.

`connect --email you@company.com` checks the token against the server-verified account before saving anything. Choose the email yourself; an agent must not infer your identity from a saved token. Configured verified aliases can resolve to one account; a matching company domain never merges accounts. Changing accounts resets `publish_on_create` rather than inheriting another person's publishing preference.

Existing connections need a one-time explicit confirmation before writes after this update:

```bash
margen status
margen confirm-account --email you@company.com
```

If the email does not match, the command stops without changing the connection. Sign in to the portal as yourself, create a fresh personal token and run `connect` again. Never paste a token into agent chat. This check prevents accidental account reuse; it does not make bearer tokens safe to share. Revoke a token if it was disclosed.

**My artifacts** matches the stored creator ID even for administrators. **Shared with me** contains explicit personal or domain grants. Administrators use **All artifacts** for their global view; seeing an artifact there does not transfer ownership. The owner's name, and email for administrators, distinguish other people's documents in list, gallery and table layouts. Separate Google email accounts remain separate unless an explicit verified alias mapping exists.
