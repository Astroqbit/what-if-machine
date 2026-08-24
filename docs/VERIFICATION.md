# Verification Design

What-If Machine is less about one model producing code and more about **measuring whether the resulting work deserves to be called complete**.

## Verification layers

### 1. Parse / syntax checks

Syntax validation catches malformed code, but the runtime treats parsing as only the first layer. A program can parse perfectly and still fail immediately when executed.

### 2. Runtime and entry-point checks

For runnable deliverables, entry-point smoke logic asks whether the program actually starts on the path a normal user would run.

This matters because a dedicated `--test` path can pass while the real application path fails.

### 3. Self-test evidence

The build instructions encourage generated GUI applications to expose a bounded `--test` mode. The test is expected to exercise named features rather than merely construct the program and exit zero.

### 4. Coverage evidence

The runtime contains coverage-oriented checks intended to detect code paths or assertions that never execute during verification.

The key question is not merely “did a test run?” but “what did that test actually reach?”

### 5. Assertion-quality / weakening checks

The runtime includes logic for detecting several patterns where verification is weakened to make a failing build appear green, including no-op checks and assertion relaxation.

### 6. Mutation-testing infrastructure

Mutation checks ask a different question from coverage:

> If the implementation were deliberately made wrong, would the test notice?

The V180 source retains mutation-testing infrastructure and logic/presentation classification, but mutation firings are disabled by default with:

```python
MUTATION_MAX_FIRES = 0
```

### 7. Completion-evidence checks

The runtime records command outcomes so a final answer cannot safely treat a refused or failed command as proof that an artifact was successfully produced or verified.

## Why these layers matter

Each layer answers a different question:

| Layer | Question |
|---|---|
| Parse | Is the file syntactically valid? |
| Runtime | Does the real program path start? |
| Self-test | Does an explicit verification path pass? |
| Coverage | Did relevant code/assertions actually execute? |
| Assertion quality | Is the test meaningful rather than decorative? |
| Mutation | Would the test notice selected wrong behavior? |
| Completion ledger | Do final claims agree with recorded execution evidence? |

No single layer proves everything. The design intentionally combines multiple imperfect measurements rather than treating one green signal as universal proof.
