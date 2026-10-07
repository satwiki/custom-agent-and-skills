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

1. Use the [security-first skill](.github/skills/security-first/SKILL.md)
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

## Evaluations

### Idea
A `baseline` answer is produced without using skill or custom
agent (just LLM), and a `with-target` answer (Skills or Agent instructions injected), then LLM-as-judge grades both
with heuristics plus an LLM judge. Open `results.md` when it finishes. No
Copilot SDK, GitHub token, or local runtime download. No PR workflow is
installed.

How to author cases, rubrics, and heuristics is in
[evals/README.md](evals/README.md). Every answer must be nonempty.
Extra regex gates are only on some cases: invented PR ids
(`release-notes`), invented providers (`repo-visualizer`), the
untrusted-document canary (`security-first`), and fabricated coverage
percentages (`code-reviewer`). Writing quality is scored by the judge,
not by these gates.

### Setup

Require Python>=3.11. Start with installing the required packages.

```powershell
python -m pip install -r requirements.txt
```

Copy [.env.example](.env.example) to `.env` and fill in the values, then
export them in your shell. Live runs need `EVAL_ENDPOINT`, `EVAL_API_KEY`, and
`EVAL_MODEL`. The key is used for generation and for the judge. `.env`
is gitignored.
>Avoid including sensitive information or API keys in `suite.json`, fixtures, or tracked
files.

OpenAI:

```powershell
$env:EVAL_ENDPOINT = "https://api.openai.com/v1"
$env:EVAL_API_KEY = "<secret>"
$env:EVAL_MODEL = "gpt-4.1"
```

Azure OpenAI (classic deployments API):

```powershell
$env:EVAL_ENDPOINT = "https://<resource>.openai.azure.com"
$env:EVAL_API_KEY = "<secret>"
$env:EVAL_MODEL = "<deployment-name>"
$env:EVAL_API_VERSION = "2024-10-21"
```

Azure Foundry / OpenAI v1 (URL already ends with `/openai/v1`):

```powershell
$env:EVAL_ENDPOINT = "https://<resource>.openai.azure.com/openai/v1"
$env:EVAL_API_KEY = "<secret>"
$env:EVAL_MODEL = "<deployment-name>"
```

Do not set `EVAL_API_VERSION` on a `/openai/v1` URL. That combination
used to call `AzureOpenAI` and produced HTTP 404 Resource not found.
The runner now uses `OpenAI(base_url=...)` for v1 URLs, and
`AzureOpenAI` only when `EVAL_API_VERSION` is set on a resource
hostname.

### Run

```powershell
python -m evals.run
python -m evals.run --target repo-visualizer
python -m evals.run --repeats 3
python -m evals.run --target repo-visualizer --repeats 3
```

* `python -m evals.run`: grade every target once
* `--target <name>`: grade one skill or agent (`release-notes`,
  `repo-visualizer`, `security-first`, `code-reviewer`)
* `--repeats <n>`: generate and grade each selected case n times

Each case makes 3 model calls per repeat:
- baseline generation,
- with-target generation,
- one judge call per answer.
Results will be available in `evals/results/<timestamp>/`:

* `results.md`: summary table, with/without-skill benchmark, and one
  section per answer
* `benchmark.json`: mean/stddev pass rate, time, and tokens plus delta
  (with_skill minus baseline), same shape as
  [agentskills.io aggregating results](https://agentskills.io/skill-creation/evaluating-skills#aggregating-results)
* `<case>-<arm>-<repeat>.txt`: the generated answer, with configured
  canaries redacted

Exit `0` when every with-target row has passing heuristics and a passing
judge. Baseline failures are expected and do not fail the command. Exit
`1` on with-target quality failures, `2` on configuration or suite
errors. Offline validation and tests make no model calls.