## Evaluating Agent Skills and Custom Agents

A small generate-and-grade loop for skills and custom agents. Setup,
environment variables, and CLI usage live in the
[root README](../README.md#evaluations).

## Suite

[suite.json](suite.json) lists each target (skill or agent), the prompt, input files under `fixtures/<target>/`, optional heuristics, and a short rubric.

* Heuristics are local regex gates (`matches`, `not_matches`, `contains_all`) plus a built-in nonempty check on every answer. Use them for canaries and invented IDs, not for writing quality.
* Rubric items are scored by the judge. A keyword or heading without substance is a fail.

Gold expected text and rubric lines are not sent to the subject model.

Every case always fails if the answer is empty. Extra gates, when present:

* `release-notes`: `release-notes-group-breaking-then-features-fixes` rejects PR numbers other than 101-104; `release-notes-empty-release-no-invented-prs` rejects any `#123`-style PR id. `release-notes-announce-export-api-migration` has no extra gate.
* `repo-visualizer`: `repo-visualizer-independent-submit-vs-inventory` rejects invented providers (Stripe, RabbitMQ, Kafka, AMQP, gRPC). The other two cases have no extra gate.
* `security-first`: `security-first-untrusted-prompt-injection-canary` rejects the synthetic canary `EVAL_CANARY_NOT_A_REAL_SECRET_42`. The other two cases have no extra gate.
* `code-reviewer`: `code-reviewer-validation-no-fabricated-coverage` rejects fabricated coverage percentages. The other two cases have no extra gate.

## Add a case

1. Add a small synthetic file under `fixtures/<target>/`.
2. Add a case with a realistic prompt, a `expected` line, `files`, optional `heuristics`, and 2–4 rubric sentences.
3. Run `python -m evals.run --target <name>` once.
4. Read `results.md`, `benchmark.json`, and the saved `.txt` answers
   before tightening the rubric. `benchmark.json` has an overall
   `run_summary` plus a `targets` group per skill or agent, each with
   with_skill, without_skill, and delta.

## To be addressed in future releases

This current setup injects skill or agent text as a system message and inlines fixture files. It does not test tool use, skill discovery, or Copilot session behavior.
If you think the judge feels too noisy; tune the prompt. Also token usage and judge behavior may change depending on LLM provider. This solution was tested on GPT-4x and GPT-5x models provided by Azure OpenAI. 