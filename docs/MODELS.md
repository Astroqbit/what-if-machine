# Model Compatibility

What-If Machine communicates with Ollama's `/api/chat` endpoint and supplies structured tool definitions. The most important model requirement is therefore **reliable tool/function calling over long iterative sessions**.

## Preferred model

### Ornith 1.5 — preferred

The author's preferred family is Ornith 1.5, especially the 35B model. The development runtime currently defaults to:

```text
ornith-1.5:35b
```

The official Ollama library exposes Ornith 1.5 under these tags:

```powershell
ollama run ornith-1.5:35b
ollama run ornith-1.5:9b
```

The earlier Ornith 1.0 release remains available as `ornith:35b` and `ornith:9b`.

Ornith is presented by Ollama as an agentic coding family. The runtime's default coding parameters (`temperature=0.6`, `top_p=0.95`, `top_k=20`) align with the precise-coding settings used during development.

## Other suitable model families

As of August 2026, Ollama marks the following public families as tools-capable:

| Family | Public Ollama examples | Notes |
|---|---|---|
| Ornith 1.5 | `ornith-1.5:35b`, `ornith-1.5:9b` | Preferred family |
| Ornith 1.0 | `ornith:35b`, `ornith:9b` | Compatible earlier release |
| Qwen3.5 | `qwen3.5:9b`, `qwen3.5:27b`, `qwen3.5:35b` | Tools + thinking; 256K variants available |
| Qwen3.6 | `qwen3.6:27b`, `qwen3.6:35b` | Tools + thinking; designed for agentic coding |
| Qwen3.8 | `qwen3.8:27b` | Tools + thinking; long-horizon agentic focus |
| Gemma 4 | `gemma4:12b`, `gemma4:26b`, `gemma4:31b` | Native function calling; larger variants provide 256K context |

These are **interface-compatible candidates**, not a claim that every quantization has been tested end to end with What-If Machine.

## Context window

The current runtime configures a fixed 256K context internally:

```text
256000
```

The current CLI does not expose a `--ctx` option. Changing the context size presently requires editing the source configuration for both the builder and judge clients.

## Custom Ollama endpoints

`--url` applies to the chat model and episode embeddings.

Example:

```powershell
python what_if_machine.py --url http://192.168.1.50:11434 --model ornith-1.5:35b --dir C:\work\mission
```

## Reproducibility note

Using the same model family and version does **not** by itself guarantee the same run. What-If Machine records the builder seed and Ollama version because replay also depends on generation state, the Ollama build and backend, the working directory, installed dependencies, and task artifacts.

For a close replay, pin `--seed`, use the same model and Ollama build, and begin from the same clean workspace.

## Practical compatibility rule

A model is a good candidate when it:

1. supports Ollama tools/function calling;
2. follows multi-step tool schemas reliably;
3. can preserve enough task context for iterative work;
4. handles code and debugging tasks well enough for the mission; and
5. does not repeatedly emit prose instead of requested tool calls.

Model quality affects how effectively the agent uses the runtime, while the runtime's verification layer is intended to reduce the damage from incorrect assumptions and false-success signals.
