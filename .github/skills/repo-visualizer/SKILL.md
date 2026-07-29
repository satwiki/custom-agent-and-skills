---
name: repo-visualizer
description: "Visualize implementation steps, feature flows, use cases, and service dependencies in large code repositories as evidence-based diagrams. Use when tracing one or more functionalities across modules, comparing related or independent workflows, mapping internal dependencies, or documenting external HTTP, A2A, JSON-RPC, gRPC, messaging, database, and third-party integrations. Produces Mermaid by default and supports requested alternative formats."
argument-hint: "functionality-or-use-cases=... [entry-points=...] [detail={overview|standard|deep}] [format=...]"
---

# Implementation Visualizer

## Overview

Trace how requested functionality is implemented and render the result as a single diagram with one or more sub-diagrams.
The diagram should display the units of work, their relationships, and the evidence that supports them.
Include internal dependencies, state transitions, data stores, messages, and external services with their protocols.
ALWAYS Honor the user's scope, format, and detail instructions before applying the defaults in this skill.

## Inputs

Infer missing inputs from the request and repository. Ask only when ambiguity
would materially change the traced workflow.

* Functionality or use cases to visualize
* Optional entry points, files, symbols, endpoints, jobs, or events
* Optional detail level: `overview`, `standard` (default), or `deep`
* Optional diagram format: Mermaid (default), PlantUML, or ASCII
* Optional output location when the user wants the diagrams saved

## Your objective

### 1. Define the requested behavior

1. Restate each requested functionality as an observable goal.
2. Identify supplied anchors such as routes, commands, dependency injections, UI actions, event types, jobs, tests, or symbols.
3. Determine level of detail requested from user's ask: overview, standard, or deep. Use the default if not specified.

### 2. Trace the implementation with evidence

1. Locate the entry point for each functionality by scanning the repo or user-provided input.
2. Follow calls, registrations, handlers, state transitions, dependency injections and data flow to the code that performs each unit of work.
3. Follow configuration and client construction far enough to identify external systems integrations.
4. Inspect tests or call sites when they provide the clearest evidence for branching, retries, failure handling, or orchestration.
5. Mark uncertain behavior as an assumption. Do not invent missing steps.

Prefer targeted symbol references and nearby call sites over broad directory summaries. When a wrapper only forwards work, continue to the component that
makes the decision, mutates state, or performs the operation.

### 3. Convert code into readable units of work

Create one node for each meaningful implementation step. Label nodes with a concise verb phrase that describes the actual work, such as `_validate_payload_order` will become `Validate order`. Do not add raw symbols, file paths, or function names to the node label. Use the evidence list to show the underlying code.

Apply these labeling rules:

* Use two to six words when practical
* Describe behavior, not implementation syntax
* Do not use a raw function, class, file, or endpoint name as the label
* Preserve domain terms needed for technical accuracy
* Split a component only when it performs distinct decisions or side effects
* Combine pass-through helpers that add no meaningful behavior

### 4. Determine diagram topology

Treat functionalities as related when at least one runtime relationship exists:

* One functionality invokes, triggers, resumes, or compensates another
* They exchange data, state, messages, or control flow
* They share an orchestrated transaction or ordered lifecycle
* A result from one is required by the other

For related functionalities, produce one connected diagram. Use labeled
subgraphs to preserve each functionality's boundary and draw the dependency
between them.

Treat functionalities as independent when no runtime control or data dependency
connects them. Produce a separate Mermaid diagram for each independent group.
Using the same utility, database, or external provider does not by itself make
otherwise independent workflows related.

When evidence is insufficient to classify the relationship, state the ambiguity
and ask one focused question before finalizing the topology.

### 5. Model dependencies and protocols

Use directional edges that match execution or data flow. Label edges whenever
the interaction type is not obvious.

* Internal synchronous call: `calls`
* Internal asynchronous work: `queues`, `publishes`, or `consumes`
* State or data access: `reads`, `writes`, or `updates`
* External request: protocol plus operation, such as `HTTP POST`,
  `A2A task`, `JSON-RPC call`, `gRPC`, or `WebSocket`
* External event or broker: protocol or transport plus event name
* Conditional path: short outcome such as `valid`, `declined`, or `retryable`

By default, show every implemented branch, retry, timeout, fallback,
compensation, and terminal failure path in the requested functionality. Omit or
collapse paths only when the user asks for a narrower or higher-level view.

### 6. Render diagrams

- Use Mermaid unless the user requests another format. For Mermaid, use
`flowchart LR` when the diagram can be covered in ~6 boxes horizontally. If not then, use `flowchart TD` to generate vertical flow which should be substantially easier to read. 
- Use stable, descriptive node IDs and quote labels.
- Do not place file paths or raw symbols inside nodes; put evidence after the diagram. 
- For another format, preserve the same topology, semantic categories, edge labels, color distinctions when supported, and visible legend.
- Every diagram must include a visible legend and these semantic classes. Omit a legend category only when the diagram has no component of that type.
- Keep the main flow readable. For a deep trace with many repeated operations, group them in a subgraph or replace them with one accurately named unit of work.

### 7. Present evidence and assumptions

After each diagram, provide a compact evidence list that maps each node to the
owning file and symbol. Include line references when available. Then list:

* External dependencies and observed protocols
* Assumptions or unresolved dynamic behavior
* Deliberately omitted details that fall outside the requested scope

Do not claim a protocol solely from a client or library name. Confirm it from
configuration, transport setup, request construction, interface contracts, or
tests whenever possible.

## Output Format

Return content in this order:

1. A one-paragraph scope summary naming the functionality groups
2. One connected diagram for each related group
3. Separate diagrams for independent groups
4. Evidence for each diagram
5. External dependency and protocol summary
6. Assumptions and omissions

When saving Mermaid output, use a Markdown file so diagrams remain renderable.
For another requested format, use its conventional file extension or a Markdown
code fence when no standalone artifact is needed.

## Quality Checks

Before finishing, verify that:

* Every requested functionality appears in exactly one diagram
* Related workflows are connected and independent workflows are separated
* Every node describes an exact unit of work rather than a raw symbol
* Every external system and confirmed protocol relevant to the flow appears
* Edge direction and branch labels match the implementation
* Every diagram contains an applicable color legend
* Node and edge claims have repository evidence
* Unknown or dynamic behavior is labeled instead of guessed
* The diagram remains legible without reading the evidence list
