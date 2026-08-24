# Model Compatibility

What-If Machine communicates with Ollama's `/api/chat` endpoint and supplies structured tool definitions. The most important model requirement is therefore **reliable tool/function calling over long iterative sessions**.

## Preferred model

### Ornith 1.5 — preferred

The author's preferred family is Ornith 1.5, especially the 35B model. The development runtime currently defaults to the local model tag:

```text
ornith-1.5:35b
```

The public Ollama library exposes Ornith under these tags:

```powershell
ollama run ornith:35b
ollama run ornith:9b
```

Ornith is specifically presented by Ollama as a tools-capable agentic coding family. The runtime's default coding parameters (`temperature=0.6`, `top_p=0.95`, `top_k=20`) also align with Ornith 1.5's published precise-coding recommendations.

## Other suitable model families

As of August 2026, Ollama marks the following public families as tools-capable:

| Family | Public Ollama examples | Notes |
|---|---|---|
| Ornith | `ornith:35b`, `ornith:9b` | Preferred family |
| Qwen3.5 | `qwen3.5:9b`, `qwen3.5:27b`, `qwen3.5:35b` | Tools + thinking; 256K variants available |
| Qwen3.6 | `qwen3.6:27b`, `qwen3.6:35b` | Tools + thinking; designed for agentic coding |
| Qwen3.8 | `qwen3.8:27b` | Tools + thinking; long-horizon agentic focus |
| Gemma 4 | `gemma4:12b`, `gemma4:26b`, `gemma4:31b` | Native function calling; larger variants provide 256K context |

These are **interface-compatible candidates**, not a claim that every quantization has been tested end-to-end with What-If Machine.

## Why the README does not say “Qwen3.5 through Qwen3.8”

That phrasing would imply every intermediate numbered release exists and was verified. At publication time, the public Ollama library has Qwen3.5, Qwen3.6, and Qwen3.8 entries; this document names them explicitly instead.

## Context window

V180 historically used a fixed 256K context. The portfolio release exposes that as:

```text
--ctx TOKENS
```

Default:

```text
256000
```

This makes it possible to lower context for smaller-context models or reduce memory use without editing the source.

## Custom Ollama endpoints

`--url` now applies consistently to both the chat model and episode embeddings. Earlier development code used the CLI URL for chat but left embedding memory hard-coded to `http://localhost:11434`.

Example:

```powershell
python what_if_machine.py --url http://192.168.1.50:11434 --model ornith:35b --dir C:\work\mission
```

## Reproducibility note

Using the same model family/version does **not** by itself guarantee the same run. What-If Machine deliberately records the builder seed and Ollama version because replay also depends on generation state, the Ollama build/backend, the working directory, installed dependencies, and task artifacts.

For a close replay, pin `--seed`, use the same model and Ollama build, and begin from the same clean workspace.

## Practical compatibility rule

A model is a good candidate when it:

1. supports Ollama tools/function calling;
2. follows multi-step tool schemas reliably;
3. can preserve enough task context for iterative work;
4. handles code/debugging tasks well enough for the mission;
5. does not repeatedly emit prose instead of requested tool calls.

Model quality affects how effectively the agent uses the runtime, while the runtime's verification layer is intended to reduce the damage from incorrect assumptions and false-success signals.
