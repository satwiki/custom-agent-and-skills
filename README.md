# custom-agent-and-skills

Satwiki's collection of reusable GitHub Copilot custom agent and Skills.

## What's included

- Repository-wide Copilot instructions: `.github/copilot-instructions.md`
- Reusable custom agent instruction examples in `.github/agents/`
- Reusable Skill definitions in `.github/skills/*/SKILL.md`

## Structure

```text
.github/
  copilot-instructions.md
  skills/
    release-notes/
      SKILL.md
    repo-visualizer/
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
