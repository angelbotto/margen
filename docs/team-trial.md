# Team trial: share how you work with agents

The first trial should create useful team knowledge while exercising artifact creation, domain access, comments and returning feedback to the originating workflow.

1. Sign in to [artifacts.botto.is](https://artifacts.botto.is) with your company email.
2. Follow the [hosted installation guide](hosted-service.md), or run `margen update` for an existing installation. Connect your own personal token through **Connect an agent**. Never share another person's token.
3. Start a fresh Claude Code, Codex or Hermes conversation and request the Margen skill. Browser-only readers do not need to install it.
4. Use the prompt below, setting your intended company domain. Share with one company by default; sharing with multiple companies requires an intentional audience choice.
5. Open a colleague's artifact in Shared, leave a contextual comment, and export the feedback as an AI prompt. Revise with the same document ID; review the draft before releasing it.

## Prompt template

> Use the current Margen skill. Analyze how I actually use Claude Code, Codex and Hermes using only the workspace, conversations and examples I have authorized you to inspect. Start by reporting which sources you can access; do not claim access to tools or histories you cannot inspect. Ask me for the few examples needed to fill important gaps.
>
> Create a shareable artifact in my voice, addressed to my team: how I work with agents, which tasks I delegate, repeatable workflows, useful prompts, context and verification practices, what has worked, what has failed, and three concrete practices colleagues can try. Include evidence for claims. Distinguish observations from recommendations; do not invent time savings, usage counts or results.
>
> Use Margen components deliberately: a workflow, a comparison table, prompt/code examples, highlights/lowlights, contextual marginal notes and next steps where they improve the explanation. Make it readable on mobile. Record the real agent, device and session when available. Do not publish credentials, client data, private conversations or unsupported personal claims.
>
> Validate and publish to my own account on https://artifacts.botto.is. I authorize sharing this specific artifact with the exact domain COMPANY_DOMAIN, with comment permission and invited visibility. Use `margen share --artifact-id ID --domain COMPANY_DOMAIN --role commenter --visibility invited`, verify the saved audience, and return the artifact link. Do not make it public or send messages to colleagues. If my account is not connected, prepare the local artifact and guide me through connecting it without asking me to paste a token into chat.

For a company theme, name it explicitly; the theme does not grant access. See [domain sharing](domain-sharing.md) for permissions, revocation and account-membership limits.

## What to observe

Record actual trial findings: time to first artifact, sign-in or install friction, whether colleagues can find it in Shared, mobile readability, quality of contextual comments and how easily feedback reaches a useful revision. These are evaluation questions, not measured results. A copied prompt is not automatic agent execution or proof that a historical session was reopened.
