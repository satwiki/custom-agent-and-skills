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
  agents/
    code-review-agent.md
```

## Usage

1. Copy these files into your own repository. Follow the same folder structure to make sure Copilot finds these.
2. Customize the instruction text for your team and project as needed.
3. Open Copilot Agent mode or Copilot CLI in GitHub or your IDE. Select the specific agent from the dropdown, or select skill by using `/`.
