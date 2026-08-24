# Architecture

## Overview

What-If Machine is a single-process Python agent runtime built around an Ollama chat client and a set of structured local tools.

Its primary workflow is:

1. Inspect the working environment.
2. Send the task and tool schemas to a local model.
3. Execute requested tool calls.
4. Record concrete tool results.
5. Detect failed or misleading verification.
6. Feed actionable evidence back to the model.
7. Continue until the build is complete or the run terminates.
8. Store a structured episode for later analysis.

## Major components

### CLI

The terminal interface supports interactive and single-prompt execution, model selection, Build/Plan agent selection, temperature and seed controls, logging, and memory-related commands.

### Ollama client

The runtime communicates with Ollama's chat API and records real prompt/completion token counts and timing fields when returned by the server.

### Tool layer

The current runtime exposes:

- `file_read`
- `file_write`
- `str_replace`
- `list_dir`
- `bash`
- `grep_search`

File tools resolve paths against the configured working directory.

### Build agent

The Build agent receives modification and execution tools and is intended to produce working artifacts rather than only recommendations.

### Plan agent

The Plan path is read-only and is intended for inspecting a project and developing an implementation approach before modification.

### Verification layer

The source contains multiple verification mechanisms developed from observed failure cases, including:

- syntax checks;
- runtime/entry-point smoke checks;
- detection of tests that pass without exercising important paths;
- line/function coverage analysis;
- detection of weakened or no-op assertions;
- final-claim checks against recorded command outcomes;
- mutation-testing infrastructure.

Mutation-gate execution is currently disabled by default in V180 (`MUTATION_MAX_FIRES = 0`).

### Episode memory

Each completed task can record:

- task text;
- tool trajectory;
- outcome;
- reflection/lesson;
- failure class;
- root cause;
- fix;
- verification evidence;
- token cost;
- temperature;
- seed;
- model and Ollama version;
- optional mutation history;
- optional stored model-thinking records;
- optional semantic embedding.

Episodes are stored as JSONL in the working directory.

### Logging

Detailed run logs are enabled by default and stored in `whatif_logs/` beside the runtime unless changed through CLI options.

## Design theme: evidence before completion

A recurring source of error in autonomous engineering systems is accepting a proxy for success:

- a parser succeeds, but runtime execution fails;
- a test returns zero, but important code never ran;
- a command is refused, but the ledger records it like an executed failure;
- a diagnostic exits zero but emits no expected evidence;
- a model's final summary claims artifacts that a prior command failed to produce.

What-If Machine adds checks around these failure classes so the model receives a more truthful description of what actually happened.

## Current limitations

- Windows is the primary developed path.
- Runtime safety controls are not a secure sandbox.
- The default model tag is specific to the author's development setup; public users can pass any suitable Ollama tool-capable model with `--model`.
- Model behavior is not uniform even when the Ollama interface supports tools.
- Full model-driven verification depends on the task, generated artifact, local dependencies, and available hardware.
