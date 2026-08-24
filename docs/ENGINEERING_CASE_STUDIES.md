# Engineering Case Studies

These examples are condensed from V180's development history. They are included because they show the project's core method: **observe a failure, reconstruct the evidence, identify what the existing measurement actually measured, change the mechanism, then compare outcomes.**

## 1. A passing self-test did not mean the application started

A generated Snake game repeatedly passed its explicit self-test while the normal application path crashed almost immediately.

The failure was traced to a test fixture using dictionary-style key access while the real caller supplied a Pygame key-state object. Production code had been bent to satisfy the fixture instead of the real input path.

### Change

V179 added an entry-point smoke check that runs the deliverable the way a user runs it, not through the test flag.

### Observed result

In the V180 development record, the smoke check first caught the failure in about **0.4 seconds**, the subsequent repair survived the real startup path, and the recorded run completed in **43 iterations / 1.2M tokens**, compared with **98–130 iterations / 6.6–7.2M tokens** on the preceding runs.

The lesson was not “tests are bad.” It was that **a test path and a user path answer different questions**.

## 2. Repetition detection was measuring lines instead of novelty

An earlier generation-loop detector counted repeated normalized lines. A degenerate model response could repeat the same content while re-wrapping it differently, so the repeated-line threshold never fired.

### Measurement

The development analysis measured novelty over 600-character windows using 8-word shingles. Recorded calibration examples included:

- degenerate generation: **0.08** novelty;
- model writing a normal game: **1.00**;
- 300 lines of near-identical enumeration: **0.74**.

A novelty floor of **0.25** over a streak of windows separated the observed failure from the measured legitimate cases better than changing the old repeated-line threshold.

### Change

The detector was changed from “how often did this line repeat?” to “is this generation still saying anything new?”

## 3. Mutation score mixed logic defects with presentation noise

Mutation testing initially produced a blended score across gameplay logic and presentation code. Many survivors were cosmetic constants or rendering details that ordinary behavioral tests should not pin exactly.

### Change

V173 separated **logic** and **presentation** mutations, prioritized logic sampling, and judged the minimum threshold on the logic sample when enough logic mutants were available.

### Outcome

The score did not magically become higher. The development notes explicitly record that logic kill rates remained low. The improvement was that the number became **more truthful and actionable**: the model saw logic failures instead of being pushed toward brittle pixel-level assertions.

## 4. A refused command was being recorded as a failed execution

V180 fixed a bookkeeping error where a command rejected by the command allowlist could still be recorded as the latest failed run of the script named in that command.

That allowed a command that **never executed** to downgrade an otherwise successful outcome.

### Change

The ledger now records a run only when the command result positively indicates that execution actually began.

This is a small implementation change with a broader research principle behind it: **absence of execution is not evidence of execution failure.**
