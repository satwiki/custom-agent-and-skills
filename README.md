# custom-agent-and-skills

A starter collection of reusable custom agent instructions and GitHub Copilot Skills.

## What's included

- Repository-wide Copilot instructions: `.github/copilot-instructions.md`
- Path-specific instruction example: `.github/instructions/agents.instructions.md`
- Reusable custom agent instruction examples in `agents/`
- Reusable Skill definitions in `.github/skills/*/SKILL.md`

## Structure

```text
.github/
  copilot-instructions.md
  instructions/
    agents.instructions.md
  skills/
    repo-onboarding/
      SKILL.md
    release-notes/
      SKILL.md
agents/
  code-review-agent.md
  issue-triage-agent.md
```

## Usage

1. Copy these files into your own repository.
2. Customize the instruction text for your team and project.
3. Open Copilot Chat/Agent mode in GitHub or your IDE and reference these agents/skills by name.
