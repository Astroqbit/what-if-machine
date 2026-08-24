# Security

## Important

What-If Machine contains safety-oriented restrictions around its file tools and shell tool, but these restrictions **must not be treated as a secure sandbox**.

The system intentionally allows development runtimes and tools such as Python, Node, package managers, Git, compilers, and test runners. Code executed through those tools may have the same operating-system permissions as the user running What-If Machine.

## Recommended operating model

- Run the agent in a dedicated workspace.
- Do not place passwords, API keys, private documents, browser profiles, SSH keys, cryptocurrency wallets, or other secrets in or near the workspace.
- Use a disposable virtual machine or container when testing untrusted prompts, models, packages, or generated code.
- Keep important projects under version control and backed up.
- Review package installation commands before allowing them in sensitive environments.
- Do not run the process as Administrator unless there is a specific, understood reason.

## Data that may be sensitive

The runtime can store detailed operational history in:

- `episodes.jsonl`
- `whatif_logs/`

These records may contain task descriptions, tool calls, command output, model reasoning/output, file names, error traces, and verification evidence. They are excluded from Git by the supplied `.gitignore`.

## Reporting

If this repository is published and you later accept outside contributions, add a private security-reporting contact before inviting vulnerability reports.
