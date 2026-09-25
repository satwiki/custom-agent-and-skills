# Custom Agents and Skills for your Development Workflow

Reusable and Extensible custom agents and skills for development and code review tasks, compatible with GitHub Copilot.


## What's included

- Reusable custom agent instruction examples in [`.github/agents/`](.github/agents/)
- Reusable Skill definitions in [`.github/skills/`](.github/skills/)


## Currently Available

```text
.github/
  skills/
    release-notes/
      SKILL.md
    repo-visualizer/
      SKILL.md
    security-first/
      SKILL.md
  agents/
    code-review-agent.md
```

## Usage

1. Clone or copy these files into your own repository. Follow the same folder structure to make sure Copilot finds these.
2. Customize the instruction text for your team and project as needed (instructions below).
3. Open Copilot Agent mode or Copilot CLI in GitHub or your IDE. Select the specific agent from the dropdown, or select skill by using `/`.

### PR reviewer
1. Make sure to connect mcp server (e.g. github, ADO etc.) in VS code and sign in. 
2. Provide a prompt: `Review PR #123` while the agent is selected in either CLI or chat mode. 
3. Additional access may be needed by the agent to read the PR (it can use `gh` CLI) and create temp file. You can either review the request in runtime, or pre-configure approvals for certain commands.

### Repo visualizer
1. Open CLI or chat window and prompt: `/implementation-visualizer Create a diagram for payment processing flow.`

### Security First

Use the [security-first skill](.github/skills/security-first/SKILL.md)
during implementation or a general code/security review. It covers APIs,
services, databases, caches, cloud resources, untrusted input, secrets, PII,
uploads, third-party dependencies, webhooks, and AI prompt injection.

- Run `/security-first Review my recent changes.` for staged, unstaged,
  and relevant untracked code, or specify `base=origin/main` for a branch review.
- Run `/security-first scope=repo Review repository security.` for a
  repository-wide review rather than the default changed-code scope.
- During implementation, request `/security-first mode=implement` with the
  feature description. The skill applies compatible secure defaults within the
  task and asks before authentication, privacy, or API-contract changes.
- Reviews are read-only until you approve fixes. The
  [code-reviewer agent](.github/agents/code-reviewer.agent.md) also applies this
  skill's security checks while retaining its broader review format.

The skill embeds OWASP Top 10:2025 checks in five security guidelines and
includes Presidio-based de-identification before PII storage or external
transfer, with explicit approval for necessary identity retention. It does
not require online reference loading, installs Presidio to verify automated PII detection finds every sensitive value.
Skill discovery depends on the coding agent. However you can explicitly
invoke it as needed.
