# What-If Machine

### IMPORTANT: "WORK IN PROGRESS" 

KNOWN ISSUES
- version Mismatched
- old info
- missing documents
- color Mismatched
- screen size issues
- misspelled names
- missing features
- broken pipelines
- timeouts
- MISSING DEPENDENCIES

**Local AI engineering and verification agent for Ollama**

What-If Machine is a Windows-first local AI system that turns complex technical requirements into working software, tools, workflows, and specialized agents through an iterative **build → test → diagnose → repair → verify** loop.

The project is built around one principle: **a generated answer is not the same thing as a verified result.**

## What makes it different

A normal coding chat can stop when the output *looks* finished. What-If Machine gives a local model structured tools, records what actually happened, reacts to failed verification, and can continue iterating when the evidence does not support completion.

The system has also been used as an experimental platform for studying AI-assisted engineering failure modes: false-success signals, tests that pass without exercising real behavior, repeated edits, misleading diagnostics, incomplete execution, and verification that measures the wrong thing.

## Core capabilities

- **General-purpose build workflow** — creates and modifies software, utilities, workflows, and task-specific agents rather than being tied to one application.
- **Build and Plan modes** — Build can modify and execute work; Plan is read-only for inspection and implementation planning.
- **Structured file operations** — read, create, replace, list, and search inside a bounded working directory.
- **Controlled command execution** — allowlisted developer commands, timeouts, path checks, and blocking for several destructive-command patterns.
- **Iterative failure recovery** — failed tool calls and verification results become evidence for the next iteration instead of silently becoming completion.
- **Evidence-oriented verification** — runtime checks, self-test guidance, entry-point smoke checks, coverage analysis, assertion-quality checks, completion-evidence checks, and mutation-testing infrastructure.
- **Persistent episode memory** — stores task outcomes, root causes, fixes, verification evidence, generation settings, and optional semantic embeddings.
- **Reproducibility controls** — records seeds, model information, temperature, token use, and Ollama version for later comparison.
- **Local-first operation** — uses an Ollama endpoint rather than requiring a hosted AI API.

> **V180 configuration note:** mutation-testing infrastructure is present, but `MUTATION_MAX_FIRES = 0` disables mutation-gate firings by default.

## Architecture

```text
Requirement
   │
   ▼
Build / Plan Agent
   │
   ├── file_read
   ├── file_write
   ├── str_replace
   ├── list_dir
   ├── grep_search
   └── bash
   │
   ▼
Tool results + evidence
   │
   ▼
Verification / failure analysis
   │
   ├── syntax & runtime checks
   ├── self-test / coverage checks
   ├── entry-point smoke checks
   ├── assertion-quality checks
   └── optional mutation checks
   │
   ▼
Iterate or report result
   │
   ▼
Episode memory + run log
```

More detail: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) and [`docs/VERIFICATION.md`](docs/VERIFICATION.md).

## Preferred and compatible models

The author's preferred model family is **Ornith 1.5**, with the **35B model preferred** and 9B as the lighter option. The development source uses the local tag `ornith-1.5:35b` by default.

For a standard Ollama library install, the public Ornith tags are:

```powershell
ollama run ornith:35b
ollama run ornith:9b
```

Other Ollama model families with native tool support are reasonable compatibility candidates, including **Qwen3.5, Qwen3.6, Qwen3.8, and Gemma 4**. Model behavior varies, so compatibility should mean *the interface is suitable*, not that every model/quantization has been benchmarked with this runtime.

See [`docs/MODELS.md`](docs/MODELS.md) for the compatibility notes and context-window guidance.

## Requirements

- Windows 11 is the primary development target.
- Python 3.10+ recommended.
- Ollama running locally or at a reachable URL.
- An Ollama chat model with tool/function-calling support.
- Python packages:
  - `httpx`
  - `rich` (recommended; the runtime has a plain-terminal fallback)
- Optional semantic-memory model:
  - `nomic-embed-text`

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

## Quick start

Start Ollama and pull a model. For the preferred public Ornith tag:

```powershell
ollama pull ornith:35b
```

Run What-If Machine in a dedicated workspace:

```powershell
python what_if_machine.py --model ornith:35b
```

If your local model is tagged `ornith-1.5:35b`, the source default can be used directly:

```powershell
python what_if_machine.py
```

Single-prompt mode:

```powershell
python what_if_machine.py --model ornith:35b "Build a small Python utility and verify it."
```

Useful options:

```text
--agent build|plan
--model MODEL
--url OLLAMA_URL
--dir WORKING_DIRECTORY
--temp TEMPERATURE
--seed SEED
--verbose
--log FILE
--no-log
```

`--ctx` defaults to 256000. Lower it for models whose native context window is smaller or when VRAM/RAM use matters.

## Persistent data

What-If Machine may create:

- `episodes.jsonl` in the working directory
- `whatif_logs/` beside the runtime
- normal project artifacts and Python caches in mission workspaces

`episodes.jsonl` and run logs may contain prompts, task history, file names, tool evidence, errors, and model output. They are excluded by the supplied `.gitignore`.

## Safety

The project contains engineering guardrails, **not a hardened security sandbox**.

The runtime intentionally allows interpreters, package managers, compilers, Git, and test runners. Programs executed through those tools inherit the operating-system permissions of the account running What-If Machine.

Recommended use:

1. Run in a dedicated workspace.
2. Keep credentials and private files outside that workspace.
3. Use version control or backups for important projects.
4. Use a disposable VM/container for untrusted code, packages, prompts, or models.
5. Review dependency-install commands in sensitive environments.

See [`SECURITY.md`](SECURITY.md).

## Verification philosophy

The project deliberately separates questions that are often collapsed into one:

- Did the file parse?
- Did the program actually start?
- Did the test execute the relevant behavior?
- Would the test notice if the behavior were wrong?
- Did a command actually run, or was it refused before execution?
- Does the final claim match the evidence produced during the run?

That distinction is the main engineering focus of the project.

## Engineering case studies

The development history contains measured examples of verification failures and the changes made in response. A concise portfolio-oriented selection is preserved in [`docs/ENGINEERING_CASE_STUDIES.md`](docs/ENGINEERING_CASE_STUDIES.md).

## Project status

**experimental portfolio release**

This repository focuses on the runtime itself. The cleaned public source compiles and its CLI smoke path is checked automatically in GitHub Actions. Full model-driven behavior depends on the selected Ollama model, local environment, task, dependencies, and generated artifacts.

## Author

Matthew Newland  
Technical Research • AI Systems • Verification • QA • Python
