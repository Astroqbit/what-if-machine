#!/usr/bin/env python
"""
What-if Machine v180.5 - Nested Learning Agent for the Terminal
Enhanced with Matrix-themed visuals, recursive self-correction, and episode memory

CURRENT VERSION: V180.5          (this file: what_if_machine.py)

V180.5 - ONE STATUS HUD, REFRESHED IN PLACE.

V180.4 corrected stale values by printing a new pair of panels after each
change. The values were right, but terminal scrollback then contained duplicate
Session Configuration and Quick Commands panels. V180.5 makes the pair a
single transient prompt HUD: while the CLI is waiting it is the only copy on
screen; when Enter is pressed, that exact rendered block and the echoed input
line are erased, the input is reprinted once as history, and the next prompt
draws the HUD again from current runtime state. A toggle therefore changes the
existing visible status without accumulating panels. The HUD is removed before
Agent.process() starts, so it never nests or fights with the separate live task
dashboard.

PREVIOUS VERSION: V180.4

V180.4 - QUICK-COMMAND STATUS IS NOW LIVE.

The Session Configuration and Quick Commands panels used to be startup-only
snapshots. Commands changed the real runtime setting, but the old OFF/value in
those panels remained on screen and made the machine appear desynchronized.
Both panels now come from one shared renderer, and every successful command
that changes displayed state immediately prints a refreshed snapshot. This
covers /autotest, /inject, /confidence, /temp, /seed, /model, /agent and
/memory clear. The Rich badges remain bright green for ON and bright red for
OFF; plain-console mode receives the same current values as text.

PREVIOUS VERSION: V180.3

V180.1 - AUTO-TEST IS THE EXISTING PHRASE, APPENDED AT THE EXISTING DOOR.

Ending a task with `test and fix it` already works as a natural-language
control instruction: the unchanged user message enters Agent.process(), stays
in the pinned task context, and the model drives the existing test -> observe
-> repair -> re-test loop. There is deliberately no second verification mode
and no forked prompt. `/autotest on` now appends that exact phrase to every
question at CLI.process_message(), the one shared door used by interactive,
one-shot, `/prompt`, Rich, fallback and plain-console paths. If the phrase is
already at the end it is not duplicated. `/autotest off` restores byte-for-byte
pass-through, and `--autotest` starts a session enabled. The state lives on the
CLI, so agent switches and conversation clears do not silently turn it off.

PREVIOUS VERSION: V180           (this file: what_if_machine.py)

V180 - A REFUSED COMMAND IS NOT A FAILED RUN.

THE V179 ENTRY SMOKE WORKED, on its first outing. Snake run of 2026-08-06
04:53, from its own log:

    05:01:47  ENTRY SMOKE: bounced - snake_game.py DIED 0.4s after start
    05:03:10  ENTRY SMOKE: snake_game.py started and was still running at
              8.0s - pass
    05:03:10  MUTATION TARGET: snake_game.py (16 edits) chosen over
              last-written test_game_start.py (1 edit)
    05:03:35  MUTATION GATE: caught 16/32 logic (50%) - passed

That is the bug that shipped three runs running, caught in 0.4s and fixed.
The model's own fix accepts BOTH shapes - `hasattr(keys, "get")` - and it
wrote test_game_start.py, its own smoke test, unprompted. Verified here: the
program starts and is still running at 8s, and 400 frames driven with a real
pygame ScancodeWrapper do not raise. 43 iterations and 1.2M tokens, against
98-130 iterations and 6.6-7.2M on the runs before it. The V173 mutation-target
override also fired for the first time, and saved the gate from planting 40
bugs in a 28-line smoke script.

AND IT WAS STILL MARKED PARTIAL. One line explains it:

    msg 81  python snake_game.py --test        -> exit 0, PASS
    msg 83  timeout 3 python snake_game.py ... -> BLOCKED, never ran

`timeout` is not in the allowlist. The refusal names snake_game.py, so the
V61.5 ledger recorded it as that script's latest run and marked it failed -
for a command that never started - and outcome check (a3) downgraded
success -> partial on it. Replayed through the real `_scripts_named_in`:
V179 stores ('snake_game.py', False); V180 stores ('snake_game.py', True).

THE FIX. `_command_executed()` identifies a real run POSITIVELY - a command
that ran always comes back with an exit code, or with the tool's timeout
report, which is what it returns when it killed a process that WAS running.
Everything else - not in the allowlist, forbidden, empty, a path outside the
sandbox - never started, and the ledger no longer records it. A skipped write
is logged rather than silent.

Same class as the V61.7 duplicate-suppression fix (`executed = dup_msg is
None`). That one taught the ledger that a suppressed duplicate did not run.
This one teaches it the same about a refusal. The rule is one rule: the
ledger records what RAN.

NOTE, not fixed here because it is a judgement call rather than a defect: the
model reached for `timeout 3 python snake_game.py` - exactly what the V179
gate does - and the sandbox refused it. Allowlisting `timeout` would let
`timeout 3 rm -rf /` past a validator that only checks each segment's first
token, so it is not a safe one-line change. The bash tool already takes its
own `timeout` parameter, and the model worked around it correctly by writing
a script, so nothing is blocked in practice.

Suite: test_v180.py, 29/0/0. test_v179.py 32/0/0, test_v178.py 28/0/0,
test_v177.py 31/0/0, test_v175.py 23/0/0, test_v173.py 66/0/0, test_v172.py
27/0/0, test_v171.py 57/0/0 all green. EXPERIMENTAL and BUILD_PROMPT
byte-identical to V179.

PREVIOUS VERSION: V179            (this file: what_if_machine_v179.py)

V179 - THE MACHINE HAS BEEN VERIFYING A PATH NOBODY RUNS, AND ITS OWN GATE
CAUSED THE DEFECT.

THE SAME BUG HAS NOW SHIPPED THREE RUNS RUNNING - mario 2026-08-05, snake
2026-08-06 02:22, snake 2026-08-06 03:59. Each time the self-test printed
every tick and exited 0, and each time `python <file>` raised on the first
frame. On the last one: 41 bash calls, 41 of them `snake_game.py --test`, and
ZERO that ran the program the way a person runs it.

THE MACHINE CAUSED IT, traced through that run's own trajectory:
  msg 17  the coverage probe fires, correctly: "handle_input() [line 375]
          NEVER RAN AT ALL ... Extend --test to CALL them with real inputs"
  msg 28  the model adds `make_keys`, a dict factory, to its test
  msg 34  the model edits PRODUCTION CODE so the dict works:
              -  if keys[pygame.K_UP] and current != (0, 1):
              +  if keys.get(pygame.K_UP, False) and current != (0, 1):
The old line was CORRECT - `keys[...]` is exactly what
pygame.key.get_pressed() supports. The new one only works for a dict, which
is the thing the fixture hands it and the thing the real caller never does.
Coverage asks "did this function execute". A fake makes that true without
making the program work, and the cheapest way to satisfy the gate was to bend
the deliverable to fit the fake.

I checked the accusation he actually made - that the mutation gate corrupts
the artifact - and it is FALSE, by measurement. A mutant is `ast.unparse`
output, which strips every comment and docstring; the shipped file has 97
comments, 4 docstrings and is CRLF throughout. The gate restores byte-for-byte
(verified again here over a full 40-mutant round). The gate that did the
damage was the coverage probe, not the mutation gate.

THE FIX - the one question no fixture can answer: does the program START?
  entry_point_smoke() runs `python <deliverable>` with no test flag and a
  short budget, and reports:
      timed out   -> it started and is still running. For anything with a
                     main loop that IS the pass, which is why 8s is enough.
      exited 0    -> it ran to completion. Fine.
      exited != 0 -> it died; the traceback is the finding.
  Measured: the two broken snake builds die in 0.2s and 0.4s with the exact
  AttributeError; the working mario build is still running at 8s.

  It runs at the completion path, keyed on the last edit so it re-runs on a
  change and is silent otherwise - the same no-repeat rule as the V178 gate
  and the V172 mutation skip. It only fires for a file whose `__main__` does
  something other than run its own test. And unlike every other gate here it
  NEVER WRITES: it cannot influence what the model produces, only report what
  the program already does. That matters, because influencing what the model
  produces is exactly how this bug got made.

  The bounce message names the failure mode directly: a fixture was built to
  satisfy a check, then production code was adjusted to accept the fixture.
  Fix the production code for what the REAL caller passes, then change the
  test to match - never the other way round.

MY OWN GAP, CAUGHT BY A3 BEFORE SHIPPING: the first has_plain_entry() treated
`if __name__ == "__main__": _test()` as a real entry point. Running that
plainly just runs the test, so smoking it proves nothing. A __main__ block
whose every call targets a name containing "test" is no longer an entry
point. C6 was also wrong first - it asserted a phrase across an f-string line
break, matching the source's wrapping instead of the message; it now asserts
on the normalised message.

Suite: test_v179.py, 32/0/0. test_v178.py 28/0/0, test_v177.py 31/0/0,
test_v175.py 23/0/0, test_v173.py 66/0/0, test_v172.py 27/0/0, test_v171.py
57/0/0 all green. EXPERIMENTAL and BUILD_PROMPT byte-identical to V178.

PREVIOUS VERSION: V178            (this file: what_if_machine_v178.py)

V178 - THE COMPLETION GATE WAS ASKING THE WRONG QUESTION, AND ASKING IT ONCE.

Its condition was "has ANY command succeeded since the last edit". On the
snake run of 2026-08-06 03:20, after the last edit at message 188:

    msg 190  exit 1   python snake_game.py --test      <- the test FAILED
    msg 194  exit 0   python -c "import pygame; ..."   <- a diagnostic
    msg 196  exit 0   python -c "import pygame; ..."   <- another

Those two probes set last_ok_bash past the edit, the condition was satisfied,
and THE GATE NEVER FIRED AT ALL. The run finished at iteration 111 with a red
self-test and a game that raises on its first blit. A diagnostic that exits 0
says nothing about whether the artifact works.

And on the mario run of 2026-08-05 16:37 the same gate fired correctly at
17:09, the model kept failing, and finished unstoppably at 17:19 - because
`completion_nudged` was a one-shot boolean.

  1  Two facts are now recorded from bash results, separately from
     last_ok_bash: last_test_pass and last_test_fail, via the V171 detectors.
     The gate bounces when the edit was never run OR when the last thing the
     TEST did was fail. Replayed against that run's real trajectory: V177
     fires NEVER, V178 fires twice, both as "test-red".
  2  `completion_nudged` becomes a SIGNATURE of the facts the bounce was
     about - (last_py_edit, last_test_fail, last_test_pass). It re-fires only
     when one of them changes, which is the rule the duplicate guard and the
     V172 mutation skip already use: never repeat over an unchanged input. It
     cannot loop by construction - suite B6 drives fifty identical
     completions and gets exactly one bounce.
  3  The mutation gate no longer spends a round when the self-test is red. It
     needs a passing baseline; without one it runs three baselines and
     reports "cannot measure", which is what rounds 2 AND 3 produced on
     2026-08-06 03:20 and again on 2026-08-05 16:37 - six wasted rounds
     across two runs, each spending budget to repeat what the completion gate
     had already said.

MY OWN BUG, CAUGHT BY THE SUITE BEFORE SHIPPING: the first version kept
"never ran" keyed on last_ok_bash alone, so a green self-test that this
machine did not happen to score as a successful bash still read as "you never
ran it". B5 failed on exactly that. `_ran_since` now takes the later of
last_ok_bash and last_test_pass - which is the whole reason the two facts are
tracked apart.

V177 IS WORKING, from this run's log: "STREAM NOVELTY WATCH: 6 consecutive
600-char windows below 25% new content (last 1%)". It fired once and cost one
recovery, where the line counter it replaced needed two on the previous run.

STILL NOT FIXED, and stated rather than buried: the shipped artifact fails
because the test creates `pygame.PixelArray(game.screen)` at line 569 and
never closes it. set_mode() returns the same display surface every time, so
every later SnakeGame() inherits the lock and the next blit raises. That is a
resource the test acquires and never releases - the machine has no mechanism
that sees it, and inventing a pygame-specific one would break the doctrine
that nothing in here knows about a framework.

Suite: test_v178.py, 28/0/0. test_v177.py 31/0/0, test_v175.py 23/0/0,
test_v173.py 66/0/0, test_v172.py 27/0/0, test_v171.py 57/0/0 all green.
EXPERIMENTAL and BUILD_PROMPT byte-identical to V177.

PREVIOUS VERSION: V177            (this file: what_if_machine_v177.py)

V177 - THE GENERATION-LOOP WATCH MEASURES THE WRONG THING. One statistic
replaced inside OllamaClient's stream reader. No new gate, no new detector,
no fallback: the cancel path, the EXPERIMENTAL switch and the recovery budget
are all the ones that were already there.

WHAT WAS WRONG. The V61 watch counted identical normalised LINES of >= 40
chars and cancelled at 8 repeats. On the snake run of 2026-08-06 it fired
twice - those are the "recovery 1 of 3" and "recovery 2 of 3" messages - and
then missed the third loop, the one that ended the run at iteration 110 of a
1,000,000 budget with a SUCCESS and a game that crashes on its first frame.

Measured on that exact message: the most-repeated line occurred FIVE times
against a threshold of 8, and 127 of its 191 lines were under the 40-char
floor and were never counted at all. A degenerate generation does not repeat
lines - it repeats CONTENT, re-wrapped, with the breaks falling elsewhere
each cycle.

MOVING THE THRESHOLD CANNOT FIX THAT, in either direction.
STREAM_LOOP_MIN_LINE is a MINIMUM: raise it and more lines are skipped and it
fires less; lower it and it starts counting `)` and blank-ish lines, which
repeat in every real file. The unit was wrong, so no value of it is right.

WHAT IS ACTUALLY TRUE OF A LOOP is that it stops saying anything new. The
reader now hashes 8-word shingles of everything generated so far and, for
each 600 chars of new output, measures the fraction of shingles never seen
before in this generation. Healthy output is ~1.0; a loop is ~0.0. Line
breaks, re-wrapping and small rewordings do not affect it.

CALIBRATION, worst value over 6 consecutive windows - the number the
threshold has to separate. Measured on real artifacts, not chosen:

    the degenerate message that slipped through        0.08
    a model writing snake_game.py                      1.00
    its --test block, 60 near-identical assertions     1.00
    300 lines of near-identical enumeration            0.74
    a file containing a duplicated 2.4k function       1.00
    a file re-emitting a 3k block it already wrote     0.86

0.25 is almost exactly the geometric mean of 0.08 and 0.74: 3x clear of the
worst legitimate case and 3x clear of the real one. A single window is NOT
safe at any threshold - one duplicated function drops it to 0.02 - which is
why the streak is 6 and not 1.

AND IT IS FASTER, not a latency trade. Driven through the real stream reader
with a fake httpx, his actual message cancels at 6,600 chars; the log shows
the old line rule needing 7,455 on the same kind of output.

REMOVED: STREAM_LOOP_MIN_LINE, STREAM_LOOP_REPEATS, line_counts, line_buf.
The recovery message no longer says "one line repeated 8+ times" - it says
how many windows went below the novelty floor, quotes the phrase the model
kept returning to, and tells it to write the smallest program that PRINTS the
value it is guessing at rather than reasoning about it again.

Suite: test_v177.py, 31/0/0. Section B drives the REAL OllamaClient stream
loop end to end and asserts the prior build does NOT cancel the same input.
One of my own fixtures was wrong first and B7 caught it: it repeated
identical lines 12 times, which the old counter catches, so it proved
nothing - it now re-wraps each repetition at a different width, giving a max
of 4 identical lines, which is the real defect. test_v175.py 23/0/0,
test_v173.py 66/0/0, test_v172.py 27/0/0, test_v171.py 57/0/0 all still
green. EXPERIMENTAL and BUILD_PROMPT byte-identical to V175.

PREVIOUS VERSION: V175            (this file: what_if_machine_v175.py)

V175 - THE RUN OF 2026-08-05 16:37 DID NOT STOP BECAUSE THE MODEL DECIDED IT
WAS DONE. It stopped because a command that ran nothing was reported to it as
a success, at the exact moment it needed that command's answer.

THE TRACE, from that run's own log:
  17:06  the self-test breaks; the red window opens and never closes again
  17:09  the completion gate fires - "edited but never run since". ONE SHOT,
         now spent
  17:13  mutation round 2: baseline --test does not pass, cannot measure
  17:15  mutation round 3: same. Two of three rounds bought nothing
  17:19  the model runs the one diagnostic that would have shown it why its
         assertion failed - a multi-line `python -c` printing the before and
         after state - and receives, in full:

             Exit code: 0

         Two turns later it emits a message with no tool call. The loop reads
         that as completion. Outcome downgrades success -> partial. 130
         iterations, red self-test, done.

WHY THAT COMMAND RETURNED NOTHING. create_subprocess_shell runs `cmd.exe /c`
on Windows, which stops at the first newline, so the command executes as
`python -c "` - an empty program. Python exits 0 and prints nothing, the
formatter omitted an empty STDOUT section, and the result was the bare exit
line. Measured in that log: 25 single-line bash calls, 23 returned output;
exactly ONE multi-line call, and it is the one that came back empty. `python
-c ""` reproduces the observed result exactly here.

Stated honestly: I cannot run cmd.exe, so the cmd.exe step is inference from
three facts - the result matches an empty program precisely, it was the only
multi-line command in the run, and every single-line command worked. The fix
does not depend on that inference being exactly right, because it removes the
multi-line path entirely AND makes a silent success speak either way.

  1  A multi-line `python -c "..."` is written to a real file in the working
     directory and run by name, so no shell can truncate it. NOT gated on
     sys.platform: one code path exercised everywhere beats a Windows-only
     branch that cannot be tested off Windows, and the two forms are
     equivalent (both give __name__ == "__main__", and staging the file in
     the working directory gives the same sys.path[0]). The staged file is
     deleted in a finally so it never reaches the artifact watcher or the
     deliverable-selection logic.
  2  A command that produces nothing on stdout AND stderr now says so
     instead of returning a bare exit line. Plenty of commands legitimately
     print nothing, so this states the fact rather than claiming failure -
     and escalates only when the command itself contains something whose
     whole job is to print, in which case it tells the model it has learned
     nothing and to re-run it as a file.

KNOWN-OPEN, not fixed here and stated rather than buried: the completion gate
is one-shot by design (V30.2), so a model that burns it early can finish
later with a red test and nothing will stop it. That is what happened at
17:09 vs 17:19. Fixing it means deciding when a second bounce is help and
when it is a loop, which is a design call, not a bug fix.

Suite: test_v175.py, 23/0/0. test_v173.py 66/0/0, test_v172.py 27/0/0 and
test_v171.py 57/0/0 all still green. EXPERIMENTAL and BUILD_PROMPT are
byte-identical to V173.

PREVIOUS VERSION: V173            (this file: what_if_machine_v173.py)

V173 - THE MUTATION SCORE NOW MEASURES SOMETHING THE MODEL CAN ACT ON.
One subsystem, no prompt change.

THE PROBLEM. A blended kill rate over a game is mostly a report on its
sprite code. Measured on the mario artifact of 2026-08-05, V172 sampling,
40 mutants: the eight survivors SHOWN to the model led with

    (500, 380, 5), (1000, 300, 7)        380 -> 381    platform coordinate
    if i % 2 == 0:                       ==  -> !=     coin sprite shading

Nothing catches those but a pixel-exact comparison, and a test that pins
sprite coordinates snaps on every cosmetic edit. So the machine was showing
the model eight things it should NOT fix, under a 50% floor it could not
reach however good the test got - which is how a warning channel teaches
that the whole channel is noise.

  1  _mutation_class(), module scope, one definition. The line is drawn at
     WHAT THE CODE PRODUCES: pixels and audio samples are presentation;
     everything else is logic. Level generation is explicitly LOGIC -
     `_generate_platforms_and_blocks` produces Block objects and a test can
     assert how many and where, so mutating it is a real defect. Classing
     every `_generate_*` as presentation would have excused six survivors
     that deserve catching; the first version of this classifier did exactly
     that and it was wrong.
  2  STRATIFIED SAMPLING. Logic is sampled first to the size the floor is
     judged at, a fifth of the budget is deliberately spent on presentation
     so the class stays visible, and any leftover goes back to logic. An
     off-class target costs one ast parse, not a self-test run. Measured on
     the same artifact: 32 logic / 8 presentation, where the old single pass
     gave roughly the reverse.
  3  BOTH NUMBERS REPORTED, floor judged on logic, blend kept for any
     existing reader. Below MUTATION_MIN_LOGIC_SAMPLE logic mutants the
     blend is used instead and the message SAYS which one it is talking
     about. The V172 noise band is computed on whichever sample the verdict
     is about, because the logic sample is the smaller of the two and
     banding it against the blend would understate the wobble.
  4  The message states the presentation number, says plainly it is NOT part
     of the floor, and tells the model not to chase it by asserting on
     sprite coordinates - measure what that code PRODUCES instead.

WHAT THIS DID NOT DO, stated because I predicted otherwise. I expected the
split to raise the number, on the reasoning that presentation mutants were
dragging it down. They were not. Three rounds of V173 on the same artifact:

    logic 9% / 25% / 12%      presentation 12% / 0% / 12%

The logic rate is no better than the blend was. That test genuinely does not
catch logic bugs, and the reason is visible elsewhere in the file: 16 calls
to `Game.__new__(Game)` build fake objects instead of running the real ones,
and the real loop is never driven. The split did not make the score better -
it made the score TRUE, made the floor reachable in principle, and put nine
actionable survivors in front of the model instead of eight sprite
constants. Those are the wins; a higher number is not one of them.

Cost: about 4 seconds per round on this artifact (24-29s vs 20-23s), from
parsing off-class targets that are then skipped rather than tested.

V173a, one line each at two sites, found by reading the messages the
2026-08-05 06:55 run actually delivered: the verdict said "inside the 18%
two different 40-MUTANT samples differ by" while the band had been computed
on the 32 LOGIC mutants it was judging. The gate exists to catch exactly
that - a number that does not measure what it claims - so it does not get to
do it in its own message. Both sites now name the scored sample. Suite D9.

Suite: test_v173.py, 66/0/0 with V172 present, 61/0/5 with only this build.
test_v172.py 27/0/0 and test_v171.py 57/0/0 both still green. EXPERIMENTAL,
BUILD_PROMPT, MUTATION_MIN_KILL_RATE, MUTATION_MAX_MUTANTS and
MUTATION_MAX_FIRES are byte-identical to V172 - section E of the suite
proves it, and E8-E11 prove by EXECUTION that the artifact is restored
byte-for-byte with nothing left behind, rather than by grepping for the
restore line (which is what E8 did first, and it failed while the code was
correct).

PREVIOUS VERSION: V172            (this file: what_if_machine_v172.py)

V172 - THE MUTATION GATE WAS NOT A MEASUREMENT. One subsystem, three
changes, all forced by the mario run of 2026-08-05 (88 iterations, 5.25M
tokens, outcome `partial`).

WHAT HAPPENED. The gate fired three times and reported 10% -> 20% -> 10%.
Checked against that run's own trajectory: there were ZERO successful edits
between round 1 and round 2, and ZERO between round 2 and round 3. The file
was byte-identical for all three. Reproduced here against the shipped
artifact, six rounds, nothing touched between them:

    8%, 20%, 10%, 8%, 22%, 5%      (spread 5-22%, a 4.4x swing)

Rounds 2 and 3 of that reproduction match his run exactly, which is the
proof that the sampling is what moved and not the code.

WHY. V61.21 re-seeds the sample per round on purpose - `1234 + 7919*round_no`
- so the model cannot write assertions against the mutants it was shown.
That is a real fix for a real failure (super_mario 2026-08-01, 16 assertions
citing a planted line and operator) and it is KEPT. But it means consecutive
rounds score DIFFERENT bugs, and _mutation_progress compared them anyway
against a +/-5 point threshold that sits far inside the spread. Three of the
five transitions in the six-round series above cross it.

WHAT IT COST. Round 3 told the model: "THIS IS WORSE THAN BEFORE YOUR LAST
CHANGE. The same check scored 20% (8 caught) before that edit and 10% (4
caught) now", named a cause - "a `try` wrapped around the whole body" - and
declared "This was my LAST check of this file". There was no edit and there
is no such try/except; the file's only handler is `except KeyboardInterrupt`,
which the model's own grep_search confirmed at step 81. It spent its last
~15 iterations hunting that phantom, stalled twice in degenerate repetition
(500s of silence each), and the session ended there.

  1  run_mutation_gate returns `file_md5` - the identity of what it measured.
  2  BOTH firing sites skip the round when the target is byte-identical to
     the last measurement AND no edit has landed since. The round is not
     spent, no mutants are planted, and the model is told plainly that
     nothing changed instead of being handed a number that only moved
     because the dice did. On his run this alone removes all three rounds.
  3  _mutation_progress takes `edits_between`. At 0 it makes no better/worse
     claim at all. Otherwise the threshold is a 2-sigma band computed from
     both samples (about 15 points at n=40, p~0.13) instead of a guessed
     5 points, so a 20%->10% wobble reads as flat while a 45%->15% collapse
     still reads as a regression. The regression text also now says that if
     you do not have a try/except, that is not the cause - the machine sent
     the model looking for one that never existed.

Also corrected: run_mutation_gate's docstring claimed "Deterministic sampling
so two runs of the same artifact score the same". That stopped being true at
V61.21 and has been wrong in the file ever since.

ON MY OWN V171 FIX 5: it made the re-measure fire more often, which without
change 2 above would have meant MORE measurements of an unchanged file, not
fewer. The mid-loop path takes the same hash check.

Suite: test_v172.py, 27/0/0 with V171 present, 20/0/7 with only this build.
test_v171.py is unchanged and still 57/0/0 against V170. EXPERIMENTAL,
BUILD_PROMPT, MUTATION_MAX_FIRES, MUTATION_MAX_MUTANTS and
MUTATION_MIN_KILL_RATE are byte-identical to V171 - nothing outside the gate
was touched, and section D of the suite proves it.

PREVIOUS VERSION: V171            (this file: what_if_machine_v171.py)

V171 - FIVE FIXES, ALL FOUND BY CROSS-REFERENCING THE mario_game RUN OF
2026-08-04 (60 iterations, 14.3 MB log, ended at the iteration cap with no
final summary and no VERDICT). Every claim below was reproduced by execution
against that run's own recorded tool results, not reasoned from the source.

WHAT THAT RUN DID: green self-test at step 13, coverage probe fires (31 of 62
functions never executed), green again at step 29, mutation gate bounces at
8%, and then 29 more steps over 47 minutes during which the artifact went
from 0 failures to 19 and the run died in a rewrite loop. It PEAKED AT STEP
29. Of the 17 failures it shipped with, 16 are defects in the test the model
wrote (a PixelArray axis swap, a camera transform ignored, and 19 PixelArray
objects created with none closed, which locks the surface so any later blit
raises) and exactly 1 exposes a real game bug.

  FIX 1   _is_test_fail WAS BLIND TO THE FAILURE SHAPE THIS MACHINE'S OWN
          PROMPT PRODUCES. The GUI protocol gives the model
          `print("SELF-TEST OK")` for the pass path and nothing for the fail
          path, so the model wrote its own: `FAIL: <msg>` lines and exit 1.
          Driven through the old detector that returns False - no
          ASSERTIONERROR, no "SELF-TEST FAIL", and the exit-code fallback
          additionally demanded the token "TEST" in the output, which appears
          only inside "SELF-TEST OK" on the PASS path. The detector saw every
          pass and no failure. Now: line-anchored FAIL:/FAILED: markers, ALL
          exit codes read rather than re.search's first (a wrapper that
          prints its child's "Exit code: 1" and then exits 0 was scored
          neither way), and the COMMAND accepted as evidence of testhood.
          Measured on the real run: red window opens 1 -> 2.
  FIX 2   EVERY ASSERTION ANALYSER KEYED ON THE TOKEN `assert`. The artifact
          had 0 assert statements and 128 `check(cond, msg)` calls, so
          _assert_bodies, _assert_lines and noop_assert_findings all returned
          empty, and test_edit_warning short-circuited on line 1
          (`if "assert" not in old_str: return ""`). A model could disable
          the entire test-weakening defence by naming its helper `check`,
          and one did - "TEST WEAKENED ... the edit drops 8 assertion(s)" is
          in that run's log with nobody warned. Now assertions are detected
          structurally: locally-defined helpers that test a parameter and
          record a failure, plus a shape pattern for edit fragments that do
          not parse. Measured: 0 -> 129 claims, 0 -> 127 traced lines,
          warnings delivered to the model 1 -> 5.
  FIX 3   AN OVERSIZED ANCHOR THAT MISSED WAS SEARCHED FOR ANYWAY. The
          candidates engine is superlinear: benchmarked on the real file,
          100 lines 22s, 200 lines 96s, 400 lines 270s. The model tried to
          replace its whole 911-line test block three times; the run log
          shows 365s and 367s of wall clock between end-of-generation and the
          next iteration, immediately after each miss. Refused now BEFORE any
          search, and only on the count==0 path - an exact match of any size
          still applies. 911-line miss: >269s -> 0.00s.
  FIX 4   THE SPIRAL BREAKER NAMED THE WRONG FILE. tgt came from
          last_py_edit_path ("most recently written"), so after a successful
          file_write of run_test.py the model was told "you are in a
          rewrite-the-whole-file loop on run_test.py" while all three failing
          edits were on mario_game.py. Same slot also chose the mutation
          gate's victim, which would have planted 40 bugs in a 19-line
          wrapper. Two new slots: last_failed_edit_path for the message, and
          per-file edit counts for the deliverable (30 edits vs 1).
  FIX 5   THE GATE PROMISED A RE-MEASURE IT COULD NOT DELIVER. Its message
          ends "I will re-measure after your next successful run of the
          self-test", but the gate only ran inside the completion branch - so
          the re-measure waited for the next attempt to FINISH. That run
          bounced at 8%, worked 29 more steps, never attempted completion
          again, and burned 1 round of a budget of 3. The V61.18
          regression-catcher had nothing to compare against. The re-measure
          now also fires mid-loop on a red->green transition, still bounded
          by MUTATION_MAX_FIRES, and both call sites build their message from
          one shared mutation_round_message() so the wording cannot drift.

Accounting: 11,651 -> 12,207 lines. 120 lines removed, every one replaced in
place (85 of them are the gate's message text relocated verbatim into the
shared builder). LF endings preserved, no CRLF introduced. EXPERIMENTAL,
BUILD_PROMPT and the mutation constants are byte-identical to V170 - none of
these fixes touches the prompt. Suite: test_v171.py, 57/0/0 with both builds
present, 54/0/4 with only this one (differential tests skip by name).

KNOWN-OPEN, stated rather than guessed at: on the recorded run FIX 5 would
not itself have fired, because after the bounce that run never reached a
passing test again. Its value is prospective - it is what makes the promise
true the next time a model does what the message tells it to do.

PREVIOUS VERSION: V61.29b        (this file: what_if_machine.py)

V61.7 through V61.29 landed after this header was last written and are
documented at their call sites, not here. Index, so the header never again
claims to be a version the code is not:

  V61.7   str_replace REPORTED FAILURE ON AN EDIT IT HAD ALREADY WRITTEN.
          The tolerant multi-line path raised NameError on `delta` while
          building its own success message, AFTER the file was on disk. The
          outer handler cannot tell "never wrote" from "wrote, then crashed
          formatting the receipt", so the model retried an edit the file
          already had, the retry missed, and the failed-edit cache learned
          the wrong lesson. `wrote` flag + a distinct message that says DO
          NOT RETRY.
  V61.8   node --check ran with text=True, so the PARENT encoded stdin with
          the locale codec. One emoji on Windows/cp1252 raised inside
          subprocess's writer thread - uncatchable from here - and node got
          a TRUNCATED file, reporting a phantom syntax error on innocent
          code. Encode to bytes explicitly. Same class fixed at the
          interpreter-probe site.
  V61.9   `except KeyboardInterrupt: pass` is correct code and was being
          warned about, so the whole warning read as noise and the REAL
          swallower next to it was ignored for six consecutive edits.
          BENIGN_SWALLOW_RE. Plus: warnings ride on a ✅ so nothing in the
          reaction chain could see them - a swallower count that never
          falls across three edits to one file now escalates. Plus two
          defects in the tolerant indent loop: a whitespace-only file line
          lending its own newline as a prefix, and max(0, rel) making
          dedent structurally impossible.
  V61.10  THE TOLERANT PATH COULD NOT DEDENT AT ALL. "Adopt the file's own
          prefix" stamps the file's corruption back over the model's
          correction whenever the leading whitespace IS the bug. Measured:
          41 corrections reverted in one 735-line replace, ✅ reported.
          Now compares leading whitespace in COLUMNS - equal means adopt,
          differs means the model is asserting an indent and its line goes
          in verbatim.
  V61.11  A PASSING --test IS NOT EVIDENCE UNTIL YOU KNOW WHAT IT RAN. The
          horror_snake suite printed 15 ticks and ALL TESTS PASSED while
          never calling update(), draw() or handle_input(); 7 of 7 mutants
          survived. test_coverage_probe re-runs the same --test under a
          call tracer and names the functions that never executed. Plus
          noop_assert_findings: `assert True, "wall collision works"` is
          not a weak test, it is an absent test wearing a tick.
  V61.11a The body of that gate lives in _coverage_message so it can be
          CALLED BY A TEST. Shipped inline the first time and it referenced
          two attributes that do not exist. The helpers had unit tests; the
          call site had none - the same defect the gate exists to catch.
  V61.12  The lesson validator now refuses to store a lesson that prescribes
          an operation this sandbox REFUSES (the horror_snake run stored
          "use file_write instead of str_replace" at confidence 0.85 -
          file_write cannot overwrite, so that lesson teaches the next run
          to walk into the rewrite spiral). Plus: an empty model response
          used to "resend the same context", a deterministic fixed point -
          five identical iterations, ~129,000 prompt tokens spent re-asking
          a question that could not answer differently. From the second
          strike the input CHANGES.
  V61.13  THE COVERAGE PROBE'S OWN EXIT CODE WAS COLLECTED AND NEVER READ.
          A --test that dies partway leaves every function below the crash
          point in the never-executed list, so V61.11's gate accused the
          model of not testing code that runs fine. Reproduced: a --test
          that raises only under SDL_VIDEODRIVER=dummy passed the model's
          own bash run with exit 0 and "ALL TESTS PASSED", while the probe
          returned 1 of 4 executed and named the other three. The probe now
          RETRIES without the headless drivers - no new risk, the model just
          ran the same command that way itself - and if both attempts die,
          the gate ABSTAINS rather than accusing. Silent to the model on
          purpose: V61.9's rule is that a warning must be actionable, and
          the model cannot fix this machine's probe.
  V61.14  THE MODEL WAS THINKING INTO A BUCKET WITH A HOLE IN IT. On the
          booby_game run it reached the SAME conclusion in iterations 8, 9,
          10 and 11 - "just set lives=0 directly instead of relying on
          collision detection" - and acted on it zero times, then made five
          consecutive edits to one test block whose 10th and 11th differ
          only in whether the shark moves onto the booby or the booby onto
          the shark. Its reasoning was GOOD: step 9 derives the gravity-
          ordering bug from first principles in 1,813 characters. It simply
          could not see any of it - `thinking` was captured to the episode
          and never put back, so every iteration re-derived from scratch.
          24,306 chars of reasoning produced that run, 0 re-entered the
          context, while the context sat at ~17K of a 256K window: 6.6%
          full. Nothing was compacted and nothing was evicted. The
          forgetting was plumbing, not pressure. Message now carries
          `thinking` and folds it into the assistant turn's content on the
          wire. FOLDED rather than sent as a `thinking` field because this
          file has never tested whether Ollama 0.32.5 accepts that field
          INBOUND, and an unverified wire field that errors kills a run
          instead of degrading it. REFEED_THINKING turns it off.
  V61.15  REASONING AS A TOOL PRECONDITION, NOT A PROMPT REQUEST. Measured on
          the snake_game run of 2026-07-31: 263,102 prompt tokens against
          14,665 completion, an 18:1 read/write ratio, final context 20,020 of
          256,000 - 92% of the window unused. Eight of eighteen turns spent
          64-140 completion tokens and five of those were "run the test again"
          and nothing else. The model is not shallow; nothing ever ASKS it
          anything. Every turn's implicit question is "what tool next", and a
          small question gets a small answer - while BUILD_PROMPT's second
          line, the first substantive thing it reads, says "Do NOT just
          describe what you would do - actually DO it by calling the tools."
          A prompt asking for more competes with that line, drifts over a long
          run, and leaves no moment where the machine can tell whether it was
          followed. A REQUIRED TOOL FIELD is a precondition: the call does not
          exist without it. bash gains `expect`, str_replace gains `intent`
          and `supersedes`, file_write gains `plan`. Each is tied to an
          observed failure, not to sounding rigorous - see REASONING_FIELDS.
          Two identical `supersedes` in a row on one file is the booby
          five-blind-edit loop made mechanically visible. Bounded at
          REASONING_MAX_BOUNCES like every other gate here, and stripped in
          ToolExecutor before tool.execute(**args) so no tool signature moves.
  V61.17  THE MUTATION GATE. Coverage asks "did the function RUN"; this asks
          "would the test NOTICE if the function were WRONG", and they are
          different questions. snake_game, 2026-08-01: coverage passed at
          20/21 executed, noop_assert_findings returned nothing, both were
          correct - and deleting the scoring, the growth, the death and the
          food respawn from Game.run() each still printed SELF-TEST OK. The
          test asserted against a TRANSCRIPTION of the loop the model had
          pasted into run_test, with its own comment saying so: "This is the
          exact same logic from Game.run() lines 228-244". Nothing that reads
          the test's TEXT can catch that; planting a bug and watching the test
          not flinch can. Ported from VERITY's _Mutator with two additions it
          does not have. (1) SKIP RANGES: VERITY assumes the verifier is a
          separate file, but here the test lives inside the artifact behind
          --test, and 108 of snake's 422 mutation points (26%) fall inside
          run_test - mutating an assertion usually makes the test fail, which
          scores as "killed" and INFLATES the rate (whole-file 25%, game-code
          only 22%). (2) NAMED SURVIVORS, ranked: ast.unparse re-renders the
          whole file so a mutant cannot be diffed, the node must say what it
          changed at visit time off the ORIGINAL tree. And a raw survivor list
          is mostly dismissible - snake's first six were `255 -> 256` in a
          colour and `2 -> 3` in a radius - so control flow sorts before
          constants and real logic before draw/render. The model now sees
          "line 243 in run(): `>` -> `<=`" first. Always restores the file in
          a finally, purges __pycache__, deterministic sampling, one shot.
  V61.17a MEASURE THE VERIFIER BEFORE MEASURING WITH IT. One baseline run
          cannot tell a passing test from a flaky one, and a flaky test scores
          mutants as killed FOR FREE. booby_game's --test passes 21 runs in 24
          untouched, and its kill rate wandered 30/35/38/40/42% across
          identical invocations - the gate was partly measuring its own noise,
          and produced one spurious None which was the baseline check working
          by accident. A non-deterministic self-test is a WORSE defect than a
          weak one: a weak test is silent about bugs, a flaky one is silent at
          random and teaches the model to re-run until green. So BASELINE_RUNS
          untouched runs come first and flakiness is reported INSTEAD of a
          kill rate, with the usual cause named (unseeded randomness reaching
          an assertion). Verified against a known-flaky and a known-solid
          artifact, six gate runs each: 6/6 FLAKY and 6/6 a stable 91%.
  V61.17b THE GATE LEFT A MUTANT ON DISK. The `finally` in run_mutation_gate
          covers exceptions; it does NOT cover the process dying - Ctrl-C, a
          supervisor timeout, an OOM kill, a closed terminal. Reproduced for
          real on 2026-08-01 while auditing the very artifact this gate had
          just improved: a 40-mutant run against a 6.7s self-test overran a
          sandbox timeout, python was killed, and snake_game.py was left as
          `ast.unparse` output - every comment stripped, every string
          requoted, one operator inverted. Silent destruction of the user's
          file by the tool measuring it, caught only because the next --test
          failed on a line that should have passed. The original is now
          written to <file>.mutbak BEFORE the first mutation, every gate run
          RECOVERS from a stray .mutbak first, and the copy is removed on the
          way out so the next run cannot mistake a legitimate edit for a
          kill. If the backup cannot be written the gate refuses to mutate.
          Also adaptive: the mutant count is sized from the MEASURED cost of
          one self-test rather than assumed. snake's test went 0.2s -> 6.7s
          the moment it started driving the real Game.run() through
          clock.tick(FPS) - correct, and 33x slower - so a fixed 40 blew the
          budget and caused the kill above. A slow self-test now buys a
          smaller sample and says so, instead of a dead run.
  V61.17c TWO DEFECTS WEAR THE SAME SURVIVOR, AND THE GATE GAVE ONE ANSWER TO
          BOTH. A bug surviving in a function the test NEVER CALLS means the
          test misses a code path. A bug surviving in a function the test DOES
          call means the path is fine and the ASSERTION is too weak. Opposite
          fixes. After the first bounce told snake_game to stop transcribing
          Game.run() and call it, the model did exactly that - coverage went
          from 20/21 to 21/21, every function executing - and the survivors
          simply moved to check_collision(), spawn() and draw_snake(), all of
          which the test now calls. Repeating "your test re-implements the
          logic" there is advice ALREADY FOLLOWED, which is the V61.9 failure:
          a warning the model cannot act on teaches it the whole channel is
          noise, and the next real warning gets ignored too. The gate now
          cross-references its survivors against the coverage probe and says
          which defect it is actually looking at. For the assertion case it
          names the shape: `assert thing.check()` cannot detect a mutation
          that makes check() return True in EVERY case, because the mutant
          satisfies it too - so add the opposite case, one input that must
          return True and one that must return False. Verified on the current
          snake_game: 11 survivors, 11 in called functions, 0 in dead ones,
          and the message says so.
  V61.18  RE-MEASURE THE FIX, AND SAY WHEN IT MADE THINGS WORSE. The gate
          measured once, so the model's rewrite was never checked - and on
          2026-08-01 that rewrite made the artifact BLINDER. Told its 12% was
          too low, the model wrapped the whole test body in
          `except SystemExit: pass`; Game.run() ends by calling sys.exit(), so
          the handler fired on the first scenario, 31 assertions were skipped,
          and the file shipped printing "passed_scenarios contains 0 items"
          then "SELF-TEST OK". Deleting the scoring, the growth and the
          collision from the game all survived. 54 iterations, 1,916,641
          tokens, and the machine could not see that its own advice had made
          things worse. Now MUTATION_MAX_FIRES rounds, with three different
          things said: REGRESSION names both numbers and the usual cause
          (wider exception handling instead of stronger assertions),
          IMPROVED says so and continues, FLAT ends the loop early because
          repeating a move that did not work is the one move guaranteed not
          to work. Bounded on evidence, not only on a count.
          Plus the swallower warning now reports what each handler COVERS.
          "2 silent exception swallower(s) at line(s) 268, 524" drew the
          reply "swallower(s) are in cleanup/teardown paths", which was HALF
          true - 268 and 524 really are teardown, one statement and zero
          assertions each - and that is why it stuck. Line 512 held 140
          statements and 31 ASSERTIONS. The warning now separates them and
          names the SystemExit trap specifically.
  V61.19  AN ASSERTION THAT NEVER RUNS CANNOT FAIL, AND NOTHING COULD SEE IT.
          The 2026-08-01 artifact shipped with 31 assertions in run_test of
          which 14 executed - the other 17, every one about score, growth,
          game_over and high_score, were skipped because the whole body sat
          inside `except SystemExit: pass` and Game.run() ends by calling
          sys.exit(). The test printed SELF-TEST OK. Neither gate saw it:
          coverage said 21/21 functions ran (true - they ran, inside the
          first scenario), noop_assert_findings said nothing (the assertions
          are well written, they just never execute), and the MUTATION RATE
          WENT UP, 12% -> 17%, because single-operator mutants are not
          feature deletions and the surviving early assertions still caught a
          few. Every existing instrument reported improvement while the test
          went blind.
          So _COVERAGE_TRACER now records executed LINES, not just called
          functions, scoped to the artifact's own file so the cost is paid
          nowhere else - measured overhead 0.4s on a 3.2s self-test. The
          probe reports asserts_total / asserts_run / asserts_never, and both
          surfaces lead with it: the first passing --test, so the model
          learns before building on the illusion, and the completion gate,
          because the trap can be introduced after that surface has fired.
          Ranked FIRST in the advice - strengthening assertions that never
          run is wasted work. Verified: 17 of 31 flagged on the real
          artifact, silent on a healthy four-assertion test.
  V61.20  THE UNCAPPED LOG IS ON BY DEFAULT. It was opt-in, and every log
          handed over for analysis since has been the TERMINAL capture
          instead - the 2026-08-01 run's own mutation-gate message was only
          recoverable because the model happened to quote it back. A run that
          cannot be reconstructed is a run nothing can be learned from, and
          every fix in this changelog came from reading one.
          It does NOT go in the working directory. The model is told "Files
          here right now: ..." and has list_dir, file_read and grep_search
          aimed there; a log sitting in it would be listed, read - these are
          1.7 to 7.4 MB, one file_read would end the run, which is precisely
          the V30.5 self-read that cost a quarter of a context - grepped, and
          handed to the mutation gate as another artifact. It goes beside the
          runtime, in whatif_logs/, ONE FILE PER RUN, stamped and pruned to
          DEBUG_LOG_KEEP so it cannot grow without bound and so "send me the
          log for that run" is unambiguous. is_machine_self() covers the
          directory too, for the case where the machine is run FROM the
          workspace and beside-the-runtime IS the mission directory.
          Started before CLI construction so a run that dies in initialize()
          still leaves a log. The path prints unconditionally, not through
          debug_print - where the log is should never be a question. --log
          overrides the path, --no-log disables it, and any failure to create
          or write the directory silently disables logging rather than
          stopping a build.
  V61.21  THE SURVIVOR LIST WAS USED AS A TO-DO LIST. super_mario run of
          2026-08-01: 128 iterations, 10,170,633 tokens, outcome FAILURE.
          The gate fired at 5%, the model replied "I'll systematically fix
          each planted bug by making my assertions catch operator-level
          changes", and wrote SIXTEEN assertions that name a planted mutation
          by line and operator -
            assert player.w == 32, "... - line 794 mutation (* -> /)"
          The rate went 5% -> 18%, the test got no better, and one of those
          very assertions is what the delivered artifact finally died on.
          Three faults, all mine. (1) The seed was FIXED at 1234, so round 2
          replanted the same 40 bugs round 1 had just been shown - targeting
          them was a winning move. It now re-seeds per round, so an assertion
          aimed at this round's sample buys nothing next round and gaming
          costs more than fixing. (2) The message handed over line numbers
          with no statement that they are a SAMPLE. Every path through
          _mutation_advice now ends with that caveat - there is no way to
          emit the list without it. (3) Nothing detected the gaming.
          _gaming_findings does, off the AST, and it is reported FIRST,
          above every other finding.
          Also: when the coverage probe crashes, three features went silent
          at once - the survivor split, the assertion-execution finding, and
          the advice, which fell back to one generic sentence 84 times in
          that run while the probe held real data (53 of 81 assertions never
          executed). The probe failure is now REPORTED rather than papered
          over: a test whose result depends on how it is invoked is worth
          knowing about on its own.
  V61.22  A BOUNCE MUST NOT COST MORE THAN THE THING IT ASKS FOR. The
          spongebob run of 2026-08-01 opened: file_write without `plan` ->
          CALL REJECTED. file_write without `plan` -> CALL REJECTED.
          file_write without `plan` -> accepted, because REASONING_MAX_BOUNCES
          had run out. Three complete 21KB files, 6,634 and 6,544 completion
          tokens burned on the two that were discarded, ~3 minutes for zero
          progress, and the field was never supplied once.
          The model was not being stubborn. My own description opened with
          "REQUIRED, and SECONDARY: write `content` in full FIRST - no plan is
          worth losing a line of it" - written to stop V61.15a's truncated
          content, and reading exactly like permission to skip the plan.
          The shape was worse than the wording. `bash.expect` and
          `str_replace.intent` cost a sentence to re-emit, which is why 18 of
          19 were filled on the earlier run; `file_write.plan` costs the whole
          file, and the model did not even re-issue - writes 1, 2 and 3 were
          different files rewritten from scratch, which is how a NameError on
          an undefined `Lanes` became a NameError on an undefined `FPS`.
          So REASONING_ASK_AFTER: for those tools the field stays in the
          schema and is still asked for, but a missing one never blocks the
          call - the work is accepted and the question is appended to the
          RESULT, answered next turn for the price of a sentence. And it is
          no longer advertised as required, because listing a field as
          required and then admitting it after two bounces teaches the model
          that "required" is negotiable - in the same schema that carries
          `content`, where it is not.
  V61.23  THE VERIFICATION CHAIN STARTED ONE STEP TOO LATE. The spongebob
          file that was finally accepted raises NameError on an undefined
          FPS at its first frame, has Background.update() as `pass`, and
          contains NO --test at all - and every gate in this file was silent,
          because coverage, assertion tracing and the mutation gate all fire
          on a PASSING self-test and there was no self-test to run. Three
          checks now run on the WRITE itself, where the file exists and
          nothing has been verified yet: names used but never bound, function
          bodies that are only `pass`, and a __main__ with no --test branch.
          Both code checks are conservative because a false positive lands on
          the first write of every run. Undefined skips entirely on
          `from x import *`. Stubs suppress the two legitimate shapes: a
          BASE-CLASS CONTRACT, verified against super_mario.py where the
          naive check flagged Entity.draw and two _FakeSound.play and all
          three were correct code, and deliberate test doubles. Name matching
          alone cannot do it - Background.update() being `pass` while
          Player.update() is real IS a defect, and only the inheritance edge
          separates the cases. Verified: every spongebob defect caught, zero
          findings on snake_game.py and super_mario.py.
          On size, which is what prompted this: a floor would buy padding.
          Measured, mario's first write was 66,960 characters in ONE call at
          20,237 completion tokens, so spongebob's 21KB was a choice and not
          a ceiling. The note states that budget - but only when something is
          missing, and it says "do not pad" out loud. What makes a file worth
          100KB is implemented features, so the findings lead and the size
          follows.
  V61.24  TWO BUGS OF MINE, BOTH VISIBLE IN THE FIRST FOUR STEPS OF THE
          spongebob run of 2026-08-01.
          (1) THE MACHINE CONTRADICTED ITS OWN DOCUMENTATION. `supersedes`
          says verbatim "If this is the first edit to this region, write
          'first edit'." That is 10 characters against REASONING_MIN_CHARS =
          24, so the model did exactly as instructed and the call was
          rejected for the field being "too short". REASONING_SENTINELS
          whitelists the prescribed answer per (tool, field). Kept in a
          separate table because anything added to REASONING_FIELDS is copied
          straight into the tool schema sent to Ollama - a stray key there is
          a wire-format change, not a config change. Verified the sentinel is
          not a loophole: 'ok' and '' still reject, and 'first edit' in
          bash.expect still rejects.
          (2) A CALL THAT NEVER RAN WAS SCORED AS A SUCCESS. "CALL REJECTED"
          and "CALL INCOMPLETE" begin with no recognised failure prefix, so
          _detect_tool_success returned True - the exact V21 "BLOCKED:"
          defect, reintroduced by me two versions after writing the comment
          about it. Consequences compounded: the rejected call went into
          _ok_call_counts, so the model's identical retry at step 4 came back
          "DUPLICATE CALL SUPPRESSED: this call already succeeded earlier in
          this run and nothing has changed since" - locked out of a one-line
          fix by a rejection that should never have fired, and told its retry
          duplicated a success that never happened. It also wrote
          "str_replace: OK (patched spongebob_run.py)" into the trajectory and
          therefore into the reflection evidence, for a call that changed
          nothing.
  V61.25  THE MODEL LEARNED MY DELIMITER AND STARTED WRITING IT ITSELF.
          V61.14 folded thinking into content as <reasoning>...</reasoning>
          and I noted at the time that imitation was a risk. It happened. On
          the spongebob_shooter run of 2026-08-01, 26 of 143 thinking blocks
          contain a reasoning tag the model wrote, and assistant turns came
          back with the same paragraph twice inside two opens and THREE
          closes: the model opened the tag in `content`, so the machine's own
          fold nested inside it and the markup could not balance. The same
          reasoning was then paid for twice in a context that reached 162,568
          tokens over 11.35M.
          _fold_reasoning now unwraps whatever tags the model emitted, keeping
          its words, and folds only when the thinking ADDS something -
          measured as the fraction of the thinking's distinct words already
          present in content. Chosen over SequenceMatcher, which scored the
          real duplicate at 0.52 and a harmless one-line stub at 0.51, with no
          threshold between them; on word overlap the same pairs are 63% and
          50%, against 24% for a turn that genuinely added an explanation and
          6% for wholly new reasoning. Gated on length, because dedup only
          pays on a large block while a short one is cheap to keep and is the
          likeliest false match.
          Also: "Messages: showing last 200 of 292 (92 earlier hidden)" reads
          like the model lost 92 messages. It never did - that is a cap on the
          DEBUG ECHO and every message was in the request. A log line that
          looks like data loss will be read as data loss, so it now says which
          it is.
  V61.26  THE MACHINE COULD NOT PRODUCE ITS OWN MEASUREMENTS ON REQUEST.
          The spongebob_shooter summary of 2026-08-01 reported "Round 1: 8/40
          caught (20%), Round 2: 11/40 (28%), Round 3: 18/40 (45%)". Across
          all 143 thinking blocks the model reasons about 11/40 (28%) seven
          times from turn 76 and 18/40 (45%) once at turn 134; "20%" appears
          exactly once, in turn 142 - the turn that WROTE the summary - and
          the only "8/40" match is the tail of "18/40". Whether a third
          firing happened is NOT answerable from the episode, because the
          gate's numbers lived in a chat message and a debug line and nowhere
          else. That is the defect: a measurement the machine cannot produce
          on request is a measurement the model can invent, and a reader
          checking the claim has nothing to check it against.
          Every firing is now recorded - round, killed, tested, rate,
          survivor count, skipped assertions, file - and persisted to the
          episode as mutation_history. Absent when the gate never fired, so
          older episodes load unchanged.
  V61.27  SHIPPED UNVERIFIED, RECORDED AS SUCCESS. mario_game, 2026-08-03,
          63 iterations, 2,765,398 tokens: last passing --test at step 41,
          then EIGHT successful edits, a --test that FAILED at step 51 with
          AttributeError on pygame.array, four more edits, and a stop with no
          further run. Episode: outcome success, confidence 0.95, grounded
          True. The delivered file fails its own --test 0 of 6 times here, in
          every SDL configuration, on the line the model was last editing.
          Three holes, all mine, all the same shape - a check that knew and
          said nothing.
          (1) The V30.2 gate computes exactly this ("a successful .py edit
          postdates the last successful bash"), bounces ONCE, then accepts
          the next completion REGARDLESS. Loop-proof by design and therefore
          mute about a model that never went back. The bounce stays one-shot;
          the RECORD now does not. Same evidence, same mechanical test,
          applied to the outcome where it cannot be argued with: edited after
          the last verification is `partial`, never `success`.
          (2) run_mutation_gate returned None when its own baseline run
          failed, and the caller did nothing - the entire mutation check
          vanished on one debug line. V61.13 taught precisely this for the
          coverage probe, abstain but SAY SO, and I did not carry it across.
          It now returns an `unrunnable` result and the model is told its
          build cannot be measured and why.
          (3) _notify wrote only to the live dashboard. Those lines ARE the
          record of what the machine decided, and auditing this run meant
          inferring gate behaviour from its ABSENCE, because "COMPLETION
          GATE: bounced" appears nowhere in a 10 MB log. They go to the log
          now.
  V61.28  DELIVERABLE SPLIT FINALLY ESCALATES. It has warned since V45 and
          never had a consequence - the last item still open from the
          original audit of this file. super_mario, 2026-08-03: file_write
          super_mario.py, an overwrite refusal, then super_mario_bros.py
          created at step 17, its --test failed at step 18, and the model
          went back to super_mario.py and never touched the second file
          again. Both ship broken; both fail their own --test here.
          That run was already caught, by "nothing was ever verified" - no
          bash succeeded at all. The shape that is NOT caught is one green
          file and one abandoned: outcome success, last_py_edit_path pointing
          at the good one, and nothing anywhere asking about the other.
          last_py_edit_path is a single slot, so a run producing two files
          only ever guards one; built_deliverables is a set.
          Deliberately narrow: only a file the model RAN and never got green
          is counted. "Written and never run at all" is ambiguous - the mario
          run wrote coverage_check.py purely to analyse its own source, and
          flagging that would downgrade an honest success. "Ran it, it
          failed, walked away" is not ambiguous. Files never run at all stay
          covered by the two checks above.
          V61.27 confirmed working on this same run: "COMPLETION GATE:
          bounced - super_mario.py was edited but never run since" is in the
          log, where before it went only to a dashboard that scrolls away.
  V61.29  THE COMMONEST WAY A GAME SELF-TEST DIES IS THAT IT CANNOT PRESS A
          KEY. Two shapes, both from the super_mario run of 2026-08-03, both
          invisible to every gate here because they surface as an ordinary
          AssertionError the model then spends iterations "fixing" in the
          wrong place - four of them on "Space press should transition to
          playing (got menu)".
            (A) post-then-get_pressed. The test posts KEYDOWN to the event
                QUEUE and calls handle_input(), which reads
                pygame.key.get_pressed() - hardware state. The input never
                arrives and the assertion cannot pass, whatever the game does.
            (B) the test calls pygame.key.get_pressed() ITSELF and branches on
                it. Headless, nothing is pressed, so the guard is always False,
                the action never runs, and the test fails a correct game.
          The check is on WHICH function the test calls, not on the presence
          of post(): the earlier snake_game posts the same events and then
          drives Game.run(), which reads pygame.event.get(). That pairing is
          CORRECT and scores zero findings - it is the control that stopped
          this from being a blunt "no post() in tests" rule.
          Prevention as well as detection. The GUI protocol in BUILD_PROMPT is
          the one section the model demonstrably follows - it writes a --test
          mode every run - so the rule that key state must be an ARGUMENT the
          test can construct goes there, phrased as the spongebob prompt
          phrased it, since that prompt produced a step(dt, keys) the test
          could drive and the runs without it did not.
  V61.29a THE PROMPT EDIT ABOVE CRASHED THE MACHINE BEFORE IT STARTED. The
          example key dict was written {"left": False, "up": True} with SINGLE
          braces; BUILD_PROMPT goes through .format(), which read that as a
          replacement field, and every run died with KeyError: '"left"' eight
          frames deep in create_agent - no banner, no log, nothing to read.
          Escaped now. But BUILD_PROMPT is 12KB of hand-edited English with
          eight real placeholders in it and this WILL happen again, so the
          call is wrapped: name the offending placeholder, say that braces in
          prose must be doubled, and start anyway with the text left literal.
          A malformed sentence in the manual is a far smaller problem than a
          machine that will not run. Verified by reintroducing the exact bug -
          it now returns the full prompt with a diagnosis instead of raising.
  V61.29b THE MAIN EDIT PATH NEVER RAN THE COMPLETENESS CHECKS AT ALL.
          V61.23 and V61.29 were attached by matching the exact text of the
          swallow_warning lines. Three matched. The fourth - the exact-match
          branch of str_replace, where nearly every edit in every run lands -
          ends with "))" instead of ")" and matched neither pattern, so from
          V61.23 onward it has silently carried no undefined-name check, no
          stub check, no missing---test check and no input check.
          mario_game, 2026-08-03, is the proof: the delivered file contains
          SIX untestable-input findings and the run logged zero, while
          "PLAYER_ACCELERATION used but never defined" fired exactly once -
          on the initial file_write, through a path that did match. Every
          edit for the rest of that run went unchecked.
          The cause is mine and it is not the typo. My patch asserted it had
          hit 3 sites and I accepted 3 without ever asking how many sites
          existed; the assertion confirmed my guess instead of testing it.
          There are four, all four are wired, and the check is now on the
          COUNT OF UNWIRED SITES rather than on a number I chose.
  V61.15a A MISSING REQUIRED ARGUMENT CAME BACK AS A PYTHON TRACEBACK.
          First live run of V61.15 returned "Error: FileWriteTool.execute()
          missing 1 required positional argument: 'content'". The gap is
          PRE-EXISTING and reproduces on the untouched file: ToolExecutor has
          filtered EXTRA arguments since V23 and never once checked for
          MISSING ones, so an omission fell through to tool.execute(**args)
          and surfaced as a TypeError. That string does not say the write did
          not happen, does not name what to send, and reads like a defect in
          the machine rather than something the model can fix.
          V61.15 did not create it but made it fire, and that part IS the
          fault of this feature: `plan` asked for a full design document in
          the SAME JSON object as a 16KB file - two large outputs in one call,
          on the single most output-heavy call of the run - and the model
          dropped one of them. Two fixes. The gap is closed for every tool
          with a message naming the missing argument, its schema description,
          and the rule that CONTENT is the part that must never be sacrificed.
          And `plan` is now explicitly SECONDARY and brief: content first, in
          full, then a few lines - not an essay competing with the file.
  V61.16  THE LOG WAS THE THING BEING TRUNCATED. debug_print serialized
          dict/list payloads through [:5000] and everything else through
          [:500]. BUILD_PROMPT is 11,585 chars (11,867 as indented JSON), so
          5,000 showed 42% OF THE SYSTEM PROMPT ALONE and every message after
          it was invisible in every "Sending to Ollama" block - which is why
          no <reasoning> block was ever visible in the snake_game log and the
          only proof V61.14 reached the model was a stray "</reasoning>" the
          model leaked into its own replies twice. Not simply raised, because
          the echo re-serializes the WHOLE history every iteration: O(n^2),
          ~1.3 MB uncapped for that run against 90 KB at the old cap. So two
          sinks - DEBUG_MAX_CHARS for the screen (0 = unlimited) and
          DEBUG_LOG_FILE for an UNCAPPED mirror that writes even when VERBOSE
          is off. Storage caps raised too: thinking was stored at 8,000
          against a largest observed block of 7,310 (690 chars of headroom,
          and V61.14 exists to make reasoning longer), and trajectory args at
          32,000 - recovering snake's first write from the trajectory is how
          the 2.8%-game / 61%-test split was measured, and a genuinely large
          first write would have been cut, making that analysis impossible.
  V61.14a THE FIRST CUT OF V61.14 CAPPED EACH TURN AT 2000 CHARS, a number
          picked from nothing, and it was wrong twice against the very run
          it was built from. SIZE: that run's per-turn reasoning peaks at
          7,310 chars; a 2000 cap truncates 3 of 17 turns and destroys 9,037
          chars - 37% of the reasoning. DIRECTION: cutting the HEAD keeps
          the throat-clearing and drops the conclusion. Measured on every
          block over 600 chars there, the last operative decision phrase
          sits at 70-98% through the text; "The cleanest fix is to directly
          set lives=0" is the LAST line of iteration 11. A head-cut at 2000
          removes exactly the sentence that would have stopped the loop.
          Now: no per-turn cap. A budget sized as a FRACTION of num_ctx (so
          it scales when the window does) drops WHOLE blocks from the OLDEST
          turns, never cuts one in half, and always keeps the newest block
          even when it alone exceeds the budget - without that last rule a
          single large block evicted every turn including itself, which the
          V61.14a test caught and reading the code did not.

NEW IN V61.6 - THE TWO str_replace DEFECTS FOUND BY AUDIT

He reported the symptom: "sometimes it cant find the exact match and never
str_replaces it and moves on and repeats later." Audited by driving the REAL
StrReplaceTool over real files. The matcher itself is sound - exact match,
CRLF file with LF old_str and the reverse, literal backslash-n, single-line
indent tolerance, multi-line recovery from trailing spaces / tabs / uniform
indent shift, and ambiguity correctly refused. Two defects, one of them the
symptom he described and one worse that he had not seen.

(1) A FAILED EDIT THAT CANNOT CHANGE ITS OWN OUTCOME WAS RE-RUN FOREVER.
    The duplicate guard cached SUCCESSES only, so a repeated call that WORKED
    was suppressed while a repeated "String not found" sailed through -
    backwards. Measured: four identical failing str_replace calls all ran,
    while two identical successful bash calls were suppressed on the second.
    A repeated success is wasted work; a repeated miss is GUARANTEED to miss
    again, because the file has not been written since.
    The V30.7 escalating nudge could not see it either: it counts CONSECUTIVE
    misses and any successful step resets the streak, so his exact pattern -
    miss, other work, miss again later - never escalated.
    Now the two tools whose failure is a pure function of file state,
    str_replace and file_write, have their failures remembered, and a repeat
    is answered with what changed (nothing) and what to do instead. bash is
    EXCLUDED on purpose: a failing command can legitimately pass after an edit
    somewhere else. The V41.3 basename purge clears the failed-edit cache by
    the same rule it clears the success cache - once the file is written, the
    guarantee that justified suppressing the edit is gone.

(2) THE TOLERANT MULTI-LINE PATH SILENTLY RE-INDENTED ACROSS LEVELS.
    It matches by per-line stripped equality, so the region can span two indent
    levels - but it took ONE delta from the FIRST line and applied it to every
    replacement line. Proven:

        file                old_str      result (before)
        for i in r:         acc += i     for i in r:
            acc += i        return acc       acc += i * 2
        return acc                           return acc   <- MOVED IN

    `return acc` went from 4 spaces to 8 and ended up inside the loop, so the
    function returned on the first pass. It PARSES, so the syntax gate could
    not see it. A silent behaviour change is the worst thing an edit tool can
    do, and the success message even claimed "new_str was written as given",
    which was never true.
    A delta in CHARACTERS was wrong a second way: 8 spaces in the file minus
    one tab in old_str is a delta of 7, so 7 spaces were bolted in front of a
    line that still carried its own tab. My first patch kept the delta and my
    own suite caught it - the fix is not a better delta.
    No delta now. Each replacement line ADOPTS THE FILE'S OWN PREFIX for the
    line it replaces, plus whatever extra indent the model asked for RELATIVE
    to its own old_str, measured in columns with tabs expanded. Lines past the
    matched region carry the last prefix forward. A tab-indented file keeps its
    tabs; a model deliberately nesting one level deeper still gets it.

New suite test_v613.py, 28/28, path-independent and differential: it loads the
prior build alongside and asserts the prior build exhibits BOTH defects and
this one does not, then re-proves every tolerant case that must keep working
and every call the guard must still let through.

NEW IN V61.5 - DID THE THING YOU ARE CITING ACTUALLY FINISH?

From the run of 2026-07-29, seed 2120226666. The final report said "Graphics
verified - Screenshots captured for all states" and listed four PNGs as
complete evidence. The capture script was written to take fifteen captures and
died on the fifth:

    NameError: name 'collect_game' is not defined

Two more variable-name bugs sat behind that one - a `from spongebob_runner
import random` placed LATER in the same function, which makes `random` local to
the whole of main(), and a capture that positioned its obstacle against the
PREVIOUS test's player object. With all three fixed the same script produces
19 of 19 captures, every one of them 208-1,147 colours and under 0.2% black.
The game was never the problem. Two typos in the capture harness hid two
thirds of the evidence, and the summary then presented the surviving four as
if they were the plan.

The machine already KNEW. That bash call returned a traceback and was recorded
as a failure - one of 31 that run. Nothing connected "the last run of this
script failed" to "the summary cites this script as proof".

- NEW _scripts_named_in(): basenames of runnable files (.py .sh .ps1 .bat .cmd
  .js .mjs .ts .rb .pl .lua) mentioned in a piece of text. Ignores data files,
  so a report listing PNGs is not mistaken for one citing code.
- The loop now records, for every bash call, which scripts that command ran and
  how the run ended. LAST run wins, so a script that failed and was then fixed
  is not held against the summary.
- NEW ONE-SHOT GATE at completion, in the same shape as the V30.2 gate above it
  - answered or ignored, the next completion is accepted, so it cannot loop.
  It reads the final answer, finds the runnable files it cites, and if this
  run's LAST invocation of one of them failed, it says so with the step number
  and offers the only two honest ways out: fix it and run it until it exits 0,
  or state how far it got and which claims are therefore unverified.
- DETERMINISTIC. No model judges it. It compares basenames in the final answer
  against this run's own bash outcomes and nothing else, so it can neither
  hallucinate a problem nor be talked out of one.
- Also removed: the "output_gate" key in EXPERIMENTAL controlled NOTHING - the
  watcher it was meant to gate lives in a build that was never taken, so the
  switch was decoration. Gone rather than left looking like a feature.

NEW IN V61.4 - PUTTING THE UNPROVEN THINGS BEHIND A SWITCH:

Built on the file you sent back. Nothing removed - 0 lines deleted.

The separation that should have been there from the start: changes proven by
EXECUTING them against artifacts you uploaded stay ON; changes reasoned from
documentation that never ran against your model are OFF, in one EXPERIMENTAL
dict near the top of the file. Turn one on, run your normal prompt, compare.

OFF: ollama_keep_alive, ollama_num_keep (never exercised against
ornith-vision on your machine), output_gate (designed before I had read your
final report). With all three off, the JSON this machine posts to Ollama is
byte-identical to the build your good spongebob run used - asserted, not
claimed.

ON, each reproduced here against your own files: V60.2 marker scoping (your
real 409,058-char read of source_code.md was recorded as a FAILURE and fired
two phantom gates); V60.3 _safe_kill (Process.kill() after exit raises
ProcessLookupError, confirmed by running it); the timeout message (your log
shows an 1,820s gap while the message said 900s and the real limit is 1800s);
the assertion-relaxation warning (your real step-6 edit turned
`assert score > 1234` into `>= 1234` on a score 3,600 measured frames never
move).

ALSO FIXED, and this is the one most likely to have hurt a build: V61.2 kept
the detector armed until a test PASSES, but the window only closes on a
CANONICAL pass phrase - so a build whose tests print anything else keeps it
open all run, and every later assertion edit appended the full warning to the
tool result. Twenty of those in a context is a model being talked over while
it works. It now warns ONCE per open window and logs the rest with the reason
they were not injected. A new failing test re-arms it.

TIMELINE, for the record: WHAT-IF_MACHINE_V61.py is byte-identical to the
V60.3 build, and your good spongebob run wrote its screenshots after it. That
run used V60.2 and V60.3. They are not what black-framed anything.

NEW IN V61.2 - HIS THREE QUESTIONS:

(A) "shouldn't the prompt cache be 100 percent not 25 percent?" num_keep is
    not "how much is cached" - prefix caching already covers 100% of whatever
    prefix is unchanged, uncapped. num_keep is how many LEADING tokens survive
    when the window OVERFLOWS: the runtime keeps the first num_keep, discards
    a chunk after them, keeps the recent tail. At 100% there is nothing left
    to discard and no room for new tokens, so the shift cannot happen at all.
    It has to be a slice. But he was right that the slice was too narrow for
    the wrong reason: it covered only the system prompt, so a long run could
    survive a shift still knowing HOW to work while having forgotten WHAT it
    was asked to build. num_keep now covers system prompt + TASK, re-synced
    the moment the task arrives. Measured: BUILD_PROMPT is 11,585 chars, so
    with his 364-char mission that pins 4,111 tokens (1.6% of 256K) and with
    the 27,131-char STUDIO prompt 13,033 (5.1%). NUM_KEEP_MAX raised
    16384 -> 32768 so a large mission is never clipped. The 25% ceiling never
    binds at these sizes; it exists so a pathological prompt on a small window
    cannot pin the window shut.

(B) "why would it be silent one step later for the same edit, silent is bad
    for logs" - correct, and it was the same defect class as everything else
    in this lineage: a check that reports nothing is indistinguishable from a
    check that found nothing. Two changes. The detector now RUNS on every
    str_replace touching assertions, unconditionally - detection is never
    gated. Arming decides only WHO HEARS IT: inside the red window the warning
    is appended to the tool result where the model reads it; outside, it still
    goes to the operator log as "TEST WEAKENED (not warned - no test failure
    open)", naming the change and the file, so the log can never be misread as
    "checked and clean". And the red window is now the V45.11 shape, which had
    never reached this lineage: it opens on a bash result that is a recognised
    test FAILURE and stays open until one actually PASSES, instead of closing
    the moment any successful step goes by. The V45.8 adjacent-step trigger is
    kept as the first disjunct, so nothing that warned before stops warning.

(C) OLLAMA_NUM_PARALLEL=2 - DELIBERATELY NOT RECOMMENDED, and I was wrong to
    float it. Per Ollama's own FAQ, parallel request processing INCREASES the
    context allocation by the number of parallel requests: required memory
    scales by NUM_PARALLEL * context length, so a 2K context with 4 parallel
    requests becomes 8K. At num_ctx=256000 that means asking for 512,000
    tokens of KV cache. On this box that is an OOM or a spill to system RAM,
    and a spilled KV cache is far slower than the cache-miss it was meant to
    avoid. It is a server-side environment variable in any case - no code here
    can set it. Worth checking instead: `ollama show <model>` reports the
    model's real context length, and the server log line runner.num_ctx=...
    shows what was actually allocated. If the model's true window is smaller
    than 256000, Ollama silently drops the OLDEST tokens when the prompt
    exceeds it - which is exactly the "it stops remembering my build prompt"
    symptom, and exactly what num_keep now protects against.

NEW IN V61.1 - KEEPING THE PROMPT HOT, AND CATCHING THE OTHER WEAKENING:

(1) OLLAMA PROMPT CACHE. Ollama reuses the KV cache for a prompt prefix when
    the next request starts with the SAME BYTES, and this machine already
    qualifies: self.system_prompt is assigned once and never mutated, injected
    lessons are appended as a Message rather than folded into the system
    prompt, and self.messages is append-only - so api_messages is a growing
    list behind a byte-identical prefix. Two settings were missing:
      - keep_alive. Ollama unloads the model after 5 MINUTES idle by default
        and the cache goes with it, which is ordinary think-time at the
        prompt. Now sent TOP-LEVEL on /api/chat (it is not an option),
        OllamaClient.KEEP_ALIVE = "30m". Use "-1" to pin forever, "0" to
        unload immediately, or None to send nothing. OLLAMA_KEEP_ALIVE does
        the same server-wide.
      - num_keep. The number of leading tokens that survive a context shift.
        Without it the OLDEST tokens go first, and the oldest tokens are the
        build prompt. The audit run of 2026-07-29 reached 96% of 256K, which
        is exactly where that bites. Agent.__init__ now calls
        client.sync_prompt_cache(system_prompt), sizing it from the REAL
        prompt at chars/3 + 128 - deliberately an over-count, since over-
        counting only pins a little of the first user turn while under-
        counting would drop the tail of the build prompt off the front.
        Clamped to 16384 and to 25% of num_ctx.
    NOTE, not a code change: the builder and the judge share one Ollama slot,
    so a judge call between iterations overwrites the slot's cache and the
    next build call re-reads its prefix. That is bounded to task boundaries.
    OLLAMA_NUM_PARALLEL >= 2 gives them a slot each if it ever matters.
    To see whether any of this is working, read prompt_eval_duration in the
    /api/chat response: fast means the cache was warm, slow means it recomputed.

(2) THE TIMEOUT MESSAGE LIED. The client's limit was 1800s while the message
    said "(900s)". His 2026-07-29 log shows a 1820s gap between "Calling
    Ollama: iteration 11" and "Episode saved" - the real 1800s timeout - and
    the number in the message matched nothing, so the log could not be read.
    Both now come from OllamaClient.REQUEST_TIMEOUT_S.

(3) test_edit_warning LEARNS RELAXATION. The V45.8 detector watches for a
    DROPPED CALL TARGET. The spongebob run (seed 894106943) used the other
    shape and walked straight through: `game.hud.update(1/60)` became a
    60-iteration loop and `assert score > 1234` became `assert score >= 1234`.
    No call was dropped - update() is called SIXTY times now, so every
    count-based and call-based check reads it as MORE testing. It is not.
    HUD.update does `score += int(dt * self.speed)` = int(0.1417) = 0, so the
    score is frozen; measured, 3,600 real frames move it zero points. Changing
    > to >= made a dead scoreboard go green, and the episode then recorded
    "patched score increment logic" for a patch that never touched scoring.
    Now detected: comparison operators ranked by STRENGTH (== strongest, then
    > <, then >= <= in, then != is-not not-in) with any drop on a MATCHED pair
    of assertions flagged; assertions deleted; thresholds moved in the
    permissive direction; an assertion that became a tautology; assertions
    newly wrapped in try:. Assertions are paired by similarity so the
    comparison is the SAME claim before and after, not two unrelated lines.
    Warning only, never a block - same contract as the V28.1 swallow warning.
    The V45.8 call-drop text is UNCHANGED and still emitted byte-for-byte when
    it is the only signal, so anything downstream matching on its wording
    keeps working; the relaxation block is additive.
    difflib was imported inside two functions only and is now imported at
    module scope, since the detector needs it there.

(The V61.1 KNOWN-OPEN about adjacent-step-only arming is CLOSED by (B) above.)

New permanent suite test_v611.py, 38/38, path-independent: it replays the REAL
step-6 arguments from his episode through the real test_edit_warning (prior
build silent, this build warns), re-proves the frozen-score bug by arithmetic,
covers six other relaxation shapes AND seven edits that must stay silent,
asserts the call-drop message is byte-identical to the prior build, and
captures the actual HTTP payload to prove keep_alive is top-level while
num_keep is inside options.

NEW IN V60.3 - KILLING A PROCESS THAT IS ALREADY DEAD:
- Found by the machine auditing its own source (V60.2 run, seed 915816533):
  it was the ONE real bug in a 12-finding audit, and it is real. asyncio's
  Process.kill() raises ProcessLookupError once the process has exited -
  confirmed here by execution, not by reading the docs.
- Both call sites are inside `except asyncio.TimeoutError:` handlers, which
  is precisely when the process is most likely to have just died: a program
  that finishes in the same instant the timeout fires, or on Windows one the
  taskkill tree-kill already reaped before the fallback line runs.
- Worse than the audit reported: an exception raised INSIDE an except block
  is not caught by that try's SIBLING handlers. At the run_verification site
  the neighbouring `except Exception as e: return "⚠️ Verification error"`
  cannot see it, so a timed-out verification raised out of the function
  instead of returning "⚠️ Verification timed out (15s)".
- New BashTool._safe_kill, used by both branches of _kill_tree. Two guards,
  because the returncode check ALONE is a race - returncode can still read
  None while the OS has already reaped the process: skip the kill when the
  exit is already known, AND swallow ProcessLookupError, which means the only
  thing the call wanted has already happened. Nothing else is swallowed - a
  PermissionError or a broken transport still propagates, because that is a
  fact about this machine's own environment and must not be laundered away.
- Same-class sweep: those two were the ONLY live .kill() / .terminate() call
  sites in the file. The class is confined there because V25 had already
  routed every timeout path through the one shared _kill_tree helper.
- OBSERVED, NOT FIXED (different class, so not folded into this pass): if
  `asyncio.wait_for(tk.wait(), timeout=5)` times out, the taskkill process
  itself is left behind. That is a leak, not an exception, and it needs its
  own decision.
- Suite extended to test_marker_v603.py, 34/34: it drives the REAL _kill_tree
  against a process that has genuinely exited and awaited, proves V60.2
  raises ProcessLookupError on that input and V60.3 does not, and proves a
  LIVE process is still actually killed (returncode not None afterwards).

NEW IN V60.2 - MARKER CONTAMINATION:
- A tool result is not always the machine talking. file_read returns a whole
  file, str_replace echoes up to 1,000,000 chars of file content when its
  old_str misses, and bash can `type` anything. Five guards recognised this
  machine's own control strings by bare substring search over that payload,
  so a file that merely QUOTED them impersonated the gate that emits them.
  Live sighting: a DELIBERATE file_read of a copy of this machine's source
  (6,959 lines, saved as source _code.md) fired TRUNCATED WRITE and GATE
  STALLED on iteration 1 - before a single write had run - and the read was
  recorded as a FAILURE whose stored error evidence was the last line of the
  file, 'asyncio.run(main())'.
- The five sites, all one defect class:
  (1) _detect_tool_success's "--test FLAG IS NOT WIRED" test sat ABOVE the
      `tool_name == "bash"` branch and therefore failed EVERY tool. Now
      requires bash AND a result that OPENS with "LAUNCHED OK", which is the
      only shape that message ever has.
  (2)(3)(4) the loop's TRUNCATED WRITE / SYNTAX ERROR / GATE STALLED
      notifiers - operator-facing only, but they told the operator the
      opposite of what happened.
  (5) the HINT nudge, and this was the one that reached the MODEL: it told
      the model its correct, instructed action had failed and not to repeat
      the command.
- Fixed with three locks, not one: the marker TEXT now lives in one place
  (MARK_TRUNCATED_WRITE / MARK_SYNTAX_ERROR / MARK_GATE_STALLED / the
  HINT_LINE_RE) so emitter and consumer cannot drift; the constants keep the
  LEADING NEWLINES the emitter appends, which a quoted copy renders as the
  two-character escape "\\"+"n" and a numbered dump cannot produce at all;
  and Agent._machine_gate_signals adds tool scope - a write gate cannot come
  out of a file_read, and a HINT must ride on a FAILED result. Every gate
  message is byte-identical to V60.1; only who is allowed to raise it changed.
- Same-class sweep in the same pass: _tool_note's "SYNTAX ERROR" flag was
  already tool-scoped and success-path-only, but it was the last unanchored
  copy of the identical predicate, so it got the identical anchor.
- KNOWN-OPEN, deliberately not guessed at: _is_test_pass / _is_test_fail are
  bash-gated and exit-code-gated, but a canonical pass phrase is something the
  MODEL prints, not something this machine emits, so no anchor exists - a
  `type results.txt` containing "ALL TESTS PASSED" at exit 0 can still surface
  the self-awareness line. Distinguishing "ran something" from "displayed
  something" is a command-level design call, not a mechanical fix, and a wrong
  guess would silence the real surface.
- New permanent suite test_marker_v602.py, 30/30, which loads V60.1 and V60.2
  side by side: it asserts every gate message is byte-identical across the two
  builds, replays the REAL 409,058-char read of the REAL source _code.md
  through the REAL FileReadTool + _detect_tool_success + _tool_note, and
  re-proves each real gate still fires.

NEW IN V45.9:
- /seed <n> | /seed random | bare /seed. The seed was settable only at
  launch, so changing the reproducibility lever meant restarting the machine
  and losing the session. A seed lives in THREE places and this command moves
  all three together: self.seed (what the panel reports),
  client.options["seed"] (what Ollama actually samples with - OllamaClient.chat
  reads options live per request, so it takes effect on the next call), and
  gen_params["seed"] (what the episode records for replay). Bare /seed prints
  all three and shouts if they ever disagree. judge_client is deliberately
  untouched: graders stay pinned at seed 7 / temp 0.0 so the measuring
  instrument never moves with the experiment. Setting a seed while history is
  loaded warns that a real replay also needs /clear - a seed reproduces a run
  from a CLEAN start, and pinning one mid-conversation reproduces nothing.
- SAME-CLASS FIX, /model: the V45.8 KNOWN-OPEN entry "leaves judge_client and
  gen_params['model'] on the old model". Identical defect - a command moves
  one copy of a generation param and leaves the others stale, so the episode
  names a coordinate nothing ran at. Now moves all four. Removed from the
  KNOWN-NOT-FIXED list below.
- SAME-CLASS FIX, --seed: was type=int with no domain guard, so `--seed -1`
  pinned the builder to the Episode "unrecorded" sentinel and every episode
  of that run claimed it had no seed. One normalize_seed() helper now guards
  all three doors (--seed, /seed, direct CLI construction) over the machine's
  own random range 1..2**31-1, so every seed it hands out is a seed it takes
  back. Bad input RAISES at both the argparse and constructor doors rather
  than falling back to random: a typo'd seed must not silently become a
  different run than the one he asked to replay.

NEW IN V45.8 (from auditing five real runs - episodes 1-5 with their paired
artifacts. All five self-tests genuinely pass, re-executed on Linux/pygame
2.6.1; none of the verification claims was fabricated. These are the failures
the passing runs hid):
- ALLOWLIST: g++ added. It is named in the V41.1 changelog as part of the
  g++/gcc/make/cmake toolchain addition, but only the other three ever landed
  - verified by executing BashTool, not by reading the set. `head` remains
  BLOCKED deliberately; see below.
- BLOCKED MESSAGES NAME THE SUBSTITUTE. Run 5 step 11 issued `... | head -30`,
  was refused with a bare 35-name alphabetical dump, and retried at step 12
  with `| more`. The block is right; leaving the model to guess the substitute
  is what cost the iteration.
- SANDBOX RULES ARE NO LONGER STORED AS PLATFORM FACTS. Run 5 then wrote the
  lesson "On Windows, avoid using 'head' in piped commands" at confidence 0.9,
  grounded=True. That is THIS MACHINE'S allowlist recorded as a property of the
  operating system, and neither gate could catch it: 'head' matches no
  impossible/suspect regex, and it DOES appear in the evidence, so the
  causality judge saw support. BLOCKED/Access-Denied notes are now tagged
  [SANDBOX POLICY ...] at the point the evidence is made, and the reflection
  prompt forbids turning one into a platform lesson. Tag is APPENDED, never
  prefixed - _classify_failure and the duplicate guard call startswith() on
  this note (the V41.2 lesson).
- A GUI TIMEOUT IS NO LONGER A VERIFIED SUCCESS. The LAUNCHED-OK family is the
  one bash result with no error prefix AND no "Exit code:" line, so every
  exit-code check was blind to it. Run 2 hit it twice (steps 10, 13): a 30s
  hang was recorded as a SUCCESSFUL command, which set last_ok_bash (defusing
  the completion gate), satisfied the V41.1 unverified->partial test, and gave
  _extract_verification a scolding to store as proof - the stored evidence was
  literally "Do NOT re-run 'mario_snake.py' until --test is wired". An unwired
  --test that blocked to timeout is now a FAILURE, and no LAUNCHED-OK message
  is ever scraped for proof. Plain "LAUNCHED OK" stays a success: V21 added it
  deliberately for windowed apps that survive their timeout.
- DELIVERABLE SPLIT DETECTED. Run 2 was refused an overwrite on mario_snake.py
  at steps 20 and 24, then created mario_snake_game.py at step 25 and finished
  there. root_cause cited mario_snake.py:500, verification cited
  mario_snake_game.py - one learning record, two artifacts, a half-fixed
  original left on disk, 33 steps and 908K tokens for a task run 1 finished in
  4. The V30.7 breaker fired on both refusals, but its prescribed exit was
  str_replace; the model took an exit the machine did not model, which is
  rename.
- TEST SCOPE CHANGE DETECTED. Run 3 step 8 replaced a failing collision->death
  integration test (game._step()) with a direct game._die() call; step 9 then
  added two more asserts. Assert counts went 1 -> 1 -> 3, so ANY count-based
  check reads it as MORE testing. The shipped mario_snake_3.py asserts nothing
  about collision-death at all, and the reflection blamed the implementation
  ("initial implementation had logic errors") for what happened to the test.
  Call-target drift is the signal, not assert count. Warning only, never a
  block - the V28.1 swallow-warning contract.
- ONE BAD LINE NO LONGER TRUNCATES EPISODE MEMORY. The try wrapped the entire
  read loop. Verified: 9 valid episodes with a torn line at position 4 loaded
  THREE, and said so only through a debug_print invisible without -v. The file
  is appended to by a process that can be interrupted mid-write, so a torn last
  line is the EXPECTED failure and its symptom is memory quietly getting
  smaller. Now per-line, counted, and announced loudly at startup. _persist_all
  REFUSES to rewrite a damaged store, so backfill cannot make a skipped line
  permanent - the fix must not convert a load-time symptom into real data loss.

KNOWN, NOT FIXED IN V45.8 (all still open, all verified by execution):
- bash can still write files via a .py script it creates and runs; every
  write-side mechanism (syntax gate, swallow warning, dup-guard purge,
  last_py_edit) is keyed to the tool NAMES file_write/str_replace, so a write
  through bash is invisible to all of them. BUILD_PROMPT documents the route.
  Effect-keyed observation (hash the workspace around every bash call) is the
  only version that cannot be routed around.
- _looks_truncated false-positives on any apostrophe: `x = [1, 2  # don't` is
  diagnosed TRUNCATED WRITE. The two messages prescribe OPPOSITE repairs, and
  V45.6 made this the escalation path, so it misfires on the worst cases.
  CPython already reports "unterminated string literal" in e.msg; read that
  instead of counting quotes.
- the V45.7 completion gate covers .html/.css/.json but still prescribes
  "Run: python <file> --test", which cannot work for them.
- a duplicate-suppressed call is recorded in the trajectory as an executed
  success and still sets last_ok_bash.
- reflection evidence remains size-unbounded (50 x 3000 worst case), now
  interpolated twice into the reflection prompt plus once into the judge.

NEW IN V41.5 (from auditing the mario_snake episode - the run SUCCEEDED,
verified by a real 'ALL TESTS PASSED' exit 0 at step 94, and still stored a
false lesson at confidence 0.92):
- WHOLE TOOL ERROR NOW REACHES THE REFLECTION, not just line 1.
  _extract_error_evidence assumed "tool-level errors already state the problem
  on line 1". False for the ones that matter: str_replace's whitespace error
  states the SYMPTOM on line 1 and the CAUSE on line 2 - "most often tabs vs
  spaces, a trailing space... Line endings were already normalized, so it is
  NOT CRLF". Only line 1 was stored, 12 times, so the reflection saw
  "whitespace" plus "Windows" and concluded CRLF. It wrote convert_to_lf.py,
  which does only data.replace(b'\r\n', b'\n') and cannot remove a trailing
  space, then credited it for a recovery actually caused by single-line edits
  silently stripping those trailing spaces (the single-line path writes back
  prefix + new_str.strip()). The lesson stored grounded=True / 0.92, clearing
  _filter_candidates_by_quality, and would have been injected into every
  later run.
  NOT a truncation-limit problem - the full message is 548 chars against a
  3000 cap that never fired. lines[0] discarded the diagnosis by itself.
  Also added ❌ and ⚠️ to the recognised prefixes: "❌ VERIFICATION FAILED:\n
  <real error>" carries its whole payload on the FOLLOWING lines and was not
  being treated as a tool error at all - BUT only when the body is not a
  Python traceback. A tool header wrapping a traceback is subprocess output,
  not tool prose, and the traceback extractor reads it far better
  ("ZeroDivisionError: ... | at app.py:3" rather than every line joined by
  pipes, where a long trace could push the exception line - which comes LAST -
  past the cap). Probed by a File "...", line N frame specifically, since
  "Error:" itself matches an exception-shaped regex.
  Structural previews are matched by their 🔍 / [Lines headers only. A bare
  numbered-line pattern would be redundant (every dump is emitted UNDER a 🔍
  header by _generate_helpful_preview) and would false-break legitimate error
  text such as "404: Not Found" or a compiler's "1: warning".
  KNOWN, NOT FIXED: the reflection evidence block caps the COUNT of failures
  shown (MAX_FAILURES_SHOWN 50) but never their SIZE - each note is
  interpolated uncapped. On the mario_snake episode this change takes evidence
  from 5.7KB to 11.1KB (+95%); the worst case is 50 x 3000 = 150KB (~37K
  tokens) in a single reflection prompt. Within budget for 256k, but it is a
  size-unbounded path and a per-note cap there is a design call.
  Cap stays 3000, matching the traceback branch: the ❌ payload is unbounded
  subprocess stderr with no upstream slice, so a compiler wall must not be
  halved on the way in. Structural previews (🔍 markers,
  [Lines a-b] headers, numbered source dumps from the candidates engine) are
  cut - navigation aids for the model in the moment, not causal evidence, and
  large enough to swamp the reflection prompt.
  Third fix of this same class: V41.2 fixed "exit code N swallows stderr" and
  "failed bash drops its command"; this fixes "line 1 swallows the
  explanation". In every case the evidence path kept the symptom and threw
  away the cause.

NEW IN V41.3 (from the mario_snake wall-collision log - two bugs that
compounded into a 16-iteration deadlock at steps 32-47):
- STR_REPLACE NOW APPLIES A UNIQUE WHITESPACE-INSENSITIVE MATCH. V30.6
  correctly DIAGNOSED the invisible-whitespace family (a lone trailing
  space, tabs-vs-spaces, an NBSP) and then returned an ERROR - after having
  already proven the match was UNIQUE. The single-line path 40 lines above
  trusts that exact same uniqueness and applies the edit. Multi-line was
  excluded only because the strip-and-re-prefix strategy would lose
  indentation on lines 2+, which does not apply when you locate the real
  line span and splice new_str over it. Two file lines carried a trailing
  space after a comma; the model retyped them without it and hit this
  branch on FIVE attempts (steps 32, 36, 38, 45, 46).
  Also replaced the joined-substring test with per-line WINDOW matching:
  "b\nc" is a substring of "ab\nc" but is not a line-aligned match, so the
  old count()==1 check could fire on a partial line. Ambiguous (>1) matches
  still refuse, and a leading-indent difference re-indents new_str by the
  measured delta rather than trusting the model's indentation.
- DUPLICATE GUARD NOW INVALIDATES ON WRITE. _ok_call_counts was populated
  and NEVER purged, so the guard's claim - "nothing has changed in between,
  so the result would be identical" - was simply false after any edit.
  str_replace succeeded at step 42 and file_read of that same region was
  still suppressed at steps 44 and 47 with "nothing has changed since".
  The compounding failure: str_replace's own error told the model to
  "file_read the target region and copy old_str byte-for-byte", and the
  duplicate guard blocked exactly that - the machine closing the recovery
  path it had just prescribed. By step 34 the model had lost the thread
  entirely and restarted its plan from scratch. A successful file_write or
  str_replace now purges every cached signature naming that file (basename
  match, so relative/absolute/bash-command references all clear).
KNOWN, NOT FIXED (observed in the same log): a multi-line `python -c "..."`
command returns exit 0 with EMPTY stdout under CMD - the literal newline
inside the quoted argument breaks it. The machine records exit 0 as success
with note "ran '...' -> exit 0", so nothing flags that a command which
should have printed 14 lines printed none; steps 33, 39 and 40 were burned
on it before a single-line rewrite worked at step 41. A "succeeded but
produced no output when output was expected" signal is the open question.

NEW IN V41.2 (from the second Dragonfly run - the run itself diagnosed this
one: its lesson was "capture stderr for every bash invocation so that exit
code 1 failures are diagnosed from their actual error output", which reads
like generic advice but is an exact description of a defect in the evidence
path):
- ERROR MESSAGE NO LONGER DISCARDED. In _extract_error_evidence the
  "exit code N" piece was appended BEFORE a fallback gated on
  `if not pieces`, making that fallback unreachable for any nonzero exit.
  Every non-Python failure - g++, gcc, make, where, git, npm: nonzero exit,
  real text in stderr, no Python traceback - was reduced to the bare string
  "exit code 1" and the actual diagnostic thrown away. `where g++` returning
  "INFO: Could not find files for the given pattern(s)." reflected as
  "exit code 1", so the reflection could not name the cause and the grounding
  judge correctly rejected its first attempt for inventing one. The message
  capture is now gated on ABSENCE of traceback structure and the exit code
  appended after it; traceback cases are unchanged.
  This mattered most for the mission it was found on: g++ errors are exactly
  that shape, so every compile failure across all 15 checkpoints would have
  reflected as "exit code 1".
- FAILED BASH NOW RECORDS ITS COMMAND. _tool_note built "ran '<cmd>'" for a
  SUCCESSFUL bash but returned only the error for a failed one, so the
  reflection saw an error with no idea which command produced it. The command
  is now APPENDED as " [cmd: ...]" - never prefixed, because
  _classify_failure and the duplicate guard call startswith() on this note
  for "PROTOCOL ERROR", "BLOCKED:", "Access Denied" and
  "DUPLICATE SUPPRESSED".
Net effect on that step's note:
  before: exit code 1
  after:  INFO: Could not find files for the given pattern(s). | exit code 1
          [cmd: where g++ && where cl.exe]

NEW IN V41.1 (from the Dragonfly mission run: a run that executed zero
successful commands, self-declared BLOCKED, and was stored as outcome
"success"):
- ALLOWLIST REGRESSION FIXED: the V41 edit that added g++/gcc/make/cmake
  also dropped "head" from ALLOWED_CROSS_PLATFORM. Since every part of a
  chained command must be allowed, that silently blocked every
  `... 2>&1 | head -40` - the standard way to trim compiler error output,
  and exactly what the Dragonfly mission prompt instructs. Restored.
  ("w" was dropped in the same edit and is NOT restored - it lists logged-in
  users and has no use here.)
- OUTCOME MUST NOT CONTRADICT EVIDENCE. `outcome` is INITIALIZED to
  "success" and is only overwritten on the warning, protocol and
  max-iteration paths. A model that gives up and explains why produces an
  ordinary no-tool-call completion, so the default survived untouched: the
  Dragonfly episode recorded outcome "success" alongside
  verification "NONE - zero successful commands in this run". The
  fail_count>70% downgrade could not catch it either (1 failure in 5 steps).
  Two mechanical corrections, both reusing evidence already computed:
    (a) unverified is not success - if no bash command ever succeeded, the
        same test the V30.2 verification truth override already uses,
        outcome drops from "success" to "partial". Note this also applies to
        legitimate pure-file-writing runs, which is consistent: the
        verification field already says nothing was checked.
    (b) a self-declared block is a failure - an exact, LINE-ANCHORED protocol
        marker (MISSION/TASK/CHECKPOINT n/PHASE n + " BLOCKED:") in the final
        response forces outcome "failure". This is deliberately not
        natural-language inference; it matches only a marker string a task
        prompt mandates the model print, so a mention inside a quoted
        instruction mid-sentence does not trip it.
  Blast radius of the original bug was limited but real: confidence was
  correctly capped at 0.5, so _filter_candidates_by_quality already excluded
  the episode from injection - but it still counted as a success.
NOTE: this does NOT implement the KNOWN-OPEN claims-vs-evidence auditor (an
LLM pass over the final response's feature claims). That remains a design
call. The Dragonfly episode is now the best calibration case for it: any
such auditor must flag an episode whose outcome says success, whose
verification says NONE, and whose final response says it cannot complete.

NEW IN V38.1 (from a cross-referenced 3-bug diagnosis of the V38 build -
a self-test that "passed" on a broken game, a single Ollama 500 that
killed a whole run, and a correct preventive lesson rejected twice):
Three fixes plus the debug surface that hid the first one. All additive -
no existing logic removed. The two lexical fixes share one root (a naive
substring match that could not tell a phrase from its negation) and are
fixed in the same pass.
- LEXICAL NEGATION AWARENESS (shared helper _phrase_negated_in_clause):
  _is_test_pass no longer reads the 'ALL TESTS PASSED' inside 'NOT ALL
  TESTS PASSED' as a pass, and the reflection grounding floor no longer
  rejects the correct lesson 'use python NOT python3' - it now KEEPS a
  platform-impossible / forbidden token that is WARNED AGAINST in its
  clause and rejects only an unnegated, unevidenced one. The floor also
  now checks EVERY match, not just the first (so 'avoid python3 but run
  sudo' still rejects the sudo). Works in both mechanical and semantic
  /confidence modes; it still catches everything it used to.
- SELF-AWARENESS RETRACTION (mechanical, no model call): a genuinely-
  passing SHALLOW test could surface the once-per-run 'criterion met' line
  and then a DEEPER test could fail, leaving a stale green line that
  contradicting evidence could not correct. If a self-test FAILS after the
  surface fired, the machine now retracts it once. This is NOT the
  KNOWN-OPEN claims-vs-evidence auditor (an LLM pass over the final
  response) - that remains a design call; this is a narrow mechanical
  correction of one stale surface from hard test-fail evidence.
- OLLAMA PROTOCOL-ERROR RECOVERY (new capability): a 500 at template-
  render time (prompt_eval_count 0) is a DETERMINISTIC rejection of the
  replayed tool-call history - a blind resend 500s identically. V25 added
  DETECTION (the run is stored as a failure) but never RECOVERY, so one
  template hiccup ended the whole run and the reflection blamed the last
  blocked bash's shell syntax (the 500 dies at top-of-loop, before any
  trajectory step, so the FIRST prior failure was misread as primary).
  The loop now REPAIRS the history: it flattens the offending assistant
  tool-call turn (and its tool results) into one plain-text assistant
  message so the chat template has no <function> element to choke on -
  content preserved as prose, nothing the model saw is lost - and retries,
  walking back one turn per attempt (cap 4), so it always terminates. A
  new protocol_error failure class + a classifier rule + a terminal-note
  override give the reflection the right attribution when recovery is
  genuinely exhausted, instead of blaming the command.
- DEBUG SURFACE HONESTY: the per-request message dump said "Last 20
  messages" without saying how many it hid; a truncated paste of that
  window is what pointed the original bug#1 diagnosis at 'stale' history
  that was never stale. It now names the hidden count (still 20 shown, to
  keep a 256k-context run's console readable).
NOTE: the protocol-recovery path is compile-verified here but was NOT
runtime-tested against a live Ollama 500 (no ornith-vision box in the edit
environment); the flattening logic and its termination are the parts to
eyeball on the first real 500.

NEW IN V30.8 (from the mario_snake "test and fix it" run: the model
re-tested and re-patched for 6 iterations AFTER its own test passed):
Two fixes, both aimed at the model registering its own state instead of
grinding blindly. Neither is an LLM reflection - both are deterministic
and cannot confabulate.
- SELF-RESULT AWARENESS (new capability, no model call): the machine now
  recognizes the model's OWN success signal - the canonical pass phrases
  the GUI protocol tells it to print (SELF-TEST OK / ALL TESTS PASSED /
  etc.) gated on exit code 0 - and, the first time one appears, surfaces
  ONE factual line into context: "your own self-test just PASSED; your
  task criterion is met; re-running it won't change that; finish unless a
  specific requirement is still unmet." It states the fact once and lets
  the model act on it - it does NOT force a stop (per the owner: no stop
  condition, just make it self-aware). In the mario_snake run the machine
  had this info at step 12 and never told the model; it kept working to
  step 18.
- DUPLICATE MEMORY widened from 1 slot to a 100-signature set. The old
  guard only compared against the IMMEDIATELY previous call, so it caught
  a repeat only when it directly followed its twin; the mario_snake run
  alternated patch->test->same patch->test, so every repeat was separated
  by a different call, _dup_streak reset each time, and the LOOP-DETECTED
  escalation could never fire. Now up to 100 recent successful signatures
  are kept with a per-signature repeat count; a re-issue is caught however
  many calls sit between it and its original, and escalation triggers on
  the 3rd repeat (total) OR 3-in-a-row. Per-task reset preserved (no
  cross-task leak). Verified: alternating repeat now caught (was the blind
  spot), 3rd repeat escalates, pass-signal detection incl. exit-1 reject,
  surface fires exactly once. test_v308.py 9/9; 25/17/13/6 regressions
  unchanged. (One self-inflicted structural break during development - a
  str_replace that consumed _tool_note's signature - was caught by the
  existing suites and fixed; the tests doing their job.)

NEW IN V30.7 (from a second game-mission log: the miss->delete spiral):
A fresh run showed the model write game.py in ONE 951-line file_write,
then try to edit code it only remembered writing: str_replace missed
(old_str described a function not in the file), so it tried file_write
over game.py (Refusing to overwrite), then `del game.py`, then
os.remove - and the machine said NOTHING through all three. Root cause:
the in-loop reflection that nudges the model after a failure listened
ONLY for "HINT:" and "Access Denied:" - and none of Refusing-to-
overwrite, BLOCKED-del, or BLOCKED-os.remove carry either string. The
one nudge that DID fire (on the str_replace miss's HINT) also never
escalated: identical gentle text every time. So the feature existed but
its trigger was too narrow to see the spiral and too flat to break it.
Fix (surgical, to the existing injection block - no new subsystem):
- The nudge now ALSO fires on the blocked-write / failed-edit family:
  "Refusing to overwrite", BLOCKED deletes/overwrites (del, os.remove,
  os.unlink, shutil, rename), and str_replace "String not found".
- It ESCALATES: a stuck_edit_streak counter; on the 2nd consecutive hit
  it stops being gentle and NAMES the trap - "you are in a rewrite-the-
  whole-file loop", states the unchangeable facts (file_write can't
  overwrite; del/os.remove are blocked; str_replace works but your
  old_str doesn't match the bytes), and prescribes the ONLY exit:
  file_read the exact lines, copy the anchor VERBATIM, str_replace one
  region at a time.
- Any successful tool result resets the streak, so an isolated later
  miss starts gentle again. Verified end-to-end against the exact log
  sequence (miss->overwrite->del) plus no-false-positive and streak-
  reset cases: test_breaker_v307.py 6/6, and 25/25 + 17/17 + 13/13
  regressions unchanged.

NEW IN V30.6 (from the 26M-token game-mission run: the CRLF trap):
The run reached the PROOF-OF-PLAY floor correctly - a real behavioral
speed test (76 px/s vs 160 expected) FAILED the build instead of
shipping a broken game, exactly as designed - then burned ~50 of its 217
iterations, a large slice of 26M tokens, fighting a line-ending mismatch
in str_replace. The model's old_str (pasted from a prior CRLF file_read)
carried \r\n while the compare target was LF, so content.count() returned
0 - while the candidates engine scored the SAME lines [EXACT] 0.99,
because candidates .strip() every line and count() does not. The tool and
its own search tool contradicting each other is the worst signal a model
can get: proof the text is there, proof it can't be replaced. It looped,
wrote fixer scripts, created a syntax error, and eventually ran out of
context. Fix (str_replace, all paths, surgical):
- Read RAW (newline="") and match against an LF-normalized copy;
  normalize old_str/new_str endings too. A CRLF old_str now matches an
  LF file and vice versa - the contradiction is gone at the source.
- Detect the file's DOMINANT ending (crlf/lf/cr) and write it back on
  every one of the three write paths (main replace, indent-tolerant
  line, and the count==1 success), so matching a CRLF file no longer
  silently rewrites it to LF - which would have been the same trap in a
  new coat for the next edit.
- Residual-mismatch guard: if stripped-per-line text matches exactly
  once but raw doesn't (tabs-vs-spaces, trailing/NBSP space - NOT CRLF,
  since endings are normalized), the error NAMES that cause and says to
  copy from file_read, instead of routing to the candidates loop.
This is the highest-leverage fix of the saga: it converts the ~50-
iteration loop into one clean replace, and it is purely machine-side.

NEW IN V30.5 (first game-mission run on V30.4, iteration 2):
The model file_read the machine's own 246KB source unprompted - ~60K
tokens injected into history and re-sent every call after, a quarter of
the context gone before any work. Third appearance of the self-read
pattern (V26's attempt was stopped only by a cp1252 accident the V30.4
UTF-8 env removed). str_replace on the runtime was ALSO open - the model
could have edited its own executing code mid-run (same-class hole,
closed in the same pass). Fix - self-invisibility plus hard blocks,
name-agnostic via __file__ so renames to V31+ stay covered:
- Hidden from list_dir output and the startup "Files here right now"
  environment facts (don't advertise what must not be touched).
- file_read, str_replace, and grep_search (file mode) on the runtime
  return a one-line BLOCKED redirect; grep directory recursion skips it
  silently; any bash command mentioning the runtime's filename is
  refused before all other checks (covers type/python-open/self-run).

NEW IN V30.4 (from the second snake_game run - first run of the V30.3 build):
The machine's fixes all held: the candidates engine fired live ([EXACT]
at the right line, preventing a repeat-patch spiral), the model wrote
ZERO exception swallowers, its final response labeled unverified features
"Written but Unverified by Tests" (claim discipline landing), and the run
ended on a genuinely passing self-test with a truthful pinned episode.
The remaining cost: ~17 of 51 tools went to cp1252 UnicodeEncodeError -
the model's ✓ test prints crashed the Windows console encoder, got
converted to [OK] one str_replace at a time, and the binary-inspection
probes crashed on the same encoder. Fix:
- Both bash spawn sites now pass env with PYTHONUTF8=1 and
  PYTHONIOENCODING=utf-8, so child Python speaks UTF-8 regardless of the
  console codepage. Strictly enabling (pipes already decode with
  errors='replace'). This failure class also dominated a V25-era run.
- Candidate scores display at 3 decimals (V30.4 addendum, changelog line
  restored - the code landed, this note originally did not): 0.979 showed
  as "0.98 [VERY HIGH]", straddling the EXACT (>=0.98) label boundary.
- Task slices raised to 32000 (reflection prompt x2, injection
  validation, episode storage): the 8.7KB next-gen mission - and
  missions several times larger - now reach reflections and memory
  whole. 32000 matches the embedding input cap, so a mission is stored,
  reflected on, and embedded at the same width.

NEW IN V30.3 (truncation audit before the next live run - 256K context,
"don't lower any"):
Every [:N] slice in the file was inventoried, classified (model-facing /
display / storage), and 44 values RAISED, zero lowered (verified
programmatically by pairing every changed line old-vs-new). Highlights:
- args echo 2000 -> 10000 (his original number restored; the episode-size
  and reflection-prompt costs are documented at the site and accepted).
- Episode task storage 2000 -> 32000 and reflection-prompt task slices
  2000 -> 32000 (matching the nomic embedding input cap): a /prompt-loaded
  mission spec no longer loses its body in memory or in reflections.
  (V30.5 note: this changelog originally recorded 8000/10000 while the
  code carried 32000 - the code was right, the record was wrong; verified
  against the 8,675-char PROOF OF PLAY mission prompt, which passes every
  slice whole with 23,325 chars of headroom.)
- Reflection evidence chain widened: error first-line 1000 -> 3000,
  evidence join 1000 -> 3000, exception line 500 -> 1500, verification
  proof 500 -> 2000, bash note 500 -> 1500, command echo 200 -> 600
  (the snake run's ~400-char py -c probes were being cut mid-command).
- Stored meta fields (root_cause/fix/verification/lesson) 1000 -> 2000,
  fallback fields 500 -> 1000, judge reason 1000 -> 2000.
- Failed-str_replace previews: per-line 200 -> 300 chars (machine-sized
  lines were being cut in the model's own repair view).
- Ollama error passthrough 1000 -> 5000 so the model sees whole errors.
- Displays: tool-args panel 5000 -> 12000, result panels 2000 -> 5000 and
  5000 -> 10000, Episode Saved reflection line 100 -> 300 (it always
  ended in "..." mid-sentence), /prompt preview 1000 -> 2000, swallower
  line list 10 -> 25.
Checked and deliberately LEFT: file_read and bash output are fully
uncapped (nothing to fix); no message-history trimming exists anywhere;
grep result cap 5000 lines (already ~context-scale); injection/validation
per-episode slices (multiplied by up to 50 candidates in ONE prompt -
raising those risks real context blowout); embedding input 32000 (nomic
model limit); MAX_FAILURES_SHOWN 50 / TAIL_STEPS 20; dashboard layout
counts (height interacts with the crop fix). num_predict is intentionally
NOT set in code - output length is governed by the model tag's default,
which run evidence shows already allows 30KB+ single-completion writes.

NEW IN V30.2 (from the snake_game run - first live run of the V30.1 build):
The run ended with the model declaring success on a game that CRASHES at
launch: its final patch was never tested (all 7 bash calls in the run
failed), and the episode stored a fabricated verification ("the final
python run completed without errors") that the grounding judge passed at
0.85 confidence. Credit where due: the model's --test actually followed
the V28.1 feature-coverage rule (asserts every named SFX exists), and it
DID chase the swallow warning - but grep_search("except.*pass") returned
"No matches found" because the pattern spans two lines and grep is
line-based, so the machine's warning and the machine's search tool
contradicted each other and the model dropped the lead. Fixes:
- Swallow warning now includes the LINE NUMBERS of every swallower and
  says outright that a line-based grep for 'except.*pass' will find
  nothing - no more sending the model on a search its tools cannot win.
- ONE-SHOT COMPLETION GATE (mechanical, no LLM): if a successful .py
  edit postdates the last successful bash - or no command succeeded in
  the entire run - a first completion attempt is bounced once with
  explicit instructions (run --test, fix, or label 'written but
  unverified'); the next completion is accepted regardless, so it can
  never loop.
- VERIFICATION TRUTH OVERRIDE: if zero commands succeeded in the run,
  meta["verification"] is forced to "NONE - ... never verified" and
  confidence capped at 0.5, no matter what the reflection LLM wrote.
  The grounding judge letting a fabricated verification through remains
  the strongest evidence yet for the KNOWN-OPEN claims-vs-evidence
  auditor (two runs now: mario_snake claimed dead features, snake_game
  claimed a run that never happened) - still pending a design call.

NEW IN V30.1 (audit of the V30 hand-edits, diffed against V28.1):
- RESTORED the main-loop completion block. V30 deleted the 7 lines that
  handle a real no-tool-call reply (append to history, set final_response,
  break) - so EVERY run re-prompted the model after its final answer until
  max_iterations and ended as "⚠️ Reached maximum iterations" with
  outcome=failure. This was the run-killer.
- _find_similar_candidates (new in V30) is now actually CALLED: wired into
  str_replace's not-found path (top 5 region-deduped candidates with line
  numbers, per-signal evidence, and a → context excerpt; legacy preview
  remains the fallback). In V30 it had zero call sites - the same
  "fixed function nobody calls" pattern as mario_snake's _make_sound.
- _find_similar_candidates internals fixed, same signals/weights/tiers/
  return shape: (1) each start scored once instead of window-size times
  (the i/off double loop + dedup did ~17x redundant SequenceMatcher work
  and could freeze the event loop on big files; the scan also now runs in
  a worker thread), (2) context_score was ratio(target, whole window),
  which caps near 2T/(T+W) for an embedded target - even byte-exact
  blocks topped out ~0.85 and the EXACT tier was unreachable; it is now
  target coverage of the window, so exact blocks hit 1.0, (3) a
  quick_ratio pre-gate skips hopeless starts.
- Trajectory args echo capped at 2000 (V30 raised 250 to 10000: the whole
  trajectory is serialized into every episode - episodes.jsonl ~40x
  bigger per run, loaded + embedded at startup - and primary_args feeds
  the reflection prompt; 250 truly was too small, 2000 holds a whole
  function of evidence).
- Re-applied the V26 resize fix, which never made it into the V28/V30
  lineage: Live vertical_overflow "visible"->"crop" + once-per-size-change
  clear in refresh_dashboard. "visible" also stacks frames with NO resize
  whenever the dashboard is taller than the terminal - that is the
  stacked-banner glitch report.
- Stale "Three strikes" comment updated to match the V30 five-strike
  empty-response threshold (threshold itself kept as chosen).

NEW IN V28.1 (from the mario_snake sound run log):
The run "succeeded" (SELF-TEST OK, exit 0, grounded episode, 0.95
confidence) while every sound was dead and zero goombas could ever spawn.
All six live sound builders used `pygame.c_int16` (doesn't exist) inside
`except Exception: pass`; every play site was hasattr-guarded, so the
failure produced NO evidence - and the machine's entire truth apparatus
(exit codes, tracebacks, grounding) keys off surfaced evidence. The model
even FOUND the bug and fixed it - in `_make_sound`, a function nothing
calls - leaving six identical live siblings untouched. Fixes:
- SILENT-SWALLOW WARNING: every successful file_write / str_replace on a
  .py file now appends a count of `except ...: pass` (and
  contextlib.suppress) handlers, with a warning that errors inside them
  are invisible to --test. Warning only, never a block - it turns the
  swallowers themselves into trajectory evidence the model can act on.
- BUILD PROMPT, feature coverage: the --test protocol now requires the
  self-test to EXERCISE AND ASSERT every feature the task names
  (task says sounds -> build them and assert not None). "Constructed,
  updated, drew" proves only that it didn't crash.
- BUILD PROMPT, same-class sweep: after fixing any defect, grep_search
  the same file for the same pattern and fix EVERY instance in the same
  pass. One patched copy with six live siblings is not a fix.
- BUILD PROMPT, claim discipline: the final summary may only claim
  features the --test actually proved; everything else is "written but
  unverified" and must be labeled so.
- grep_search accepts a FILE path: the model naturally greped
  'mario_snake.py' for the def-signature map and got a hard
  "not a directory" error at the exact moment it needed the overview,
  falling back to paging file_read windows. grep takes files everywhere
  else in the world; now it does here too (directories still recurse).
- LAUNCHED OK now detects an unwired --test: the old message fired on
  `python mario_snake.py --test` (before the flag existed in the file)
  and its canned NEXT STEPS said to confirm with the exact command that
  had just hung. If --test was in the command and the app still blocked
  to timeout, the flag isn't wired - the message now says so and shows
  the argv branch to add.
- Server heuristic matches EXACT basenames: 'app.py' in cmd_lower also
  matched guiapp.py / snakeapp.py, rerouting a pygame launch into
  SERVER BLOCKED instead of the GUI LAUNCHED-OK path (found live by the
  V28.1 test harness). python app.py / main.py etc. still exact-match.
  KNOWN-OPEN (deliberate, needs a design call):
  nothing yet audits the FINAL RESPONSE's feature claims against
  trajectory evidence - an LLM claims-vs-evidence pass is the general
  fix and is left unimplemented pending approval.

NEW IN V25 (from the V25 line-by-line audit):
- Ollama 500 detection fixed: `status_code == 5000` made the handler dead
  code; real 500s fell through to a plain "HTTP Error:" reply that the
  run recorded as a SUCCESS episode. Client transport errors now carry
  the ⚠️ prefix, so a run that dies mid-flight is stored as a failure.
- /inject validation actually works: the validator listed 50 candidates
  but the parser only accepted 1-5, by substring ("1" matched "10"; the
  word "none" anywhere discarded everything). Now a whole-number parse
  range-checked over all 50.
- Duplicate-guard no longer leaks across tasks (the first call of a new
  task identical to the previous task's last success was suppressed as
  "already succeeded" - a fake-success vector). Consecutive suppressions
  escalate to an explicit LOOP DETECTED directive after 3 repeats.
- Suppression notices are excluded from reflection evidence (they were
  reaching the episode's verification/fix fields).
- Injection confidence floor is 0.7 by design ("real and good quality");
  the two docstrings that still said 0.5 now match the code.
- Windows-only by design: the dangling ALLOWED_UNIX / PLATFORM_RULES_UNIX
  references (latent crash on any non-Windows box) are gone.
- bash sandbox: shell WRITE redirection (> and >>) is blocked outright -
  `echo x > file.py` overwrote files past every guard, same bypass class
  as the temple python -c incident; 2>&1 stays legal. cd targets are now
  path-validated (`cd ..` moved every allowed command outside the
  sandbox). KNOWN-OPEN: running a model-written .py that performs
  deletions is still possible (only `python -c` payloads are scanned).
- Empty-response spin capped: 3 consecutive contentless, tool-less
  replies abort the task as a failure instead of resending the full
  context forever.
- /model and /prompt keep argument case (the whole command line was
  lowercased); /agent switches preserve the /inject and /confidence
  toggles instead of silently resetting them.
- grep_search truncation count fixed (said "- 500" against a 5000 cap);
  list_dir no longer silently drops a FILE named venv/node_modules/etc.
- bash timeouts are real now: "timeout" is a declared parameter (int-coerced,
  clamped 1-60) instead of being silently discarded by the schema filter -
  the model believed it set 30s while the hardcoded 60 applied. On Windows
  the kill is a TREE kill (taskkill /PID x /T /F): proc.kill() only killed
  cmd.exe, so a bare `python game.py` left the pygame window alive as an
  orphan holding the pipes, wedging the machine at proc.wait() until the
  window was closed by hand. The post-kill wait is also bounded (5s) so no
  future orphan variant can wedge that line again. Both timeout paths
  (main execute AND run_verification, which previously returned without
  killing anything and leaked hung verify processes) share one _kill_tree
  helper - any future subprocess site must use it.

NEW IN V24: /confidence toggle - the semantics dial
- /confidence on|off (default ON), mirroring /inject, switches the
  reflection system between semantic and mechanical grounding.
- ON (semantic): the model chooses failure_class from the taxonomy (the
  code regex result is offered as a suggestion, not a mandate); an LLM
  judge audits the lesson's CAUSALITY against the run evidence, replacing
  the lexical install-phrase check that made preventive lessons
  ("pygame can't be pip-installed here; use tkinter") structurally
  unstorable in any run that avoided the mistake; a lesson the judge
  still rejects after one corrective retry is stored ANNOTATED
  (grounded=false, confidence capped at 0.25) instead of being replaced
  by the template - the semantic content is preserved, flagged; and
  injection finally CONSUMES the stored quality signals: grounded=false
  episodes and low-confidence episodes (0 < c < 0.7) are filtered out
  before relevance validation (legacy episodes with confidence 0.0 pass
  unchanged, so old stores keep working).
- OFF (mechanical): exact V23 behavior - regex classification the model
  may not change, lexical grounding gate incl. install phrases,
  deterministic template fallback, confidence stored but ignored.
- BOTH modes keep the hard regex floor: platform-impossible commands
  (sudo/apt on Windows) and agent-forbidden commands are rejected outright
  unless they occurred in the run. The failure class from the original
  sudo-apt-get incident stays impossible in either mode.
- Episode gains a grounded field (bool, default true); old episodes.jsonl
  files load unchanged.

NEW IN V23 (from the mario_snake run log):
- ToolExecutor filters tool arguments to each tool's declared schema:
  models trained on richer tool APIs pass extras (ornith:35b sent a
  'description' kwarg to bash), which previously crashed the call with a
  TypeError and wasted an iteration.
- Reflection verification pins the real test proof (SELF-TEST OK /
  TESTS PASSED) instead of whatever bash happened to run last.

NEW IN V22.1 (from the temple_dash run log):
- file_read is HONEST: returns exactly the requested line range (clamped
  with notice), or the WHOLE file when no range is given. The V21
  MIN_WINDOW=500 logic inflated and slid every request (asked 870-1050,
  shown 577-1076), confusing the model and bloating context.
- bash blocks destructive inline python: os.remove/unlink/rmdir,
  shutil.rmtree/move/copy, pathlib unlink/write_text, open(...,'w') inside
  python -c payloads. Closes the bypass where the model deleted
  temple_dash.py via python -c after 'del' was blocked and file_write
  refused to overwrite.
- duplicate-call breaker: a call byte-identical to the immediately
  previous SUCCESSFUL call is suppressed with an explanation instead of
  re-run (the run repeated the passing --test 3x, a byte-offset check 3x,
  list_dir 2x - pure token burn).
- reflection evidence covers the WHOLE run (all failures capped at 10 +
  repairs + final steps), not a 12-step tail; the temple_dash episode
  misclassified because its true first failure (SyntaxError, step 2) and
  dominant failure (4x cp1252 UnicodeEncodeError) fell outside the tail.
- bash trajectory notes strip a leading cd "..." && prefix so the real
  command survives truncation.

NEW IN V21.1: Evidence-based reflections (from the snake-mario run log +
V21 review). The observed failure: a run whose real problem was a pygame
audio-buffer crash (fixed by str_replace, verified by SELF-TEST OK) saved
the reflection "Use sudo apt-get install python3-pygame..." - a lesson that
never happened, on a Windows machine where sudo/apt cannot even run.
Root causes fixed:
- EVIDENCE CAPTURE: trajectory notes previously stored only the FIRST line
  of a failed tool output, which for bash is literally "STDOUT:" - the
  reflection model never saw the traceback. Notes now carry the real
  exception line, its file:line location, and the exit code; successful
  steps record what was patched and what output proved success.
- FAILURE CLASSIFICATION: the primary failure is classified in code
  (deterministically) BEFORE the reflection prompt, per the V21 review.
- PROMPT GROUNDING: the reflection prompt no longer contains the loaded
  pip/pygame example that the model was copying; it carries the actual
  evidence, explicit platform rules, and demands structured JSON
  (root_cause / fix / verification / lesson / confidence).
- OUTPUT VALIDATION: lessons naming platform-impossible commands
  (sudo/apt/chmod on Windows), agent-forbidden commands, or install advice
  that never occurred in the run are REJECTED - one corrective retry, then
  a deterministic evidence-only fallback. Hallucinated lessons can no
  longer reach the episode store or be injected into future tasks.
- STRUCTURED EPISODES: Episode now stores failure_class, root_cause, fix,
  verification, and confidence alongside the lesson (old episodes.jsonl
  files load unchanged - new fields default to empty).
- PLATFORM RULES: explicit OS-specific never-do rules are injected into
  the build prompt ({platform_rules}) and the reflection prompt.

NEW IN V21: Evidence-driven tuning (from the neon-snake run log)
- UNIFIED SUCCESS DETECTION: dashboard now shows the agent's real verdict
  (V20 displayed green checks for Access Denied / tracebacks / exit code 1)
- ENVIRONMENT PREFLIGHT: python version, importable packages, cwd and file
  listing are probed once and injected into the system prompt (V20 burned
  ~6 of 16 iterations rediscovering these per task)
- GUI LAUNCH RECOGNITION: a tkinter/pygame app that runs the full 60s now
  reports "LAUNCHED OK" instead of a timeout failure
- GUI --test PROTOCOL in the build prompt: generated GUI apps include a
  self-check mode so success is verifiable without blocking
- MEMORY SELF-HEALING: loud startup warning when no embedding model exists
  (V20 saved unretrievable episodes silently); embedding backfill added
- SMARTER REFLECTIONS: failure reasons are recorded in the trajectory and
  fed to the reflection prompt, which now demands concrete, environment-
  specific lessons instead of platitudes
- SECURITY: every chained bash segment is validated (V20 checked only the
  first token, so `echo ok && del ...` bypassed the forbidden list)

NEW IN V20: Ollama timeout fix
- Increased Ollama API timeout from 180s to 600s (10 min) for complex tasks
- Added explicit timeout error handling with helpful message
- Prevents silent "Error:" failures on long generations
"""

import os
import sys
import ast              # V61.11: coverage probe + no-op assertion detector
import re
import json
import difflib          # V61.1: was imported inside two functions only; the
                        # assertion-relaxation detector needs it at module scope.
import asyncio
import argparse
import subprocess
import random
import time
import builtins         # V61.23: _incomplete_findings needs the builtin
                        # name list; checked against the import block rather
                        # than assumed, same as V61.17's shutil.
import hashlib          # V172: the mutation gate returns the md5 of what it
                        # measured, so a round can tell "the file changed" from
                        # "I drew a different sample". Checked against this
                        # block rather than assumed - same rule as shutil below.
import shutil           # V61.17: _purge_pycache. Was used at line 8441 via a
                        # function-local `import shutil` only, so the mutation
                        # gate's cache purge raised NameError into its own
                        # `except: pass` and silently did nothing - meaning a
                        # mutant could have been scored against its cached
                        # predecessor's bytecode. Same call-site class as
                        # V61.11a; caught by checking every module I used
                        # against the import block instead of assuming.
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass
from datetime import datetime

# V45.4: the machine's OWN stdio. V30.4 gave bash CHILDREN a UTF-8 env
# (PYTHONUTF8/PYTHONIOENCODING) but left the parent on the console
# default. Redirect stdout to a file on Windows and it drops to cp1252,
# where the first non-ASCII glyph in the banner ("\u27f3 Connecting...")
# raises UnicodeEncodeError and kills the run before Ollama is contacted.
# Same fix, applied to self. errors="replace" so a stubborn console
# degrades to "?" instead of crashing.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Global verbose flag
VERBOSE = False

# V61.16: THE LOG WAS THE THING BEING TRUNCATED.
#
# debug_print serialized dict/list payloads through [:5000] and everything
# else through [:500]. Measured: BUILD_PROMPT is 11,585 chars and 11,867 as
# indented JSON, so the 5,000 cap showed 42% OF THE SYSTEM PROMPT ALONE and
# every message after it was invisible in every "Sending to Ollama" block.
# On the snake_game run of 2026-07-31 that meant no reasoning block was ever
# visible in the log; the only proof V61.14 was reaching the model at all was
# a stray "</reasoning>" the model leaked into its own replies twice.
#
# Why this was not simply raised: the echo re-serializes the ENTIRE message
# history every iteration, so it is O(n^2). Uncapped, that run's echoes come
# to ~1.3 MB of terminal output against 90 KB at the old cap. Raising the
# screen cap to "complete" makes the terminal useless; leaving it makes the
# log useless. So: two sinks.
#
#   DEBUG_MAX_CHARS  - what goes to the SCREEN. 0 = unlimited.
#   DEBUG_LOG_FILE   - a path. When set, EVERY debug payload is also written
#                      there UNCAPPED regardless of the screen cap, so the
#                      file is the complete record and the terminal stays
#                      readable. Opened append, one process, flushed per
#                      write so a killed run still leaves a usable log.
#
# Set DEBUG_LOG_FILE and hand over that file - it has no truncation in it.
DEBUG_MAX_CHARS = 12000        # screen only; 0 = unlimited

# V61.20: THE UNCAPPED LOG IS ON BY DEFAULT. It was opt-in, and every log
# handed over for analysis since has been the terminal capture instead - the
# 2026-08-01 run's own mutation-gate message was only recoverable because the
# model happened to quote it back. A run that cannot be reconstructed is a
# run nothing can be learned from, and every fix in this changelog came from
# reading one.
#
# WHERE, and why not the obvious place: NOT the working directory. The model
# is told "Files here right now: ..." at startup and has list_dir, file_read
# and grep_search pointed at that directory. A run.log sitting in it would be
# listed, read (V30.5: the model file_read the machine's own 246KB source
# unprompted, ~60K tokens gone before any work), grepped, and handed to the
# mutation gate as another artifact. is_machine_self() hides exactly ONE
# path - the runtime - so a log beside the mission files would not be
# covered by it. It goes beside the RUNTIME instead, where none of those
# tools reach. Derived from __file__ directly rather than from MACHINE_SELF,
# which is defined further down: a forward reference here would be an
# import-time NameError, the V61.11a call-site class again.
DEBUG_LOG_DIR = Path(os.path.abspath(__file__)).parent / "whatif_logs"
DEBUG_LOG_KEEP = 20            # past run logs retained; older are pruned
DEBUG_LOG_FILE = None          # set by init_run_log(); None disables the sink


def init_run_log(explicit=None, enabled: bool = True):
    """Pick this run's log path, prune old ones, return the path or None.

    ONE FILE PER RUN, not one that grows forever: observed logs are 1.7 MB
    and 7.4 MB, so appending across runs produces something nobody opens, and
    a shared file makes "send me the log for that run" ambiguous.

    NEVER raises. If the directory cannot be created or written, logging is
    silently disabled and the run proceeds - a logging failure must not be
    able to stop a build.
    """
    global DEBUG_LOG_FILE, _DEBUG_FH
    _DEBUG_FH = None
    DEBUG_LOG_FILE = None
    if not enabled:
        return None
    try:
        if explicit:
            DEBUG_LOG_FILE = str(explicit)
            return DEBUG_LOG_FILE
        d = Path(DEBUG_LOG_DIR)
        d.mkdir(parents=True, exist_ok=True)
        DEBUG_LOG_FILE = str(d / f"whatif_{time.strftime('%Y%m%d-%H%M%S')}.log")
        # Prune oldest first. The timestamp sorts chronologically, so plain
        # name order is date order. Only whatif_*.log is touched - anything
        # else a user keeps in that directory is left alone.
        old = sorted(d.glob("whatif_*.log"))
        for f in old[:max(0, len(old) - DEBUG_LOG_KEEP + 1)]:
            try:
                f.unlink()
            except Exception:
                pass
        return DEBUG_LOG_FILE
    except Exception:
        DEBUG_LOG_FILE = None
        return None

# Storage caps, separate from display. These land in episodes.jsonl and are
# what a later audit reads back - recovering snake's first write from the
# trajectory is how the 2.8%-game / 61%-test split was measured, and that
# only worked because the write was 23,702 chars against a 32,000 cap. A
# genuinely large first write would have been cut and that analysis would
# have been impossible. THINKING_STORE_CHARS was 8,000 against a largest
# observed block of 7,310 - 690 chars of headroom, and V61.14 exists to make
# reasoning LONGER.
THINKING_STORE_CHARS = 200000
TRAJECTORY_ARG_CHARS = 1200000   # a 1M-char file_write survives whole

# V171 FIX 3: the largest old_str str_replace will SEARCH FOR after an exact
# match has already failed. Not a cap on edit size - an exact match of any
# size still applies (see StrReplaceTool.execute). 120 lines sits just above
# the 100-line/22s point on the measured cost curve and far below the
# 200-line/96s one, and it is well past any anchor a model should be copying
# out of a file_read.
STR_REPLACE_MAX_ANCHOR_LINES = 120
STR_REPLACE_MAX_ANCHOR_CHARS = 8000
PANEL_ARG_CHARS = 32000          # terminal only
_DEBUG_FH = None
_DEBUG_LAST_T = 0.0


def _debug_sink(text: str):
    """Append to DEBUG_LOG_FILE uncapped. Never raises: a logging failure
    must not be able to stop a build."""
    global _DEBUG_FH
    if not DEBUG_LOG_FILE:
        return
    try:
        if _DEBUG_FH is None:
            _DEBUG_FH = open(DEBUG_LOG_FILE, "a", encoding="utf-8",
                             errors="replace", newline="")
        _DEBUG_FH.write(text)
        _DEBUG_FH.write("\n")
        _DEBUG_FH.flush()
    except Exception:
        pass


def debug_print(msg, data=None):
    """Print debug info when verbose mode is on.

    V61.16: the screen gets DEBUG_MAX_CHARS; DEBUG_LOG_FILE gets everything.
    The file is written even when VERBOSE is off, so a run can be recorded
    without flooding the terminal.
    """
    body = ""
    if data is not None and data != "":
        if isinstance(data, (dict, list)):
            body = json.dumps(data, indent=2, default=str)
        else:
            body = str(data)
    global _DEBUG_LAST_T
    _now = time.time()
    _gap = (_now - _DEBUG_LAST_T) if _DEBUG_LAST_T else 0.0
    _DEBUG_LAST_T = _now
    _stamp = (time.strftime("%H:%M:%S", time.localtime(_now))
              + f".{int((_now % 1) * 1000):03d} +{_gap:7.1f}s")
    _debug_sink(f"\n[{_stamp}] [DEBUG] {msg}" + (f"\n{body}" if body else ""))
    if not VERBOSE:
        return
    print(f"\n[DEBUG] {msg}")
    if body:
        cap = DEBUG_MAX_CHARS
        if cap and len(body) > cap:
            print(body[:cap]
                  + f"\n... [{len(body) - cap:,} more chars"
                  + (f"; complete copy in {DEBUG_LOG_FILE}]"
                     if DEBUG_LOG_FILE else
                     "; set DEBUG_LOG_FILE for the complete record]"))
        else:
            print(body)

# Try to import optional dependencies
try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    from rich.console import Console, Group
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.prompt import Prompt
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text
    from rich.live import Live
    from rich.live_render import LiveRender
    from rich.control import Control, ControlType
    from rich.cells import cell_len
    from rich.align import Align
    from rich import box
    from rich.markup import escape  # V22.1: literal [brackets] in panels
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    def escape(text):  # no-op when rich is absent
        return text


# =============================================================================
# MATRIX RAIN EFFECT
# =============================================================================

class MatrixRain:
    """Generates matrix-style falling characters - mirrors the agent's token flow"""

    # IMPORTANT: every glyph is exactly one terminal cell wide. The former
    # full-width Katakana occupied two Windows Terminal cells while the grid
    # counted each glyph as one column. Random frames therefore wrapped into
    # extra physical rows, pushing the animation's bottom border off-screen,
    # then appeared to shrink again when the character mix changed. Half-width
    # Katakana preserves the Matrix look without changing the panel geometry.
    CHARS = "ｱｲｳWｵNｷｸHｺMｼｽTｿﾀFﾂﾃﾄﾅ-ﾇﾈﾉAﾋﾌCﾎﾏﾐﾑﾒﾓﾔﾕEﾗIﾙﾚAﾜﾝ01"
    
    def __init__(self, width=60, height=6):
        self.width = max(10, width)
        self.height = max(4, height)
        self.columns = [random.randint(0, self.height) for _ in range(self.width)]
        self.speeds = [random.randint(1, 3) for _ in range(self.width)]  # Variable speeds
        self.chars = [[' ' for _ in range(self.width)] for _ in range(self.height)]
        
    def step(self):
        """Advance the rain one step"""
        for x in range(self.width):
            # Variable speed per column
            self.columns[x] += self.speeds[x]
            if self.columns[x] > self.height + random.randint(3, 8):
                self.columns[x] = 0
                self.speeds[x] = random.randint(1, 3)  # New random speed
            
            for y in range(self.height):
                if y == self.columns[x] % self.height:
                    self.chars[y][x] = random.choice(self.CHARS)
                elif random.random() > 0.92:  # Occasional character changes
                    if self.chars[y][x] != ' ':
                        self.chars[y][x] = random.choice(self.CHARS)
                elif random.random() > 0.97:  # Fade out
                    self.chars[y][x] = ' '
                    
    def render(self) -> "Text":
        """Render the current state as Rich Text"""
        if not RICH_AVAILABLE:
            return ""
        text = Text(no_wrap=True, overflow="crop")
        for y, row in enumerate(self.chars):
            for x, char in enumerate(row):
                if char != ' ':
                    if y == self.columns[x] % self.height:
                        text.append(char, style="bold bright_white")
                    elif y == (self.columns[x] - 1) % self.height:
                        text.append(char, style="bright_green")
                    elif y == (self.columns[x] - 2) % self.height:
                        text.append(char, style="green")
                    else:
                        text.append(char, style="dim green")
                else:
                    text.append(' ')
            if y < self.height - 1:
                text.append('\n')
        return text


# =============================================================================
# LIVE STATUS DISPLAY
# =============================================================================

class AgentStatusDisplay:
    """
    Persistent live dashboard showing agent's real-time cognitive state.
    
    Features:
    - Real iteration progress with progress bar
    - Context window usage (green → yellow → red)
    - Tool history with success/failure indicators
    - Current phase indicator (Waiting for Ollama, Executing tool, etc.)
    - Elapsed time tracking
    - Live matrix rain background
    - Current activity description
    - Episode memory integration with review mode
    """
    
    def __init__(self, max_iterations=1000000, max_tokens=256000, messages_getter=None, system_prompt_getter=None, memory_stats=None, inject_enabled=False, confidence_enabled=True):    
        # Default Context = 32768
        # Core state
        self.iteration = 0
        self.max_iterations = max_iterations
        self.current_tool = None
        self.current_tool_args = None
        self.tool_history = []  # [(name, success, duration_ms), ...]
        self.status = "initializing"
        
        # Context tracking - REAL tokens from Ollama
        self.context_tokens = 0          # Current context size (real from Ollama)
        self.max_tokens = max_tokens
        self.message_count = 0
        self._messages_getter = messages_getter  # Callable that returns agent.messages
        self._system_prompt_getter = system_prompt_getter  # Callable that returns system prompt
        
        # REAL token tracking from Ollama API
        self.real_prompt_tokens = 0       # Last prompt_eval_count from Ollama
        self.real_completion_tokens = 0   # Last eval_count from Ollama  
        self.total_prompt_tokens = 0      # Accumulated across all iterations
        self.total_completion_tokens = 0  # Accumulated across all iterations
        self.using_real_tokens = False    # Flag: are we showing real or estimated?
        
        # Episode memory tracking
        self.memory_stats = memory_stats or {"total": 0, "successes": 0, "failures": 0}
        self.lessons_candidates = 0  # How many candidates found by embedding search
        self.lessons_injected = 0  # How many actually injected (if enabled)
        self.inject_enabled = inject_enabled  # Whether auto-inject is on
        self.confidence_enabled = confidence_enabled  # V24: semantic reflection mode
        self.episode_saved = False  # Whether episode was saved at end
        self.last_reflection = ""  # Preview of saved reflection
        
        # Timing
        self.start_time = time.time()
        self.phase_start_time = time.time()
        self.tool_start_time = None
        
        # Phase tracking
        self.phase = "Starting"  # Starting, Thinking, Calling Ollama, Executing Tool, Processing Response
        self.phase_detail = ""   # Additional detail like tool name or "iteration 3"
        
        # Visual elements
        self.matrix = MatrixRain(60, 3)
        self.frame_count = 0
        self.last_result_preview = ""
        self.error_message = ""
        
        # Activity log (last few events)
        self.activity_log = []
    
    def set_lessons_found(self, candidates: list):
        """Called when embedding search finds candidates"""
        self.lessons_candidates = len(candidates)
        if candidates:
            self.log_activity(f"Found {len(candidates)} candidate episodes")
    
    def set_lessons_injected(self, episodes: list):
        """Called when lessons are actually injected (after LLM validation)"""
        self.lessons_injected = len(episodes)
        self.log_activity(f"Injected {len(episodes)} validated lessons")
    
    def set_episode_saved(self, episode):
        """Called when episode is saved after task completion"""
        self.episode_saved = True
        self.last_reflection = episode.reflection[:100] + "..." if len(episode.reflection) > 100 else episode.reflection
        self.memory_stats["total"] += 1
        if episode.outcome == "success":
            self.memory_stats["successes"] += 1
        else:
            self.memory_stats["failures"] += 1
        self.log_activity(f"Episode saved: {episode.outcome}")
        
    def log_activity(self, message: str):
        """Add to activity log with timestamp"""
        elapsed = time.time() - self.start_time
        self.activity_log.append((elapsed, message))
        # Keep last 500
        if len(self.activity_log) > 500:
            self.activity_log.pop(0)
    
    def set_real_tokens(self, prompt_tokens: int, completion_tokens: int):
        """
        Set REAL token counts from Ollama API response.
        
        Called after each Ollama chat() call with:
        - prompt_tokens: prompt_eval_count (tokens in the prompt/context)
        - completion_tokens: eval_count (tokens generated)
        """
        if prompt_tokens > 0:
            self.using_real_tokens = True
            self.real_prompt_tokens = prompt_tokens
            self.real_completion_tokens = completion_tokens
            self.context_tokens = prompt_tokens  # This IS the real context size
            self.total_prompt_tokens += prompt_tokens
            self.total_completion_tokens += completion_tokens
            self.log_activity(f"Tokens: {prompt_tokens:,} prompt + {completion_tokens:,} completion")
    
    def get_total_tokens(self) -> int:
        """Get total tokens used across all iterations"""
        return self.total_prompt_tokens + self.total_completion_tokens
    
    def compute_context_tokens(self) -> int:
        """
        Fallback: Estimate tokens from message content when real data unavailable.
        
        Uses chars/4 heuristic - only used before first Ollama response arrives.
        """
        if self.using_real_tokens:
            return self.context_tokens  # Return real value if available
            
        messages = self._messages_getter()
        total_chars = len(self._system_prompt_getter()) + 20  # +20 for role wrapper
        
        for msg in messages:
            msg_dict = msg.to_dict() if hasattr(msg, 'to_dict') else msg
            total_chars += len(json.dumps(msg_dict, default=str))
        
        # chars/4 is a reasonable approximation for most tokenizers
        return total_chars // 4
    
    def update_context_tokens(self):
        """Update context token count - uses real data if available, else estimates"""
        if not self.using_real_tokens:
            # Only estimate if we don't have real data yet
            self.context_tokens = min(self.max_tokens, self.compute_context_tokens())
        self.message_count = len(self._messages_getter())
    
    def set_phase(self, phase: str, detail: str = ""):
        """Update current phase"""
        self.phase = phase
        self.phase_detail = detail
        self.phase_start_time = time.time()
        self.log_activity(f"{phase}" + (f": {detail}" if detail else ""))
        
    def start_iteration(self, iteration: int):
        """Called when a new iteration begins"""
        self.iteration = iteration
        self.status = "thinking"
        self.set_phase("Calling Ollama", f"iteration {iteration}")
        # REAL token estimation from actual message content
        self.update_context_tokens()
        
    def start_tool(self, name: str, args: dict):
        """Called when a tool execution begins"""
        self.current_tool = name
        self.current_tool_args = args
        self.tool_start_time = time.time()
        self.status = "tool_call"
        self.set_phase("Executing Tool", f"{TOOL_ICONS.get(name, '🔧')} {name}")
        
    def finish_tool(self, name: str, success: bool, result_preview: str = ""):
        """Called when a tool execution completes"""
        duration_ms = int((time.time() - self.tool_start_time) * 1000) if self.tool_start_time else 0
        self.tool_history.append((name, success, duration_ms))
        self.status = "success" if success else "error"
        self.last_result_preview = result_preview[:800] if result_preview else ""
        self.current_tool = None
        self.current_tool_args = None
        self.set_phase("Processing Response", f"tool returned {'✓' if success else '✗'}")
        # CRITICAL: Recompute tokens after tool result - this is when context explodes
        # (a single file_read can add 5000+ tokens)
        self.update_context_tokens()
        
    def set_waiting(self):
        """Called when waiting for Ollama response"""
        self.status = "thinking"
        self.set_phase("Waiting for Ollama", "streaming response...")
        
    def set_complete(self):
        """Called when processing is complete"""
        self.status = "complete"
        self.set_phase("Complete", f"{len(self.tool_history)} tools used")
        
    def set_error(self, message: str):
        """Called on error"""
        self.status = "error"
        self.error_message = message
        self.set_phase("Error", message[:500])
        
    def get_elapsed(self) -> str:
        """Get formatted elapsed time"""
        elapsed = time.time() - self.start_time
        if elapsed < 60:
            return f"{elapsed:.1f}s"
        else:
            mins = int(elapsed // 60)
            secs = int(elapsed % 60)
            return f"{mins}m {secs}s"
    
    def get_phase_elapsed(self) -> str:
        """Get time in current phase"""
        elapsed = time.time() - self.phase_start_time
        return f"{elapsed:.1f}s"
        
    def make_layout(self) -> "Panel":
        """Create the full dashboard layout"""
        if not RICH_AVAILABLE:
            return None
        
        self.frame_count += 1
        self.matrix.step()
        
        # ═══════════════════════════════════════════════════════════════
        # LEFT COLUMN: Progress metrics
        # ═══════════════════════════════════════════════════════════════
        
        # Iteration progress
        iter_pct = min(20, self.iteration * 20 // max(self.max_iterations, 1))
        iter_bar = "█" * iter_pct + "░" * (20 - iter_pct)
        iter_color = "bright_green" if self.iteration < 50 else "yellow" if self.iteration < 80 else "red"
        iter_section = (
            f"[bold cyan]Iteration[/bold cyan]\n"
            f"[bold]{self.iteration}[/bold][dim]/{self.max_iterations}[/dim]\n"
            f"[{iter_color}]{iter_bar}[/{iter_color}]"
        )
        
        # Context window usage - NOW WITH REAL TOKENS
        ctx_pct = min(100, self.context_tokens * 100 // self.max_tokens)
        ctx_color = "bright_green" if ctx_pct < 50 else "yellow" if ctx_pct < 80 else "red"
        ctx_bar_len = ctx_pct // 5
        ctx_bar = "█" * ctx_bar_len + "░" * (20 - ctx_bar_len)
        # Show REAL indicator when using actual Ollama token counts
        token_label = "[green]REAL[/green]" if self.using_real_tokens else "[dim]~est[/dim]"
        ctx_section = (
            f"[bold cyan]Context Window[/bold cyan] {token_label}\n"
            f"[bold]{self.context_tokens:,}[/bold][dim]/{self.max_tokens:,}[/dim]\n"
            f"[{ctx_color}]{ctx_bar}[/{ctx_color}] [{ctx_color}]{ctx_pct}%[/{ctx_color}]"
        )
        
        # Elapsed time + total tokens used
        total_toks = self.get_total_tokens()
        time_section = (
            f"[bold cyan]Elapsed[/bold cyan]\n"
            f"[bold bright_white]{self.get_elapsed()}[/bold bright_white]\n"
            f"[dim]Total: {total_toks:,} toks[/dim]"
        )
        
        # Episode memory section - show candidates vs injected
        mem_total = self.memory_stats["total"]
        mem_success = self.memory_stats["successes"]
        
        # Show candidates found vs actually injected
        if self.lessons_candidates > 0:
            if self.inject_enabled and self.lessons_injected > 0:
                lessons_indicator = f"[bold green]📚 {self.lessons_injected}/{self.lessons_candidates}[/bold green]"
            elif self.inject_enabled:
                lessons_indicator = f"[yellow]📚 0/{self.lessons_candidates}[/yellow]"  # Found but none validated
            else:
                lessons_indicator = f"[dim magenta]📚 ({self.lessons_candidates})[/dim magenta]"  # Review mode
        else:
            lessons_indicator = "[dim]📚 -[/dim]"
        
        saved_indicator = "[green]💾 ✓[/green]" if self.episode_saved else "[dim]💾 -[/dim]"
        inject_status = "[green]ON[/green]" if self.inject_enabled else "[dim]OFF[/dim]"
        conf_status = "[green]ON[/green]" if self.confidence_enabled else "[dim]OFF[/dim]"
        
        memory_section = (
            f"[bold cyan]Memory[/bold cyan]\n"
            f"[dim]Episodes:[/dim] [bold]{mem_total}[/bold] [dim]({mem_success}✓)[/dim]\n"
            f"{lessons_indicator} {saved_indicator}\n"
            f"[dim]Inject:[/dim] {inject_status} [dim]Sem:[/dim] {conf_status}"
        )
        
        left_col = f"{iter_section}\n\n{ctx_section}\n\n{time_section}\n\n{memory_section}"
        
        # ═══════════════════════════════════════════════════════════════
        # CENTER COLUMN: Current status and phase
        # ═══════════════════════════════════════════════════════════════
        
        # Status with animated spinner - DIFFERENT animations for different states
        status_colors = {
            "initializing": "dim",
            "thinking": "yellow", 
            "tool_call": "bold bright_cyan", 
            "success": "bright_green", 
            "error": "bold red",
            "complete": "bold bright_green"
        }
        status_color = status_colors.get(self.status, "white")
        
        # Different spinners for different states
        if self.status == "thinking":
            spinners = ["◐ ", "◓ ", "◑ ", "◒ "]
            spinner = spinners[self.frame_count % 4]
        elif self.status == "tool_call":
            # More active animation for tool execution
            spinners = ["⚡", "⚙ ", "🔧", "⚙ "]
            spinner = spinners[self.frame_count % 4]
        elif self.status == "success":
            spinner = "✓ "
        elif self.status == "error":
            spinner = "✗ "
        elif self.status == "complete":
            spinner = "● "
        else:
            spinner = "○ "
        
        status_section = f"[{status_color}]{spinner}{self.status.upper()}[/{status_color}]"
        
        # Phase with elapsed
        phase_section = (
            f"[bold bright_white]{self.phase}[/bold bright_white]\n"
            f"[dim]{self.phase_detail}[/dim]\n"
            f"[dim]({self.get_phase_elapsed()})[/dim]"
        )
        
        # Current tool being executed (if any)
        if self.current_tool:
            tool_icon = TOOL_ICONS.get(self.current_tool, "🔧")
            tool_color = TOOL_COLORS.get(self.current_tool, "white")
            # Show truncated args
            args_preview = ""
            if self.current_tool_args:
                if "path" in self.current_tool_args:
                    args_preview = self.current_tool_args["path"]
                elif "command" in self.current_tool_args:
                    args_preview = self.current_tool_args["command"][:70]
            tool_section = (
                f"[bold {tool_color}]▶ {tool_icon} {self.current_tool}[/bold {tool_color}]\n"
                f"[dim]{args_preview}[/dim]"
            )
        else:
            tool_section = "[dim]No active tool[/dim]"
        
        center_col = f"{status_section}\n\n{phase_section}\n\n{tool_section}"
        
        # ═══════════════════════════════════════════════════════════════
        # RIGHT COLUMN: Tool history
        # ═══════════════════════════════════════════════════════════════
        
        history_lines = ["[bold cyan]Tool History[/bold cyan]"]
        if self.tool_history:
            for tool, success, duration in self.tool_history[-10:]:  # Last 10 tools
                icon = "✓" if success else "✗"
                color = "green" if success else "red"
                t_icon = TOOL_ICONS.get(tool, "🔧")
                history_lines.append(f"[{color}]{icon}[/{color}] {t_icon} {tool} [dim]{duration}ms[/dim]")
        else:
            history_lines.append("[dim]No tools called yet[/dim]")
        
        # Success/fail summary
        if self.tool_history:
            successes = sum(1 for _, s, _ in self.tool_history if s)
            failures = len(self.tool_history) - successes
            history_lines.append(f"\n[green]✓ {successes}[/green] [red]✗ {failures}[/red]")
        
        right_col = "\n".join(history_lines)
        
        # ═══════════════════════════════════════════════════════════════
        # BUILD LAYOUT
        # ═══════════════════════════════════════════════════════════════
        
        # Three-column table
        table = Table(show_header=False, box=None, padding=(0, 2), expand=True)
        table.add_column(width=24)
        table.add_column(width=28)
        table.add_column(width=24)
        table.add_row(left_col, center_col, right_col)
        
        # Activity log at bottom
        activity_text = Text()
        activity_text.append("─" * 70 + "\n", style="dim")
        for elapsed, msg in self.activity_log[-8:]:
            activity_text.append(f"[{elapsed:>6.1f}s] ", style="dim")
            activity_text.append(f"{msg}\n", style="white")
        
        # Combine: matrix rain + table + activity log
        return Panel(
            Group(
                Align.center(self.matrix.render()),
                table,
                activity_text
            ),
            title="[bold bright_green]◈ WHAT-IF MACHINE ◈[/bold bright_green]",
            subtitle=f"[dim]Frame {self.frame_count} | {self.get_elapsed()} elapsed[/dim]",
            border_style="bright_green",
            box=box.DOUBLE
        )


# =============================================================================
# THINKING ANIMATION FRAMES
# =============================================================================

THINKING_FRAMES = [
    "◈ Analyzing   ●○○○○",
    "◈ Analyzing   ○●○○○",
    "◈ Analyzing   ○○●○○",
    "◈ Reasoning   ○○○●○",
    "◈ Reasoning   ○○○○●",
    "◈ Planning    ●○○○○",
    "◈ Planning    ○●○○○",
    "◈ Deciding    ○○●○○",
    "◈ Deciding    ○○○●○",
    "◈ Executing   ○○○○●",
]


# =============================================================================
# SECURITY
# =============================================================================

class SecurityError(Exception):
    pass


class PathValidator:
    def __init__(self, working_dir: str = None):
        self.working_dir = Path(working_dir or os.getcwd()).resolve()
    
    def validate(self, path: str) -> Path:
        requested = Path(path)
        if not requested.is_absolute():
            requested = self.working_dir / requested
        resolved = requested.resolve()
        try:
            resolved.relative_to(self.working_dir)
        except ValueError:
            raise SecurityError(f"Access Denied: '{path}' is outside working directory")
        return resolved


# =============================================================================
# TOOLS
# =============================================================================

class BaseTool(ABC):
    def __init__(self, working_dir: str = None):
        self.validator = PathValidator(working_dir)
    
    @property
    @abstractmethod
    def name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> dict:
        pass
    
    @abstractmethod
    async def execute(self, **kwargs) -> Any:
        pass
    
    def to_schema(self) -> dict:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters
            }
        }


# V30.5: the runtime's own file. Missions keep trying to read it - the
# V26 mission run attempted it via python -c open() (stopped only by a
# cp1252 accident that the V30.4 UTF-8 env has since removed), and the
# first game-mission run on V30.4 file_read the whole 246KB machine at
# iteration 2: ~60K tokens injected into history and RE-SENT on every
# call after. The runtime is not mission material. It is hidden from
# listings and startup facts, and reads/edits/executions of it are
# refused. Name-agnostic via __file__ - survives renames to V31+.
MACHINE_SELF = Path(os.path.abspath(__file__)).resolve()

SELF_BLOCK_MSG = (
    "BLOCKED: '{name}' is the agent runtime executing this session - it is "
    "not part of the mission. Do not read, modify, or run it. Continue with "
    "the mission files."
)


def is_machine_self(p) -> bool:
    # V61.20: also hides the run-log directory. Normally whatif_logs/ sits
    # beside the runtime and the working directory is elsewhere, so nothing
    # here applies. But if someone runs the machine FROM the workspace, the
    # log lands in the mission directory and everything V30.5 was written to
    # prevent comes back: it would be listed in "Files here right now",
    # file_read (these logs are 1.7-7.4 MB - one read would end the run),
    # grepped, and offered to the mutation gate. Same guard, same name-
    # agnostic shape, one extra path.
    try:
        rp = Path(p).resolve()
    except Exception:
        return False
    if rp == MACHINE_SELF:
        return True
    try:
        logdir = Path(DEBUG_LOG_DIR).resolve()
        return rp == logdir or logdir in rp.parents
    except Exception:
        return False


class FileReadTool(BaseTool):
    name = "file_read"
    description = "Read the contents of a file. Returns the file content with line numbers."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file to read"},
            "start_line": {"type": "integer", "description": "Start line (1-indexed)"},
            "end_line": {"type": "integer", "description": "End line (inclusive)"}
        },
        "required": ["path"]
    }

    async def execute(self, path: str, start_line: int = None, end_line: int = None) -> str:
        try:
            resolved_path = self.validator.validate(path)
            if is_machine_self(resolved_path):
                return SELF_BLOCK_MSG.format(name=resolved_path.name)
            if not resolved_path.exists():
                return f"Error: File '{path}' not found"
            if not resolved_path.is_file():
                return f"Error: '{path}' is not a file"

            with open(resolved_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()

            total = len(lines)
            if total == 0:
                return f"File: {path} (0 lines) lines_shown=0-0\n"

            # V22.1: the tool now returns EXACTLY what was asked for.
            # (V21's MIN_WINDOW=500 inflated every request to >=500 lines
            # and slid the window near EOF - the model asked for lines
            # 870-1050 and was shown 577-1076 labeled differently than it
            # requested, so it re-read repeatedly and burned context.)
            # Rules: no range -> the WHOLE file; a range -> those lines,
            # clamped to the file with an explicit notice when clamped.
            if start_line is None and end_line is None:
                s, e = 1, total
                notice = ""
            else:
                s = 1 if start_line is None else max(1, int(start_line))
                e = total if end_line is None else int(end_line)
                if e < s:
                    s, e = e, s
                clamped_s, clamped_e = max(1, min(s, total)), max(1, min(e, total))
                notice = ""
                if (clamped_s, clamped_e) != (s, e):
                    notice = (f" (requested {s}-{e}, clamped to the file's "
                              f"1-{total} range)")
                s, e = clamped_s, clamped_e

            result_lines = []
            for i, line in enumerate(lines[s - 1:e], start=s):
                result_lines.append(f"{i:4d} | {line.rstrip()}")

            return (
                f"File: {path} ({total} lines) lines_shown={s}-{e}{notice}\n"
                + "\n".join(result_lines)
            )

        except SecurityError as e:
            return str(e)
        except Exception as e:
            return f"Error reading file: {str(e)}"


# V28.1: silent-swallow detector (from the mario_snake sound run).
# All six sound builders died on `pygame.c_int16` inside
# `except Exception: pass`; every play site was hasattr-guarded, so the
# SELF-TEST passed with the whole feature dead. The machine's truth
# apparatus keys off SURFACED errors - `except: pass` launders them away
# before they can become evidence. This appends a WARNING (never a block)
# to successful .py writes so the swallowers themselves become visible
# trajectory evidence the model can act on. contextlib.suppress is the
# same swallower in a trenchcoat, so it is counted too.
SWALLOW_RE = re.compile(
    r"except(?:\s+[A-Za-z_][\w\.]*(?:\s+as\s+\w+)?|\s*\([^)]*\)(?:\s+as\s+\w+)?)?"
    r"\s*:\s*(?:pass\b|(?:#[^\n]*)?\n\s*pass\b)"
)
SUPPRESS_RE = re.compile(r"\bsuppress\s*\(")

# V61.9: `except KeyboardInterrupt: pass` is the CORRECT way to exit quietly
# on Ctrl+C, and SystemExit is the same story. The old regex flagged both, so
# on the fps_game run two of the reported swallowers were 1 real bug and 1
# unfixable-by-design nag. A warning the model CANNOT satisfy teaches it the
# whole warning is noise - and the real one at line 1754 was ignored along
# with it for six consecutive edits. Every warning this emits must now be
# actionable. A tuple counts as benign only if it contains NOTHING else:
# `except (KeyboardInterrupt, ValueError): pass` still swallows ValueError.
BENIGN_SWALLOW_RE = re.compile(
    r"except\s*\(?\s*(?:KeyboardInterrupt|SystemExit)"
    r"(?:\s*,\s*(?:KeyboardInterrupt|SystemExit))*\s*\)?\s*"
    r"(?:as\s+\w+\s*)?:"
)


# V45.8: markers, so the warnings below can be recognised downstream by
# _tool_note (trajectory -> episodes.jsonl -> reflection evidence) exactly the
# way the V45.3 syntax flags are.
SANDBOX_POLICY_TAG = (" [SANDBOX POLICY - this agent's own guard refused it; "
                      "NOT an operating-system limitation]")
TEST_WEAKENED_MARK = "TEST SCOPE CHANGED"
DELIVERABLE_SPLIT_MARK = "DELIVERABLE SPLIT"

# Method calls that are test scaffolding rather than the behaviour under test.
# Dropping one of these between old_str and new_str says nothing.
_CALL_RE = re.compile(r"\.\s*([A-Za-z_]\w*)\s*\(")
_SCAFFOLD_CALLS = frozenset({
    "clear", "append", "update", "pop", "copy", "get", "keys", "values",
    "items", "sort", "extend", "insert", "remove", "add", "join", "split",
    "strip", "format", "lower", "upper", "count", "index", "setdefault",
})

# V61.1: the OTHER way a failing test is made to pass without fixing anything.
#
# The V45.8 detector below watches for a DROPPED CALL TARGET, which is one
# shape of weakening. The spongebob run of 2026-07-29 (seed 894106943) used a
# different one and sailed straight through:
#
#     game.hud.update(1/60)                 ->  for _ in range(60):
#     assert game.hud.score > 1234,             game.hud.update(1/60)
#            "Score should increase"        assert game.hud.score >= 1234,
#                                                  "Score should not decrease"
#
# No call was dropped - update() is called SIXTY times now, so every
# count-based and call-based check reads that as more testing. It is not.
# HUD.update does `self.score += int(dt * self.speed)` = int(0.1417) = 0, so
# the score is frozen forever; measured, 3,600 real frames move it zero points.
# The original assertion caught that exactly. Changing > to >= made a dead
# scoreboard go green, and the episode then recorded "patched score increment
# logic" for a patch that never touched the scoring code.
#
# So: rank the comparison operators by STRENGTH and warn when a matched pair of
# assertions gets weaker. Warning only, never a block - same contract as the
# V28.1 swallow warning and the V45.8 call-drop warning above.
_ASSERT_RE = re.compile(r"^\s*assert\b(.*)$", re.MULTILINE)
_OP_RE = re.compile(r"(>=|<=|==|!=|\bis\s+not\b|\bis\b|\bnot\s+in\b|\bin\b|>|<)")
# Higher = stronger claim. A drop in rank between matched asserts is a relaxation.
_OP_STRENGTH = {
    "==": 3, "is": 3,
    ">": 2, "<": 2,
    ">=": 1, "<=": 1, "in": 1,
    "!=": 0, "is not": 0, "not in": 0,
}
_NUM_RE = re.compile(r"-?\d+(?:\.\d+)?")

# V171 FIX 2: AN ASSERTION IS A SHAPE, NOT A KEYWORD.
#
# Every assertion analyser in this file keyed on the token `assert`:
# _assert_bodies (relaxation ranking), _assert_lines (never-fired tracing) and
# noop_assert_findings (always-true detection). On the mario_game artifact of
# 2026-08-04 all three returned EMPTY - measured: 0 `assert` statements and 128
# `check(...)` calls, because the model wrote the standard collect-and-report
# harness the moment it wanted more than one failure per run:
#
#     def check(cond, msg):
#         nonlocal test_passed
#         if not cond:
#             errors.append(msg); test_passed = False
#
# That is not an evasion, it is the normal way to write a suite that reports
# all failures instead of dying on the first. But it meant a model could
# disable this machine's entire test-weakening defence by naming its helper
# `check`, and one did: 8 assertions were dropped in a single edit and the
# relaxation ranker had nothing to rank.
#
# Two detectors, because the two callers have different evidence available:
#   * FRAGMENTS (old_str/new_str) do not parse as a module, so a call is
#     matched by SHAPE - line-anchored, undotted, an assertion-ish name, and
#     either two-plus arguments (the cond, msg contract) or one argument
#     carrying a comparison. Dotted calls are excluded so `self.check_hit(a)`
#     in game code is never mistaken for a test.
#   * WHOLE SOURCES can be parsed, so _helper_assert_names finds locally
#     defined helpers STRUCTURALLY - a function that tests a parameter and
#     records a failure - and catches names the prior above would miss.
_ASSERT_CALL_RE = re.compile(
    r"^[ \t]*(?:if[ \t]+not[ \t]+)?"
    r"((?:check|expect|verify|ensure|require|must|should|fail_unless)\w*"
    r"|\w*assert\w*)"
    r"[ \t]*\(",
    re.MULTILINE)


def _split_top_level_args(text: str, open_idx: int):
    """Top-level comma-separated arguments of the call whose '(' is at
    `open_idx`. Returns [] when the parens never balance (a truncated
    fragment), so a cut-off edit can never be read as an assertion."""
    depth = 0
    args, start = [], open_idx + 1
    in_str, quote, esc = False, "", False
    for i in range(open_idx, len(text)):
        ch = text[i]
        if in_str:
            if esc:
                esc = False
            elif ch == "\\":
                esc = True
            elif ch == quote:
                in_str = False
            continue
        if ch in "\"'":
            in_str, quote = True, ch
        elif ch in "([{":
            depth += 1
        elif ch in ")]}":
            depth -= 1
            if depth == 0:
                args.append(text[start:i])
                return [a.strip() for a in args]
        elif ch == "," and depth == 1:
            args.append(text[start:i])
            start = i + 1
    return []


def _helper_call_claims(text: str, extra_names=()) -> list:
    """The CLAIM (first argument) of every helper-style assertion call."""
    out = []
    extra = {n for n in extra_names if n}
    src = text or ""
    seen_spans = set()
    for m in _ASSERT_CALL_RE.finditer(src):
        name = m.group(1)
        open_idx = src.index("(", m.end() - 1)
        if open_idx in seen_spans:
            continue
        args = _split_top_level_args(src, open_idx)
        if not args or not args[0]:
            continue
        if len(args) < 2 and not _OP_RE.search(args[0]):
            # A one-argument call with no comparison in it is a plain
            # procedure call, not a claim about a value.
            continue
        seen_spans.add(open_idx)
        out.append(" ".join(args[0].split()))
    for name in sorted(extra):
        if _ASSERT_CALL_RE.match(f"{name}("):
            continue    # already covered by the shape pattern
        for m in re.finditer(r"^[ \t]*(?:if[ \t]+not[ \t]+)?"
                             + re.escape(name) + r"[ \t]*\(", src, re.MULTILINE):
            open_idx = src.index("(", m.end() - 1)
            if open_idx in seen_spans:
                continue
            args = _split_top_level_args(src, open_idx)
            if not args or not args[0]:
                continue
            seen_spans.add(open_idx)
            out.append(" ".join(args[0].split()))
    return out


def _helper_assert_names(src: str) -> set:
    """Locally-defined functions that behave as assertions: they branch on a
    parameter and then RECORD A FAILURE - append to a list, clear a boolean,
    raise, or exit nonzero. Structural, so it does not depend on the author
    picking a name this machine happens to know. Returns () on a source that
    will not parse; callers that only have a fragment use the shape pattern.
    """
    names = set()
    try:
        tree = ast.parse(src or "")
    except (SyntaxError, ValueError):
        return names
    for fn in ast.walk(tree):
        if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        params = [a.arg for a in fn.args.posonlyargs + fn.args.args
                  if a.arg not in ("self", "cls")]
        if not params:
            continue
        # A helper is SMALL. `_update_playing` (90 lines, an `if` mentioning
        # `self`, and a dozen list appends) satisfied the naive version of
        # this test and was reported as an assertion helper - measured on
        # mario_game.py. Two tighteners, both structural:
        #   * self/cls are not parameters for this purpose;
        #   * the If must test the parameter DIRECTLY - `if not cond:` /
        #     `if cond:` / `if cond <op> x:` - not merely mention it inside a
        #     larger expression, which is what any real method does.
        body_nodes = sum(1 for _ in ast.walk(fn))
        if body_nodes > 60:
            continue
        tests_a_param = False
        records_failure = False
        for n in ast.walk(fn):
            if isinstance(n, ast.If):
                t = n.test
                if isinstance(t, ast.UnaryOp) and isinstance(t.op, ast.Not):
                    t = t.operand
                if isinstance(t, ast.Name) and t.id in params:
                    tests_a_param = True
                elif isinstance(t, ast.Compare) and isinstance(t.left, ast.Name) \
                        and t.left.id in params:
                    tests_a_param = True
            if isinstance(n, ast.Assert):
                records_failure = True
            elif isinstance(n, ast.Raise):
                records_failure = True
            elif isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                    and n.func.attr == "append":
                records_failure = True
            elif isinstance(n, ast.Assign):
                for t2 in n.targets:
                    if isinstance(t2, ast.Name) and isinstance(n.value, ast.Constant) \
                            and n.value.value is False:
                        records_failure = True
        if tests_a_param and records_failure:
            names.add(fn.name)
    return names


def _assert_bodies(text: str, extra_names=()) -> list:
    """Every assertion CLAIM in `text` - `assert <claim>` statements and
    helper-style `check(<claim>, "msg")` calls alike - message stripped,
    whitespace normalised.

    V171 FIX 2: helper calls join the assert statements here. Everything
    downstream (the drop count, the operator-strength ranking, the tautology
    test, the threshold walk) works on claim strings and needed no change -
    it was only ever starved of input.
    """
    out = []
    for m in _ASSERT_RE.finditer(text or ""):
        body = m.group(1)
        # Drop the optional , "message" tail - only the CLAIM matters here.
        depth = 0
        cut = len(body)
        for i, ch in enumerate(body):
            if ch in "([{":
                depth += 1
            elif ch in ")]}":
                depth -= 1
            elif ch == "," and depth == 0:
                cut = i
                break
        out.append(" ".join(body[:cut].split()))
    out.extend(_helper_call_claims(text, extra_names))
    return out


def _ops_of(body: str) -> list:
    return [" ".join(m.group(1).split()) for m in _OP_RE.finditer(body)]


def _is_tautology(body: str) -> bool:
    """assert X == X - true by construction, so it can never fail."""
    for op in ("==", ">=", "<=", " is "):
        if op in body:
            left, _, right = body.partition(op)
            if left.strip() and left.strip() == right.strip():
                return True
    return False


def _relaxation_findings(old_str: str, new_str: str) -> list:
    """Ways `new_str` asserts LESS than `old_str` without dropping a call."""
    # V171 FIX 2: an edit large enough to carry the helper's own definition
    # (a whole-test-block rewrite, which is exactly the shape that dropped 8
    # assertions in the mario_game run) gets the structural name set too.
    helpers = _helper_assert_names(old_str) | _helper_assert_names(new_str)
    old_a = _assert_bodies(old_str, helpers)
    new_a = _assert_bodies(new_str, helpers)
    if not old_a:
        return []
    found = []

    if len(new_a) < len(old_a):
        found.append(f"the edit drops {len(old_a) - len(new_a)} assertion(s) "
                     f"({len(old_a)} -> {len(new_a)})")

    for old_body in old_a:
        # Pair each old assertion with the new one it most resembles, so the
        # comparison is the SAME claim before and after rather than two
        # unrelated lines that happen to sit near each other.
        best, best_r = None, 0.0
        for new_body in new_a:
            r = difflib.SequenceMatcher(None, old_body, new_body).ratio()
            if r > best_r:
                best, best_r = new_body, r
        if best is None or best_r < 0.55 or best == old_body:
            continue

        o_ops, n_ops = _ops_of(old_body), _ops_of(best)
        # V171 FIX 2: with helper calls now visible, similarity pairing has
        # far more candidates to choose from, and a 0.55 match was enough to
        # pair two DIFFERENT claims - `name in se.sounds` against
        # `se.sounds[name] is not None` - and report `in` -> `is not` as a
        # weakening when the edit had actually ADDED three checks. An
        # operator drop only means anything when the claim is otherwise the
        # SAME claim, so compare the two with their operators removed first.
        _strip = lambda b: " ".join(_OP_RE.sub(" ", b).split())
        same_claim = difflib.SequenceMatcher(
            None, _strip(old_body), _strip(best)).ratio() >= 0.85
        if same_claim:
            for o, n in zip(o_ops, n_ops):
                if _OP_STRENGTH.get(n, 9) < _OP_STRENGTH.get(o, 9):
                    found.append(f"`{o}` became `{n}` in: assert {best}")
                    break

        if _is_tautology(best) and not _is_tautology(old_body):
            found.append(f"now compares a value with itself, so it cannot "
                         f"fail: assert {best}")

        o_nums, n_nums = _NUM_RE.findall(old_body), _NUM_RE.findall(best)
        if len(o_nums) == len(n_nums) and o_nums != n_nums and o_ops:
            direction = o_ops[0]
            for a, b in zip(o_nums, n_nums):
                if a == b:
                    continue
                looser = ((direction in (">", ">=") and float(b) < float(a))
                          or (direction in ("<", "<=") and float(b) > float(a)))
                if looser:
                    found.append(f"the threshold moved from {a} to {b}, which "
                                 f"admits more values through `{direction}`")
                    break

    if ("try:" in (new_str or "")) and ("try:" not in (old_str or "")) and new_a:
        found.append("the assertions are now inside a try: block, where an "
                     "AssertionError can be caught instead of failing the run")

    seen, uniq = set(), []
    for f in found:
        if f not in seen:
            seen.add(f)
            uniq.append(f)
    return uniq


def test_edit_warning(old_str: str, new_str: str) -> str:
    """V45.8: warn when an edit to a FAILING test changes WHICH production
    call the test exercises.

    Run 3, step 8. The test was failing on collision->death. The edit replaced

        game.snake.body = [(goomba.col, goomba.row)] + body[1:]
        game._step()
        assert game.state == "dead" and game.lives < 3

    with

        initial_lives = game.lives
        game._die()
        assert game.state == "dead" and game.lives == initial_lives - 1

    and step 9 then added two more asserts. Assert counts went 1 -> 1 -> 3, so
    ANY count-based check reads that as MORE testing. It is not: the failing
    integration path was replaced by a direct call to the death function, and
    the shipped mario_snake_3.py asserts nothing about collision-death at all.
    The reflection then blamed the wrong side - "initial implementation had
    logic errors requiring targeted patches" - and stored success at 0.85.

    The detectable signal is call-target drift, not assert count. Warning only,
    never a block: same contract as the V28.1 swallow warning, which works
    precisely because it turns the thing itself into trajectory evidence.
    """
    # V171 FIX 2: THIS LINE WAS THE WHOLE GATE, and it read one keyword.
    # Every path below - the V45.8 call-drop block and the V61.1 relaxation
    # block alike - was unreachable for a suite that asserts through a helper.
    # Measured on the mario_game edits of 2026-08-04: the three edits that DID
    # warn contained the token only because the fragment happened to mention
    # `assert_in_range`; the edit that dropped three real checks and nothing
    # else (msg 108) returned here and said nothing. Gate on whether the edit
    # touches assertions IN ANY FORM, using the same detector the blocks below
    # already use, so the two can never disagree again.
    _helpers = _helper_assert_names(old_str) | _helper_assert_names(new_str)
    if not _assert_bodies(old_str, _helpers):
        return ""
    old_calls = {m.group(1) for m in _CALL_RE.finditer(old_str or "")}
    new_calls = {m.group(1) for m in _CALL_RE.finditer(new_str or "")}
    dropped = sorted((old_calls - new_calls) - _SCAFFOLD_CALLS)
    # V61.1: the call-drop block below is UNCHANGED and is still emitted
    # byte-for-byte when it is the only signal, so anything downstream that
    # matches on its wording keeps working. The relaxation block is additive.
    out = ""
    if dropped:
        names = ", ".join(f"{d}()" for d in dropped)
        out += (
            f"\n\n⚠️ {TEST_WEAKENED_MARK} - this edit follows a FAILED step, touches "
            f"assertions, and stops calling: {names}.\n"
            f"   If the test was failing BECAUSE {dropped[0]}() is broken, then "
            f"routing the test around it makes the run go green without fixing "
            f"anything, and the behaviour that failed ships UNTESTED. That is the "
            f"one edit this machine cannot tell apart from progress.\n"
            f"   Keep a check on the original path. If you genuinely cannot, say so "
            f"in your final summary and label that feature 'written but unverified' "
            f"- do not let it pass silently."
        )

    relaxed = _relaxation_findings(old_str, new_str)
    if relaxed:
        bullets = "".join(f"\n     - {r}" for r in relaxed)
        out += (
            f"\n\n⚠️ {TEST_WEAKENED_MARK} - this edit follows a FAILED step and "
            f"makes the assertion WEAKER instead of making the code correct:"
            f"{bullets}\n"
            f"   A test that was failing is evidence about the CODE. Loosening the "
            f"claim until the same broken behaviour satisfies it deletes the "
            f"evidence and changes nothing else - the run goes green and the "
            f"defect ships.\n"
            f"   Before you keep this edit, settle it with a command: does the "
            f"value the assertion was checking actually MOVE? Print it, run it, "
            f"read the number. If it does not move, the bug is in the code the "
            f"assertion was pointing at, not in the assertion.\n"
            f"   If the ORIGINAL assertion really was wrong, say why in your final "
            f"summary. Do not let a relaxation pass silently."
        )
    return out


def deliverable_split_warning(new_path: str, refused: list) -> str:
    """V45.8: warn when a new file is created after an overwrite refusal on a
    different file.

    Run 2: file_write on mario_snake.py was refused at steps 20 and 24; at step
    25 the model created mario_snake_game.py and finished there. The episode's
    root_cause cites mario_snake.py:500 and its verification cites
    mario_snake_game.py - one learning record spanning two artifacts, with a
    half-fixed original left in the workspace. The V30.7 spiral breaker fired
    on both refusals, but its prescribed exit was "str_replace one region at a
    time"; the model took an exit the machine does not model, which is rename.
    That run cost 33 steps and 908K tokens for a task run 1 finished in 4.
    """
    others = [b for b in refused if b and b != new_path]
    if not others:
        return ""
    first = others[0]
    return (
        f"\n\n⚠️ {DELIVERABLE_SPLIT_MARK} - you were refused an overwrite on "
        f"{', '.join(others)} earlier in this run, and have now created "
        f"{new_path}.\n"
        f"   If this is a rewrite of {first}, you have ABANDONED that file, not "
        f"repaired it. The broken original is still on disk and is still the "
        f"deliverable the task named; a differently-named copy is not a fix, and "
        f"whoever opens {first} afterwards gets the broken one.\n"
        f"   Go back to {first} and str_replace it one region at a time. If "
        f"{new_path} is genuinely a separate component rather than a rewrite, "
        f"say so explicitly in your final summary."
    )


# V45.2: SYNTAX GATE. The V44 fracture run wrote three commas where
# semicolons belonged and shipped a file that could not parse; the defect
# survived 77 iterations because nothing checked the artifact until a human
# opened a browser. This runs on EVERY write path, so a syntax error is
# reported in the tool result of the edit that caused it, with a line number.
SYNTAX_EXT = {".py", ".js", ".mjs", ".html", ".htm", ".json"}
# V45.7: file types the completion gate considers verifiable deliverables.
VERIFIABLE_EXT = (".py", ".js", ".mjs", ".html", ".htm", ".css",
                  ".json", ".ts", ".tsx", ".jsx")
_INLINE_SCRIPT_RE = re.compile(
    r"<script([^>]*)>(.*?)</script>", re.S | re.I)
_NON_JS_TYPE_RE = re.compile(
    r"""type\s*=\s*['"]([^'"]+)['"]""", re.I)
_NODE_OK = None  # tri-state cache: None = unprobed


def _node_available() -> bool:
    """Probe once per process. Never raises."""
    global _NODE_OK
    if _NODE_OK is None:
        try:
            subprocess.run(["node", "--version"], capture_output=True,
                           timeout=10, check=True)
            _NODE_OK = True
        except Exception:
            _NODE_OK = False
    return _NODE_OK


def _check_js(source: str, line_offset: int = 0):
    """Parse JS with `node --check`, reading stdin so nothing hits disk.
    Returns (line, message) on failure, None on success or if node is absent."""
    if not source.strip() or not _node_available():
        return None
    try:
        # V61.8: BYTES, not text=True.
        #
        # text=True makes the PARENT encode stdin with the locale codec. On
        # Windows that is cp1252, and one emoji in the source (\U0001f3ae in
        # the reported case) raised UnicodeEncodeError inside subprocess's
        # _writerthread. Three things then went wrong at once:
        #   1. The except below CANNOT catch it - it is raised on another
        #      thread, so threading.excepthook prints a traceback and
        #      subprocess.run returns as if nothing happened.
        #   2. node receives a TRUNCATED file, cut at the emoji, which leaves
        #      an unterminated string. Measured: a valid 902-line source cut
        #      that way makes node report "[stdin]:901" - a phantom syntax
        #      error on code that is perfectly fine, aimed at an innocent line.
        #   3. If nothing flushes at all, node --check on empty input exits 0,
        #      so a total delivery failure reads as a CLEAN BILL OF HEALTH.
        # V30.4's utf8_subprocess_env() does not help here: it configures what
        # the CHILD emits, and this is the parent's own encoder on the way in.
        # Encoding once, explicitly, means no codec is ever chosen for us.
        r = subprocess.run(["node", "--check"],
                           input=source.encode("utf-8", "replace"),
                           capture_output=True, timeout=30)
    except Exception:
        return None
    if r.returncode == 0:
        return None
    err = (r.stderr or r.stdout).decode("utf-8", "replace").strip()
    m = re.search(r"\[stdin\]:(\d+)", err)
    line = int(m.group(1)) + line_offset if m else None
    msg = next((ln.strip() for ln in err.split("\n")
                if re.match(r"^\w*(Error|Warning):", ln.strip())), err[:200])
    return (line, msg)


# ═══════════════════════════════════════════════════════════════════════
# V61.4: EVERYTHING I COULD NOT TEST ON YOUR HARDWARE IS OFF HERE.
#
# I have no Ollama, no GPU and no pygame loop in the sandbox I work in. Some
# of what I added to this machine was proven by executing it against your own
# uploaded artifacts; some of it was reasoned from documentation and never ran
# against your model even once. Those two kinds of change do not belong in a
# working system on the same terms, and shipping them as if they did was the
# mistake.
#
# So they are separated. Everything below is OFF. Turn ONE on, run your normal
# prompt, and compare. If it helps, keep it. If it does not, it costs you one
# edit to put it back. Nothing has been deleted from your file.
#
# WHAT IS STILL ON, because each was proven by execution against artifacts you
# uploaded, not by argument:
#   - V60.2 marker scoping. Reproduced on your real 409,058-char file_read of
#     source_code.md: it was recorded as a FAILURE and fired two phantom gates.
#   - V60.3 _safe_kill. asyncio Process.kill() after exit raises
#     ProcessLookupError - confirmed by running it.
#   - the timeout message. Your log shows a 1,820s gap while the message said
#     "900s"; the client's real limit is 1800s.
#   - assertion-relaxation warning. Reproduced on your real spongebob step-6
#     edit, where `assert score > 1234` became `>= 1234` on a score that
#     3,600 measured frames never move.
# V61.14: re-feed the model's own reasoning into the messages it sees.
# ON by default - unlike the EXPERIMENTAL block below, this is not an
# unverified Ollama wire option; it only changes the TEXT of an assistant
# turn, which is exercised by the V61.14 tests in this file. Set to False to
# get the pre-V61.14 behaviour (reasoning captured to the episode, discarded
# from context).
REFEED_THINKING = True

# V61.14a: NO PER-TURN TRUNCATION. The first cut of this shipped a flat
# 2000-char per-turn cap, which was a number picked from nothing and was
# wrong twice over, both measurable against the booby_game run this feature
# exists to fix:
#
#   1. SIZE. Per-turn reasoning there ran [1245, 40, 167, 867, 1122, 117,
#      258, 127, 819, 1813, 671, 509, 4995, 1170, 2732, 344, 7310] - 24,306
#      chars total. A 2000 cap truncates 3 of 17 turns and destroys 9,037
#      chars, 37% of the reasoning, in the exact run used to justify the
#      feature. At 8000 it destroys nothing; the snake run's largest turn is
#      2,052 and it destroys nothing there either.
#   2. DIRECTION. Truncating the HEAD keeps the throat-clearing and cuts the
#      conclusion. Measured on every block over 600 chars in that run, the
#      last operative decision phrase sits at 70-98% through the text - "The
#      cleanest fix is to directly set lives=0" is the LAST line of
#      iteration 11. A head-cut at 2000 removes precisely the sentence that
#      would have stopped the loop.
#
# So: no per-turn limit. The only real risk is a very long run spending the
# whole window on reasoning, and that is handled by a BUDGET below, sized as
# a fraction of the context window so it scales when num_ctx does rather
# than being a constant that goes stale. When the budget binds, WHOLE blocks
# are dropped from the OLDEST turns - recent reasoning is what stops the
# model re-deriving what it just decided - and a block is never cut in half.
# 0.5 of a 256K window is ~384,000 chars of reasoning; the observed runs
# produce 12K-24K, and 150K has been seen. This net is for the pathological
# case, not the normal one, and should essentially never fire.
#
# PREFIX CACHE: while the budget is unbound (the normal case) the bytes of
# turn N never change once appended, so V61.1's growing-list-behind-a-stable-
# prefix property holds exactly. If the budget ever DOES bind, dropping an
# old block rewrites that turn and invalidates the cache from there. The drop
# set only grows, so that costs one invalidation per drop event rather than
# oscillating - and a re-read prefix is a far cheaper failure than a window
# spent on reasoning with no room to work.
THINKING_REFEED_CHARS = 0          # per-turn cap; 0 = no limit
# V61.25: if this fraction of the thinking's words already appear in the
# turn's content, the fold is skipped - the model said it in the open
# already. Measured on real turns: 63% for the duplicate from the
# spongebob_shooter log, 24% for a turn that genuinely added an
# explanation, 6% for wholly new reasoning.
REASONING_DEDUP_RATIO = 0.55
REASONING_DEDUP_MIN_CHARS = 200    # below this, always fold: cheap, and
                                   # the riskiest place for a false match
THINKING_REFEED_CTX_FRACTION = 0.5  # reasoning may occupy up to this much of num_ctx
THINKING_REFEED_CHARS_PER_TOKEN = 3  # same 3-chars/token estimate sync_prompt_cache uses

EXPERIMENTAL = {
    # Ollama options. Reasoned from the API docs, NEVER exercised against
    # ornith-vision on your box. If a run started behaving differently after
    # V61.1, this is the first thing to suspect and it is why it is off.
    "ollama_keep_alive": False,   # pin the model in VRAM between turns
    "ollama_num_keep": False,     # protect the prompt head from context shift

    # V61.29: STREAM /api/chat instead of waiting for a whole reply.
    # This is the switch that makes a stall READABLE - see
    # OllamaClient._chat_stream. It does NOT cap output length: httpx
    # applies its read timeout BETWEEN CHUNKS, so a long generation runs
    # as long as it likes provided tokens keep arriving. Measured in a
    # sandbox against an NDJSON server: a 4.8s generation completes under
    # a 1.5s read timeout, while a stream that goes silent raises in 2.1s.
    # Ollama has supported streaming WITH tools on /api/chat since
    # ollama/ollama#10415 (May 2025). OFF until it is run against
    # ornith-vision on your box, per the rule for everything in here.
    "ollama_stream": True,
    # Cancel a stream the moment it is provably looping. OFF: by default
    # the loop watch RECORDS and does not act, because a legitimate
    # 18,000-token file_write of repetitive draw calls is exactly the
    # shape a naive detector would murder. Read STREAM LOOP WATCH lines
    # in the log first, then decide.
    "ollama_stream_loop_cancel": True,

    # (An "output_gate" key was here in the file I sent you and controlled
    # NOTHING - the watcher it was meant to gate lives in a build you never
    # took, so the switch was decoration. Removed rather than left to look
    # like a feature. If you want the workspace watcher, say so and it comes
    # back with real wiring behind it.)
}

# V61.5: DID THE THING YOU ARE CITING ACTUALLY FINISH?
#
# From the run of 2026-07-29 seed 2120226666: the final report said
# "Graphics verified - Screenshots captured for all states" and listed four
# PNGs as complete evidence. Its capture script was written to take fifteen
# captures and died on the fifth with
# "NameError: name 'collect_game' is not defined". Two more variable-name bugs
# were behind that one; with all three fixed the same script produces 19 of 19.
#
# The machine already KNEW. That bash call came back with a traceback and was
# recorded as a failure - one of 31 that run. Nothing connected "the last run
# of this script failed" to "the summary cites this script as proof".
#
# This is that connection, and it is deterministic: no model judges it, so it
# cannot confabulate either way. The machine records which scripts each bash
# command ran and how that run ended; at completion it reads the final answer
# and checks the citations against its own record.
_SCRIPT_RE = re.compile(r"[\w.\\/-]+\.(?:py|sh|ps1|bat|cmd|js|mjs|ts|rb|pl|lua)\b",
                        re.IGNORECASE)


def _command_executed(result_content: str) -> bool:
    """Did a bash result come from a command that actually RAN?

    V180. The bash tool refuses some commands before starting them - not in
    the allowlist, forbidden, an empty command, a path outside the sandbox -
    and every refusal is returned in the same channel as a real result. The
    script ledger, the claim check and anything else reading "how did the
    last run of X end" cannot tell those apart without this.

    Positive identification, not a blacklist of phrases: a command that ran
    always comes back with an exit code (or the timeout report, which is what
    the tool returns when it killed a process that WAS running). Anything
    else never started.
    """
    text = (result_content or "").strip()
    if not text:
        return False
    if re.search(r"Exit code:\s*-?\d+", text):
        return True
    # the tool's own timeout report - the process ran and was killed
    if "timed out" in text.lower() and "HINT:" in text:
        return True
    return False


def _scripts_named_in(text: str) -> set:
    """Basenames of runnable files mentioned anywhere in `text`."""
    return {re.split(r"[\\/]", m.group(0))[-1]
            for m in _SCRIPT_RE.finditer(text or "")}


_GATE_HITS = {}          # (path, line, msg) -> consecutive count
_QUOTE_RE = {q: re.compile(r"(?<!\\)" + re.escape(q)) for q in "\"'`"}


# V60.2: MARKER CONTAMINATION - the write gates below are recognised
# downstream by SUBSTRING SEARCH over the whole tool result, and a tool
# result is not always the machine talking: file_read returns a whole file,
# str_replace echoes up to 1,000,000 chars of file content on a miss, and
# bash can `type` anything. Reading a file that merely QUOTES these strings
# made the file impersonate the gate that emits them. Live sighting: a
# deliberate file_read of a copy of this machine's own source (6,959 lines,
# saved as source _code.md) fired TRUNCATED WRITE and GATE STALLED on
# iteration 1, before a single write had run.
#
# Two locks, and each is independently enough for the common case:
#   1. the marker text lives HERE, once, and both the emitter and every
#      consumer reference the same constant - so they cannot drift apart;
#   2. the constants keep their LEADING NEWLINES. A gate is APPENDED to a
#      result, so the real thing always arrives with the "\n\n" or "\n   "
#      in front of it. In a file that quotes this source the same characters
#      appear as the two-character escape "\" + "n" inside a string literal,
#      and in any numbered dump every line is prefixed - neither can produce
#      a real newline in front of the marker.
# Consumers add a third lock (tool-name scope) in Agent._machine_gate_signals.
MARK_TRUNCATED_WRITE = "\n\n🛑 TRUNCATED WRITE - "
MARK_SYNTAX_ERROR = "\n\n🛑 SYNTAX ERROR - THIS FILE CANNOT RUN. "
MARK_GATE_STALLED = "\n   ⛔ STOP. This is the SAME error at the SAME line for the "
# Every "HINT: " this machine emits starts its own line at column 0 and rides
# on a FAILED result. Both facts are asserted by the V60.2 suite.
HINT_LINE_RE = re.compile(r"(?m)^HINT: ")


def _looks_truncated(file_text: str, line: int) -> bool:
    """V45.6: an odd number of unescaped quotes on the offending line
    means the string literal never closes - i.e. the write was CUT OFF
    mid-generation, not mistyped. Completely different repair."""
    try:
        ln = file_text.split("\n")[line - 1]
    except Exception:
        return False
    return any(len(rx.findall(ln)) % 2 for rx in _QUOTE_RE.values())


def _gate_repeats(path: str, line, msg: str) -> int:
    """Count consecutive identical gate hits. A warning that has not
    worked twice will not work a third time by being repeated."""
    key = (str(path), line, (msg or "")[:80])
    for k in list(_GATE_HITS):
        if k != key:
            _GATE_HITS.pop(k, None)      # any new error resets the streak
    _GATE_HITS[key] = _GATE_HITS.get(key, 0) + 1
    return _GATE_HITS[key]


def syntax_warning(path: str, file_text: str) -> str:
    """Parse the file that was just written. '' when it parses.

    Never raises: a checker that explodes must not break the write it is
    checking. .py and .json cost nothing (stdlib). .js/.html shell out to
    node, ~50-80ms, and silently no-op if node is not installed."""
    p = str(path).lower()
    ext = p[p.rfind("."):] if "." in p else ""
    if ext not in SYNTAX_EXT:
        return ""

    hit = None
    try:
        if ext == ".py":
            try:
                compile(file_text, str(path), "exec")
            except SyntaxError as e:
                hit = (e.lineno, f"{type(e).__name__}: {e.msg}")
        elif ext == ".json":
            try:
                json.loads(file_text)
            except ValueError as e:
                hit = (getattr(e, "lineno", None), f"JSONDecodeError: {e}")
        elif ext in (".js", ".mjs"):
            hit = _check_js(file_text)
        else:  # .html / .htm - every inline <script> that is actually JS
            for m in _INLINE_SCRIPT_RE.finditer(file_text):
                attrs, body = m.group(1), m.group(2)
                if "src=" in attrs.lower():
                    continue
                t = _NON_JS_TYPE_RE.search(attrs)
                if t and "javascript" not in t.group(1).lower() \
                      and "module" not in t.group(1).lower():
                    continue  # <script type="text/template"> etc.
                hit = _check_js(body, file_text[:m.start(2)].count("\n"))
                if hit:
                    break
    except Exception:
        return ""  # a broken checker must never block a write

    if not hit:
        _GATE_HITS.clear()
        return ""
    line, msg = hit
    where = f"line {line}" if line else "an undetermined line"
    seen = _gate_repeats(path, line, msg)
    stuck = ""
    if seen >= 3:
        stuck = (
            MARK_GATE_STALLED
            + f"{seen}th write in a row. Whatever you have been doing is not "
            f"fixing it and repeating it will not start working. Change "
            f"approach NOW: delete the entire broken statement (from the "
            f"start of its line to the end of it) and re-issue it from "
            f"scratch in SMALLER pieces. Do not edit around it again."
        )
    if line and _looks_truncated(file_text, line):
        return (
            MARK_TRUNCATED_WRITE
            + f"{path} line {line} has an unclosed "
            f"string literal, so this file cannot run. Your content was CUT "
            f"OFF mid-generation; this is not a typo and the text you meant "
            f"to write does not exist on disk.\n"
            f"   DO NOT copy the truncated text into a new old_str or "
            f"new_str - that carries the truncation forward and fixes "
            f"nothing. DO NOT delete the lines after it; they are not the "
            f"problem, the unterminated string is swallowing them.\n"
            f"   Do ONE of these instead: (a) str_replace the truncated "
            f"TAIL with the complete remainder of the statement including "
            f"its closing quote, or (b) delete the whole partial statement "
            f"and re-issue it as SEVERAL smaller writes. If a block keeps "
            f"truncating, it is too large for one call - split it."
            + stuck
        )
    return (
        MARK_SYNTAX_ERROR
        + f"{msg} at {where} of "
        f"{path}. The write SUCCEEDED and the broken text is on disk now. "
        f"file_read around {where} and fix it with str_replace BEFORE anything "
        f"else - do not continue to the next block, do not run your verifier, "
        f"do not report progress. A file that does not parse fails 100% of its "
        f"features no matter what any structural check reports.\n"
        f"   DIAGNOSIS: the reported line is where the parser GAVE UP, not "
        f"necessarily where the mistake is. Read the 2-5 lines ABOVE it and "
        f"check how each one TERMINATES - a comma where a semicolon belongs, "
        f"or one stray bracket, produces exactly this error pointing at a line "
        f"that looks innocent. If two inspections of that region find nothing, "
        f"the region is not the problem: move UP, do not read it a third time."
        + stuck
    )


def _swallow_scopes(file_text: str):
    """[(line, stmts_covered, asserts_covered, exc_names)] for each handler
    that silently discards its exception.

    V61.18: the line number alone is not enough to act on. The snake_game run
    of 2026-08-01 emitted "2 silent exception swallower(s) at line(s) 268,
    524" on three consecutive edits and the model answered, reasonably:
    "swallower(s) are in cleanup/teardown paths (`_auto_quit` timer callback
    and `pygame.quit()` finally block)". That was HALF true, which is exactly
    why it stuck - 524 really is teardown. 512 was `except SystemExit: pass`
    wrapped around the ENTIRE test body, and because Game.run() ends by
    calling sys.exit(), it fired on the first scenario and skipped every
    assertion after it. The delivered artifact printed
    "passed_scenarios contains 0 items" and then "SELF-TEST OK".
    A warning that cannot tell those two apart invites the rationalisation.
    Counting what the try block CONTAINS can.
    """
    try:
        tree = ast.parse(file_text)
    except SyntaxError:
        return []
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Try):
            continue
        stmts = sum(1 for _ in ast.walk(node)) and len(node.body)
        asserts = sum(1 for n in ast.walk(node) if isinstance(n, ast.Assert)
                      and any(n is x or n in ast.walk(b) for b in node.body
                              for x in [b]))
        for h in node.handlers:
            body_is_pass = all(isinstance(s, ast.Pass) for s in h.body)
            if not body_is_pass:
                continue
            names = []
            t = h.type
            if isinstance(t, ast.Name):
                names = [t.id]
            elif isinstance(t, ast.Tuple):
                names = [e.id for e in t.elts if isinstance(e, ast.Name)]
            elif t is None:
                names = ["<bare except>"]
            if names and all(n in ("KeyboardInterrupt", "SystemExit")
                             for n in names) and asserts == 0:
                continue          # V61.9 benign, and it guards nothing
            out.append((h.lineno, stmts, asserts, names or ["Exception"]))
    return out


def input_test_findings(src: str):
    """[(line, message)] for input tests that CANNOT work, whatever the code does.

    V61.29. Two shapes, both observed, both mechanical, and both invisible to
    every existing gate because they surface as an ordinary AssertionError the
    model then spends iterations "fixing" in the wrong place.

    (A) POST-THEN-get_pressed. super_mario.py, 2026-08-03:
            pygame.event.post(pygame.Event(pygame.KEYDOWN, {'key': K_SPACE}))
            game.handle_input()          # reads pygame.key.get_pressed()
            assert game.state == 'playing'
        Posting to the event QUEUE never changes what get_pressed() returns.
        The assertion cannot pass, and the model burned iterations 27-30 on
        it. Contrast the snake_game run, where the same post() is followed by
        Game.run(), which reads pygame.event.get() - that pairing is correct
        and must not be flagged, so the check is on WHICH function the test
        calls, not on the presence of post().

    (B) A TEST THAT READS REAL KEY STATE. super_mario_bros.py, same run:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                game.handle_input()
            assert game.state == 'playing'
        Nothing is pressed during a headless test, so the guard is always
        False, the action never runs, and the assertion fails on a game that
        may be perfectly correct. A test must CONSTRUCT the input it wants -
        a dict, or a fake array like the make_keys() helper another run wrote
        - never sample the keyboard.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []

    def _reads_pressed(fn):
        for n in ast.walk(fn):
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                    and n.func.attr == "get_pressed"):
                return True
        return False

    pressed_fns = set()
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)) and _reads_pressed(fn):
            pressed_fns.add(fn.name)

    out = []
    test_scopes = [n for n in ast.walk(tree)
                   if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                   and "test" in n.name.lower()]
    # a bare `if "--test" in sys.argv:` block counts as the test too
    for n in ast.walk(tree):
        if isinstance(n, ast.If) and "--test" in ast.dump(n.test):
            test_scopes.append(n)

    for scope in test_scopes:
        posts = [n for n in ast.walk(scope)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                 and n.func.attr == "post"]
        for n in ast.walk(scope):
            if not (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)):
                continue
            if n.func.attr == "get_pressed":
                out.append((n.lineno,
                            "the test calls pygame.key.get_pressed() itself. "
                            "Nothing is pressed during a headless run, so every "
                            "key reads False and any branch on it is dead. "
                            "CONSTRUCT the input instead - a plain dict, or a "
                            "fake key array - and pass it in."))
            elif posts and n.func.attr in pressed_fns:
                out.append((n.lineno,
                            f"the test posts a key event and then calls "
                            f"{n.func.attr}(), which reads "
                            f"pygame.key.get_pressed(). Posting to the event "
                            f"QUEUE does not change get_pressed(), so this "
                            f"input never arrives. Either drive the loop that "
                            f"reads pygame.event.get(), or make the function "
                            f"take its key state as an argument the test can "
                            f"hand it."))
    return sorted(set(out))


def _incomplete_findings(src: str):
    """(undefined_names, stub_functions) - the two mechanical marks of a file
    that was written but not finished.

    V61.23. The spongebob run of 2026-08-01 produced a 21KB game whose very
    first frame would raise NameError on an undefined FPS, whose
    Background.update() was `pass`, and which contained no --test at all -
    and every gate in this file was silent, because they all fire on a
    PASSING self-test and there was no self-test to run. The machine's whole
    verification chain starts one step too late.
    Both checks are conservative, because a false positive here is expensive:
    it lands on the first write of every run.
      UNDEFINED: skipped entirely if the file uses `from x import *`, which
        makes the question undecidable. Builtins, imports, every binding
        form, comprehension targets, except-as, global/nonlocal and every
        argument name count as bound.
      STUBS: a `pass` body is normal in two legitimate shapes and both are
        suppressed. A BASE-CLASS CONTRACT - Entity.draw() is `pass` and
        Player(Entity).draw() is real, verified against super_mario.py where
        the naive check flagged all three of its stubs and every one was
        legitimate - and a deliberate test double, Fake*/Mock*/Null*/Dummy*.
        Name matching alone is not enough: Background.update() being `pass`
        while Player.update() is real is a genuine defect, and only the
        inheritance edge tells the two cases apart.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None, None

    star = any(isinstance(n, ast.ImportFrom) and any(a.name == "*" for a in n.names)
               for n in ast.walk(tree))
    undefined = []
    if not star:
        bound = set(dir(builtins))
        for n in ast.walk(tree):
            if isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
                bound.add(n.id)
            elif isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                bound.add(n.name)
            elif isinstance(n, (ast.Import, ast.ImportFrom)):
                for al in n.names:
                    bound.add((al.asname or al.name).split(".")[0])
            elif isinstance(n, ast.ExceptHandler) and n.name:
                bound.add(n.name)
            elif isinstance(n, (ast.Global, ast.Nonlocal)):
                bound.update(n.names)
            elif isinstance(n, ast.arg):
                bound.add(n.arg)
        seen = {}
        for n in ast.walk(tree):
            if (isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
                    and n.id not in bound):
                seen.setdefault(n.id, n.lineno)
        undefined = sorted(seen.items(), key=lambda kv: kv[1])

    # class -> its base class names, for the contract rule
    bases, real_methods = {}, {}
    for c in ast.walk(tree):
        if not isinstance(c, ast.ClassDef):
            continue
        bases[c.name] = {b.id for b in c.bases if isinstance(b, ast.Name)}
        for b in c.body:
            if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body = [x for x in b.body
                        if not (isinstance(x, ast.Expr)
                                and isinstance(x.value, ast.Constant)
                                and isinstance(x.value.value, str))]
                if body and not all(isinstance(x, ast.Pass) for x in body):
                    real_methods.setdefault(b.name, set()).add(c.name)

    def _overridden(owner, method):
        for sub in real_methods.get(method, ()):
            seen_c, stack = set(), [sub]
            while stack:                       # walk the inheritance chain up
                cur = stack.pop()
                if cur in seen_c:
                    continue
                seen_c.add(cur)
                if owner in bases.get(cur, ()):
                    return True
                stack.extend(bases.get(cur, ()))
        return False

    FAKE = ("fake", "mock", "null", "dummy", "stub", "noop")
    stubs = []
    for c in ast.walk(tree):
        owner = c.name if isinstance(c, ast.ClassDef) else ""
        members = c.body if isinstance(c, ast.ClassDef) else []
        if owner and any(k in owner.lower() for k in FAKE):
            continue
        for b in members:
            if not isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            body = [x for x in b.body
                    if not (isinstance(x, ast.Expr)
                            and isinstance(x.value, ast.Constant)
                            and isinstance(x.value.value, str))]
            empty = (not body) or all(
                isinstance(x, ast.Pass)
                or (isinstance(x, ast.Expr) and isinstance(x.value, ast.Constant)
                    and x.value.value is Ellipsis) for x in body)
            if empty and not _overridden(owner, b.name):
                stubs.append((f"{owner}.{b.name}" if owner else b.name, b.lineno))
    for b in tree.body:                        # module-level stub functions
        if isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef)):
            body = [x for x in b.body
                    if not (isinstance(x, ast.Expr)
                            and isinstance(x.value, ast.Constant)
                            and isinstance(x.value.value, str))]
            if (not body) or all(isinstance(x, ast.Pass) for x in body):
                stubs.append((b.name, b.lineno))
    return undefined, sorted(set(stubs), key=lambda kv: kv[1])


def _incomplete_text(path: str, file_text: str) -> str:
    """V61.23: the note appended when a .py file is written or edited.

    Reports what is UNFINISHED, and only then how much room is left. The
    size line is not a padding target and says so - measured, mario's first
    write was 66,960 characters in ONE call at 20,237 completion tokens, so
    spongebob's 21KB was a choice and not a ceiling and the model should
    know the budget exists. But what makes a file worth 100KB is implemented
    features, so findings come first and size appears only when something is
    actually missing.
    """
    if not str(path).lower().endswith(".py"):
        return ""
    try:
        undefined, stubs = _incomplete_findings(file_text)
    except Exception:
        return ""
    if undefined is None:
        return ""
    parts = []
    if undefined:
        names = ", ".join(f"`{n}` (line {ln})" for n, ln in undefined[:8])
        parts.append(
            f"\n\n\u26d4 {len(undefined)} NAME(S) USED BUT NEVER DEFINED: {names}"
            + (f" ... and {len(undefined) - 8} more" if len(undefined) > 8 else "")
            + "\n   This file raises NameError the moment that line runs. No "
              "test can pass around it.")
    if stubs:
        names = ", ".join(f"`{n}` (line {ln})" for n, ln in stubs[:8])
        parts.append(
            f"\n\n\u26a0 {len(stubs)} FUNCTION(S) WITH AN EMPTY BODY: {names}"
            + (f" ... and {len(stubs) - 8} more" if len(stubs) > 8 else "")
            + "\n   Base-class contracts and deliberate test doubles are NOT "
              "counted, so these are features you named and did not write.")
    try:
        for ln, msg in input_test_findings(file_text)[:4]:
            parts.append(f"\n\n\u26d4 UNTESTABLE INPUT at line {ln}: {msg}")
    except Exception:
        pass
    if "--test" not in file_text and "__main__" in file_text:
        parts.append(
            "\n\n\u26d4 THIS FILE HAS NO --test MODE. Every check this "
            "machine runs - coverage, assertion tracing, the mutation gate - "
            "starts from a passing self-test, so without one NOTHING here can "
            "tell you whether any feature works. Add it before adding more "
            "game.")
    if parts:
        parts.append(
            f"\n\n(For scale: this file is {len(file_text):,} characters. One "
            f"file_write on this machine has carried 66,960 characters in a "
            f"single call, so there is room - but only for implemented "
            f"features. Do not pad.)")
    return "".join(parts)


def swallow_warning(path: str, file_text: str) -> str:
    """Return a warning string if the written .py file contains silent
    exception swallowers, else ''. Appended to file_write / str_replace
    success messages - all write paths must use it (same-class rule).

    V30.2: includes LINE NUMBERS and a grep caveat. In the snake_game run
    the model did the right thing - warning fired, it immediately ran
    grep_search("except.*pass") - and got "No matches found", because the
    swallowers span two lines and grep is line-based. The machine's own
    warning and its own search tool contradicted each other, so the model
    reasonably dropped the lead. Give it the line numbers directly."""
    syn = syntax_warning(path, file_text)
    if not str(path).endswith(".py"):
        return syn
    hits = sorted(
        file_text[:m.start()].count("\n") + 1
        for rx in (SWALLOW_RE, SUPPRESS_RE)
        for m in rx.finditer(file_text)
        if not (rx is SWALLOW_RE and BENIGN_SWALLOW_RE.match(m.group(0)))
    )
    if not hits:
        return syn + _noop_assert_text(path, file_text)
    where = ", ".join(str(n) for n in hits[:25]) + (" ..." if len(hits) > 25 else "")
    return syn + (
        f"\n⚠ WARNING: {len(hits)} silent exception swallower(s) at line(s) {where} "
        f"(`except ...: pass` / suppress). Errors inside them are INVISIBLE to you and "
        f"to --test: a feature can die in there and the self-test still passes. "
        f"file_read those lines; print the exception or let it raise, and make your "
        f"--test assert the swallowed feature actually works. (They span two lines, "
        f"so a line-based grep_search for 'except.*pass' will find NOTHING - use "
        f"these line numbers instead.)"
    ) + _swallow_scope_text(file_text) + _noop_assert_text(path, file_text)


def _swallow_scope_text(file_text: str) -> str:
    """V61.18: name the swallowers that cover ASSERTIONS, separately."""
    try:
        scopes = _swallow_scopes(file_text)
    except Exception:
        return ""
    armed = [s for s in scopes if s[2] > 0]
    if not armed:
        return ""
    lines = []
    for ln, stmts, asserts, names in armed[:6]:
        lines.append(
            f"      line {ln}: `except {' / '.join(names)}: pass` sits on a try "
            f"block holding {stmts} statement(s) and {asserts} ASSERTION(S)")
    return (
        f"\n\n\u26d4 OF THOSE, {len(armed)} SWALLOW ASSERTIONS - not teardown:\n"
        + "\n".join(lines)
        + "\n   If ANY line in that try raises, every assertion below it is "
          "SKIPPED and the run continues to whatever prints your pass message. "
          "That is not a cleanup handler and it must not be dismissed as one. "
          "Note especially that Game/main loops which call sys.exit() raise "
          "SystemExit, so `except SystemExit: pass` around a test body ends the "
          "test at the first such call. Move the handler to cover ONLY the "
          "statement that legitimately raises, or assert afterwards that the "
          "scenarios actually ran."
    )


def _noop_assert_text(path: str, file_text: str) -> str:
    """V61.11: assertions that cannot fail, reported on every write path."""
    if not str(path).endswith(".py"):
        return ""
    found = noop_assert_findings(file_text)
    if not found:
        return ""
    lines = "; ".join(f"line {ln}: {why}" for ln, why in found[:8])
    return (
        f"\n\n\u26a0 WARNING: {len(found)} assertion(s) that CANNOT FAIL - {lines}"
        + (" ..." if len(found) > 8 else "")
        + ". An assertion with a constant test runs, prints its tick and proves "
          "NOTHING; the feature it is named after is untested. Assert on a value "
          "the code under test RETURNED or CHANGED, not on a literal."
    )


# V61.9: parse a swallower warning back out of a tool result, so the LOOP can
# tell whether the model is actually reducing them. Returns (count, lines) or
# None when the result carries no such warning.
_SWALLOW_ECHO_RE = re.compile(
    r"WARNING: (\d+) silent exception swallower\(s\) at line\(s\) ([^(]+)\("
)


def parse_swallow_warning(content: str):
    m = _SWALLOW_ECHO_RE.search(content or "")
    if not m:
        return None
    return int(m.group(1)), m.group(2).strip()


# ══════════════════════════════════════════════════════════════════════════
# V61.11: A PASSING --test IS NOT EVIDENCE UNTIL YOU KNOW WHAT IT RAN.
#
# horror_snake run of 2026-07-31, seed 352219103. `python horror_snake.py
# --test` printed 15 ticks and ALL TESTS PASSED, exit 0. _is_test_pass said
# True, the SELF-AWARENESS surface fired and told the model its success
# criterion was met and to write the summary. The episode stored
# outcome=success, confidence 0.85, grounded=True.
# The game was frozen. `move_timer += dt` accumulates SECONDS and was
# compared against move_interval=150 MILLISECONDS, so the snake took its
# first step after 4,500 frames - 2.5 minutes. Mutation testing afterwards:
# deleting the entire body of update(), removing wall collision, removing
# self-collision, removing food scoring, removing speed scaling - 7 of 7
# mutants SURVIVED that suite. It could not fail.
# The reason is measurable and was measurable at the time: --test never
# called update(), draw(), or handle_input(). 12 of the file's 24 functions
# never executed once. Six of the fifteen "tests" asserted on values the
# test itself had just assigned.
# BUILD_PROMPT already says "a feature your --test never touches is
# UNVERIFIED - do not claim it works". Nothing measured which features it
# touched. This does: it re-runs the same --test under sys.settrace and
# reports which functions defined in the file never executed.
# ══════════════════════════════════════════════════════════════════════════

_COVERAGE_TRACER = r"""
import sys, runpy, json, os
target = os.path.abspath(sys.argv[1])
hit = set()
lines = set()
# V61.19: line-level tracing, scoped to the artifact ONLY. The local tracer is
# returned exclusively for frames whose code object lives in the target file,
# so the cost is paid on the game's own lines and on nothing in pygame,
# runpy or the stdlib. Function-call coverage answers "did this run"; only
# line coverage can answer "did this ASSERTION run", which is the question
# that catches a test body skipped by an exception handler.
def _local(frame, event, arg):
    if event == "line":
        lines.add(frame.f_lineno)
    return _local
def _t(frame, event, arg):
    if event == "call":
        co = frame.f_code
        try:
            if os.path.abspath(co.co_filename) == target:
                hit.add(co.co_name)
                lines.add(frame.f_lineno)
                return _local
        except Exception:
            pass
    return None
sys.argv = [sys.argv[1]] + sys.argv[2:]
sys.settrace(_t)
code = 0
try:
    runpy.run_path(target, run_name="__main__")
except SystemExit as e:
    code = e.code if isinstance(e.code, int) else 0
except BaseException as e:
    code = 1
    sys.stderr.write("PROBE-ERR:%s: %s\n" % (type(e).__name__, e))
finally:
    sys.settrace(None)
sys.stderr.write("PROBE-JSON:" + json.dumps(
    {"hit": sorted(hit), "lines": sorted(lines), "code": code}) + "\n")
"""


def _assert_lines(src: str):
    """[(lineno, source_snippet)] for every assert inside a test function.

    V61.19: only asserts the author MEANT to run - ones inside a function
    whose name contains "test". An assert in library code that never fires is
    normal; an assert in run_test() that never fires is the test lying.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    text = src.splitlines()
    out = []
    # V171 FIX 2: a suite written with a collect-and-report helper has zero
    # ast.Assert nodes, so this returned [] for the whole mario_game file -
    # 128 real checks, none of them traceable. Helper CALLS count as
    # assertions here, and the helper's own body is excluded so its internal
    # bookkeeping is not reported as a test line.
    helpers = _helper_assert_names(src)
    # V171 FIX 2: "a function whose name contains test" missed the single
    # commonest shape this machine's own prompt asks for -
    # `def main(): if "--test" in sys.argv:` - so mario_game.py, 128 real
    # checks, traced as zero. A function that GUARDS ON the --test flag is a
    # test scope by construction, whatever it is called.
    def _is_test_scope(fn):
        if "test" in fn.name.lower():
            return True
        for n in ast.walk(fn):
            if isinstance(n, ast.If):
                seg = ast.dump(n.test)
                if "--test" in seg or "'--test'" in seg:
                    return True
                for c in ast.walk(n.test):
                    if isinstance(c, ast.Constant) and isinstance(c.value, str) \
                            and c.value in ("--test", "--selftest", "--self-test"):
                        return True
        return False

    for fn in ast.walk(tree):
        if not (isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
                and _is_test_scope(fn)):
            continue
        skip = {id(h) for h in ast.walk(fn)
                if isinstance(h, (ast.FunctionDef, ast.AsyncFunctionDef))
                and h.name in helpers}
        inner = set()
        for h in ast.walk(fn):
            if id(h) in skip:
                inner |= {id(x) for x in ast.walk(h)}
        for n in ast.walk(fn):
            if id(n) in inner:
                continue
            if isinstance(n, ast.Assert):
                ln = n.lineno
                snip = text[ln - 1].strip() if 0 < ln <= len(text) else ""
                out.append((ln, snip[:96]))
            elif (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                    and n.func.id in helpers and n.args):
                ln = n.lineno
                snip = text[ln - 1].strip() if 0 < ln <= len(text) else ""
                out.append((ln, snip[:96]))
    return sorted(set(out))


def _defined_callables(src: str, path: str):
    """(name, lineno) for every def/async def. None if the file will not parse."""
    try:
        tree = ast.parse(src, str(path))
    except SyntaxError:
        return None
    return [(n.name, n.lineno) for n in ast.walk(tree)
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]


class _Mutator(ast.NodeTransformer):
    """Apply exactly ONE mutation, at the target-th eligible node (post-order).

    Ported from VERITY's _Mutator with two changes that this machine needs:

      SKIP RANGES. VERITY assumes the verifier is a SEPARATE FILE from the
      code under test - it has a verifier_scope check for exactly that. Here
      the test lives INSIDE the artifact behind `--test`, so a naive
      whole-file pass mutates the test's own assertions. Measured on the
      snake_game run of 2026-08-01: 108 of 422 mutation points (26%) fall
      inside run_test. Those prove nothing about whether the test catches
      GAME bugs, and worse, mutating an assertion usually makes the test fail,
      which scores as "killed" and INFLATES the rate. Whole-file: 25%.
      Game-code only: 22%.

      NOTES. VERITY reports a survivor as "a planted bug survived". That is
      true and unusable. `ast.unparse` re-renders the entire file, so the
      mutant cannot be diffed against the original to find what changed - the
      node has to say so at visit time, off the ORIGINAL tree, where the line
      numbers are still real. "line 231: score += 10 -> score -= 10" is an
      argument. "a planted bug survived" is a complaint.
    """
    _CMP = {ast.Lt: ast.GtE, ast.GtE: ast.Lt, ast.Gt: ast.LtE, ast.LtE: ast.Gt,
            ast.Eq: ast.NotEq, ast.NotEq: ast.Eq,
            ast.In: ast.NotIn, ast.NotIn: ast.In,
            ast.Is: ast.IsNot, ast.IsNot: ast.Is}
    _BIN = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Div,
            ast.Div: ast.Mult, ast.FloorDiv: ast.Mult, ast.Mod: ast.Mult,
            ast.Pow: ast.Mult}
    _BOOL = {ast.And: ast.Or, ast.Or: ast.And}
    _NAMES = {ast.Lt: "<", ast.GtE: ">=", ast.Gt: ">", ast.LtE: "<=",
              ast.Eq: "==", ast.NotEq: "!=", ast.In: "in", ast.NotIn: "not in",
              ast.Is: "is", ast.IsNot: "is not", ast.Add: "+", ast.Sub: "-",
              ast.Mult: "*", ast.Div: "/", ast.FloorDiv: "//", ast.Mod: "%",
              ast.Pow: "**", ast.And: "and", ast.Or: "or"}

    def __init__(self, target: int, skip=()):
        self.target = target
        self.idx = -1
        self.applied = False
        self.skip = tuple(skip)
        self.note = ""
        self.kind = ""
        self.func = ""
        self._fn_stack = []

    def visit_FunctionDef(self, node):
        self._fn_stack.append(node.name)
        self.generic_visit(node)
        self._fn_stack.pop()
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

    def _eligible(self, node) -> bool:
        ln = getattr(node, "lineno", 0)
        return not any(lo <= ln <= hi for lo, hi in self.skip)

    def _hit(self, node, desc: str, kind: str = "") -> bool:
        if not self._eligible(node):
            return False
        self.idx += 1
        if self.idx == self.target:
            fn = self._fn_stack[-1] if self._fn_stack else ""
            self.kind = kind
            self.func = fn
            where = f" in {fn}()" if fn else ""
            self.note = f"line {getattr(node, 'lineno', 0)}{where}: {desc}"
            return True
        return False

    def _n(self, op) -> str:
        return self._NAMES.get(type(op), type(op).__name__)

    def visit_Compare(self, node):
        self.generic_visit(node)
        if node.ops and type(node.ops[0]) in self._CMP:
            new = self._CMP[type(node.ops[0])]
            if self._hit(node, f"`{self._n(node.ops[0])}` -> `{self._n(new())}`", "compare"):
                node.ops[0] = new()
                self.applied = True
        return node

    def visit_BinOp(self, node):
        self.generic_visit(node)
        if type(node.op) in self._BIN:
            new = self._BIN[type(node.op)]
            if self._hit(node, f"`{self._n(node.op)}` -> `{self._n(new())}`", "arith"):
                node.op = new()
                self.applied = True
        return node

    def visit_BoolOp(self, node):
        self.generic_visit(node)
        if type(node.op) in self._BOOL:
            new = self._BOOL[type(node.op)]
            if self._hit(node, f"`{self._n(node.op)}` -> `{self._n(new())}`", "bool"):
                node.op = new()
                self.applied = True
        return node

    def visit_UnaryOp(self, node):
        self.generic_visit(node)
        if isinstance(node.op, (ast.Not, ast.USub)):
            kind = "not" if isinstance(node.op, ast.Not) else "unary -"
            if self._hit(node, f"dropped `{kind}`", "unary"):
                self.applied = True
                return node.operand
        return node

    def visit_Constant(self, node):
        if isinstance(node.value, bool):
            if self._hit(node, f"`{node.value}` -> `{not node.value}`", "bool"):
                node.value = not node.value
                self.applied = True
        elif isinstance(node.value, (int, float)):
            if self._hit(node, f"`{node.value}` -> `{node.value + 1}`", "const"):
                node.value = node.value + 1
                self.applied = True
        return node


def _test_line_ranges(src: str):
    """Line spans of the artifact's OWN test code, to be left unmutated."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    out = []
    for n in ast.walk(tree):
        if (isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and "test" in n.name.lower()):
            out.append((n.lineno, n.end_lineno or n.lineno))
    return out


def _mutation_points(src: str, skip=()) -> int:
    m = _Mutator(target=-1, skip=skip)
    try:
        m.visit(ast.parse(src))
    except SyntaxError:
        return 0
    return m.idx + 1


def _make_mutant(src: str, target: int, skip=()):
    """(mutant_source, {note, kind, func}) or (None, None)."""
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return None, None
    m = _Mutator(target, skip=skip)
    tree = m.visit(tree)
    if not m.applied:
        return None, None
    ast.fix_missing_locations(tree)
    try:
        new_src = ast.unparse(tree)
    except Exception:
        return None, None
    if new_src == src:
        return None, None
    return new_src, {"note": m.note, "kind": m.kind, "func": m.func}


def _mutation_backup_path(path):
    return str(path) + ".mutbak"


def _restore_stray_mutant(path):
    """If a previous gate run was KILLED mid-mutation, put the file back.

    V61.17b: the `finally` inside run_mutation_gate covers exceptions. It does
    NOT cover the process dying - Ctrl-C, a supervisor timeout, an OOM kill, a
    closed terminal. Reproduced for real: a 40-mutant run on a 6.7s self-test
    exceeded a sandbox timeout, python was killed, and the artifact was left
    as `ast.unparse` output - every comment stripped, every string requoted,
    one operator inverted. Silent destruction of the user's file by the tool
    that was supposed to be measuring it, and the only reason it was caught is
    that the next --test failed on a line that should have passed.
    So the original is written to disk BEFORE the first mutation and this runs
    at the START of every gate, recovering whatever the last kill left behind.
    """
    bak = _mutation_backup_path(path)
    try:
        if os.path.exists(bak):
            data = open(bak, encoding="utf-8", errors="replace",
                        newline="").read()
            if data:
                open(path, "w", encoding="utf-8", newline="").write(data)
                debug_print(f"MUTATION GATE: recovered {os.path.basename(path)} "
                            f"from {os.path.basename(bak)} - a previous run was "
                            f"killed mid-mutation")
            os.unlink(bak)
            return True
    except Exception as e:
        debug_print(f"could not recover stray mutant: {e}")
    return False


def has_plain_entry(src: str) -> bool:
    """True if the file has an `if __name__ == "__main__"` block that does
    something OTHER than run its own test flag - i.e. a real entry point a
    person would invoke."""
    try:
        tree = ast.parse(src or "")
    except (SyntaxError, ValueError):
        return False
    for n in ast.walk(tree):
        if not isinstance(n, ast.If):
            continue
        d = ast.dump(n.test)
        if "__name__" not in d or "__main__" not in d:
            continue
        body = ast.dump(ast.Module(body=n.body, type_ignores=[]))
        # a block that ONLY dispatches on a test flag is not a plain entry
        if "'--test'" in body or '"--test"' in body:
            for sub in n.body:
                if isinstance(sub, ast.If):
                    sd = ast.dump(sub)
                    if "--test" in sd and (sub.orelse or len(n.body) > 1):
                        return True
            continue
        # nor is a block whose every call is to something named *test* -
        # `if __name__ == "__main__": _test()` means running it plainly IS
        # running the test, so starting it proves nothing new. Caught by A3.
        calls = [c for c in ast.walk(n) if isinstance(c, ast.Call)]
        if calls:
            names = []
            for c in calls:
                if isinstance(c.func, ast.Name):
                    names.append(c.func.id.lower())
                elif isinstance(c.func, ast.Attribute):
                    names.append(c.func.attr.lower())
            if names and all("test" in nm for nm in names):
                continue
        return True
    return False


def entry_point_smoke(path: str, cwd: str = None, timeout_s: int = 8) -> dict:
    """Start the program the way a person starts it, briefly, and report.

    V179. THE MACHINE HAS BEEN VERIFYING A PATH NOBODY RUNS.

    Measured across three consecutive runs (mario 2026-08-05, snake
    2026-08-06 02:22, snake 2026-08-06 03:59) the shipped artifact raised
    AttributeError on the FIRST FRAME of real play while its self-test
    printed every tick and exited 0. In the last of those: 41 bash calls,
    41 of them `snake_game.py --test`, and ZERO that ran the program the way
    a person runs it.

    Worse, the machine caused it. The coverage probe correctly reported that
    handle_input() never ran. The model satisfied that by building a dict
    fixture and then REWRITING THE WORKING PRODUCTION CODE to fit the
    fixture - `keys[pygame.K_UP]`, which is what pygame actually hands it,
    became `keys.get(pygame.K_UP, False)`, which only a dict supports. The
    edit is at message 34 of that run, 17 messages after the probe. Coverage
    asks "did this function execute"; a fake makes that true without making
    the program work.

    The one question no fixture can fake is whether the program STARTS.
    Interpreting the result:
      timed out  -> it started and is still running. For anything with a main
                    loop that IS the pass, and it is why the timeout is short.
      exited 0   -> it ran to completion. Fine.
      exited !=0 -> it died. That is the finding, with the traceback.
    Bounded, killed on timeout, and it never touches the file - so unlike
    every other gate here it cannot influence what the model writes, only
    report what already happens.
    """
    out = {"ran": False, "crashed": False, "timed_out": False,
           "returncode": None, "error": "", "seconds": 0.0}
    if not os.path.exists(path):
        return out
    started = time.time()
    proc = None
    try:
        proc = subprocess.Popen(
            [sys.executable, os.path.basename(path)],
            cwd=cwd or os.path.dirname(path) or ".",
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            env=utf8_subprocess_env())
        try:
            _o, _e = proc.communicate(timeout=timeout_s)
            out["returncode"] = proc.returncode
            out["ran"] = True
            if proc.returncode != 0:
                out["crashed"] = True
                tail = (_e or b"").decode("utf-8", "replace").strip().splitlines()
                out["error"] = "\n".join(tail[-12:])
        except subprocess.TimeoutExpired:
            out["ran"] = True
            out["timed_out"] = True
    except Exception as e:
        out["error"] = f"could not start it: {e}"
    finally:
        if proc and proc.poll() is None:
            try:
                proc.kill()
                proc.wait(timeout=5)
            except Exception:
                pass
        out["seconds"] = round(time.time() - started, 1)
    return out


def run_mutation_gate(path, cwd=None, max_mutants: int = 40,
                      timeout: int = 60, budget_s: int = 180, round_no: int = 0):
    """Plant one bug at a time in `path`; check the artifact's --test catches it.

    Returns {'killed','tested','rate','survivors','skipped_test_region'} or
    None when the gate cannot run (no --test, syntax error, baseline already
    failing, nothing to mutate).

    ALWAYS restores the original file, in a finally, on every path - a gate
    that can leave a mutant on disk is worse than no gate. NEVER raises.

    V172 - THE SAMPLE IS NOT THE SAME BETWEEN ROUNDS. This docstring used to
    say "Deterministic sampling so two runs of the same artifact score the
    same", which stopped being true at V61.21 when the shuffle seed became
    `1234 + 7919*round_no` on purpose. Measured on the 2026-08-05 artifact,
    byte-identical file, six rounds: 8%, 20%, 10%, 8%, 22%, 5%. The sampling
    is deterministic GIVEN round_no; it is not comparable ACROSS round_no,
    and callers must treat the rate as a sample, not a score. `file_md5` is
    returned so a caller can tell "the artifact changed" from "I drew
    different bugs".
    """
    original = None
    try:
        path = str(path)
        if not path.lower().endswith(".py") or not os.path.exists(path):
            return None
        _restore_stray_mutant(path)          # V61.17b, before we read it
        original = open(path, encoding="utf-8", errors="replace",
                        newline="").read()
        if "--test" not in original:
            return None
        skip = _test_line_ranges(original)
        n = _mutation_points(original, skip)
        if not n:
            return None

        wd = cwd or os.path.dirname(os.path.abspath(path)) or "."
        base = os.path.basename(path)
        env = utf8_subprocess_env()
        env["SDL_VIDEODRIVER"] = "dummy"
        env["SDL_AUDIODRIVER"] = "dummy"

        def verifier_passes():
            r = subprocess.run([sys.executable, base, "--test"],
                               capture_output=True, timeout=timeout,
                               env=env, cwd=wd)
            return r.returncode == 0

        # V61.17a: MEASURE THE VERIFIER BEFORE MEASURING WITH IT. A single
        # baseline run cannot tell a passing test from a flaky one, and a
        # flaky test scores mutants as "killed" FOR FREE - the test failed on
        # its own, not because of the planted bug. Measured on booby_game.py:
        # its --test passes 6 runs in 10 with no changes whatsoever, and its
        # kill rate wandered 35%/38%/40%/42% across identical invocations. The
        # rate was partly measuring its own noise. It also produced a spurious
        # None on one run, which was this check working correctly by accident.
        # A non-deterministic self-test is a WORSE defect than a weak one -
        # a weak test is silent about bugs, a flaky one is silent at random
        # and teaches the model to re-run until green - so it is reported
        # instead of a kill rate, not alongside it.
        t_base = time.time()
        baseline = sum(1 for _ in range(BASELINE_RUNS) if verifier_passes())
        per_run = (time.time() - t_base) / max(1, BASELINE_RUNS)
        if baseline == 0:
            # V61.27: this returned None and the caller did nothing, so the
            # ENTIRE mutation check vanished without a word to the model.
            # mario_game 2026-08-03: one debug line, no measurement, and the
            # run closed at confidence 0.95. V61.13 taught exactly this for
            # the coverage probe - abstain, but SAY SO - and I did not carry
            # it across. A distinct result, so the caller can tell "the test
            # does not pass under me" from "nothing to mutate".
            debug_print("MUTATION GATE: baseline --test does not pass; "
                        "cannot measure")
            return {"unrunnable": True, "baseline": 0,
                    "baseline_runs": BASELINE_RUNS, "killed": 0, "tested": 0,
                    "rate": 0.0, "survivors": [], "asserts_never": [],
                    "skipped_test_region": bool(skip)}
        if baseline < BASELINE_RUNS:
            debug_print(f"MUTATION GATE: verifier is FLAKY "
                        f"({baseline}/{BASELINE_RUNS} baseline runs passed)")
            return {"flaky": True, "baseline": baseline,
                    "baseline_runs": BASELINE_RUNS, "killed": 0, "tested": 0,
                    "rate": 0.0, "survivors": [],
                    "skipped_test_region": bool(skip)}

        # V61.17b: size the sample to the MEASURED cost of one run instead of
        # assuming 40 fit. snake_game's self-test went from 0.2s to 6.7s the
        # moment it started driving the real Game.run() through
        # clock.tick(FPS) - correct, and 33x slower - so a fixed 40 blew the
        # budget and got the run killed. Whatever fits, honestly reported.
        affordable = max(4, int(budget_s / max(0.05, per_run)))
        planned = min(max_mutants, affordable)
        if planned < max_mutants:
            debug_print(f"MUTATION GATE: self-test takes {per_run:.1f}s, so "
                        f"{planned} mutants fit in {budget_s}s (asked for "
                        f"{max_mutants}). A slow self-test buys a weaker "
                        f"measurement.")
        # V61.21: A DIFFERENT SAMPLE EVERY ROUND. The seed was fixed at 1234,
        # so round 2 replanted the SAME 40 bugs round 1 had just been shown -
        # which makes writing an assertion about those exact lines a winning
        # move. On the super_mario run of 2026-08-01 the model took it: 16
        # assertions in its test cite a planted mutation by line number and
        # operator ("Player width should be 32 but got 8 - line 794 mutation
        # (* -> /)"). The rate went 5% -> 18% and the test got no better; one
        # of those assertions is what the delivered artifact finally died on.
        # Re-seeding per round means an assertion aimed at this round's sample
        # buys nothing next round, so gaming costs more than fixing.
        targets = list(range(n))
        random.Random(1234 + 7919 * int(round_no)).shuffle(targets)
        # write the safety copy BEFORE the first mutation touches the file
        bak = _mutation_backup_path(path)
        try:
            open(bak, "w", encoding="utf-8", newline="").write(original)
        except Exception as e:
            debug_print(f"MUTATION GATE: cannot write {bak} ({e}); "
                        f"refusing to mutate without a recovery copy")
            return None
        killed = tested = 0
        survivors = []
        started = time.time()
        # V173: STRATIFIED. The old loop walked the shuffled list once and
        # took whatever came, which on a game means the sample is mostly
        # sprite and level-generation code - 28 of 37 survivors on the
        # 2026-08-05 artifact. Each of those costs a full self-test run to
        # learn something the model cannot act on. Logic is sampled FIRST to
        # the size the floor is judged at; a fifth of the budget is then
        # deliberately spent on presentation so the class stays visible; and
        # anything left over goes back to logic.
        by_class = {"logic": [0, 0], "presentation": [0, 0]}   # [killed, tested]
        seen_class = {}          # target -> 'logic' | 'presentation' | 'dead'
        pres_quota = max(2, int(round(planned * MUTATION_PRESENTATION_SHARE)))

        def _score_pass(want, limit):
            """Test targets of class `want` until `tested` reaches `limit`."""
            nonlocal killed, tested
            for t in targets:
                if tested >= limit or tested >= planned:
                    return
                if time.time() - started > budget_s:
                    return
                known = seen_class.get(t)
                if known == "dead" or (known is not None and known != want):
                    continue
                mutant, meta = _make_mutant(original, t, skip)
                if mutant is None:
                    seen_class[t] = "dead"
                    continue
                cls = _mutation_class(meta.get("func"))
                seen_class[t] = cls
                if cls != want:
                    continue        # costs one parse, saves one test run
                try:
                    open(path, "w", encoding="utf-8", newline="").write(mutant)
                    _purge_pycache(wd)
                    survived = verifier_passes()
                except Exception:
                    continue
                finally:
                    open(path, "w", encoding="utf-8", newline="").write(original)
                    _purge_pycache(wd)
                tested += 1
                by_class[cls][1] += 1
                if survived:
                    meta["mclass"] = cls
                    survivors.append(meta)
                else:
                    killed += 1
                    by_class[cls][0] += 1

        _score_pass("logic", planned - pres_quota)
        _score_pass("presentation", planned)
        _score_pass("logic", planned)          # fill if presentation ran short
        if not tested:
            return None
        # V61.17c: TWO DIFFERENT DEFECTS WEAR THE SAME SURVIVOR. A bug that
        # survives in a function the test NEVER CALLS means the test misses a
        # code path. A bug that survives in a function the test DOES call
        # means the path is exercised and the ASSERTION is too weak. Those
        # need opposite fixes, and the first version of this gate gave the
        # first answer to both. Measured: after the gate told snake_game to
        # stop transcribing Game.run() and call it, the model did exactly
        # that - coverage went to 21/21, every function executing - and the
        # survivors simply moved to check_collision(), spawn() and
        # draw_snake(), all of which the test now calls. Repeating "your test
        # re-implements the logic" there is advice already followed, which is
        # the V61.9 failure mode: a warning the model cannot act on teaches it
        # the whole channel is noise.
        ran = None
        skipped_asserts = []
        assert_total = 0
        gaming = _gaming_findings(original)
        try:
            cov = test_coverage_probe(path, wd)
            if cov and not cov.get("exit"):
                never = {n for n, _ in cov["never"]}
                ran = {m.get("func") for m in survivors} - never
                skipped_asserts = cov.get("asserts_never") or []
                assert_total = cov.get("asserts_total") or 0
        except Exception:
            ran = None
        # Rank survivors by how hard they are to wave away. V61.9's rule is
        # that a warning the model can dismiss teaches it the whole channel is
        # noise, and a raw survivor list is FULL of dismissible entries: on
        # snake_game the first six were `255 -> 256` in a colour tuple and
        # `2 -> 3` in a circle radius. Those are draw constants and no sane
        # test should catch them. The damning ones - scoring, growth, death,
        # respawn - are control flow inside real logic. So: control flow
        # before constants, and non-rendering functions before draw/render.
        # V173: the private _RENDER tuple that used to live here is now
        # _DRAW_MARKERS/_ASSET_MARKERS at module scope, because the sampler and
        # scorer need the same definition and a second copy would fork.
        def _weight(m):
            render = _mutation_class(m.get("func")) == "presentation"
            kind = m.get("kind") or ""
            return (render,                                  # drawing last
                    kind == "const",                         # constants last
                    0 if kind in ("compare", "bool") else 1) # control flow first
        survivors.sort(key=_weight)
        _lk, _lt = by_class["logic"]
        _pk, _pt = by_class["presentation"]
        return {"killed": killed, "tested": tested,
                "rate": killed / tested,
                # V173: the two numbers that mean different things. `rate` is
                # kept as the blend so anything reading it still works, but
                # the floor is judged on logic_rate - see the block above
                # _mutation_class for why the blend is not a target.
                "logic_killed": _lk, "logic_tested": _lt,
                "logic_rate": (_lk / _lt) if _lt else 0.0,
                "presentation_killed": _pk, "presentation_tested": _pt,
                "presentation_rate": (_pk / _pt) if _pt else 0.0,
                # V172: the identity of what was measured. Three rounds of
                # the 2026-08-05 mario run scored 10% / 20% / 10% with ZERO
                # successful edits between them - the file was byte-identical
                # and the gate reported a 2x swing, then accused the model of
                # a regression "before that edit". The caller now has the one
                # fact that settles it.
                "file_md5": hashlib.md5(original.encode("utf-8",
                                                        "replace")).hexdigest(),
                "survivors": [m["note"] for m in survivors],
                "skipped_test_region": bool(skip),
                "seconds_per_run": round(per_run, 2),
                "survivors_in_called_fns": [
                    m["note"] for m in survivors
                    if ran is not None and m.get("func") in ran],
                "survivors_in_dead_fns": [
                    m["note"] for m in survivors
                    if ran is not None and m.get("func") and m["func"] not in ran],
                "asserts_total": assert_total,
                "asserts_never": skipped_asserts,
                "gaming": gaming,
                "probe_failed": ran is None}
    except Exception as e:
        debug_print(f"mutation gate failed: {e}")
        return None
    finally:
        # belt and braces: if anything above escaped, the file goes back.
        try:
            if original is not None and os.path.exists(path):
                if open(path, encoding="utf-8", errors="replace",
                        newline="").read() != original:
                    open(path, "w", encoding="utf-8",
                         newline="").write(original)
                    debug_print("MUTATION GATE: restored original after an "
                                "unexpected exit")
            # the recovery copy has done its job; leaving it would make the
            # NEXT run think a kill happened and overwrite a legitimate edit.
            b = _mutation_backup_path(path)
            if os.path.exists(b):
                os.unlink(b)
        except Exception:
            pass


def _purge_pycache(wd):
    """Stale bytecode would let a mutant test its own cached predecessor."""
    try:
        for root, dirs, _ in os.walk(wd):
            for d in list(dirs):
                if d == "__pycache__":
                    shutil.rmtree(os.path.join(root, d), ignore_errors=True)
                    dirs.remove(d)
    except Exception:
        pass


def _mutation_scored(mut):
    """(rate, killed, tested, label) - the number the floor is judged on.

    V173. Prefer the LOGIC sample; fall back to the blend when the logic
    sample is too small to act on, and say which one it is either way so a
    reader of the message is never guessing.
    """
    if not mut:
        return 0.0, 0, 0, "logic"
    lt = int(mut.get("logic_tested") or 0)
    if lt >= MUTATION_MIN_LOGIC_SAMPLE:
        return (float(mut.get("logic_rate") or 0.0),
                int(mut.get("logic_killed") or 0), lt, "logic")
    return (float(mut.get("rate") or 0.0), int(mut.get("killed") or 0),
            int(mut.get("tested") or 0), "all")


def _mutation_noise_band(prev, cur) -> float:
    """2-sigma band on the DIFFERENCE of two independent kill-rate samples.

    V172. Each round scores `tested` mutants drawn at random from a few
    hundred mutation points, so the rate is a binomial proportion and the
    difference of two rounds carries the error of both. Measured against the
    real artifact of 2026-08-05, byte-identical file, six rounds:

        8%, 20%, 10%, 8%, 22%, 5%      (spread 5-22%, a 4.4x swing)

    Three of the five consecutive transitions in that series cross the old
    +/-5 point threshold, so on an UNCHANGED file the comparator would have
    cried regression or improvement three times out of five. It did exactly
    that on his run and the model believed it.

    se = sqrt(p(1-p)/n) per round; the difference adds the variances. At
    n=40 and p~0.13 that is about 11 points, which correctly swallows the
    20%->10% "regression" that ended that run.
    """
    out = 0.0
    for m in (prev, cur):
        # V173: band the sample the VERDICT is about. Judging the logic rate
        # against a band computed from the blended n would understate the
        # wobble, because the logic sample is the smaller of the two.
        rate, _k, n, _lbl = _mutation_scored(m)
        n = max(int(n), 1)
        pr = min(max(float(rate), 0.0), 1.0)
        out += pr * (1.0 - pr) / n
    return 2.0 * (out ** 0.5)


def _mutation_progress(prev, cur, fires, edits_between=None):
    """(verdict_text, is_last_round) comparing this measurement to the last.

    V61.18. The three outcomes need three different things said, and saying
    the wrong one is how a warning channel dies:
      REGRESSION - the change made the test blinder. Name both numbers; the
        model cannot see this on its own because its test still prints OK.
      IMPROVED   - say so, and keep going.
      FLAT       - the move did not work; repeating it will not work either,
        so this becomes the last round.

    V172 - TWO WAYS THIS WAS SAYING THINGS THAT WERE NOT TRUE, both proven
    on the mario run of 2026-08-05:

    (1) IT ATTRIBUTED THE DELTA TO AN EDIT THAT NEVER HAPPENED. Rounds 1, 2
        and 3 fired at three consecutive completion attempts with ZERO
        successful edits between them - the file was byte-identical, checked
        against the trajectory. Round 3 nonetheless told the model
        "THIS IS WORSE THAN BEFORE YOUR LAST CHANGE ... 20% before that edit
        and 10% now", and named a cause: a `try` wrapped around the whole
        test body. There was no such try/except - the file's only handler is
        `except KeyboardInterrupt`, which the model's own grep confirmed. It
        spent its last ~15 iterations hunting that phantom, stalled twice in
        degenerate repetition, and the session ended there. `edits_between`
        is now a required input to the judgement, and when it is 0 no
        better/worse claim is made at all.

    (2) IT TREATED SAMPLING NOISE AS SIGNAL. V61.21 deliberately re-seeds the
        sample per round (`1234 + 7919*round_no`) so the model cannot write
        assertions against the mutants it was shown - a good property, kept.
        But it means consecutive rounds score DIFFERENT bugs, and the old
        +/-5 point threshold is far inside that spread. The band is now
        computed from the two samples instead of guessed, and the text says
        which sample it is talking about.

    The docstring this replaces claimed "Sampling caveat ... the mutants are
    drawn deterministically" and blamed the difference on a rewritten file
    having a different number of mutation points. That has not been true
    since V61.21; run_mutation_gate's own docstring still says the same
    thing and is corrected in this build too.
    """
    if prev is None:
        return "", fires >= MUTATION_MAX_FIRES
    a, ka, _na, _la = _mutation_scored(prev)
    b, kb, _nb, _lb = _mutation_scored(cur)
    last = fires >= MUTATION_MAX_FIRES
    band = _mutation_noise_band(prev, cur)

    # (1) Nothing was edited: the difference cannot be about anything the
    # model did, so do not tell it that it was.
    if edits_between == 0:
        return (
            f"\n\n\u2139 SAME FILE AS MY LAST CHECK. Nothing has been edited "
            f"since then, so this round is a second sample of the same test, "
            f"not a result of anything you did. It scored {b:.0%} ({kb} "
            f"caught) against {a:.0%} ({ka}) last time - that gap is the "
            f"measurement moving, not the test. Ignore the difference and "
            f"work on the survivors.",
            last)

    if (b < a - band) or (kb < ka and b < a - band):
        return (
            f"\n\n\u26d4 THIS IS WORSE THAN BEFORE YOUR LAST CHANGE. The check "
            f"scored {a:.0%} ({ka} caught) before that edit and {b:.0%} "
            f"({kb} caught) now - a drop bigger than the "
            f"{band:.0%} these {_nb}-mutant samples wobble "
            f"by, so it is real. Your test still prints its pass message, so "
            f"nothing you can see reports this - only planting bugs does.\n"
            f"   The usual cause is a test that got WIDER exception handling "
            f"rather than stronger assertions: a `try` wrapped around the "
            f"whole body means the first raise skips every assertion below it "
            f"and the run still reaches your pass message. Check what your "
            f"handlers COVER before adding another - and if you do not have "
            f"one, that is not the cause here and you should not go looking "
            f"for it. Consider reverting to the previous shape and "
            f"strengthening one assertion at a time.",
            last)
    if b > a + band:
        return (
            f"\n\n\u2713 Better than before: {a:.0%} -> {b:.0%} "
            f"({ka} -> {kb} caught), which clears the {band:.0%} these "
            f"samples wobble by. The direction is right; it is still under "
            f"the floor. Keep doing what you just did to the remaining ones.",
            last)
    return (
        f"\n\n\u26a0 NO MEASURABLE CHANGE: {a:.0%} -> {b:.0%} ({ka} -> {kb} "
        f"caught), inside the {band:.0%} two different "
        f"{_nb}-mutant samples differ by on their own. What "
        f"you changed did not move this number, so doing more of it will not "
        f"move it either. Something about the approach is wrong, not the "
        f"amount of it.",
        True)


def _gaming_findings(src: str):
    """Assertions that name a planted mutation instead of a behaviour.

    V61.21: the survivor list reads like a to-do list, and on the
    super_mario run of 2026-08-01 it was used as one - 16 assertions in
    run_test cite a line number and an operator flip, e.g.
      assert player.w == 32, "... - line 794 mutation (* -> /)"
    That assertion proves nothing about the player being the right size; it
    proves the model read my message. It is worse than a weak assertion,
    because it LOOKS like progress and moves the kill rate, and one of them
    is what the delivered artifact finally died on. Detected here so the
    gate can refuse to count it.
    """
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return []
    lines = src.splitlines()
    pat = re.compile(r"mutation|planted bug|operator flip|\u2192\s*[-+*/<>=!]",
                     re.I)
    out = []
    for fn in ast.walk(tree):
        if not (isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef))
                and "test" in fn.name.lower()):
            continue
        for n in ast.walk(fn):
            if not isinstance(n, ast.Assert):
                continue
            lo, hi = n.lineno, (n.end_lineno or n.lineno)
            seg = "\n".join(lines[lo - 1:hi])
            if pat.search(seg):
                out.append((lo, seg.strip().splitlines()[-1].strip()[:88]))
    return out


def _mutation_advice(mut) -> str:
    """Name the defect the survivors actually show, not the usual one.

    Two survivor populations, opposite fixes. Sending the wrong one is worse
    than sending nothing: the model has already done what it is being told to
    do, concludes the channel is noise, and stops reading it.
    """
    dead = mut.get("survivors_in_dead_fns") or []
    called = mut.get("survivors_in_called_fns") or []
    out = []
    # V61.19: an assertion that never EXECUTES outranks one that is merely
    # weak, and it is invisible from the outside - the test still prints its
    # pass message. Measured on the snake_game artifact of 2026-08-01: 31
    # assertions in run_test, 14 executed, 17 skipped, because the whole body
    # sat inside `except SystemExit: pass` and Game.run() ends by calling
    # sys.exit(). Say this FIRST; strengthening assertions that never run is
    # wasted work.
    gaming = mut.get("gaming") or []
    if gaming:
        shown = "\n".join(f"      line {ln}: {t}" for ln, t in gaming[:6])
        out.append(
            f"\n\n\u26d4 STOP: {len(gaming)} of your assertions are written "
            f"ABOUT THE PLANTED BUGS rather than about the game:\n" + shown
            + (f"\n      ... and {len(gaming) - 6} more"
               if len(gaming) > 6 else "")
            + "\n   Those prove nothing. The mutants I plant are a RANDOM "
              "SAMPLE and the next round draws a different one, so an "
              "assertion naming a line number and an operator cannot help you "
              "twice - and it cannot help a player either. Delete the mutation "
              "references from those messages and make each one state what the "
              "GAME should do: not \"line 794 mutation (* -> /)\" but \"a "
              "player is 32px wide so it fits a 2-tile gap\". If you cannot "
              "say why the value matters to the game, the assertion is not "
              "worth writing.")
    if mut.get("probe_failed"):
        out.append(
            "\n\n\u26a0 I could not trace this run, so I cannot tell you "
            "WHICH of your assertions never execute or which functions your "
            "test skips - the artifact behaved differently under the tracer "
            "than under your own command. That is worth knowing on its own: a "
            "test whose result depends on how it is invoked is not a stable "
            "measurement of anything.")
    skipped = mut.get("asserts_never") or []
    if skipped:
        total = mut.get("asserts_total") or len(skipped)
        shown = "\n".join(f"      line {ln}: {t}" for ln, t in skipped[:8])
        out.append(
            f"\n\n\u26d4 BEFORE ANY OF THAT: {len(skipped)} of your {total} "
            f"assertions NEVER EXECUTED on the passing run. I traced every "
            f"line of the file while your own --test ran; these lines were "
            f"never reached:\n" + shown
            + (f"\n      ... and {len(skipped) - 8} more"
               if len(skipped) > 8 else "")
            + "\n   The test printed its pass message anyway, so nothing you "
              "can see reports this. An assertion that does not run cannot "
              "fail, and the features it names are UNTESTED no matter how "
              "well it is written. Usual causes: an exception handler around "
              "the test body that swallows the first raise and skips the rest "
              "(`except SystemExit: pass` catches the sys.exit() a game loop "
              "ends with), an early return, or a pass message printed outside "
              "the block that was supposed to guard it. Fix this FIRST - "
              "strengthening assertions that never run is wasted work.")
    if dead:
        out.append(
            "\n\nSome of these are in code your --test NEVER EXECUTES"
            f" ({len(dead)} of them). That usually means the test re-"
            "implements the logic it is checking instead of CALLING it -"
            " assertions against a copy pass no matter what the real function"
            " does. Make the test drive the actual code path.")
    if called:
        out.append(
            "\n\nThe rest are in functions your test DOES call"
            f" ({len(called)} of them), so the code path is fine and the"
            " ASSERTION is what is too weak. The usual shape is an assertion"
            " that only ever checks ONE outcome: `assert thing.check()` cannot"
            " detect a mutation that makes check() return True in every case,"
            " because the mutant satisfies it too. For each survivor above,"
            " add the OPPOSITE case - one input that must return True AND one"
            " that must return False, one score that must change AND one that"
            " must not. An assertion only catches a bug if some reachable"
            " version of the code would FAIL it.")
    if not out:
        out.append(
            "\n\nMake the test assert outcomes specific enough that a wrong"
            " version of each function would fail them.")
    # V61.21: the survivor list is a SAMPLE, and saying so is not optional.
    # Without it the list reads as a to-do list - which is exactly how the
    # super_mario run used it. Appended to every variant, so there is no path
    # through this function that hands over line numbers without the caveat.
    out.append(
        "\n\nNote on the list above: those are a random sample of the bugs I "
        "can plant, and the NEXT round draws a different sample from the same "
        "code. Fixing the sample does not raise the score; fixing the test "
        "does. Never write an assertion that mentions a mutation, a line "
        "number, or an operator - state what the game should do and why.")
    return "".join(out)


# Kill-rate floor for the completion gate. VERITY ships 0.5 and that is the
# number both measured artifacts fail: booby_game 32%, snake_game 25%
# whole-file / 22% game-code-only.
# V179: how long the entry-point smoke check lets the deliverable run
# before deciding it started successfully. Short on purpose: a crash in
# these artifacts happens on the first frame (measured: 0.2s and 0.4s on
# the two broken snake builds), while anything with a main loop is still
# running - and still running IS the pass.
ENTRY_SMOKE_TIMEOUT_S = 8
MUTATION_MIN_KILL_RATE = 0.5
MUTATION_MAX_MUTANTS = 40

# V173: SCORE LOGIC AND PRESENTATION SEPARATELY.
#
# On the mario artifact of 2026-08-05 the gate reported 10%. Of the 37
# survivors, measured:
#     17  _draw_* / draw / draw_background
#     11  _generate_* (sprites, level layout, sounds)
#      9  real gameplay - update, handle_input, run, shrink, _hit_block
# Twenty-eight of thirty-seven were in code that draws or builds assets, and
# the specific survivors there are things like
#     (500, 380, 5), (1000, 300, 7)      380 -> 381
#     if i % 2 == 0:                     == -> !=      (coin sprite shading)
# Nothing catches those except a pixel-exact comparison, and a test that
# asserts pixel-exact sprite layout snaps on every cosmetic change. So a
# blended score punishes the model for not writing a test it should not
# write, and hides the nine that matter:
#     self.player.vx -= PLAYER_ACCEL * 0.16      * -> /   movement speed
#     self.player.x = brect.left - self.width    - -> +   collision resolve
#     dt = self.clock.tick(FPS) / 1000.0         / -> *   frame timing
# A 50% floor over the blend is unreachable however good the test gets. Over
# the LOGIC mutants it is both reachable and worth reaching, which is the
# whole point of having a floor.
#
# One definition, used by the sampler, the scorer and the survivor ranker -
# the ranker's private _RENDER tuple was the only copy and it lived inside
# run_mutation_gate, so a second consumer would have forked it.
#
# The line is drawn at WHAT THE CODE PRODUCES. Pixels and audio samples can
# only be checked by measuring the artifact, and a test that pins sprite
# coordinates snaps on every cosmetic edit - that is presentation. Level
# layout is NOT: `_generate_platforms_and_blocks` produces Block objects and
# a test can assert how many there are and where, so mutating it is a real
# defect the test should catch. Classing every `_generate_*` as presentation
# would have excused six of the 2026-08-05 survivors that deserve catching.
_DRAW_MARKERS = ("draw", "render", "paint", "blit", "_ui", "display")
_ASSET_MARKERS = ("sprite", "sound", "audio", "background", "texture",
                  "asset", "animation_frame", "waveform")


def _mutation_class(func_name) -> str:
    """'presentation' for code whose output is pixels or audio, else 'logic'.

    Deliberately name-based and nothing cleverer: the alternative is judging
    a function by what it calls, and a physics update that happens to call a
    helper named draw_debug would flip class on an unrelated edit.
    """
    fn = (func_name or "").lower()
    if any(k in fn for k in _DRAW_MARKERS):
        return "presentation"
    if any(k in fn for k in _ASSET_MARKERS):
        return "presentation"
    return "logic"
# Minimum logic sample before the floor is judged on logic alone. Below this
# the number is too small to act on, so the blended rate is used and the
# message says which one it is talking about.
MUTATION_MIN_LOGIC_SAMPLE = 8
# Share of the sample deliberately spent on presentation code, so the class
# stays VISIBLE rather than silently untested. The rest goes to logic.
MUTATION_PRESENTATION_SHARE = 0.2


# V61.18: how many times the gate may measure one run. 3, not 1, because a
# single measurement cannot see whether the fix helped - and once it did not.
# Not unbounded, because each firing costs a full sample: 13s against a 0.2s
# self-test, ~140s against the 6.7s one the last run produced. The gate also
# stops EARLY the moment a round fails to improve.
MUTATION_MAX_FIRES = 0 # 0 to deactivate or 3 is default

# V171 FIX 5: ONE BUILDER, TWO CALL SITES.
#
# The gate's own message ends "I will re-measure after your next successful
# run of the self-test." It could not keep that promise: the gate only ran
# inside the completion branch, so the re-measure happened at the model's NEXT
# ATTEMPT TO FINISH, not at its next green test. In the run of 2026-08-04 the
# model was bounced at 8%, worked for 29 more steps, never attempted
# completion again, and was never re-measured - MUTATION_MAX_FIRES is 3 and
# exactly one round ever fired. The V61.18 regression-catcher (a rewrite that
# makes the test WORSE) therefore had nothing to compare against, which is the
# whole reason it stopped being one-shot.
#
# The re-measure now also fires mid-loop on a red->green transition. Both
# sites build their message HERE so the wording can never drift apart, and so
# the one-shot/bounded accounting stays in a single place.
def mutation_round_message(mut, target: str, prev, round_no: int,
                           edits_between=None):
    """Text for one mutation round.

    Returns (notify, user_text, last_round). user_text is None when the round
    is a PASS or could not produce a measurement - the caller then does
    nothing but log. Byte-identical to the strings the completion gate emitted
    in V170; only the file they name changed (see V171 FIX 4).
    """
    if not mut:
        return None, None, False
    if mut.get("unrunnable"):
        return (
            f"MUTATION GATE: cannot measure - {target} --test does not "
            f"pass when I run it",
            f"\u26d4 I CANNOT VERIFY THIS BUILD (one-time). I "
            f"ran `python {target} --test` "
            f"{mut['baseline_runs']} times myself and it did "
            f"not pass once, so every check I have - coverage, "
            f"assertion tracing, mutation - is unavailable and "
            f"this file is going out unmeasured.\n"
            f"Your own last run of it may have passed. If so, "
            f"something changed after that run, or the result "
            f"depends on how it is invoked. Either way it is "
            f"not a build anyone can trust.\n"
            f"Run the self-test yourself RIGHT NOW, before "
            f"anything else, and read the traceback. If it "
            f"fails, fix it. If you finish without a passing "
            f"run, say plainly in your summary that the final "
            f"state of the file was never executed.",
            False)
    if mut.get("flaky"):
        return (
            f"MUTATION GATE: bounced - {target} self-test is "
            f"non-deterministic",
            f"⛔ FLAKY SELF-TEST (one-time): I ran "
            f"`python {target} --test` "
            f"{mut['baseline_runs']} times WITHOUT CHANGING "
            f"ANYTHING and it passed {mut['baseline']} of "
            f"those times.\n\n"
            f"A test that fails at random cannot verify "
            f"anything: a green run proves nothing, and the "
            f"habit it teaches is to re-run until green. This "
            f"is a worse defect than a weak test, and it "
            f"blocks any measurement of whether your test "
            f"catches real bugs.\n"
            f"The usual cause in a game is unseeded randomness "
            f"reaching an assertion - random spawn positions, "
            f"random velocities, or a timer. Find the "
            f"assertion whose inputs are not fixed and either "
            f"seed the generator at the top of the test or "
            f"set the values explicitly. Then run it "
            f"{mut['baseline_runs']} times in a row and "
            f"confirm it passes every time.",
            False)
    _rate, _killed, _n, _label = _mutation_scored(mut)
    if _rate < MUTATION_MIN_KILL_RATE:
        verdict, last_round = _mutation_progress(prev, mut, round_no,
                                                 edits_between)
        # V173: lead with LOGIC survivors. The ranker sorts presentation
        # last, so the top 8 are now mutants the model can act on instead of
        # eight sprite constants - on the 2026-08-05 artifact the first six
        # shown were `380 -> 381` in a platform coordinate and `== -> !=` in
        # coin shading, which is how a warning channel teaches the model that
        # the whole channel is noise.
        shown = mut["survivors"][:8]
        _pt = int(mut.get("presentation_tested") or 0)
        _pk = int(mut.get("presentation_killed") or 0)
        _ptxt = ""
        if _label == "logic" and _pt:
            _ptxt = (f"\nSeparately, of {_pt} bugs planted in your drawing and "
                     f"asset-generation code, your test caught {_pk}. That is "
                     f"NOT part of the floor and you should not chase it by "
                     f"asserting on sprite coordinates - a test that pins "
                     f"pixel positions breaks on every cosmetic change. If you "
                     f"want to cover that code, measure what it PRODUCES (a "
                     f"rendered frame is not one flat colour, a generated "
                     f"sound is not all zeroes), not the numbers inside it.\n")
        elif _label == "all":
            _ptxt = (f"\nI could not separate game logic from drawing code "
                     f"here - fewer than {MUTATION_MIN_LOGIC_SAMPLE} of the "
                     f"bugs I could plant landed in non-drawing functions, so "
                     f"this number is over everything.\n")
        return (
            f"MUTATION GATE: bounced - {target} "
            f"caught {_killed}/{_n} planted "
            f"{_label} bugs ({_rate:.0%})"
            + (f" [presentation {_pk}/{_pt}]" if _pt else ""),
            f"⛔ MUTATION CHECK (one-time): I planted "
            f"{_n} single-operator bugs in "
            f"{'the game logic of ' if _label == 'logic' else ''}"
            f"{target} - one at a time, each "
            f"restored afterwards - and re-ran your --test on "
            f"each. It caught {_killed} of them: a "
            f"{_rate:.0%} kill rate against a "
            f"{MUTATION_MIN_KILL_RATE:.0%} floor.\n"
            + _ptxt
            + f"\nYour test passing is therefore NOT evidence the "
            f"features work. These bugs were planted in your "
            f"code and your test did not notice:\n"
            + "\n".join(f"   - {s}" for s in shown)
            + (f"\n   ... and {len(mut['survivors']) - len(shown)} more"
               if len(mut["survivors"]) > len(shown) else "")
            + verdict
            + _mutation_advice(mut)
            + (f"\n\nThis was my LAST check of this file - I "
               f"will not measure again this run, so what you "
               f"do next ships unverified."
               if last_round else
               f"\n\nI will re-measure the moment your self-test "
               f"passes again - you do not have to finish first.")
            + f"\n\nIf you finish without fixing this, say "
            f"plainly in your summary that the self-test does "
            f"not detect these defects.",
            last_round)
    return (None, None, False)
# Baseline runs of the untouched artifact before any bug is planted. 3 is
# enough to catch booby_game's 6-in-10 flakiness with high probability
# (~94%) at a cost of ~3 seconds. Raising it buys certainty linearly.
BASELINE_RUNS = 3


def test_coverage_probe(path, cwd=None, timeout: int = 90):
    """Re-run `<path> --test` under a call tracer.

    Returns {'defined', 'executed', 'never': [(name, line)], 'exit', 'error',
    'headless'} or None when the probe could not produce an answer (no --test,
    syntax error, timeout, no JSON marker). NEVER raises: a probe that cannot
    run must not take the agent down with it, and must not be reported as a
    finding.

    V61.13: 'exit' is the PROBE RUN's exit code and it is not decoration. If
    the probe run dies partway, every function below the crash point is
    reported as never-executed - functions that DO run in the model's own
    environment. Measured: a --test that raises only when
    SDL_VIDEODRIVER=dummy passed the model's own bash run with exit 0 and
    "ALL TESTS PASSED", while the probe returned executed 1/4 and named the
    other three as untested. Handing that to the model is a false accusation
    aimed at a test that was already fine, and it would send it to rewrite
    working code.
    So: if the headless attempt fails, RETRY WITHOUT the dummy drivers before
    concluding anything. That is not a new risk - the caller only reaches
    here because the model itself just ran the same `--test` through bash
    with no dummy driver at all and it exited 0, so any window this opens was
    already opened one step earlier, and the timeout still applies. A clean
    non-headless run is a real measurement and is returned as one. If BOTH
    attempts fail, the headless result is returned with its non-zero 'exit'
    intact so the caller can see the instrument is broken and abstain.
    """
    try:
        path = str(path)
        if not path.lower().endswith(".py") or not os.path.exists(path):
            return None
        src = open(path, encoding="utf-8", errors="replace").read()
        if "--test" not in src:
            return None
        defs = _defined_callables(src, path)
        if not defs:
            return None

        def _attempt(headless: bool):
            env = utf8_subprocess_env()
            if headless:
                # a probe must never pop a window or grab an audio device.
                # FORCED, not setdefault. utf8_subprocess_env() hands back
                # os.environ.copy(), so setdefault is not a no-op on
                # principle - it would PRESERVE an inherited
                # SDL_VIDEODRIVER=x11 / windib and let the probe open a real
                # window mid-run. Two setdefault lines used to sit here and
                # were overwritten by these two on the very next line, so
                # they could never take effect; deleting them is
                # byte-identical (verified against a hostile env). Do not
                # re-add them.
                env["SDL_VIDEODRIVER"] = "dummy"
                env["SDL_AUDIODRIVER"] = "dummy"
            else:
                # V61.13: not merely "leave them alone" - an inherited dummy
                # would defeat the whole point of the retry. Remove them, so
                # this attempt sees exactly what the model's own bash run saw.
                env.pop("SDL_VIDEODRIVER", None)
                env.pop("SDL_AUDIODRIVER", None)
            r = subprocess.run(
                [sys.executable, "-c", _COVERAGE_TRACER, path, "--test"],
                capture_output=True, timeout=timeout, env=env,
                cwd=cwd or os.path.dirname(os.path.abspath(path)) or ".",
            )
            err = r.stderr.decode("utf-8", "replace")
            if "PROBE-JSON:" not in err:
                return None
            tail = err[err.rindex("PROBE-JSON:") + len("PROBE-JSON:"):]
            data = json.loads(tail.splitlines()[0])
            hit = set(data.get("hit") or ())
            never = [(n, ln) for (n, ln) in defs if n not in hit]
            # V61.19: which of the test's OWN assertions actually executed.
            ran_lines = set(data.get("lines") or ())
            a_all = _assert_lines(src)
            a_never = [(ln, t) for (ln, t) in a_all if ln not in ran_lines]
            # the tracer writes PROBE-ERR:<Type>: <msg> before the JSON when
            # the run died; carry it out so the caller can say WHY, not just
            # that something went wrong.
            perr = ""
            for ln in err.splitlines():
                if ln.startswith("PROBE-ERR:"):
                    perr = ln[len("PROBE-ERR:"):].strip()
            return {"defined": len(defs), "executed": len(defs) - len(never),
                    "never": never, "exit": data.get("code"),
                    "error": perr, "headless": headless,
                    "asserts_total": len(a_all),
                    "asserts_run": len(a_all) - len(a_never),
                    "asserts_never": a_never}

        out = _attempt(True)
        if out is None or not out.get("exit"):
            return out
        try:
            retry = _attempt(False)
        except Exception:
            retry = None
        if retry is not None and not retry.get("exit"):
            return retry
        return out
    except Exception:
        return None


def noop_assert_findings(src: str):
    """Lines carrying an assertion that CANNOT fail.

    `assert True` and `assert (cond, "msg")` (a non-empty tuple is always
    truthy) are not weak tests, they are absent tests wearing a tick. In the
    horror_snake suite `assert True, "Wall collision should be detected"`
    printed "[PASS] Wall collision detection OK" while calling no game code
    at all. Static and certain - no heuristics, no false positives.
    """
    out = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    # V171 FIX 2: `check(True, "Wall collision detected")` is the same absent
    # test wearing the same tick, and this returned nothing for it. The
    # helper's own body is skipped so its internal `if not cond` is not read
    # as a constant test.
    helpers = _helper_assert_names(src)
    helper_bodies = set()
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)) and fn.name in helpers:
            helper_bodies |= {id(x) for x in ast.walk(fn)}
    for n in ast.walk(tree):
        if id(n) in helper_bodies:
            continue
        if isinstance(n, ast.Assert):
            t = n.test
            if isinstance(t, ast.Constant) and bool(t.value):
                out.append((n.lineno, f"assert {t.value!r} - always true"))
            elif isinstance(t, ast.Tuple) and t.elts:
                out.append((n.lineno, "assert (a, b) - a non-empty tuple is always true"))
        elif (isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                and n.func.id in helpers and n.args):
            t = n.args[0]
            if isinstance(t, ast.Constant) and bool(t.value):
                out.append((n.lineno,
                            f"{n.func.id}({t.value!r}, ...) - always true"))
            elif isinstance(t, ast.Tuple) and t.elts:
                out.append((n.lineno,
                            f"{n.func.id}((a, b), ...) - a non-empty tuple "
                            f"is always true"))
    return out


def _tools_working_dir(tools) -> str:
    """Sandbox root, taken from any tool's PathValidator. Never raises.

    V61.11a: the Agent has no .working_dir and ToolExecutor has only .tools -
    every tool carries its own PathValidator (BaseTool.__init__), so ask one
    of those. Verified against the real classes, not from memory.
    """
    try:
        for t in (tools or {}).values():
            wd = getattr(getattr(t, "validator", None), "working_dir", None)
            if wd:
                return str(wd)
    except Exception:
        pass
    return os.getcwd()


class FileWriteTool(BaseTool):
    name = "file_write"
    description = "Create a new file with the specified content."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to create/write"},
            "content": {"type": "string", "description": "Content to write"}
        },
        "required": ["path", "content"]
    }

    async def execute(self, path: str, content: str) -> str:
        try:
            resolved_path = self.validator.validate(path)

            # HARD GUARD: never overwrite existing files
            if resolved_path.exists():
                return (
                    f"❌ Refusing to overwrite existing file '{path}'. "
                    f"Use str_replace to modify it."
                )

            resolved_path.parent.mkdir(parents=True, exist_ok=True)

            # Only normalize structural escapes, NOT inside string literals
            # Check if entire content is on one line with \n scattered (broken structure)
            if "\n" not in content and "\\n" in content:
                # File has NO real newlines but has literal \n - definitely broken
                content = content.replace("\\n", "\n")
                content = content.replace("\\t", "\t")

            with open(resolved_path, "w", encoding="utf-8") as f:
                f.write(content)

            return (f"✅ Successfully wrote new file {len(content)} bytes to {path}"
                    + swallow_warning(path, content)
                    + _incomplete_text(path, content))

        except SecurityError as e:
            return str(e)
        except Exception as e:
            return f"Error writing file: {str(e)}"


class StrReplaceTool(BaseTool):
    name = "str_replace"
    description = "Replace a unique string in a file. The old_str must appear exactly once."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to edit"},
            "old_str": {"type": "string", "description": "String to find (must be unique)"},
            "new_str": {"type": "string", "description": "Replacement string"}
        },
        "required": ["path", "old_str", "new_str"]
    }
    
    def _find_similar_candidates(self, content: str, search_str: str):
        """Return ranked candidates using sliding semantic windows.

        V30.1 - same signals, same weights, same tiers, same return shape;
        three fixes to the V30 internals:
        1. Enumerate each candidate start ONCE. The V30 i/off double loop
           scored every start from up to window-size different anchors and
           dedup then discarded the duplicates - pure wasted work (~17x
           redundant SequenceMatcher calls for a 20-line old_str), slow
           enough on a 4,500-line file to freeze the event loop.
        2. context_score was SequenceMatcher(target, whole_window).ratio().
           ratio() = 2M/(len(a)+len(b)), so a target EMBEDDED in a larger
           window mathematically caps near 2T/(T+W): even a byte-exact
           block topped out around 0.85 total and the EXACT tier (>=0.98)
           was unreachable by construction. Now context_score = coverage:
           the fraction of the target present in the surrounding window
           (matching blocks / len(target)) - an exact block in any
           neighborhood scores 1.0 and the tiers mean what they say.
        3. Cheap gates run before any expensive comparison: a rolling
           token-overlap prefilter (character-level quick_ratio prunes
           almost nothing on source code - every block shares most of its
           character multiset - so V30.1 gates on shared \\w+ tokens with
           the target first), then quick_ratio, and the context scan only
           runs when the 0.70 floor is still mathematically reachable.
        """
        import difflib
        lines = content.splitlines()
        search_lines = search_str.splitlines()
        if not search_lines:
            return [], lines

        target = "\n".join(search_lines).strip().lower()
        target_len = max(1, len(search_lines))
        radius = max(1, min(8, target_len // 2))
        first = search_lines[0].strip().lower()
        search_indent = len(search_lines[0]) - len(search_lines[0].lstrip())

        results = []
        n = len(lines)
        block_sm = difflib.SequenceMatcher(None, "", target)  # seq2 cached
        line_sm = difflib.SequenceMatcher(None, "", first)    # seq2 cached

        # Rolling token-overlap gate (V30.1). Tokenize every line once,
        # keep a running token count over the current target_len-line
        # block, and compare against the target's tokens in O(target
        # vocabulary) per start. Renames leave keywords/structure tokens
        # shared, so real candidates survive a 0.35 floor easily; the
        # ~95% of starts that share almost no vocabulary are skipped
        # before any O(len^2) SequenceMatcher work.
        target_counts = {}
        for w in re.findall(r"\w+", target):
            target_counts[w] = target_counts.get(w, 0) + 1
        t_total = sum(target_counts.values())
        line_tokens = [re.findall(r"\w+", l.lower()) for l in lines]
        roll = {}
        for j in range(min(target_len, n)):
            for w in line_tokens[j]:
                roll[w] = roll.get(w, 0) + 1

        for start in range(n):
            if t_total:
                overlap = sum(min(c, roll.get(w, 0)) for w, c in target_counts.items())
                gate_ok = (overlap / t_total) >= 0.35
            else:
                gate_ok = True  # pure-punctuation old_str: no token signal

            if gate_ok:
                block = lines[start:start + target_len]
                block_text = "\n".join(block).strip().lower()
                if block_text:
                    block_sm.set_seq1(block_text)
                    if block_sm.quick_ratio() >= 0.30:
                        line_sm.set_seq1(block[0].strip().lower())
                        line_score = line_sm.ratio()
                        block_score = block_sm.ratio()

                        # Context scan only if the 0.70 floor is reachable
                        # even with a perfect context (0.55) + exact bonus.
                        if 0.20 * line_score + 0.25 * block_score + 0.65 >= 0.70:
                            w_start = max(0, start - radius)
                            w_end = min(n, start + target_len + radius)
                            window_text = "\n".join(lines[w_start:w_end]).lower()
                            ctx_sm = difflib.SequenceMatcher(None, target, window_text)
                            covered = sum(b.size for b in ctx_sm.get_matching_blocks())
                            context_score = min(1.0, covered / max(1, len(target)))

                            score = (
                                0.20 * line_score +
                                0.55 * context_score +
                                0.25 * block_score
                            )

                            if block_text == target:
                                score = min(1.0, score + 0.10)

                            indent_penalty = 0.0
                            if block:
                                if (len(block[0]) - len(block[0].lstrip())) != search_indent:
                                    indent_penalty = 0.03
                            score -= indent_penalty

                            if score >= 0.70:
                                if score >= 0.98:
                                    conf = "EXACT"
                                elif score >= 0.90:
                                    conf = "VERY HIGH"
                                elif score >= 0.80:
                                    conf = "HIGH"
                                else:
                                    conf = "POSSIBLE"

                                results.append((
                                    start,
                                    score,
                                    block[0] if block else "",
                                    conf,
                                    {
                                        "line_score": line_score,
                                        "context_score": context_score,
                                        "block_score": block_score,
                                        "indent_penalty": indent_penalty,
                                        "exact_bonus": block_text == target,
                                    }
                                ))

            # Advance the rolling window: drop line `start`, add the line
            # entering at `start + target_len`.
            for w in line_tokens[start]:
                c = roll.get(w, 0) - 1
                if c > 0:
                    roll[w] = c
                else:
                    roll.pop(w, None)
            nxt = start + target_len
            if nxt < n:
                for w in line_tokens[nxt]:
                    roll[w] = roll.get(w, 0) + 1

        results = sorted(results, key=lambda r: (-r[1], r[0]))
        return results, lines

    def _generate_helpful_preview(self, content: str, search_str: str, path: str) -> str:
        """
        Generate preview showing LIKELY match locations instead of just file start.
        
        Addresses the truncated_bug where preview shows beginning of file
        but the actual match location is in middle/end.
        """
        import difflib
        
        lines = content.splitlines()
        search_lines = search_str.splitlines()
        first_search_line = search_lines[0].strip() if search_lines else search_str[:300]
        
        # Find lines similar to what was searched
        candidates = []
        for i, line in enumerate(lines):
            if not line.strip():
                continue
            ratio = difflib.SequenceMatcher(
                None, 
                first_search_line.lower(), 
                line.strip().lower()
            ).ratio()
            if ratio > 0.7:  # 70% similar
                candidates.append((i, ratio, line))
        
        # LINE-NUMBER CONTRACT for everything below: `lines` is 0-indexed and
        # every printed label is idx+1, so a section header must claim
        # (first_idx + 1) through (last_idx + 1). The middle header used to
        # claim mid-10..mid+9 while the body printed mid-9..mid+10 - verified
        # against a file whose line N contains "L<N>", wrong at every size.
        # This preview is read by a model that is about to choose new line
        # numbers from it, so an off-by-one header is worse than no header.
        if candidates:
            # Sort by similarity, show top matches
            candidates.sort(key=lambda x: x[1], reverse=True)
            preview_parts = [
                f"🔍 [Found {len(candidates)} similar lines - possible match targets:]"
            ]
            for line_num, ratio, line in candidates[:20]:
                # Show context around each match
                start = max(0, line_num - 10)
                end = min(len(lines), line_num + 11)
                context_lines = []
                for idx in range(start, end):
                    marker = "→" if idx == line_num else " "
                    context_lines.append(f"  {marker} {idx+1:4d}: {lines[idx][:500]}")
                context = "\n".join(context_lines)
                preview_parts.append(
                    f"\n--- Near line {line_num+1} ({ratio:.0%} similar) ---\n{context}"
                )
            return "\n".join(preview_parts)
        else:
            # No similar content found - show strategic file sections
            preview_parts = [f"🔍 [No similar content found. File structure:]"]

            if len(lines) > 100: # Show beginning
                preview_parts.append(f"\n[Lines 1-100]:")
                preview_parts.append("\n".join(f" {i+1:4d}: {l[:500]}" for i, l in enumerate(lines[:100])))

                # Show middle
                mid = len(lines) // 2
                # Header matches displayed line numbers (indices + 1): the body
                # walks mid-20..mid+19, which prints mid-19..mid+20.
                preview_parts.append(f"\n[Lines {mid-19}-{mid+20}] (middle):")
                preview_parts.append("\n".join(f" {i+1:4d}: {lines[i][:500]}" for i in range(mid-20, mid+20) if i < len(lines)))

                # Show end
                preview_parts.append(f"\n[Lines {len(lines)-49}-{len(lines)}] (end):")
                # The first item in a 50-line tail is index len-50, so enumerate
                # starts there and the first printed label is len-49.
                preview_parts.append("\n".join(f" {i+1:4d}: {l[:500]}" for i, l in enumerate(lines[-50:], len(lines)-50)))
            else:
                # Small file, show all with line numbers
                preview_parts.append("\n".join(f" {i+1:4d}: {l[:500]}" for i, l in enumerate(lines)))

            return "\n".join(preview_parts)

    
    async def execute(self, path: str, old_str: str, new_str: str) -> str:
        # V61.7: every write below is followed by message-building code that
        # can raise (it did: an undefined `delta`). The catch-all at the bottom
        # cannot tell "never wrote" from "wrote, then crashed formatting the
        # receipt", and reporting the second as a failure is the worst lie this
        # tool can tell - the model retries an edit the file already has, the
        # retry misses, and the failed-edit cache learns the wrong lesson.
        wrote = False
        try:
            resolved_path = self.validator.validate(path)
            if is_machine_self(resolved_path):
                return SELF_BLOCK_MSG.format(name=resolved_path.name)
            if not resolved_path.exists():
                return f"Error: File '{path}' not found"
            
            # V30.6: read RAW (newline="") so we can see and preserve the
            # file's real line endings, then match against an LF-normalized
            # copy. The snake_game run burned ~50 iterations (a large slice
            # of 26M tokens) on this exact trap: the model's old_str carried
            # \r\n from a prior CRLF file_read while the compare target was
            # LF, so content.count() returned 0 while the candidates engine
            # scored the SAME lines [EXACT] 0.99 - because candidates .strip()
            # every line and count() does not. Tool and its own search tool
            # contradicting each other is the worst failure a model can face:
            # it sees proof the text is there and proof it can't be replaced.
            # The universal-newline read this replaced hid CRLF on read but
            # left old_str's endings untouched, so the mismatch survived.
            with open(resolved_path, "r", encoding="utf-8", newline="") as f:
                raw_content = f.read()

            # Detect the file's dominant ending to preserve it on write.
            crlf_n = raw_content.count("\r\n")
            lf_only_n = raw_content.count("\n") - crlf_n
            cr_only_n = raw_content.count("\r") - crlf_n
            if crlf_n >= lf_only_n and crlf_n >= cr_only_n and crlf_n > 0:
                file_ending = "\r\n"
            elif cr_only_n > lf_only_n and cr_only_n > 0:
                file_ending = "\r"
            else:
                file_ending = "\n"

            def _norm_nl(s: str) -> str:
                return s.replace("\r\n", "\n").replace("\r", "\n")

            # `content` is the LF-normalized view everything matches against.
            content = _norm_nl(raw_content)

            # Normalize literal "\n" if needed, then line endings on BOTH
            # sides so a CRLF old_str matches an LF file and vice versa.
            old_str_norm = old_str
            new_str_norm = new_str
            if "\\n" in old_str and "\n" not in old_str and "\n" in content:
                old_str_norm = old_str.replace("\\n", "\n")
                new_str_norm = new_str.replace("\\n", "\n")
            old_str_norm = _norm_nl(old_str_norm)
            new_str_norm = _norm_nl(new_str_norm)

            count = content.count(old_str_norm)
            if count == 0:
                # V171 FIX 3: AN OVERSIZED ANCHOR THAT MISSED IS REFUSED
                # HERE, BEFORE ANY SEARCH.
                #
                # Everything below this point - the single-line fallback, the
                # whitespace-tolerant window scan, and above all the
                # evidence-ranked candidates engine - is superlinear in the
                # size of old_str. Benchmarked against the real 2,092-line
                # mario_game.py with the real tool:
                #
                #      20 lines /    750 chars ->    0.18s
                #      50 lines /  2,200 chars ->    1.19s
                #     100 lines /  4,526 chars ->   22.33s
                #     200 lines /  9,473 chars ->   95.57s
                #     400 lines / 18,324 chars ->  269.56s
                #
                # In the run of 2026-08-04 the model tried to replace its
                # whole test block in one call: 911 lines / 41,000 chars,
                # three times. Its log shows the cost directly - 365s and
                # 367s of wall clock between the end of generation and the
                # next iteration, each immediately after a "String not
                # found". With the generation those turns cost (233s, 454s,
                # 692s) the last three iterations of that run burned about
                # 35 minutes and produced nothing.
                #
                # The cap applies ONLY on the count==0 path. An anchor of any
                # size that matches EXACTLY still applies, because
                # content.count() is linear and already answered - a large
                # legitimate edit is not affected. What is refused is
                # SEARCHING for a giant anchor that is not there, which is
                # never the right next move anyway: the answer is always to
                # read a region and edit it, and saying so in 0.0s is
                # strictly better than saying so in six minutes.
                _anchor_lines = old_str_norm.count("\n") + 1
                if (_anchor_lines > STR_REPLACE_MAX_ANCHOR_LINES
                        or len(old_str_norm) > STR_REPLACE_MAX_ANCHOR_CHARS):
                    _al = old_str_norm.splitlines()
                    _head = "\n".join(f"    {l[:120]}" for l in _al[:3])
                    _tail = "\n".join(f"    {l[:120]}" for l in _al[-3:])
                    return (
                        f"Error: String not found in {path}, and old_str is "
                        f"TOO LARGE TO SEARCH FOR "
                        f"({_anchor_lines:,} lines / {len(old_str_norm):,} chars; "
                        f"the limit is {STR_REPLACE_MAX_ANCHOR_LINES:,} lines / "
                        f"{STR_REPLACE_MAX_ANCHOR_CHARS:,} chars).\n"
                        f"File has {len(content):,} chars "
                        f"({content.count(chr(10)) + 1:,} lines).\n\n"
                        f"I did not run the similar-region search: on an "
                        f"anchor this size it takes MINUTES and its answer is "
                        f"always the same one you are reading now.\n\n"
                        f"WHY THIS FAILED: an anchor this long is being "
                        f"recalled, not copied - every line of it has to "
                        f"match the file byte for byte, and one drifted "
                        f"character anywhere in "
                        f"{_anchor_lines:,} lines misses the whole thing. "
                        f"Retyping it larger cannot fix that.\n\n"
                        f"DO THIS INSTEAD - one small region at a time:\n"
                        f"  1. file_read the region you want to change "
                        f"(start_line/end_line).\n"
                        f"  2. Copy 5-15 lines from what file_read returned, "
                        f"verbatim, as old_str.\n"
                        f"  3. str_replace that. Repeat for the next region.\n"
                        f"Several small edits that land beat one large edit "
                        f"that does not.\n\n"
                        f"Your anchor began:\n{_head}\n    ...\nand ended:\n{_tail}"
                    )
            if count == 0:
                # --- Whitespace/indent fallback for common cases (safe) ---
                # Only attempt if BOTH old_str and new_str are single lines
                # Multi-line new_str would lose indentation on lines 2+, so require exact match
                if "\n" not in old_str_norm and "\n" not in new_str_norm:
                    target = old_str_norm.strip()
                    matches = []
                    for i, line in enumerate(content.splitlines(True)):  # keep line endings
                        if line.strip() == target:
                            matches.append((i, line))

                    if len(matches) == 1:
                        i, line = matches[0]
                        # Replace the whole line, preserving original indentation and newline
                        replacement_line = ""
                        # Preserve original leading whitespace from the matched line
                        prefix = line[:len(line) - len(line.lstrip())]
                        # Preserve original newline ending if present
                        line_ending = "\n" if line.endswith("\n") else ""
                        replacement_line = prefix + new_str_norm.strip() + line_ending

                        # Rebuild file content with the replaced line
                        lines = content.splitlines(True)
                        lines[i] = replacement_line
                        new_content = "".join(lines)

                        # V30.6: preserve the file's original dominant ending.
                        out_content = new_content.replace("\n", file_ending) if file_ending != "\n" else new_content
                        with open(resolved_path, "w", encoding="utf-8", newline="") as f:
                            f.write(out_content)
                        wrote = True

                        return (
                            f"✅ Successfully replaced (indent-tolerant) line in {path} "
                            f"(matched by stripped equality)."
                            + swallow_warning(path, new_content)
                            + _incomplete_text(path, new_content)
                        )

                    elif len(matches) > 1:
                        # Too risky to guess; show snippets to help craft a unique anchor
                        snippets = []
                        for j, (i, line) in enumerate(matches[:10], start=1):
                            snippets.append(f"--- Match {j} at line {i+1} ---\n{line}")
                        joined = "\n".join(snippets)
                        preview = content[:1000000] + "..." if len(content) > 1000000 else content
                        return (
                            f"Error: String not found exactly in {path}, but a stripped match "
                            f"was found {len(matches)} times (ambiguous).\n\n"
                            f"{joined}\n\n"
                            f"HINT: Use a longer/more specific old_str (include surrounding lines)."
                        )

                # V41.3: APPLY the whitespace-insensitive match instead of
                # refusing it. V30.6 correctly DIAGNOSED this family (a lone
                # trailing space, tabs-vs-spaces, an NBSP) and then returned
                # an error - having already proven the match is UNIQUE. The
                # single-line path 40 lines above trusts exactly that same
                # uniqueness and applies the edit; multi-line was excluded
                # only because the strip-and-re-prefix strategy would lose
                # indentation on lines 2+. That does not apply here: we
                # locate the real line span and splice new_str over it, so
                # new_str goes in exactly as written.
                #
                # The mario_snake run is why: two lines carried a trailing
                # space after a comma, the model retyped them without it, and
                # this branch fired on FIVE separate attempts (steps 32, 36,
                # 38, 45, 46) while telling the model to file_read and copy
                # byte-for-byte - which the duplicate guard was simultaneously
                # blocking. 16 iterations, zero progress.
                #
                # Window matching per line, NOT a substring count on joined
                # stripped text: "b\nc" is a substring of "ab\nc" but is not a
                # line-aligned match, so the old count()==1 test could fire on
                # a partial line. Windows cannot.
                st_lines = [l.strip() for l in old_str_norm.splitlines()]
                c_lines = content.splitlines(True)   # keep line endings
                nlines = len(st_lines)
                hits = []
                if nlines and "\n" in old_str_norm:
                    for i in range(len(c_lines) - nlines + 1):
                        if [c_lines[j].strip() for j in range(i, i + nlines)] == st_lines:
                            hits.append(i)

                if len(hits) == 1:
                    i = hits[0]
                    new_block = new_str_norm.splitlines(True) or [""]
                    # V61.6: PER-LINE indentation, taken from the file.
                    #
                    # This path matches by per-line STRIPPED equality, so the
                    # region it matches can span more than one indent level.
                    # The previous version took a single delta from the FIRST
                    # line and applied it to every replacement line, which
                    # silently re-indented the rest. Proven by execution:
                    #
                    #     file            old_str      result (old code)
                    #     for i in r:     acc += i     for i in r:
                    #       acc += i        return       acc += i * 2
                    #     return acc                     return acc   <- MOVED
                    #
                    # `return acc` went from 4 spaces to 8 and ended up INSIDE
                    # the loop, so the function returned on the first pass. It
                    # parses, so the syntax gate cannot see it - a silent
                    # behaviour change is the worst thing an edit tool can do.
                    #
                    # And a delta in CHARACTERS is wrong whenever the two sides
                    # use different whitespace: 8 spaces in the file minus one
                    # tab in old_str is a delta of 7, which bolted 7 spaces in
                    # front of a line that still carried its own tab.
                    #
                    # So no delta. Each replacement line ADOPTS THE FILE'S OWN
                    # PREFIX for the line it replaces, plus whatever extra
                    # indent the model asked for RELATIVE to its own old_str
                    # (measured with tabs expanded, so the comparison is in
                    # columns rather than characters). Lines past the end of
                    # the matched region carry the last prefix forward.
                    old_lines_n = old_str_norm.splitlines()

                    def _cols(t):
                        lead = t[:len(t) - len(t.lstrip())]
                        return len(lead.expandtabs(4))

                    def _mk_ws(model_prefix, cols):
                        """`cols` columns of indent in the FILE's own whitespace."""
                        cols = max(0, cols)
                        if model_prefix and set(model_prefix) <= {"\t"}:
                            return "\t" * (cols // 4) + " " * (cols % 4)
                        return " " * cols

                    prefix, rel, model_owns = "", 0, False
                    anchor_new = anchor_out = None
                    shifted = []
                    # V61.10: THE PREMISE ITSELF WAS WRONG FOR HALF THE CASES.
                    #
                    # "Adopt the file's own prefix" is right when old_str differs
                    # from the file only by a TRAILING space - the leading
                    # whitespace is identical, so adopting it is a no-op and the
                    # V61.6 two-indent-level fix still holds. It is catastrophic
                    # when the file's LEADING whitespace is the very bug being
                    # fixed: the model writes clean Python in old_str AND
                    # new_str, this path matches by stripped equality, rel comes
                    # out 0, and the file's corruption is stamped back on top of
                    # the correction. The tool then reports ✅.
                    # Proven on horror_snake.py, run of 2026-07-31: a 735-line
                    # replace announced "41 of 735 line(s) took the file's own
                    # leading whitespace" - 41 corrections reverted - and left
                    # `IndentationError: unexpected indent` at line 13. Every
                    # subsequent tolerant-path attempt to remove that space was
                    # reverted the same way; only the two edits that happened to
                    # take the EXACT-match path ever stuck. Through this branch
                    # the machine was structurally incapable of dedenting.
                    # The discriminator: compare leading whitespace in COLUMNS.
                    #   equal   -> old_str agrees with the file, adopt the file's
                    #              exact prefix (keeps tabs, keeps V61.6).
                    #   differs -> the model is ASSERTING an indent the file does
                    #              not have. It is the one writing the code.
                    #              Its new_str line goes in verbatim.
                    # V61.7: the message below used to cite `delta`, the single
                    # uniform shift THIS path deleted. The name went; the
                    # f-string kept referencing it, so every trip through this
                    # branch raised NameError AFTER the write and the outer
                    # handler reported "Error editing file" for an edit that
                    # had already landed. Count what actually happened instead.
                    #
                    # V61.9: two defects in the loop itself, both reproduced
                    # against the fps_game run of 2026-07-31, both of which
                    # produced the SyntaxError the model then spent two
                    # iterations undoing.
                    #  (1) A WHITESPACE-ONLY FILE LINE HAS NO INDENT TO LEND.
                    #      fl[:len(fl)-len(fl.lstrip())] on a blank line is the
                    #      WHOLE line, newline included, so that "\n" was bolted
                    #      in front of the next replacement line and split
                    #      `print(...)` from its `raise` with a blank. Skip
                    #      blank lines; carry the last real prefix forward.
                    #  (2) max(0, rel) MADE DEDENT IMPOSSIBLE. A replacement
                    #      line could go deeper than the file line it replaced
                    #      but never shallower, so closing an inner block to
                    #      open an outer one silently kept the inner indent:
                    #      `except` landed at 24 with its body also at 24.
                    #      rel may now go negative, floored at column 0.
                    # Lines PAST the matched region no longer carry a rel
                    # computed for some other line - they keep their own
                    # spacing relative to the last line that was mapped.
                    reindented = 0
                    for k, l in enumerate(new_block):
                        mapped = k < nlines and k < len(old_lines_n)
                        if mapped:
                            fl = c_lines[i + k]
                            if fl.strip():
                                prefix = fl[:len(fl) - len(fl.lstrip())]
                                model_owns = bool(
                                    old_lines_n[k].strip()
                                    and _cols(old_lines_n[k]) != _cols(fl)
                                )
                            if old_lines_n[k].strip():
                                rel = _cols(l) - _cols(old_lines_n[k])
                        if not l.strip():
                            shifted.append(l)
                            continue
                        if mapped and model_owns:
                            out = l                       # verbatim, as written
                            target = _cols(l)
                        else:
                            if mapped:
                                target = len(prefix.expandtabs(4)) + rel
                            elif anchor_new is None:
                                target = _cols(l)
                            else:
                                target = anchor_out + (_cols(l) - anchor_new)
                            target = max(0, target)
                            out = _mk_ws(prefix, target) + l.lstrip()
                        anchor_new, anchor_out = _cols(l), target
                        if out != l:
                            reindented += 1
                        shifted.append(out)
                    new_block = shifted
                    # Match the trailing newline state of the region replaced.
                    last_old = c_lines[i + nlines - 1]
                    if last_old.endswith("\n") and not new_block[-1].endswith("\n"):
                        new_block[-1] += "\n"
                    elif not last_old.endswith("\n") and new_block[-1].endswith("\n"):
                        new_block[-1] = new_block[-1].rstrip("\n")

                    new_content = "".join(c_lines[:i] + new_block + c_lines[i + nlines:])
                    out_content = (new_content.replace("\n", file_ending)
                                   if file_ending != "\n" else new_content)
                    with open(resolved_path, "w", encoding="utf-8", newline="") as f:
                        f.write(out_content)
                    wrote = True
                    return (
                        f"✅ Successfully replaced block in {path} at line {i + 1} "
                        f"(matched ignoring per-line leading/trailing whitespace - your "
                        f"old_str differed only by invisible whitespace, most often a "
                        f"trailing space). Each new line was re-indented to match the "
                        f"line it replaced, so a block spanning two indent levels keeps "
                        f"both"
                        + (f". {reindented} of {len(new_block)} line(s) took the "
                           f"file's own leading whitespace."
                           if reindented else ".")
                        + swallow_warning(path, new_content)
                        + _incomplete_text(path, new_content)
                    )

                if len(hits) > 1:
                    return (
                        f"Error: String not found in {path} by exact match, and a "
                        f"whitespace-insensitive match occurs {len(hits)} times "
                        f"(ambiguous - refusing to guess which one you meant).\n"
                        f"HINT: extend old_str with surrounding lines to make it unique."
                    )


                # V30.1: the V30 similarity engine existed but NOTHING called
                # it - the same "fixed function nobody calls" pattern as
                # mario_snake's _make_sound. Wire it in: rank candidate
                # regions (off the event loop - the scan is CPU-bound and
                # must not freeze the Live dashboard), fall back to the
                # legacy preview when nothing clears the 0.70 floor.
                candidates, all_lines = await asyncio.to_thread(
                    self._find_similar_candidates, content, old_str_norm
                )
                if candidates:
                    # Region-dedup for display: adjacent starts are the same
                    # region; show one entry per distinct area, best first.
                    span = max(1, len(old_str_norm.splitlines()))
                    shown, taken = [], []
                    for cand in candidates:
                        if any(abs(cand[0] - t) < span for t in taken):
                            continue
                        taken.append(cand[0])
                        shown.append(cand)
                        if len(shown) == 5:
                            break
                    parts = [f"🔍 CANDIDATES (evidence-ranked, top {len(shown)} of {len(candidates)} regions):"]
                    for rank, (ln, score, _first_line, conf, m) in enumerate(shown, 1):
                        c_start = max(0, ln - 2)
                        c_end = min(len(all_lines), ln + span + 2)
                        ctx = "\n".join(
                            f"  {'→' if c_start + k == ln else ' '} {c_start + k + 1:4d}: {all_lines[c_start + k][:300]}"
                            for k in range(c_end - c_start)
                        )
                        parts.append(
                            f"\n#{rank} line {ln + 1}  score {score:.3f}  [{conf}]  "
                            f"(line {m['line_score']:.2f} / context {m['context_score']:.2f} / block {m['block_score']:.2f})\n{ctx}"
                        )
                    preview = "\n".join(parts)
                else:
                    # Default: show helpful preview with likely match locations
                    preview = self._generate_helpful_preview(content, old_str_norm, path)
                return (
                    f"Error: String not found in {path}.\n"
                    f"File has {len(content)} chars ({len(content.splitlines())} lines).\n\n"
                    f"{preview}\n\n"
                    f"HINT: file_read the → region, then copy old_str EXACTLY from it "
                    f"(include surrounding lines to make it unique)."
                )



            elif count > 1:
                # Show small snippets around the first few occurrences to help craft a unique anchor
                snippets = []            
                start = 0
                max_snips = 10
                for i in range(max_snips):
                    idx = content.find(old_str_norm, start)
                    if idx == -1:
                        break
                    # grab some context around the match
                    left = max(0, idx - 1000)
                    right = min(len(content), idx + len(old_str_norm) + 1000)
                    snippet = content[left:right]
                    snippets.append(f"--- Occurrence {i+1} at char {idx} ---\n{snippet}")
                    start = idx + len(old_str_norm)
                joined = "\n\n".join(snippets) if snippets else "(no snippets available)"
                
                # Analyze if duplicates might be in different contexts (functions/classes)
                contexts_found = set()
                for snippet in snippets:
                    # Try to extract function/class context
                    func_match = re.search(r'(?:def|class|async def)\s+(\w+)', snippet)
                    if func_match:
                        contexts_found.add(func_match.group(1))
                
                if len(contexts_found) > 1:
                    severity_msg = "⚠️ NOTE: Matches found in DIFFERENT functions/classes"
                    hint = "Include the function signature or class name in old_str to target a specific one."
                else:
                    severity_msg = "String appears in similar contexts"
                    hint = "Include more surrounding lines to make old_str unique."
                
                contexts_str = f"Contexts detected: {', '.join(contexts_found)}" if contexts_found else ""
                
                return (
                    f"Error: String appears {count} times in {path}. Must be unique.\n\n"
                    f"{severity_msg}\n"
                    f"{contexts_str}\n\n"
                    f"Here are up to {max_snips} occurrence previews (±500 chars):\n{joined}\n\n"
                    f"HINT: {hint}"
                )

            new_content = content.replace(old_str_norm, new_str_norm)
            # V30.6: emit the file's ORIGINAL dominant ending. newline="" +
            # explicit ending means we write exactly these bytes; without
            # this, matching a CRLF file would rewrite it as LF and every
            # subsequent CRLF-anchored edit would then miss - the same trap
            # in a new coat.
            out_content = new_content.replace("\n", file_ending) if file_ending != "\n" else new_content
            with open(resolved_path, "w", encoding="utf-8", newline="") as f:
                f.write(out_content)
            wrote = True
            
            return (f"✅ Successfully replaced string in {path}"
                    + swallow_warning(path, new_content)
                    # V61.29b: THE MAIN EDIT PATH HAD NO COMPLETENESS CHECK.
                    # V61.23 and V61.29 were attached by matching the exact
                    # text of the swallow_warning lines; this one ends with
                    # "))" instead of ")" and silently matched neither, so the
                    # exact-match branch - which is where nearly every edit
                    # lands - has never once run them. mario_game 2026-08-03:
                    # the delivered file has SIX untestable-input findings
                    # and the run logged zero, while "PLAYER_ACCELERATION used
                    # but never defined" fired once, on the initial
                    # file_write, through a path that did match. I asserted my
                    # patch hit 3 sites and never asked how many existed.
                    + _incomplete_text(path, new_content))
        except SecurityError as e:
            return str(e)
        except Exception as e:
            if wrote:
                return (
                    f"⚠️ THE EDIT WAS APPLIED to {path} and the file on disk is "
                    f"already changed - but building the confirmation message "
                    f"crashed: {type(e).__name__}: {e}\n"
                    f"DO NOT RETRY THIS EDIT. Your old_str is no longer in the "
                    f"file; retrying will report 'String not found' and cost you "
                    f"the iteration. file_read the region to confirm the new text "
                    f"is there, then continue. This is a bug in str_replace "
                    f"itself, not in your call."
                )
            return f"Error editing file: {str(e)}"


class ListDirTool(BaseTool):
    name = "list_dir"
    description = "List files and directories at a path."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to list (default: .)"},
            "max_depth": {"type": "integer", "description": "Max depth (default: 5)"}
        },
        "required": []
    }
    
    async def execute(self, path: str = ".", max_depth: int = 5) -> str:
        try:
            resolved_path = self.validator.validate(path)
            if not resolved_path.exists():
                return f"Error: Path '{path}' not found"
            if not resolved_path.is_dir():
                return f"Error: '{path}' is not a directory"
            
            def list_tree(dir_path: Path, prefix: str = "", depth: int = 0) -> list:
                if depth >= max_depth:
                    return []
                items = []
                try:
                    entries = sorted(dir_path.iterdir(), key=lambda e: (not e.is_dir(), e.name.lower()))
                    skip = {"__pycache__", "node_modules", ".git", "venv", ".venv"}

                    # Separate visible from hidden entries
                    visible_entries = []
                    hidden_dirs = []
                    for e in entries:
                        if e.is_file() and is_machine_self(e):
                            continue  # V30.5: runtime is invisible to missions
                        if e.name.startswith("."):
                            if e.is_dir():
                                hidden_dirs.append(e.name)
                        elif e.name in skip and e.is_dir():
                            # V25: only DIRS named venv/node_modules/etc fold
                            # into the [hidden] marker - a plain FILE with one
                            # of those names was silently dropped entirely.
                            hidden_dirs.append(e.name)
                        else:
                            visible_entries.append(e)
                    
                    
                    for i, entry in enumerate(visible_entries):
                        # Entry is last only if no hidden dirs follow
                        is_last = (i == len(visible_entries) - 1) and not hidden_dirs
                        connector = "└── " if is_last else "├── "
                        if entry.is_dir():
                            items.append(f"{prefix}{connector}📁 {entry.name}/")
                            extension = "    " if is_last else "│   "
                            items.extend(list_tree(entry, prefix + extension, depth + 1))
                        else:
                            size = entry.stat().st_size
                            items.append(f"{prefix}{connector}📄 {entry.name} ({size:,} bytes)")
                    
                    # Show hidden directory markers at the end
                    if hidden_dirs:
                        hidden_str = ", ".join(sorted(hidden_dirs))
                        items.append(f"{prefix}└── [hidden: {hidden_str}]")
                        
                except PermissionError:
                    items.append(f"{prefix}[Permission denied]")
                return items
            
            result = [f"📁 {resolved_path.name}/"]
            result.extend(list_tree(resolved_path))
            return "\n".join(result)
        except SecurityError as e:
            return str(e)
        except Exception as e:
            return f"Error listing directory: {str(e)}"


def utf8_subprocess_env() -> dict:
    """V30.4: bash children inherit a UTF-8-capable stdio config.
    The snake_game run burned ~17 of 51 tools on cp1252
    UnicodeEncodeError: the model's own test prints (✓) crashed on the
    Windows console, it converted them to [OK] one str_replace at a
    time, and its binary-inspection probes then crashed on the same
    encoder. PYTHONUTF8=1 + PYTHONIOENCODING=utf-8 make child Python
    speak UTF-8 regardless of the console codepage - the machine
    already decodes pipes with errors='replace', so this is strictly
    enabling. Kills the whole recurring failure class."""
    env = os.environ.copy()
    env["PYTHONUTF8"] = "1"
    env["PYTHONIOENCODING"] = "utf-8"
    return env


class BashTool(BaseTool):
    name = "bash"
    description = "Execute a shell command and return output."
    parameters = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "Command to execute"},
            "timeout": {"type": "integer", "description": "Seconds before the command is killed (1-60, default 60)"}
        },
        "required": ["command"]
    }
    
    # OS-aware allowed commands - safe subset only
    # NOTE: Many commands are redundant with built-in tools:
    #   - list_dir replaces ls/dir
    #   - file_read replaces cat/type  
    #   - grep_search replaces grep/findstr
    #   - file_write auto-creates dirs (replaces mkdir)
    # Cross-platform safe commands (package managers, runtimes, test runners)
    ALLOWED_CROSS_PLATFORM = {
        "git", "npm", "npx", "yarn", "pip", "pip3", 
        "python", "py", "node", "cargo", "go",
        "pytest", "jest", "flask", "uvicorn", "gunicorn", "echo",
        "cd", "sort",  # navigation + output trimming
        "gcc", "g++", "make", "cmake", "clang", "clang++", "ninja", "chcp", "fc", "tar"
        # V45.8: g++ is named in the V41.1 changelog as part of the
        # g++/gcc/make/cmake toolchain addition, but only the other three
        # landed. Verified by executing BashTool: `g++ --version` returned
        # BLOCKED while `gcc --version` ran. A C++ mission could probe with
        # `where g++` and then be refused the compiler it just found.
    }
    
    # Windows specific  
    ALLOWED_WINDOWS = {
        "dir", "type", "findstr", "where", "curl"
        # Intentionally NO: del, rd, rmdir, reg, net, taskkill, shutdown, powershell, cmd
    }
    
    # DANGEROUS - Never allow these regardless of OS
    FORBIDDEN = {
        "rm", "del", "rmdir", "rd",      # File/dir deletion
        "format", "fdisk",                # Disk operations
        "reg", "regedit",                 # Registry
        "net", "netsh",                   # Network/user manipulation  
        "taskkill", "kill", "pkill",      # Process killing
        "shutdown", "reboot", "init",     # System control
        "powershell", "cmd", "bash", "sh", "zsh",  # Shell escapes
        "sudo", "su", "runas",            # Privilege escalation
        "chmod", "chown",                 # Permission changes - agent can advise user instead
        "eval", "exec",                   # Code execution
    }

    # V45.8: run 5 step 11 issued `... 2>&1 | head -30`, was refused, and
    # retried at step 12 with `| more`. One iteration, and then something
    # worse: the run stored the lesson "On Windows, avoid using 'head' in
    # piped commands (use 'more' instead)" at confidence 0.9,
    # grounded=True. That is THIS SANDBOX'S allowlist recorded as a fact
    # about the operating system, and neither grounding gate can catch it
    # (verified: 'head' matches no impossible/suspect regex, and it DOES
    # appear in the evidence, so the causality judge sees support).
    # The block is deliberate. What cost the iteration was the bare
    # 35-name alphabetical dump, which left the model to guess a
    # substitute. Name it instead.
    COMMAND_SUBSTITUTES = {
        "head": "file_read with start_line/end_line",
        "tail": "file_read with start_line/end_line",
        "cat": "file_read",
        "ls": "list_dir",
        "grep": "grep_search   (it takes a FILE path or a directory)",
        "sed": "str_replace",
        "awk": "a .py file you create with file_write, then run",
        "wc": "a .py file you create with file_write, then run",
        "touch": "file_write",
        "mkdir": "file_write   (it creates parent directories automatically)",
        "cp": "file_read then file_write",
        "mv": "file_read then file_write   (renaming is blocked)",
        "which": "where",
        "export": "nothing - environment changes do not persist between calls",
    }

    # V22.1: destructive file operations reachable through inline Python.
    # In the temple_dash run the model was refused a file_write overwrite,
    # got BLOCKED on 'del', and then simply ran
    #   python -c "import os; os.remove('temple_dash.py')"
    # - deleting the file anyway, because segment validation only checks
    # the shell token ('python', allowed) and never the -c payload.
    # These patterns are scanned inside any inline python -c code and
    # block deletion, rename/replace (deletion of the target), and
    # write/truncate (a file_write-overwrite bypass).
    DESTRUCTIVE_PY_RE = re.compile(
        r"(os\s*\.\s*(remove|unlink|rmdir|removedirs|rename|replace)\s*\("
        r"|shutil\s*\.\s*(rmtree|move|copyfile|copy2?)\s*\("
        r"|\.\s*unlink\s*\("
        r"|\.\s*rmdir\s*\("
        r"|\.\s*write_text\s*\("
        r"|\.\s*write_bytes\s*\("
        r"|send2trash"
        r"|open\s*\([^)]*['\"](?:r\+|[wax]\+?)b?['\"])",
        re.IGNORECASE,
    )

    @classmethod
    def _destructive_inline_py(cls, command: str):
        """Return the offending pattern if an inline `python -c` payload
        contains a destructive file operation, else None."""
        for seg in cls._split_segments(command):
            parts = seg.split()
            if not parts:
                continue
            head = re.sub(r"\.(exe|bat|cmd)$", "", os.path.basename(parts[0]).lower())
            if head in ("python", "python3", "py") and ("-c" in parts):
                m = cls.DESTRUCTIVE_PY_RE.search(seg)
                if m:
                    return m.group(0)
        return None

    @staticmethod
    def _write_redirection(command: str):
        """V25: quote-aware scan for shell WRITE redirection. '>' and '>>'
        overwrite/truncate files while segment validation only ever looks
        at each segment's HEAD token - `echo x > snake.py` sailed through
        and defeated both the file_write no-overwrite guard and
        DESTRUCTIVE_PY_RE (same bypass class as the temple python -c
        incident). Returns the offending snippet, or None.
        '2>&1' (fd duplication) stays legal; '>' inside quotes
        (e.g. python -c "print('a > b')") is ignored."""
        quote = None
        i, n = 0, len(command)
        while i < n:
            ch = command[i]
            if quote:
                if ch == quote:
                    quote = None
                i += 1
                continue
            if ch in ("'", '"'):
                quote = ch
                i += 1
                continue
            if ch == ">":
                nxt = command[i + 1] if i + 1 < n else ""
                if nxt == "&":  # 2>&1-style fd duplication - harmless
                    i += 2
                    continue
                return command[max(0, i - 8):i + 12].strip()
            i += 1
        return None

    @staticmethod
    def _safe_kill(proc) -> None:
        """V60.3: kill a process that may ALREADY BE DEAD.

        Every call site is inside an `except asyncio.TimeoutError:` handler,
        and by the time that handler runs the process may have exited on its
        own - a program that finishes in the same instant the timeout fires,
        or, on Windows, one the taskkill tree-kill just reaped a moment
        before the fallback runs. asyncio's Process.kill() then raises
        ProcessLookupError (confirmed by execution on 3.12), and an exception
        raised INSIDE an except block is not caught by that try's sibling
        handlers: at the run_verification site the neighbouring
        `except Exception` cannot see it, so it escaped the function
        entirely and a timed-out verification became an unhandled crash
        instead of the "⚠️ Verification timed out (15s)" string.

        Two guards, because the check alone is a race - returncode can still
        read None while the OS has already reaped the process:
          - skip the kill outright when the exit is already known;
          - swallow ProcessLookupError, which means the only thing this
            function wanted has already happened.
        Nothing else is swallowed: a real failure (PermissionError, a broken
        transport) still propagates, because that is a fact about the
        machine's own environment and must not be laundered away.
        """
        if proc.returncode is not None:
            return
        try:
            proc.kill()
        except ProcessLookupError:
            pass  # already exited between the timeout and this line

    @staticmethod
    async def _kill_tree(proc):
        """V25: kill a subprocess AND its children, then wait bounded.
        proc.kill() only terminates the DIRECT child - with
        create_subprocess_shell on Windows that is cmd.exe, which orphans
        the real program still holding the stdout/stderr pipes. Every
        timeout path must use this, or the orphan either wedges the caller
        (main execute) or leaks a live process (run_verification)."""
        if sys.platform == "win32":
            try:
                tk = await asyncio.create_subprocess_exec(
                    "taskkill", "/PID", str(proc.pid), "/T", "/F",
                    stdout=asyncio.subprocess.DEVNULL,
                    stderr=asyncio.subprocess.DEVNULL,
                )
                await asyncio.wait_for(tk.wait(), timeout=5)
            except Exception:
                # V60.3: was a bare proc.kill(). See _safe_kill - this is the
                # exact path where the process is most likely already dead,
                # because taskkill may have killed it and then hung or
                # errored on its own wait.
                BashTool._safe_kill(proc)  # fallback: at least kill the shell
        else:
            BashTool._safe_kill(proc)
        try:
            await asyncio.wait_for(proc.wait(), timeout=5)
        except asyncio.TimeoutError:
            pass  # orphan still holds pipes; never wedge the caller
    
    @classmethod
    def get_allowed(cls):
        """Return the allowed commands. V25: Windows-only by design - the
        old else-branch referenced ALLOWED_UNIX, which never existed
        (latent AttributeError on any non-Windows box)."""
        return cls.ALLOWED_CROSS_PLATFORM | cls.ALLOWED_WINDOWS
    
    @property
    def ALLOWED(self):
        """Property for backward compatibility"""
        return self.get_allowed()
    
    # V21: GUI frameworks whose apps block forever by design
    GUI_MARKERS = ("tkinter", "pygame", "turtle", "PyQt5", "PyQt6", "PySide2",
                   "PySide6", "kivy", "arcade")

    @staticmethod
    def _split_segments(command: str) -> list:
        """
        V21: quote-aware split on shell chaining operators (&&, ||, ;, |, &)
        so EVERY chained part gets validated - not just the first token.
        Redirections like 2>&1 are preserved (the & after > is not a chain).
        """
        segments, buf, quote = [], [], None
        i, n = 0, len(command)
        while i < n:
            ch = command[i]
            if quote:
                buf.append(ch)
                if ch == quote:
                    quote = None
                i += 1
                continue
            if ch in ("'", '"'):
                quote = ch
                buf.append(ch)
                i += 1
                continue
            if command[i:i + 2] in ("&&", "||"):
                segments.append("".join(buf))
                buf = []
                i += 2
                continue
            if ch == "&" and buf and buf[-1] == ">":
                buf.append(ch)  # part of a redirection like 2>&1
                i += 1
                continue
            if ch in (";", "|", "&"):
                segments.append("".join(buf))
                buf = []
                i += 1
                continue
            buf.append(ch)
            i += 1
        segments.append("".join(buf))
        return [s.strip() for s in segments if s.strip()]

    def _gui_file_in_command(self, parts: list) -> str:
        """
        If the command runs a local .py file that imports a GUI framework,
        return that filename, else None. Used to reinterpret a 60s timeout
        as "launched and stayed alive" instead of a failure.
        """
        try:
            for arg in parts[1:]:
                if arg.startswith("-") or not arg.endswith(".py"):
                    continue
                try:
                    resolved = self.validator.validate(arg)
                except SecurityError:
                    return None
                if not resolved.exists():
                    return None
                with open(resolved, "r", encoding="utf-8", errors="replace") as f:
                    head = f.read()
                if any(m in head for m in self.GUI_MARKERS):
                    return arg
                return None
        except Exception:
            return None
        return None

    async def execute(self, command: str, timeout=None) -> str:
        # V25: the model kept passing "timeout" (often as a string) and the
        # V23 schema filter silently discarded it - it believed it set 30s
        # while the hardcoded 60 applied. Now declared, coerced, clamped.
        try:
            tool_timeout = max(1, min(int(timeout), 60)) if timeout is not None else 60
        except (TypeError, ValueError):
            tool_timeout = 60
        parts = command.split()
        if not parts:
            return "Error: Empty command"
        
        # V21: validate EVERY chained segment, not just the first token.
        # In V20, `echo ok && del /s /q *` passed validation because only
        # `echo` was checked - the shell then executed the forbidden half.
        allowed = self.get_allowed()
        checked = []
        for seg in self._split_segments(command):
            seg_parts = seg.split()
            if not seg_parts:
                continue
            seg_cmd = os.path.basename(seg_parts[0]).lower()
            seg_cmd = re.sub(r"\.(exe|bat|cmd)$", "", seg_cmd)
            checked.append(seg_cmd)
            # V25: validate the cd target - 'cd' was allowed with ANY
            # argument, so 'cd .. && type file' operated outside the
            # sandbox that PathValidator guards everywhere else.
            if seg_cmd == "cd":
                cd_arg = seg.strip()[2:].strip()
                if cd_arg.lower().startswith("/d "):  # cmd.exe drive flag
                    cd_arg = cd_arg[3:].strip()
                cd_arg = cd_arg.strip('"').strip("'")
                if cd_arg:
                    try:
                        self.validator.validate(cd_arg)
                    except SecurityError as e:
                        return str(e)
            if seg_cmd in self.FORBIDDEN:
                return (f"BLOCKED: '{seg_cmd}' is forbidden for safety "
                        f"(found inside a chained command). Use built-in tools instead.")
            if seg_cmd not in allowed:
                sub = self.COMMAND_SUBSTITUTES.get(seg_cmd)
                return (f"BLOCKED: command '{seg_cmd}' not in allowed list "
                        f"(every part of a chained command must be allowed)."
                        + (f"\nUSE THIS INSTEAD: {sub}" if sub else "")
                        + f"\nThis is THIS SANDBOX'S allowlist - a rule of this "
                          f"agent, NOT a limitation of the operating system. Do "
                          f"not conclude anything about Windows from it.\n"
                        + f"Allowed: {', '.join(sorted(allowed))}")
        # V22.1: scan inline python -c payloads for destructive file ops
        # (the os.remove bypass from the temple_dash run).
        destructive = self._destructive_inline_py(command)
        if destructive:
            return (f"BLOCKED: inline python containing '{destructive}' is forbidden - "
                    f"files in this sandbox cannot be deleted, renamed over, or "
                    f"overwritten from bash. Use str_replace to modify an existing "
                    f"file (in several calls if the change is large); file_write "
                    f"only creates NEW files.")
        # V25: shell write-redirection is the same bypass class ('echo x >
        # file.py' overwrites; 'type nul > file.py' truncates; targets were
        # never path-validated). Blocked outright - the agent has file_write
        # and str_replace for every legitimate write. 2>&1 remains allowed.
        redirect = self._write_redirection(command)
        if redirect:
            return (f"BLOCKED: shell write-redirection ('{redirect}') is forbidden - "
                    f"redirecting output to a file can overwrite files or escape "
                    f"the sandbox. Use file_write to create NEW files and "
                    f"str_replace to modify existing ones. (2>&1 is still allowed.)")
        base_cmd = checked[0] if checked else ""
        
        # =================================================================
        # SERVER DETECTION - Block commands that hang forever + AUTO-VERIFY
        # =================================================================
        cmd_lower = command.lower()
        # V30.5: any bash mention of the runtime's own filename is the
        # self-read / self-run pattern - refuse outright, before any
        # other check.
        if MACHINE_SELF.name.lower() in cmd_lower:
            return SELF_BLOCK_MSG.format(name=MACHINE_SELF.name)
        
        # Helper to run verification commands
        async def run_verification(verify_cmd: str, work_dir: Path) -> str:
            """Run a safe verification command and return the result"""
            try:
                proc = await asyncio.create_subprocess_shell(
                    verify_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=work_dir,
                    env=utf8_subprocess_env()  # V30.4: cp1252-proof children
                )
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=15)
                out = stdout.decode(errors='replace').strip()
                err = stderr.decode(errors='replace').strip()
                
                if proc.returncode == 0:
                    return f"✅ VERIFIED: {out or 'Success (no output)'}"
                else:
                    return f"❌ VERIFICATION FAILED:\n{err or out or 'Unknown error'}"
            except asyncio.TimeoutError:
                # V25: same orphan class as the main path. This used to
                # return WITHOUT killing anything - a verify command that
                # hung (e.g. an app.py that starts its server at import
                # time, which is exactly what this function probes) leaked
                # a live process holding the pipes.
                await self._kill_tree(proc)
                return "⚠️ Verification timed out (15s)"
            except Exception as e:
                return f"⚠️ Verification error: {e}"
        
        # Parse out `cd <dir> &&` prefix to get target directory
        target_dir = self.validator.working_dir
        actual_cmd = command
        
        if " && " in command:
            parts_split = command.split(" && ", 1)
            first_part = parts_split[0].strip()
            if first_part.lower().startswith("cd "):
                dir_name = first_part[3:].strip().strip('"').strip("'")
                potential_dir = self.validator.working_dir / dir_name
                if potential_dir.exists() and potential_dir.is_dir():
                    target_dir = potential_dir
                actual_cmd = parts_split[1] if len(parts_split) > 1 else command
        
        # Patterns that indicate server/long-running process with their verifications
        server_patterns = [
            ("flask run", "flask", "python -c \"import flask; from app import app; print('Flask app OK')\""),
            ("uvicorn ", "uvicorn", "python -c \"import uvicorn; print('Uvicorn OK')\""),
            ("gunicorn ", "gunicorn", "python -c \"import gunicorn; print('Gunicorn OK')\""),
            ("streamlit run", "streamlit", "python -c \"import streamlit; print('Streamlit OK')\""),
            ("python -m flask", "flask", "python -c \"import flask; from app import app; print('Flask app OK')\""),
            ("python -m uvicorn", "uvicorn", "python -c \"import uvicorn; print('Uvicorn OK')\""),
            ("python -m http.server", "http.server", "python -c \"import http.server; print('http.server OK')\""),
        ]
        
        for pattern, name, verify_cmd in server_patterns:
            if pattern in cmd_lower:
                result = await run_verification(verify_cmd, target_dir)
                run_hint = f"cd {target_dir.name} && flask run" if "flask" in name.lower() else f"cd {target_dir.name} && {actual_cmd}"
                return (
                    f"🚫 SERVER BLOCKED: '{name}' runs forever and would hang.\n\n"
                    f"🔍 AUTO-VERIFICATION in {target_dir.name}/:\n"
                    f"   > {verify_cmd}\n"
                    f"   {result}\n\n"
                    f"✅ Your server code is ready! Tell the user to run it manually with:\n"
                    f"   {run_hint}"
                )
        
        # Detect `python app.py` or `python main.py` etc (likely servers)
        # But allow `python -c`, `python -m pytest`, `python script.py --test`
        if base_cmd in ("python", "python3", "py"):
            # Check if it's running a .py file directly (not -c, -m, etc.)
            has_py_file = any(arg.endswith('.py') for arg in parts[1:] if not arg.startswith('-'))
            has_safe_flag = any(f in cmd_lower for f in [' -c ', ' -m pytest', ' -m unittest', '--test', '--check', '--dry-run', '--version', '--help'])
            
            if has_py_file and not has_safe_flag:
                # Check if it looks like a web app file
                web_indicators = ['app.py', 'main.py', 'server.py', 'wsgi.py', 'asgi.py', 'run.py', 'web.py', 'api.py']
                # V28.1: EXACT basename match, not substring. 'app.py' in
                # cmd_lower also matched guiapp.py / snakeapp.py / whatsapp.py,
                # rerouting a pygame launch into SERVER BLOCKED + pointless
                # import-verification instead of the GUI LAUNCHED-OK path.
                # Same trap class as grep_search's file rejection: a hard
                # misroute of a perfectly reasonable call. (Found live by the
                # V28.1 test harness, not in a run log.)
                py_basenames = [os.path.basename(a).lower() for a in parts[1:]
                                if a.endswith('.py') and not a.startswith('-')]
                for indicator in web_indicators:
                    if indicator in py_basenames:
                        # Extract module name from filename
                        module_name = indicator.replace('.py', '')
                        
                        # Try multiple verification approaches
                        verify_commands = [
                            f'python -c "import {module_name}; print(\'{module_name} imports OK\')"',
                            f'python -c "from {module_name} import *; print(\'All exports OK\')"',
                        ]
                        
                        # If it's app.py, also try Flask-specific check
                        if module_name == 'app':
                            verify_commands.insert(0, 'python -c "from app import app; print(\'Flask app object OK\')"')
                        
                        # Run verifications until one succeeds
                        results = []
                        success = False
                        for v_cmd in verify_commands:
                            result = await run_verification(v_cmd, target_dir)
                            results.append(f"   > {v_cmd}\n   {result}")
                            if "✅" in result:
                                success = True
                                break  # Stop on first success
                        
                        status = "READY" if success else "NEEDS FIXES"
                        
                        return (
                            f"🚫 SERVER BLOCKED: '{indicator}' may run forever.\n\n"
                            f"🔍 AUTO-VERIFICATION in {target_dir.name}/:\n"
                            + "\n".join(results) + "\n\n"
                            f"📋 STATUS: {status}\n"
                            + (f"✅ Code verified! Tell user to run: cd {target_dir.name} && python {indicator}\n"
                               if success else
                               f"⚠️ Fix the errors above, then tell user to run: cd {target_dir.name} && python {indicator}\n")
                            + f"\nIf this is NOT a server, re-run with: python {indicator} --test"
                        )
        
        # Cross-platform command normalization (legacy support)
        if sys.platform == "win32":
            if command.strip().startswith("mkdir -p "):
                command = "mkdir " + command.replace("mkdir -p ", "").strip()
            elif command.strip().startswith("mkdir --parents "):
                command = "mkdir " + command.replace("mkdir --parents ", "").strip()

        # V175: A MULTI-LINE COMMAND IS TRUNCATED BY cmd.exe AND THE
        # TRUNCATION LOOKS LIKE SUCCESS.
        #
        # create_subprocess_shell runs `cmd.exe /c <command>` on Windows.
        # cmd.exe stops at the first newline, so a command that begins
        #
        #     python -c "
        #     import pygame, sys
        #     ...
        #     print(f'After _player_die: game_state={g.game_state}')
        #     "
        #
        # executes as `python -c "` - an EMPTY program. Python exits 0 and
        # prints nothing, the formatter below omits an empty STDOUT section,
        # and the model receives the single line `Exit code: 0`.
        # _detect_tool_success scores that a success. The model is told its
        # diagnostic ran fine and printed nothing.
        #
        # This ended the run of 2026-08-05 16:37. Measured in that log: 25
        # single-line bash calls, 23 returned output; ONE multi-line call -
        # the model's final diagnostic, the one command that would have shown
        # it why its assertion failed - returned `Exit code: 0` and nothing
        # else. Two turns later the model produced a message with no tool
        # call and the run ended at iteration 130 with a red self-test.
        #
        # The fix keeps the capability instead of refusing it: the code is
        # written to a real file in the working directory and run as a
        # script. Deliberately NOT gated on sys.platform - one code path that
        # is exercised everywhere beats a Windows-only branch that cannot be
        # tested off Windows, and `python file.py` and `python -c` are
        # equivalent here (both give __name__ == "__main__", and putting the
        # file in the working directory gives the same sys.path[0]).
        _tmp_script = None
        _m = re.match(
            r'^\s*(python3?|py)\s+-c\s+(["\'])(.*)\2\s*(2>&1|>\s*\S+|)\s*$',
            command, re.DOTALL)
        if _m and "\n" in _m.group(3):
            try:
                _tmp_script = os.path.join(self.validator.working_dir,
                                           f"_wim_cmd_{os.getpid()}.py")
                with open(_tmp_script, "w", encoding="utf-8", newline="") as _f:
                    _f.write(_m.group(3))
                command = (f'{_m.group(1)} "{os.path.basename(_tmp_script)}" '
                           f'{_m.group(4)}').strip()
                debug_print(f"BASH: multi-line `-c` rewritten to "
                            f"{os.path.basename(_tmp_script)} - a shell would "
                            f"have truncated it at the first newline")
            except Exception as e:
                debug_print(f"BASH: could not stage multi-line command ({e}); "
                            f"running it as given")
                _tmp_script = None

        try:
            # Use asyncio subprocess for non-blocking execution
            # This allows the dashboard to keep refreshing during long commands
            proc = await asyncio.create_subprocess_shell(
                command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.validator.working_dir,
                env=utf8_subprocess_env()  # V30.4: cp1252-proof children
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=tool_timeout)
            except asyncio.TimeoutError:
                # V25: tree-kill via _kill_tree - proc.kill() only killed
                # the DIRECT child (cmd.exe on Windows), orphaning the real
                # program (e.g. the pygame window) with the pipes open and
                # wedging the machine at the wait until closed by hand.
                await self._kill_tree(proc)
                # V21: a GUI app that ran the full 60s without crashing LAUNCHED.
                # Reporting that as an error made the agent (and the episode
                # outcome) treat its own success as a failure.
                gui_file = self._gui_file_in_command(parts)
                if gui_file:
                    # V28.1: if --test was ALREADY in the command and the
                    # app still blocked until the timeout, the flag is NOT
                    # wired - a working --test exits in about a second. The
                    # old canned NEXT STEPS told the model to "confirm
                    # with: python <file> --test", i.e. the exact command
                    # that just hung (mario_snake tool [14]). ornith
                    # recovered by adding the branch; a weaker model loops.
                    if "--test" in parts:
                        return (
                            f"LAUNCHED OK - BUT YOUR --test FLAG IS NOT WIRED: '{gui_file}' "
                            f"opened a GUI window and blocked for the full {tool_timeout}s "
                            f"even though you passed --test. A working --test exits in about "
                            f"a second, so nothing in '{gui_file}' checks sys.argv for it.\n\n"
                            f"NEXT STEPS:\n"
                            f"1. Add the self-test branch to '{gui_file}' BEFORE the main loop:\n"
                            f"     if \"--test\" in sys.argv:\n"
                            f"         run_test(); raise SystemExit(0)\n"
                            f"2. Re-run: python {gui_file} --test\n"
                            f"Do NOT re-run '{gui_file}' until --test is wired - it will block again."
                        )
                    return (
                        f"LAUNCHED OK: '{gui_file}' opened a GUI window and ran for {tool_timeout}s "
                        f"without crashing (the timeout closed it - that is expected for "
                        f"windowed apps).\n\n"
                        f"NEXT STEPS:\n"
                        f"1. If the file has a --test mode, confirm with: python {gui_file} --test\n"
                        f"2. Otherwise verify imports: python -c \"import {Path(gui_file).stem}\"\n"
                        f"3. Tell the user to run it themselves: python {gui_file}\n"
                        f"Do NOT re-run '{gui_file}' without --test - it will block again."
                    )
                return (
                    f"Error: Command timed out ({tool_timeout}s)\n\n"
                    "⚠️ RECOVERY SUGGESTIONS:\n"
                    "• If running a GUI app: It may have started but is waiting for user interaction. "
                    "Add --headless or --test flags if available.\n"
                    "• If running a server: It may be running successfully in foreground. "
                    "Try running with & or using a shorter test command.\n"
                    "• If stuck on input: The program may be waiting for stdin. "
                    "Pipe input with: echo 'input' | command\n"
                    "• If genuinely slow: Break into smaller steps or increase timeout.\n\n"
                    "HINT: Consider what the program is WAITING for, not just that it timed out."
                )
            
            output = ""
            if stdout:
                output += f"STDOUT:\n{stdout.decode('utf-8', errors='replace')}\n"
            if stderr:
                output += f"STDERR:\n{stderr.decode('utf-8', errors='replace')}\n"
            output += f"\nExit code: {proc.returncode}"
            # V175: SILENCE IS NOT SUCCESS WHEN THE COMMAND WAS MEANT TO
            # SPEAK. `Exit code: 0` on its own is indistinguishable from a
            # command that ran and reported, and that is exactly what the
            # truncated diagnostic returned in the run of 2026-08-05 16:37.
            # Plenty of commands legitimately print nothing, so this does not
            # claim failure - it states the fact, and only escalates when the
            # command itself contains something whose whole job is to print.
            if not stdout and not stderr:
                _speaks = any(k in command for k in
                              ("print(", "echo ", "console.log", "printf",
                               "--version", "-V", "pprint", "sys.stdout"))
                output += "\n(the command produced NO OUTPUT on stdout or stderr)"
                if _speaks and proc.returncode == 0:
                    output += (
                        "\n\u26a0 It exited 0 yet printed nothing, and it "
                        "contains statements meant to print. Do NOT read this "
                        "as an answer - you have learned nothing from it. The "
                        "usual causes are that the program never reached the "
                        "print, or that the shell did not run the whole "
                        "command. Re-run it as a FILE you write with "
                        "file_write and execute by name, which cannot be "
                        "truncated and can be read back.")
            return output.strip() or "(No output)"
        except Exception as e:
            return f"Error: {str(e)}"
        finally:
            # V175: the staged script is scratch, not a deliverable - it must
            # not survive into the workspace where the artifact watcher and
            # the deliverable-selection logic would both see a new .py file.
            if _tmp_script:
                try:
                    os.unlink(_tmp_script)
                except OSError:
                    pass


class GrepSearchTool(BaseTool):
    name = "grep_search"
    description = "Search for a regex pattern in one file (pass its path) or recursively in a directory."
    parameters = {
        "type": "object",
        "properties": {
            "pattern": {"type": "string", "description": "Pattern to search"},
            "path": {"type": "string", "description": "File or directory to search (default: .)"},
            "file_pattern": {"type": "string", "description": "File glob (e.g., *.py)"}
        },
        "required": ["pattern"]
    }
    
    async def execute(self, pattern: str, path: str = ".", file_pattern: str = "*") -> str:
        try:
            resolved_path = self.validator.validate(path)
            # V28.1: accept a FILE path too. In the mario_snake run the
            # model greped 'mario_snake.py' for the def-signature map - a
            # completely natural call (grep takes files everywhere else in
            # the world) - and the hard "not a directory" rejection cost it
            # the overview at the exact moment it needed one, forcing a
            # fallback to paged file_read windows. Directories still
            # recurse exactly as before.
            if is_machine_self(resolved_path):
                return SELF_BLOCK_MSG.format(name=resolved_path.name)
            if resolved_path.is_file():
                candidates = [resolved_path]
                rel_base = resolved_path.parent
            elif resolved_path.is_dir():
                candidates = None  # recurse via rglob below
                rel_base = resolved_path
            else:
                return f"Error: '{path}' is not a file or directory"

            try:
                regex = re.compile(pattern, re.IGNORECASE)
            except re.error as e:
                return f"Invalid regex: {e}"
            
            results = []
            skip = {"__pycache__", "node_modules", ".git", "venv"}
            
            file_iter = candidates if candidates is not None else resolved_path.rglob(file_pattern)
            for file_path in file_iter:
                if not file_path.is_file():
                    continue
                if is_machine_self(file_path):
                    continue  # V30.5: runtime is invisible to missions
                # skip-set applies to directory recursion only: a file the
                # model names EXPLICITLY is searched wherever it lives.
                if candidates is None and any(
                    p in skip or p.startswith(".") for p in file_path.parts
                ):
                    continue
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line_num, line in enumerate(f, 1):
                            if regex.search(line):
                                rel = file_path.relative_to(rel_base)
                                results.append(f"{rel}:{line_num}: {line.rstrip()}")
                except (PermissionError, IOError):
                    continue
            
            if not results:
                return f"No matches found for '{pattern}'"
            if len(results) > 5000:
                return "\n".join(results[:5000]) + f"\n\n... and {len(results) - 5000} more"
            return "\n".join(results)
        except SecurityError as e:
            return str(e)
        except Exception as e:
            return f"Error: {str(e)}"


def get_all_tools(working_dir: str = None) -> dict:
    return {
        "file_read": FileReadTool(working_dir),
        "file_write": FileWriteTool(working_dir),
        "str_replace": StrReplaceTool(working_dir),
        "list_dir": ListDirTool(working_dir),
        "bash": BashTool(working_dir),
        "grep_search": GrepSearchTool(working_dir),
    }


# V61.15: REASONING AS A TOOL PRECONDITION, NOT A PROMPT REQUEST.
#
# BUILD_PROMPT's second line is "You MUST use your tools... Do NOT just
# describe what you would do - actually DO it by calling the tools." That is
# an instruction to stop deliberating and act, it is the first substantive
# thing the model reads, and it is obeyed. Measured on the snake_game run of
# 2026-07-31 (seed 103603307, 18 iterations): 263,102 prompt tokens against
# 14,665 completion, an 18:1 read/write ratio, with a final context of 20,020
# of 256,000 - 92% of the window unused. Eight of eighteen turns spent 64-140
# completion tokens; five of those were "run the test again" and nothing else.
#
# The failure is not depth-of-thought, it is that nothing ever ASKS. Every
# turn's implicit question is "what tool next", and a small question gets a
# small answer. A prompt asking for more is advisory - it competes with the
# line above, it drifts over a long run, and there is no moment where the
# machine can tell whether it was followed. A REQUIRED TOOL FIELD is a
# precondition: the call does not exist without it.
#
# Each field below is here because a specific observed failure would have
# been surfaced by it, not because it sounded rigorous:
#
#   bash.expect - snake iteration 5. The model's own reasoning that turn
#     said "MOVE_INTERVAL = 100 with comment 'ms'... dt is in seconds...
#     would take ~100 seconds to trigger. This is definitely a bug! Let me
#     fix this properly." Then it ran the test instead, and fixed the bug two
#     turns later. It had the answer and dispatched anyway. Stating what a
#     run should show BEFORE running it makes "I already know this will not
#     tell me what I need" impossible to skip past silently.
#
#   str_replace.intent + .supersedes - booby_game steps 7-11: five
#     consecutive edits to ONE test block with no run between them, of which
#     the 10th and 11th differed only in whether the shark moved onto the
#     booby or the booby onto the shark. Naming what the previous edit failed
#     to do turns that loop into a written record the model has to read back;
#     two identical `supersedes` values in a row is a stall the machine can
#     see mechanically, which is what STALL_HINT below reports.
#
#   file_write.plan - the one-shot write is where the whole build is decided.
#     snake's first write was 16,405 bytes and carried a units contradiction
#     (MOVE_INTERVAL in ms, dt in seconds) that made the game move once per
#     ~104 seconds - written minutes apart, invisible without a design pass.
#     Enumerating the features and how --test will PROVE each one is the plan
#     step, enforced where it cannot be forgotten instead of asked for in a
#     prompt that competes with "actually DO it".
#
# These are stripped in ToolExecutor before tool.execute(**args), so no tool's
# signature changes and no existing behaviour moves.
REASONING_FIELDS = {
    "bash": {
        "expect": {
            "type": "string",
            "description": (
                "REQUIRED. What you expect this command to show, and what "
                "result would prove you WRONG. Be specific: name the output, "
                "exit code, or error you are predicting. If you already know "
                "what this will show, say why you are running it anyway."
            ),
        },
    },
    "str_replace": {
        "intent": {
            "type": "string",
            "description": (
                "REQUIRED. What behaviour this edit changes and why. If this "
                "edits a TEST rather than the code under test, say so "
                "explicitly and state what the test will still prove "
                "afterwards."
            ),
        },
        "supersedes": {
            "type": "string",
            "description": (
                "REQUIRED. If a previous edit to this file did not achieve "
                "what you wanted, name what it failed to do. If this is the "
                "first edit to this region, write 'first edit'."
            ),
        },
    },
    "file_write": {
        "plan": {
            "type": "string",
            "description": (
                "Name each feature the task asks for and, for each one, the "
                "--test assertion that would FAIL if that feature were "
                "deleted. Add the units and type of any timing, position or "
                "score value shared between two functions. A few lines, not "
                "an essay. Include `content` complete in this same call - a "
                "truncated file is a failed call."
            ),
        },
    },
}

# V61.22: TOOLS WHOSE RETRY COST IS THE WHOLE PAYLOAD ARE NEVER REJECTED.
#
# The spongebob run of 2026-08-01 opened like this: file_write without
# `plan` -> CALL REJECTED. file_write without `plan` -> CALL REJECTED.
# file_write without `plan` -> accepted, because REASONING_MAX_BOUNCES had
# run out. Three complete 21KB files, 6,634 and 6,544 completion tokens
# burned on the two that were thrown away, ~3 minutes for zero progress, and
# the field was never supplied even once. The model was not being stubborn;
# it was doing what I told it to. My own description opened with "REQUIRED,
# and SECONDARY: write `content` in full FIRST - no plan is worth losing a
# line of it", which was written to stop V61.15a's truncated-content bug and
# reads exactly like permission to skip the plan.
#
# The deeper error is the shape, not the wording. `bash.expect` and
# `str_replace.intent` cost a sentence to re-emit, so rejecting those is
# cheap and the model complies immediately - 18 of 19 filled on the earlier
# run. `file_write.plan` costs the ENTIRE FILE to re-emit, and the model did
# not even re-issue: writes 1, 2 and 3 were different files, rewritten from
# scratch each time, which is how a NameError on an undefined `Lanes` got
# traded for a NameError on an undefined `FPS`.
#
# So: the cost of a bounce must be proportional to the size of the argument
# being retried. For tools listed here the field stays in the schema and is
# still asked for, but a missing one NEVER blocks the call - the work is
# accepted and the question is appended to the RESULT, which the model
# answers on the next turn for the price of a sentence.
REASONING_ASK_AFTER = {"file_write"}

# Minimum characters for a reasoning field to count as answered. Deliberately
# low: this is a floor against an empty string or "ok", not a word count the
# model has to pad to hit. The stall check below does the real work.
REASONING_MIN_CHARS = 24
# V61.24: ...except where the schema itself prescribes a SHORT answer.
# `supersedes` says, verbatim, "If this is the first edit to this region,
# write 'first edit'." That is 10 characters against a 24-character floor, so
# the model did exactly as instructed and was rejected for it - the machine
# contradicting its own documentation, at the first edit of the run. Kept as
# a separate table so the schema entries stay clean JSON: anything added to
# REASONING_FIELDS is copied straight into the tool schema sent to Ollama,
# and a stray key there is a wire-format change, not a config change.
REASONING_SENTINELS = {
    ("str_replace", "supersedes"): ("first edit",),
}
# How many times ONE tool may be bounced for a missing field before the call
# is let through with a note. Bounded like every other gate in this file - a
# gate that can loop is worse than no gate.
REASONING_MAX_BOUNCES = 2


def get_tool_schemas(tools: dict) -> list:
    """V61.15: schemas carry the reasoning fields the executor then requires."""
    out = []
    for tool in tools.values():
        s = tool.to_schema()
        extra = REASONING_FIELDS.get(getattr(tool, "name", ""))
        if not extra:
            out.append(s)
            continue
        try:
            fn = s.get("function", s)
            params = fn.get("parameters") or {}
            props = dict(params.get("properties") or {})
            req = list(params.get("required") or [])
            ask_after = getattr(tool, "name", "") in REASONING_ASK_AFTER
            for k, v in extra.items():
                props[k] = dict(v)
                # V61.22: only advertise as required what is actually
                # enforced. Listing a field as required and then letting the
                # call through after two bounces teaches the model that
                # "required" is negotiable - and it is the same schema that
                # carries `content`, which genuinely is.
                if not ask_after and k not in req:
                    req.append(k)
            # rebuild rather than mutate: to_schema() may hand back a
            # reference into the class-level `parameters` dict, and editing
            # that in place would corrupt the tool for every later call and
            # for the executor's own declared-argument filter.
            fn["parameters"] = {**params, "properties": props, "required": req}
        except Exception as e:
            debug_print(f"could not attach reasoning fields to "
                        f"{getattr(tool, 'name', '?')}: {e}")
        out.append(s)
    return out


# =============================================================================
# EPISODE MEMORY - Persistent Learning Across Sessions
# =============================================================================

@dataclass
class Episode:
    """Single learning episode from a completed task"""
    task: str
    trajectory: list  # [(tool_name, args_summary, success, evidence_note), ...]
    outcome: str  # "success" | "failure" | "partial"
    reflection: str  # The lesson (V21.1: evidence-based, validated)
    iterations: int
    token_cost: int
    timestamp: str
    embedding: list = None  # Semantic vector for similarity search
    # V21.1: structured learning fields (per the V21 review). Old episode
    # files load fine - these default to empty for pre-V21.1 records.
    failure_class: str = ""   # deterministic classification of primary failure
    root_cause: str = ""      # evidence-derived cause of the primary failure
    fix: str = ""             # what repair was applied
    verification: str = ""    # how success was proven
    confidence: float = 0.0   # model confidence in the lesson (0-1)
    grounded: bool = True     # V24: False = judge could not tie lesson to evidence
    # V45: generation params. Without these an episode cannot be interpreted
    # later - a run at temp 0.15 and a run at 0.6 are indistinguishable in
    # the log. -1 / "" = unrecorded (pre-V45 records).
    temperature: float = -1.0
    seed: int = -1
    model: str = ""
    # V45.1: a seed only reproduces within one Ollama build/backend.
    # Without this, 'seed 1847362' is not a replayable coordinate.
    ollama_version: str = ""
    mutation_history: list = None  # V61.26: what the MUTATION GATE actually
    # measured, one entry per firing. Persisted because it was the only
    # evidence that could refute a summary claiming rounds that did not
    # happen - and it existed nowhere but a chat message and a debug line.
    thinking_log: list = None  # V30.9: [(step, thinking), ...] model reasoning,
    # review-only. Defaults None so pre-V30.9 episodes load unchanged.
    
    def to_dict(self) -> dict:
        d = {
            "task": self.task,
            "trajectory": self.trajectory,
            "outcome": self.outcome,
            "reflection": self.reflection,
            "iterations": self.iterations,
            "token_cost": self.token_cost,
            "timestamp": self.timestamp,
            "failure_class": self.failure_class,
            "root_cause": self.root_cause,
            "fix": self.fix,
            "verification": self.verification,
            "confidence": self.confidence,
            "grounded": self.grounded,
            "temperature": self.temperature,
            "seed": self.seed,
            "model": self.model,
            "ollama_version": self.ollama_version
        }
        if self.embedding:
            d["embedding"] = self.embedding
        if self.thinking_log:
            d["thinking_log"] = self.thinking_log
        if self.mutation_history:
            d["mutation_history"] = self.mutation_history
        return d
    
    @staticmethod
    def from_dict(d: dict) -> "Episode":
        return Episode(
            task=d["task"],
            trajectory=d["trajectory"],
            outcome=d["outcome"],
            reflection=d["reflection"],
            iterations=d["iterations"],
            token_cost=d["token_cost"],
            timestamp=d["timestamp"],
            embedding=d.get("embedding"),
            failure_class=d.get("failure_class", ""),
            root_cause=d.get("root_cause", ""),
            fix=d.get("fix", ""),
            verification=d.get("verification", ""),
            confidence=d.get("confidence", 0.0),
            grounded=d.get("grounded", True),
            temperature=d.get("temperature", -1.0),
            seed=d.get("seed", -1),
            model=d.get("model", ""),
            ollama_version=d.get("ollama_version", ""),
            thinking_log=d.get("thinking_log"),
            mutation_history=d.get("mutation_history")
        )


class EpisodeMemory:
    """
    Persistent episode storage with semantic search.
    
    Uses Ollama embeddings for meaning-based similarity, not keyword matching.
    A task about "pygame platformer" will match "make snake game" because
    they're semantically related (game development), not because they share words.
    """
    
    def __init__(self, working_dir: str, embedding_model: str = "nomic-embed-text:latest"):
        self.working_dir = Path(working_dir)
        self.filepath = self.working_dir / "episodes.jsonl"
        self.embedding_model = embedding_model
        self.base_url = "http://localhost:11434"
        self.episodes: list[Episode] = []
        self._embeddings_available = None  # Lazy check
        self._load()
    
    def _load(self):
        """Load episodes from disk"""
        self.episodes = []
        # V45.8: [(lineno, reason), ...] - lines that could not be parsed.
        self.load_errors = []
        if self.filepath.exists():
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    for lineno, line in enumerate(f, 1):
                        line = line.strip()
                        if not line:
                            continue
                        # V45.8: ONE malformed line used to abort the whole load,
                        # because the try wrapped the entire loop. Verified: a
                        # store of 9 valid episodes with a torn line at position
                        # 4 loaded THREE - six lessons gone, reported only by a
                        # debug_print that is invisible without -v. This file is
                        # appended to by a process that can be interrupted
                        # mid-write, so a torn last line is the EXPECTED failure,
                        # and its symptom is memory silently getting smaller.
                        try:
                            self.episodes.append(Episode.from_dict(json.loads(line)))
                        except Exception as e:
                            self.load_errors.append(
                                (lineno, f"{type(e).__name__}: {e}"))
                            debug_print(f"Skipped malformed episode line "
                                        f"{lineno}: {e}")
                debug_print(f"Loaded {len(self.episodes)} episodes from {self.filepath}")
            except Exception as e:
                self.load_errors.append((0, f"{type(e).__name__}: {e}"))
                debug_print(f"Failed to load episodes: {e}")
    
    async def check_embeddings_available(self) -> bool:
        """Check if embedding model is available"""
        if self._embeddings_available is not None:
            return self._embeddings_available
        
        if not HTTPX_AVAILABLE:
            self._embeddings_available = False
            return False
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                models = [m["name"] for m in response.json().get("models", [])]
                # Check if any embedding model is available
                self._embeddings_available = any(
                    "embed" in m.lower() or "nomic" in m.lower() 
                    for m in models
                )
                if not self._embeddings_available:
                    debug_print(f"No embedding model found. Run: ollama pull {self.embedding_model}")
        except Exception as e:
            debug_print(f"Failed to check embedding models: {e}")
            self._embeddings_available = False
        
        return self._embeddings_available
    
    async def get_embedding(self, text: str) -> list:
        """Get semantic embedding vector for text"""
        if not HTTPX_AVAILABLE:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/api/embeddings",
                    json={"model": self.embedding_model, "prompt": text[:32000]}  # based on nomic embed text 8192 token limit
                )
                if response.status_code == 200:
                    return response.json().get("embedding")
                else:
                    debug_print(f"Embedding failed: {response.status_code}")
                    return None
        except Exception as e:
            debug_print(f"Embedding error: {e}")
            return None
    
    @staticmethod
    def cosine_similarity(a: list, b: list) -> float:
        """Compute cosine similarity between two vectors"""
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = sum(x * x for x in a) ** 0.5
        norm_b = sum(x * x for x in b) ** 0.5
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)
    
    async def save(self, episode: Episode):
        """Save episode with embedding"""
        # Generate embedding for the task
        if await self.check_embeddings_available():
            episode.embedding = await self.get_embedding(episode.task + " " + episode.reflection)
        
        self.episodes.append(episode)
        try:
            with open(self.filepath, "a", encoding="utf-8") as f:
                f.write(json.dumps(episode.to_dict()) + "\n")
            debug_print(f"Saved episode: {episode.task[:500]}...")
        except Exception as e:
            debug_print(f"Failed to save episode: {e}")
    
    async def search(self, task: str, top_k: int = 50) -> list[tuple[float, Episode]]:
        """
        Find semantically similar episodes using embeddings.
        
        Returns list of (similarity_score, episode) tuples, sorted by similarity.
        Score ranges from -1 to 1, where 1 = identical meaning.
        """
        if not self.episodes:
            return []
        
        # Get embedding for the query
        if not await self.check_embeddings_available():
            debug_print("Embeddings not available, skipping search")
            return []
        
        # V21: heal any embedding-less episodes first so they can be found
        await self.backfill_embeddings()

        query_embedding = await self.get_embedding(task)
        if not query_embedding:
            return []
        
        # Score each episode by semantic similarity
        scored = []
        for ep in self.episodes:
            if ep.embedding:
                similarity = self.cosine_similarity(query_embedding, ep.embedding)
                scored.append((similarity, ep))
        
        # Sort by similarity (descending) and return top_k
        scored.sort(reverse=True, key=lambda x: x[0])
        return scored[:top_k]
    
    def _persist_all(self):
        """V21: rewrite the whole jsonl (used after backfilling embeddings)."""
        # V45.8: skipping a bad line on load means self.episodes is now a
        # SUBSET of the file. This function truncates and rewrites from that
        # subset, so backfill_embeddings would make the skip permanent - the
        # V45.8 load fix would have turned a load-time symptom into real
        # data loss. Refuse while the store is damaged; the operator is told
        # at startup and nothing overwrites the file until it is repaired.
        if getattr(self, "load_errors", None):
            debug_print(f"Refusing to rewrite {self.filepath.name}: "
                        f"{len(self.load_errors)} line(s) failed to load and "
                        f"a rewrite would delete them permanently.")
            return
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                for ep in self.episodes:
                    f.write(json.dumps(ep.to_dict()) + "\n")
        except Exception as e:
            debug_print(f"Failed to persist episodes: {e}")

    async def backfill_embeddings(self) -> int:
        """
        V21: episodes saved while no embedding model was installed have no
        vector and are invisible to search() forever. Once an embedding
        model IS available, retro-fit them so old lessons become findable.
        Returns how many episodes were backfilled.
        """
        if not await self.check_embeddings_available():
            return 0
        missing = [ep for ep in self.episodes if not ep.embedding]
        if not missing:
            return 0
        done = 0
        for ep in missing:
            vec = await self.get_embedding(ep.task + " " + ep.reflection)
            if vec:
                ep.embedding = vec
                done += 1
        if done:
            self._persist_all()
            debug_print(f"Backfilled embeddings for {done} episodes")
        return done

    def get_stats(self) -> dict:
        """Get memory statistics for dashboard"""
        if not self.episodes:
            return {"total": 0, "successes": 0, "failures": 0,
                    "with_embeddings": 0,
                    "load_errors": len(getattr(self, "load_errors", []))}
        
        successes = sum(1 for ep in self.episodes if ep.outcome == "success")
        failures = sum(1 for ep in self.episodes if ep.outcome == "failure")
        with_embeddings = sum(1 for ep in self.episodes if ep.embedding)
        return {
            "load_errors": len(getattr(self, "load_errors", [])),
            "total": len(self.episodes),
            "successes": successes,
            "failures": failures,
            "with_embeddings": with_embeddings
        }


# =============================================================================
# OLLAMA CLIENT
# =============================================================================

@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict
    index: int = 0


@dataclass
class ChatResponse:
    content: str
    tool_calls: list = None
    done: bool = True
    raw_response: dict = None  # Store raw response for debugging
    prompt_tokens: int = 0     # REAL token count from Ollama (prompt_eval_count)
    completion_tokens: int = 0 # REAL token count from Ollama (eval_count)
    # Ollama returns these on every /api/chat reply, in NANOSECONDS.
    # Verified against docs.ollama.com/api/usage. eval_duration can be
    # ABSENT on an empty completion (ollama/ollama#8553), so read with
    # .get() and default to 0 - never assume the key is there.
    total_duration_ns: int = 0
    load_duration_ns: int = 0
    prompt_eval_duration_ns: int = 0
    eval_duration_ns: int = 0
    thinking: str = ""         # V30.9: the model's reasoning channel. Ollama
    # returns this separately from content; the machine had been dropping it.
    # Captured into the EPISODE for review only - never fed back into the
    # message history the model sees. Diagnostic: the mario_snake run showed
    # the model confabulating in `thinking` ("I see the issue" / "the tests
    # are passing") one step before any evidence existed, while content was
    # a bland summary - and that reasoning was invisible because it was never
    # stored. This makes it visible without changing behavior.


class OllamaClient:
    # V61.1: KEEPING THE BUILD PROMPT HOT.
    #
    # Ollama already prefix-caches: the KV cache for a prompt prefix is reused
    # when the next request starts with the SAME BYTES. This machine already
    # satisfies that - self.system_prompt is assigned once and never mutated,
    # injected lessons are appended as a Message rather than folded into the
    # system prompt, and self.messages is append-only. So api_messages is a
    # growing list behind a byte-identical prefix, which is exactly the shape
    # the cache wants. Two things were still missing:
    #
    #   keep_alive - Ollama unloads the model after 5 MINUTES of inactivity by
    #     default and the KV cache goes with it. That is ordinary think-time
    #     between tasks at the prompt, so the build prompt was being re-read
    #     from cold constantly. This is a TOP-LEVEL field on /api/chat, not an
    #     option. Set to "-1" to pin the model in VRAM forever, or "0" to go
    #     back to unloading immediately. OLLAMA_KEEP_ALIVE does the same thing
    #     server-wide if you would rather not set it per request.
    #
    #   num_keep - the number of leading tokens that survive a context shift.
    #     Without it, when the window fills, the OLDEST tokens are discarded
    #     first, and the oldest tokens are the system prompt. The audit run of
    #     2026-07-29 reached 96% of 256K, which is exactly where this bites.
    #     Set per-agent by _sync_prompt_cache() below, from the real prompt.
    #
    # Both are here as module-visible attributes so you can change them in one
    # place, or set KEEP_ALIVE to None to send nothing at all.
    # V61.4: None means "send nothing", which is what Ollama saw before I
    # touched this. Set EXPERIMENTAL["ollama_keep_alive"] = True to use it.
    KEEP_ALIVE = "30m" if EXPERIMENTAL.get("ollama_keep_alive") else None
    # Ceilings on the computed num_keep: never pin more than this many tokens,
    # and never more than this fraction of the context window.
    NUM_KEEP_MAX = 65536
    NUM_KEEP_CTX_FRACTION = 0.75
    # 30 min for complex generations. The timeout message quotes THIS.
    # NOTE: with stream=False this is a TOTAL budget and its expiry hands
    # the caller nothing at all - no partial text, no token count, no
    # timings. That absence is why a stall could not be diagnosed.
    REQUEST_TIMEOUT_S = 900.0
    # V61.29: streaming budgets. STREAM_STALL_S is SILENCE, not total
    # runtime - the clock resets on every chunk. 500s of dead air from a
    # server that was mid-generation is a wedge, not slow hardware.
    STREAM_STALL_S = 500.0
    # V61.30: streaming has NO total budget of its own - httpx's read timeout
    # only measures SILENCE, so a model generating steadily at 57 tok/s runs
    # unbounded. On the 2026-08-04 21:06 run the measured decay curve puts
    # generation at ~57 tok/s by 86k context and num_ctx=256000 leaves 170k
    # tokens of headroom - 49 minutes of legal, non-silent output. Switching
    # to stream=True therefore RAISED the worst case from 30 min to 49 min
    # until this existed. It is a WALL-CLOCK budget, not a num_predict cap:
    # nothing is truncated by token count, and when it trips the caller gets
    # the partial output plus the measurement instead of a black box.
    STREAM_TOTAL_BUDGET_S = REQUEST_TIMEOUT_S
    # V177: A GENERATION LOOP IS A COLLAPSE IN NOVELTY, NOT A REPEATED LINE.
    #
    # The V61 watch counted identical normalised LINES of >= 40 chars and
    # cancelled at 8 repeats. On the snake run of 2026-08-06 that fired twice
    # and then missed the third loop - the one that ended the run - because a
    # degenerate generation does not repeat lines, it repeats CONTENT with
    # different line breaks. Measured on that exact message: the most-repeated
    # line occurred 5 times against a threshold of 8, and 127 of its 191 lines
    # were under 40 chars and therefore invisible to the counter. It was
    # delivered as a normal response, carried no tool call, and the loop read
    # that as "finished" at iteration 110 of a 1,000,000 budget.
    #
    # Raising or lowering the 40-char floor cannot fix that. Raising it skips
    # MORE lines; lowering it starts counting `)` and blank-ish lines, which
    # repeat legitimately in every file ever written. The unit was wrong.
    #
    # What is actually true of a loop is that it stops saying anything new.
    # So: hash 8-word shingles of everything generated so far, and for each
    # WINDOW chars of new output measure the fraction of its shingles never
    # seen before in this generation. Healthy output is ~1.0. A loop is ~0.0.
    # Line breaks, re-wrapping and small rewordings do not affect it.
    #
    # MEASURED, on real artifacts, worst value over STREAK consecutive
    # windows (the number the threshold has to separate):
    #
    #   the degenerate snake message that slipped through   0.08
    #   ... a model writing snake_game.py                   1.00
    #   ... its --test block, 60 near-identical asserts     1.00
    #   ... 300 lines of near-identical enumeration         0.74
    #   ... a file containing a duplicated 2.4k function    1.00
    #   ... a file re-emitting a 3k block it already wrote  0.86
    #
    # 0.25 sits almost exactly at the geometric mean of 0.08 and 0.74, so it
    # is 3x clear of the worst legitimate case and 3x clear of the real one.
    # Cancels at 3,600 chars; on the message above it would have cancelled at
    # 6,600, where the OLD line rule needed 7,455 - so this is also faster on
    # his own data, not a latency trade. Records only unless
    # EXPERIMENTAL['ollama_stream_loop_cancel'] is on, exactly as before.
    STREAM_NOVELTY_SHINGLE = 8      # words per shingle
    STREAM_NOVELTY_WINDOW = 600     # chars of new output per measurement
    STREAM_NOVELTY_MIN = 0.25       # below this the window said nothing new
    STREAM_NOVELTY_STREAK = 6       # consecutive low windows before cancelling

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "ornith:35b", options: dict = None):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.options = options or {"num_ctx": 256000, "temperature": 0.6} # Default = 32768

    def sync_prompt_cache(self, system_prompt: str, task: str = "") -> int:
        """Pin the system prompt AND the task against context-shift eviction.

        num_keep is NOT "how much is cached" - prefix caching already covers
        100% of whatever prefix is unchanged, with no ceiling. num_keep is the
        number of LEADING tokens that survive when the window overflows: the
        runtime keeps the first num_keep tokens, discards a chunk after them,
        and keeps the recent tail. Setting it to the whole window would leave
        nothing to discard and no room for new tokens, so the shift that keeps
        a long run alive could not happen at all. It has to be a slice.

        V61.2: the slice now covers the TASK too. Pinning only the system
        prompt meant a long run could survive a context shift still knowing
        HOW to work while having forgotten WHAT it was asked to build - the
        worse of the two losses. Measured on the real prompts: BUILD_PROMPT is
        11,585 chars, so build prompt + his 364-char mission pins ~4,111
        tokens (1.6% of a 256K window) and build prompt + the 27,131-char
        STUDIO prompt pins ~13,033 (5.1%). The ceilings below never bind at
        those sizes; they exist only so a pathologically large prompt on a
        small window cannot pin the window shut.

        Estimates tokens as chars/3, which OVER-counts for English and code -
        deliberately, because over-counting only pins a little extra, while
        under-counting would let the tail of the prompt fall off the front.
        Returns the value actually set.
        """
        # V61.4: off by default - this option was never run against your model.
        if not EXPERIMENTAL.get("ollama_num_keep"):
            self.options.pop("num_keep", None)
            return 0
        est = (len(system_prompt or "") + len(task or "")) // 3 + 128
        ctx = int(self.options.get("num_ctx", 0) or 0)
        cap = self.NUM_KEEP_MAX
        if ctx:
            cap = min(cap, int(ctx * self.NUM_KEEP_CTX_FRACTION))
        self.options["num_keep"] = max(0, min(est, cap))
        debug_print(f"num_keep set to {self.options['num_keep']} "
                    f"(prompt {len(system_prompt or '')} chars"
                    + (f" + task {len(task)} chars)" if task else ")")
                    + (" [CLAMPED]" if est > cap else ""))
        return self.options["num_keep"]

    async def chat(self, messages: list, tools: list = None) -> ChatResponse:
        if not HTTPX_AVAILABLE:
            return ChatResponse(content="Error: httpx not installed. Run: pip install httpx")
        
        payload = {
            "model": self.model,
            "messages": messages,
            "options": self.options,
            "stream": False,
        }
        # V61.1: top-level, per the Ollama API - it is NOT an entry in options.
        if self.KEEP_ALIVE is not None:
            payload["keep_alive"] = self.KEEP_ALIVE
        if tools:
            payload["tools"] = tools
        
        debug_print("Sending to Ollama:", {"model": self.model, "message_count": len(messages), "has_tools": bool(tools)})
        # V38.1: name the hidden count so this 20-message window can't be
        # misread as the whole array (a truncated paste of it is what pointed
        # an earlier bug#1 diagnosis at 'stale' history that was never stale).
        debug_print(
            # V61.25: "(92 earlier hidden)" reads like the model lost 92
            # messages. It did not - every one is in the request; 200 is a
            # cap on this DEBUG ECHO alone. Say which, because a log line
            # that looks like data loss will be read as data loss.
            f"Messages: ALL {len(messages)} sent to the model"
            + (f"; echoing the last 200 here (display cap only, nothing was "
               f"dropped from the request):" if len(messages) > 200 else ":"),
            messages[-200:] if len(messages) > 200 else messages)

        # V61.29: same payload, same caller contract, different wire mode.
        if EXPERIMENTAL.get("ollama_stream"):
            payload["stream"] = True
            return await self._chat_stream(payload)
        
        try:
            # V61.1: one constant, used by BOTH the client and the message
            # below. It read "(900s)" while the real limit was 1800s, which
            # is why a real 1800s hang could not be told apart from anything
            # else by reading the log.
            async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT_S) as client:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                
                debug_print(f"Response status: {response.status_code}")
                
                if response.status_code == 500:
                    error_text = response.text[:5000]
                    debug_print("500 Error from Ollama:", error_text)
                    return ChatResponse(
                        content=f"⚠️ Ollama returned 500 error. This usually means:\n"
                                f"1. The model doesn't support tool calling properly\n"
                                f"2. The context window is too small\n"
                                f"3. The message format is wrong\n\n"
                                f"Error: {error_text[:5000]}\n\n"
                                f"Try: /model ornith:9b",
                        raw_response={"error": error_text}
                    )
                
                response.raise_for_status()
                data = response.json()
                
                _ld = data.get("load_duration", 0) or 0
                _pd = data.get("prompt_eval_duration", 0) or 0
                _ed = data.get("eval_duration", 0) or 0
                _pc = data.get("prompt_eval_count", 0) or 0
                _ec = data.get("eval_count", 0) or 0
                debug_print(
                    "TIMING  total={:.1f}s  load={:.1f}s  "
                    "prompt_eval={:.1f}s ({} tok, {:.0f} tok/s)  "
                    "gen={:.1f}s ({} tok, {:.0f} tok/s)".format(
                        (data.get("total_duration", 0) or 0) / 1e9,
                        _ld / 1e9,
                        _pd / 1e9, _pc, (_pc / (_pd / 1e9)) if _pd else 0,
                        _ed / 1e9, _ec, (_ec / (_ed / 1e9)) if _ed else 0))
                debug_print("Response from Ollama:", data.get("message", {}))
                
        except httpx.HTTPStatusError as e:
            return ChatResponse(content=f"⚠️ HTTP Error: {str(e)[:2000]}")
        except httpx.TimeoutException:
            return ChatResponse(content=f"⚠️ Ollama request timed out ({self.REQUEST_TIMEOUT_S:.0f}s). The model is taking too long.\n\n"
                                        f"This can happen with:\n"
                                        f"• Very complex responses with lots of code\n"
                                        f"• Large context windows\n"
                                        f"• Slower hardware\n\n"
                                        f"Try: Simplify the request or use a smaller/faster model.")
        except Exception as e:
            return ChatResponse(content=f"⚠️ Error: {str(e)[:2000]}")
        
        tool_calls = None
        if "message" in data:
            msg = data["message"]
            if "tool_calls" in msg and msg["tool_calls"]:
                tool_calls = []
                for i, tc in enumerate(msg["tool_calls"]):
                    func = tc.get("function", {})
                    args = func.get("arguments", {})
                    # Handle case where arguments might be a string
                    if isinstance(args, str):
                        try:
                            args = json.loads(args)
                        except:
                            args = {}
                    tool_calls.append(ToolCall(
                        id=tc.get("id", f"call_{i}"),
                        name=func.get("name", "unknown"),
                        arguments=args,
                        index=i
                    ))

                debug_print(f"Parsed {len(tool_calls)} tool calls")
            content = msg.get("content") or ""
            return ChatResponse(
                content=content, 
                tool_calls=tool_calls, 
                raw_response=data,
                prompt_tokens=data.get("prompt_eval_count", 0),
                completion_tokens=data.get("eval_count", 0),
                thinking=(msg.get("thinking") or ""),  # V30.9: capture, don't drop
                total_duration_ns=data.get("total_duration", 0) or 0,
                load_duration_ns=data.get("load_duration", 0) or 0,
                prompt_eval_duration_ns=data.get("prompt_eval_duration", 0) or 0,
                eval_duration_ns=data.get("eval_duration", 0) or 0,
            )
        
        return ChatResponse(
            content="", 
            raw_response=data,
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0)
        )
    
    @staticmethod
    def _parse_tool_calls(raw_list):
        """Same shaping the non-streaming path does, on an accumulated list."""
        out = []
        for i, tc in enumerate(raw_list or []):
            func = tc.get("function", {})
            args = func.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except Exception:
                    args = {}
            out.append(ToolCall(id=tc.get("id", f"call_{i}"),
                                name=func.get("name", "unknown"),
                                arguments=args, index=i))
        return out or None

    async def probe_server(self) -> dict:
        """V61.29: is the SERVER wedged, or was that one REQUEST wedged?

        A stall cannot tell you which, and the difference decides whether
        retrying is sane. /api/ps also reports context_length - what Ollama
        actually allocated, as opposed to the num_ctx that was asked for -
        and size_vram, which is where a spilled KV cache shows up.
        Verified against docs.ollama.com/api/ps. NEVER raises.
        """
        out = {"reachable": False, "loaded": [], "error": ""}
        if not HTTPX_AVAILABLE:
            out["error"] = "httpx not installed"
            return out
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                r = await client.get(f"{self.base_url}/api/ps")
                if r.status_code != 200:
                    out["error"] = f"/api/ps returned {r.status_code}"
                    return out
                out["reachable"] = True
                for m in (r.json().get("models") or []):
                    out["loaded"].append({
                        "model": m.get("model") or m.get("name"),
                        "ctx": m.get("context_length"),
                        "vram": m.get("size_vram"),
                        "expires_at": m.get("expires_at"),
                    })
        except Exception as e:
            out["error"] = str(e)[:300]
        return out

    async def _chat_stream(self, payload: dict) -> ChatResponse:
        """V61.29: STREAMING /api/chat, so that a stall is an EVENT and not
        an absence.

        THE PROBLEM THIS SOLVES. With stream=False the request either returns
        a complete reply or nothing whatsoever. On the mario_game run of
        2026-08-04 the 66th call never returned: 65 calls before it had
        succeeded, the payload was structurally clean (137 messages, every
        tool_call answered), and the log recorded exactly nothing about the
        failure because there was nothing to record. The machine was asked to
        read an error that did not exist.

        WHAT STREAMING BUYS, AND WHAT IT DOES NOT COST. httpx applies its READ
        timeout between chunks. A generation of any length survives as long as
        tokens keep arriving; a server that goes quiet is caught in seconds.
        So this is not a length cap and num_predict stays unset - deliberately,
        the run evidence shows single completions over 17,000 tokens that are
        real work.

        ACCUMULATION IS MANDATORY. content, thinking AND tool_calls all arrive
        spread across chunks; the final chunk (done=true) carries the aggregate
        counts and nanosecond durations. Per
        docs.ollama.com/capabilities/streaming.

        RETURN CONTRACT. Identical ChatResponse shape to the non-streaming
        path. If the stream ends early, content is the ⚠️ line (so every
        existing caller still recognises an error) and raw_response["stall"]
        carries the measurement AND the partial output, so Agent.process can
        hand the model back its own unfinished turn instead of dying.
        """
        url = f"{self.base_url}/api/chat"
        content_parts, thinking_parts, tool_calls_raw = [], [], []
        final, chunks, first_token_s = {}, 0, None
        stall_kind = ""
        # V177: novelty accumulator replaces the line counter
        nov_seen, nov_buf, nov_low, nov_fired, loop_line = set(), "", 0, False, ""
        t0 = time.time()
        timeout = httpx.Timeout(connect=30.0, read=self.STREAM_STALL_S,
                                write=120.0, pool=30.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream("POST", url, json=payload) as response:
                    debug_print(f"Response status: {response.status_code} (streaming)")
                    if response.status_code >= 400:
                        body = (await response.aread()).decode(errors="replace")[:5000]
                        debug_print(f"{response.status_code} Error from Ollama:", body)
                        if response.status_code == 500:
                            # unchanged wording, and raw_response keeps the
                            # "error" key _is_protocol_error keys off.
                            return ChatResponse(
                                content=f"⚠️ Ollama returned 500 error. This usually means:\n"
                                        f"1. The model doesn't support tool calling properly\n"
                                        f"2. The context window is too small\n"
                                        f"3. The message format is wrong\n\n"
                                        f"Error: {body}\n\n"
                                        f"Try: /model ornith:9b",
                                raw_response={"error": body})
                        return ChatResponse(
                            content=f"⚠️ HTTP Error: {response.status_code} {body[:2000]}")
                    async for raw_line in response.aiter_lines():
                        raw_line = raw_line.strip()
                        if not raw_line:
                            continue
                        try:
                            d = json.loads(raw_line)
                        except Exception:
                            continue          # a partial line is not a failure
                        chunks += 1
                        m = d.get("message") or {}
                        c, th = m.get("content") or "", m.get("thinking") or ""
                        if (c or th) and first_token_s is None:
                            first_token_s = time.time() - t0
                        if c:
                            content_parts.append(c)
                        if th:
                            thinking_parts.append(th)
                        if m.get("tool_calls"):
                            tool_calls_raw.extend(m["tool_calls"])
                        if d.get("done"):
                            final = d
                            break
                        if (time.time() - t0) > self.STREAM_TOTAL_BUDGET_S:
                            stall_kind = "overrun"
                            break
                        # ── novelty watch (records; only cancels if switched on)
                        if c or th:
                            nov_buf += (c or th)
                            while len(nov_buf) >= self.STREAM_NOVELTY_WINDOW:
                                win = nov_buf[:self.STREAM_NOVELTY_WINDOW]
                                nov_buf = nov_buf[self.STREAM_NOVELTY_WINDOW:]
                                words = re.sub(r"\s+", " ", win).strip().lower().split()
                                k = self.STREAM_NOVELTY_SHINGLE
                                shing = [" ".join(words[i:i + k])
                                         for i in range(max(0, len(words) - k + 1))]
                                if len(shing) < 5:
                                    continue
                                fresh = [s for s in shing if s not in nov_seen]
                                novelty = len(fresh) / len(shing)
                                nov_seen.update(shing)
                                if novelty < self.STREAM_NOVELTY_MIN:
                                    nov_low += 1
                                    # keep the most-repeated fragment as the
                                    # evidence the recovery message quotes
                                    if not loop_line and shing:
                                        loop_line = max(
                                            shing, key=lambda s: shing.count(s))[:160]
                                else:
                                    nov_low = 0
                                if (nov_low >= self.STREAM_NOVELTY_STREAK
                                        and not nov_fired):
                                    nov_fired = True
                                    debug_print(
                                        f"STREAM NOVELTY WATCH: "
                                        f"{self.STREAM_NOVELTY_STREAK} consecutive "
                                        f"{self.STREAM_NOVELTY_WINDOW}-char windows "
                                        f"below {self.STREAM_NOVELTY_MIN:.0%} new "
                                        f"content (last {novelty:.0%}) after "
                                        f"{chunks} chunks / "
                                        f"{sum(len(p) for p in content_parts):,} "
                                        f"chars: {loop_line!r}")
                                    if EXPERIMENTAL.get("ollama_stream_loop_cancel"):
                                        stall_kind = "degenerate-repetition"
                                        break
                        if stall_kind:
                            break
        except httpx.ReadTimeout:
            stall_kind = "silent"
        except httpx.TimeoutException:
            stall_kind = "connect-or-write"
        except Exception as e:
            return ChatResponse(content=f"⚠️ Error: {str(e)[:2000]}")

        content = "".join(content_parts)
        thinking = "".join(thinking_parts)
        elapsed = time.time() - t0
        pc = final.get("prompt_eval_count", 0) or 0
        ec = final.get("eval_count", 0) or 0
        pd = final.get("prompt_eval_duration", 0) or 0
        ed = final.get("eval_duration", 0) or 0
        debug_print(
            "TIMING (stream)  wall={:.1f}s  chunks={}  first_token={}  "
            "load={:.1f}s  prompt_eval={:.1f}s ({} tok)  gen={:.1f}s ({} tok, "
            "{:.0f} tok/s)".format(
                elapsed, chunks,
                f"{first_token_s:.1f}s" if first_token_s is not None else "NEVER",
                (final.get("load_duration", 0) or 0) / 1e9,
                pd / 1e9, pc, ed / 1e9, ec,
                (ec / (ed / 1e9)) if ed else 0))

        if stall_kind:
            diag = {
                "kind": stall_kind,
                "chunks": chunks,
                "elapsed_s": round(elapsed, 1),
                "silence_budget_s": self.STREAM_STALL_S,
                "first_token_s": (round(first_token_s, 1)
                                  if first_token_s is not None else None),
                "content_chars": len(content),
                "thinking_chars": len(thinking),
                "tool_calls_seen": len(tool_calls_raw),
                "loop_line": loop_line,
                "partial_content": content,
                "partial_thinking": thinking,
            }
            debug_print("STREAM STALLED:", {k: v for k, v in diag.items()
                                            if not k.startswith("partial_")})
            if stall_kind == "overrun":
                where = (f"GENERATION - it never went quiet. Tokens were still "
                         f"arriving when the {self.STREAM_TOTAL_BUDGET_S:.0f}s "
                         f"wall-clock budget ran out")
                head = (f"⚠️ Ollama stream OVERRAN {self.STREAM_TOTAL_BUDGET_S:.0f}s "
                        f"of continuous generation ({len(content):,} chars).")
            elif first_token_s is None:
                where = "PROMPT PROCESSING - not one token ever arrived"
                head = (f"⚠️ Ollama stream stalled ({stall_kind}) after "
                        f"{elapsed:.0f}s with "
                        f"{self.STREAM_STALL_S:.0f}s of silence.")
            else:
                where = (f"GENERATION - first token at {first_token_s:.1f}s, "
                         f"then {len(content):,} chars, then silence")
                head = (f"⚠️ Ollama stream stalled ({stall_kind}) after "
                        f"{elapsed:.0f}s with "
                        f"{self.STREAM_STALL_S:.0f}s of silence.")
            return ChatResponse(
                content=f"{head}\nStopped during: {where}.",
                raw_response={"stall": diag},
                thinking=thinking,
                prompt_tokens=pc, completion_tokens=ec)

        return ChatResponse(
            content=content,
            tool_calls=self._parse_tool_calls(tool_calls_raw),
            raw_response=final,
            prompt_tokens=pc,
            completion_tokens=ec,
            thinking=thinking,
            total_duration_ns=final.get("total_duration", 0) or 0,
            load_duration_ns=final.get("load_duration", 0) or 0,
            prompt_eval_duration_ns=pd,
            eval_duration_ns=ed,
        )

    async def list_models(self) -> list:
        if not HTTPX_AVAILABLE:
            return []
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(f"{self.base_url}/api/tags")
            data = response.json()
            return [m["name"] for m in data.get("models", [])]
    
    async def get_version(self) -> str:
        """V45.1: Ollama build string, recorded so a seed means something.
        Never raises - an unknown version must not stop a run."""
        try:
            if not HTTPX_AVAILABLE:
                return ""
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(f"{self.base_url}/api/version")
                if r.status_code == 200:
                    return str(r.json().get("version", ""))
        except Exception:
            pass
        return ""

    async def check_connection(self) -> bool:
        try:
            if not HTTPX_AVAILABLE:
                return False
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except:
            return False


class ToolExecutor:
    def __init__(self, tools: dict):
        self.tools = tools
        # V61.15 per-run state. Bounces are counted PER TOOL and capped, so a
        # model that will not produce the field costs at most
        # REASONING_MAX_BOUNCES iterations and then proceeds - every gate in
        # this file is bounded for the same reason.
        self._reasoning_bounces = {}
        # path -> last `supersedes` text, for the repeat-edit stall check.
        self._last_supersedes = {}

    def _check_reasoning(self, name: str, args: dict):
        """(clean_args, rejection_or_None, hint_or_empty).

        Pulls the V61.15 fields out of args, decides whether the call may
        proceed, and returns a hint to append to a successful result. Never
        raises: a reasoning gate that can crash the executor would take down
        runs it was meant to improve.
        """
        spec = REASONING_FIELDS.get(name)
        if not spec:
            return args, None, ""
        try:
            given = {k: str(args.get(k) or "").strip() for k in spec}
            clean = {k: v for k, v in args.items() if k not in spec}
            def _answered(field, val):
                if len(val) >= REASONING_MIN_CHARS:
                    return True
                low = val.lower().strip().strip(".")
                return any(low.startswith(t) for t in
                           REASONING_SENTINELS.get((name, field), ()))
            missing = [k for k, v in given.items() if not _answered(k, v)]
            if missing and name in REASONING_ASK_AFTER:
                # V61.22: never block a call whose retry cost is the payload.
                fields = "; ".join(f"`{k}` - {spec[k]['description']}"
                                   for k in missing)
                return clean, None, (
                    f"\n\n\u2139 The file was written. Before your next tool "
                    f"call, answer this in your reply - it costs you a "
                    f"sentence now and I am not asking you to send the file "
                    f"again: {fields}"
                )
            if missing:
                n = self._reasoning_bounces.get(name, 0)
                if n < REASONING_MAX_BOUNCES:
                    self._reasoning_bounces[name] = n + 1
                    fields = ", ".join(
                        f"`{k}` ({spec[k]['description']})" for k in missing)
                    return clean, (
                        f"CALL REJECTED - {name} requires reasoning you did not "
                        f"supply. Missing or too short: {fields}\n"
                        f"   Nothing was executed and no file changed. Re-issue "
                        f"the SAME call with that field filled in. This is not "
                        f"a formatting complaint: the field exists because the "
                        f"answer changes what the right call is."
                    ), ""
                # bounced enough - let it through, but say so out loud rather
                # than silently dropping the requirement.
                debug_print(f"REASONING GATE: {name} missing {missing} after "
                            f"{n} bounces - proceeding without it")
                return clean, None, ""

            hint = ""
            # V61.15 stall check. booby steps 7-11 were five edits to one
            # block; had the model been asked each time what the previous
            # edit failed to do, the SAME answer twice in a row is the loop
            # made visible. Mechanical, no model judgement.
            if name == "str_replace":
                path = str(args.get("path") or "")
                sup = given.get("supersedes", "")
                prev = self._last_supersedes.get(path)
                if (prev and sup.lower() == prev.lower()
                        and not sup.lower().startswith("first edit")):
                    hint = (
                        "\n   ⛔ STALL: your `supersedes` for this file is "
                        "WORD-FOR-WORD what you wrote last edit. You are "
                        "re-attempting a fix you already made without new "
                        "evidence. RUN something before editing this file "
                        "again."
                    )
                self._last_supersedes[path] = sup
            return clean, None, hint
        except Exception as e:
            debug_print(f"reasoning gate failed open on {name}: {e}")
            return args, None, ""

    async def execute(self, tool_call: ToolCall) -> dict:
        if tool_call.name not in self.tools:
            return {"tool_name": tool_call.name, "content": f"Unknown tool: {tool_call.name}"}
        try:
            tool = self.tools[tool_call.name]
            args = tool_call.arguments if isinstance(tool_call.arguments, dict) else {}
            # V61.15: take the reasoning fields FIRST. They are in the schema
            # the model sees but NOT in tool.parameters, so the V23 filter
            # below would otherwise drop them as "unsupported" and log noise.
            args, rejection, hint = self._check_reasoning(tool_call.name, args)
            if rejection:
                return {"tool_name": tool_call.name, "content": rejection}
            # V23: filter arguments to the tool's declared schema. Models
            # trained on richer tool APIs attach extras - ornith:35b passed
            # a 'description' kwarg to bash, which crashed the call with
            # "unexpected keyword argument" and burned an iteration.
            declared = set(tool.parameters.get("properties", {}).keys())
            dropped = sorted(set(args) - declared)
            if dropped:
                args = {k: v for k, v in args.items() if k in declared}
                debug_print(f"Dropped unsupported {tool_call.name} argument(s): {dropped}")
            # V61.15a: PRE-EXISTING GAP - this filtered EXTRA arguments since
            # V23 but never checked for MISSING ones, so an omitted required
            # argument reached tool.execute(**args) and came back as
            # "Error: FileWriteTool.execute() missing 1 required positional
            # argument: 'content'". That is a Python traceback, not an
            # instruction: it does not say the write did not happen, does not
            # name what to send, and reads like a defect in the machine rather
            # than something the model can fix. Caught here instead, with the
            # schema's own description of the missing field so the retry has
            # everything it needs.
            required = [k for k in (tool.parameters.get("required") or [])
                        if k not in args or args.get(k) is None]
            if required:
                props = tool.parameters.get("properties", {})
                detail = "; ".join(
                    f"`{k}` - {props.get(k, {}).get('description', 'required')}"
                    for k in required)
                return {"tool_name": tool_call.name, "content": (
                    f"CALL INCOMPLETE - {tool_call.name} was not run and "
                    f"nothing changed. Missing required argument(s): {detail}\n"
                    f"   Re-issue the call with every required argument in ONE "
                    f"object. If the payload is large, the file CONTENT is the "
                    f"part that must be complete - never omit it to make room "
                    f"for anything else."
                )}
            result = await tool.execute(**args)
            return {"tool_name": tool_call.name, "content": str(result) + hint}
        except Exception as e:
            return {"tool_name": tool_call.name, "content": f"Error: {str(e)}"}


# =============================================================================
# AGENT
# =============================================================================

BUILD_PROMPT = """You are an expert software development assistant with access to tools.

IMPORTANT: You MUST use your tools to accomplish tasks. Do NOT just describe what you would do - actually DO it by calling the tools.

ENVIRONMENT:
- Operating System: {os_type}
- Shell: {shell_type}
- Python: Use 'python' not 'python3' on Windows

=== ENVIRONMENT FACTS (verified at startup - TRUST THESE, do not re-probe) ===
- Python version: {python_version}
- Importable packages: {available_packages}
- You are ALREADY INSIDE the working directory: {cwd_abs}
- Files here right now: {dir_listing}

FACTS-BASED RULES:
- Use RELATIVE paths only (e.g. "snake_game.py"). Absolute paths outside the
  working directory are BLOCKED by the sandbox - do not attempt them.
- Never run cd/pwd/list_dir to discover where you are - it is stated above.
- If a package is NOT in the importable list, do NOT pip-install it if it may
  need compiling (pygame, numpy, etc. often fail to build from source).
  PIVOT IMMEDIATELY to the standard library instead (tkinter for GUI/games,
  wave+winsound for audio, http.server for web).
- Do not retry a failed pip install with a different version - older versions
  build WORSE, not better.

=== PLATFORM RULES (hard constraints for THIS machine) ===
{platform_rules}

=== GUI / GAME VERIFICATION PROTOCOL ===
Any app that opens a window (tkinter, pygame, turtle) blocks forever when run,
so a 60s timeout on `python app.py` usually means it LAUNCHED SUCCESSFULLY but was not TESTED correctly.
To verify GUI apps properly:
1. ALWAYS include a `--test` mode in the code you write:
     if "--test" in sys.argv:
         app = MainClass()   # construct everything, draw one frame if possible
         print("SELF-TEST OK"); raise SystemExit(0)
   (place BEFORE mainloop; for tkinter call app.root.update() once first)
2. The --test MUST EXERCISE AND ASSERT every feature the task names, not
   just construct-and-draw. "Constructed, updated, drew" only proves it did
   not crash. Task says sounds? Build them and `assert snd is not None`.
   Task says enemies? Assert at least one spawns. A feature your --test
   never touches is UNVERIFIED - do not claim it works.
3. INPUT MUST BE PASSABLE. The commonest way a game self-test dies is that
   it cannot press a key. Two shapes that CANNOT work, both measured:
     - posting a KEYDOWN event and then calling a function that reads
       pygame.key.get_pressed(). Posting goes to the event QUEUE; get_pressed
       reads hardware state. The input never arrives.
     - calling pygame.key.get_pressed() inside the test. Headless, nothing is
       pressed, so every key is False and any branch on it is dead.
   Take the key state as an ARGUMENT the test can construct - a plain dict
   like {{"left": False, "up": True}}, or a fake array - so the test hands the
   input in rather than trying to make the keyboard produce it. A test may
   post events ONLY if it then drives the loop that reads pygame.event.get().
4. Verify with: python <file>.py --test  (fast, exit code tells the truth)
5. Only after --test passes, you can continue with task.
6. PARSING IS NOT RUNNING, AND THIS IS THE MOST COMMON WAY A BUILD SHIPS
   DEAD. `node --check` proves the file contains no syntax error. It proves
   NOTHING about whether the code executes. A file can parse perfectly and
   throw on the first line of its main loop, in which case 0% of its
   features work and 100% of its identifiers are present. After the parse
   check passes, EXECUTE it:
     - `npm install jsdom` (npm is allowed), then load the page under jsdom
     - stub the heavy dependencies (3D library, audio, canvas) with
       permissive Proxy objects that answer any property or call, so that
       anything which throws is YOUR code and not the library's
     - stub requestAnimationFrame to invoke its callback a BOUNDED number
       of times (30-40) so the main loop runs without recursing forever
     - dispatch whatever click or event starts the app
     - collect EVERY thrown error (window 'error' listener + try/catch
       around the frame driver); exit non-zero if the list is non-empty
   Then report SEPARATELY what this proved and what it did not: stubbed
   libraries mean library-API misuse is still unverified, and that belongs
   in your summary under "written but unverified".

BASH CONSTRAINTS:
- Allowed commands: {allowed_commands}
- To run Python apps: python <file.py>
- Do NOT use: export, set, flask CLI directly.
- bash CANNOT create, overwrite, or delete files. Inline `python -c` payloads
  containing open(...,'w'/'a'/'x'/'r+'), .write_text, .write_bytes,
  os.remove, os.rename, shutil.move/copy, and shell redirection (> >>) are
  all BLOCKED. Use str_replace to change an existing file and file_write to
  make a new one.
- Do NOT retry a blocked command with different quoting or escaping - the
  guard matches the OPERATION, not the syntax, so it will block every time.
  If you need to DERIVE something from a file (extract a section, transform
  it, feed it to a parser), put that logic INSIDE a .py file you create with
  file_write, then run it. The guard scans the bash command string, not the
  contents of a script you execute.
- Do NOT shell out to python to print file contents or line ranges.
  file_read accepts start_line and end_line and does this natively, with no
  quoting hazard and no risk of hitting a blocked command. Writing
  `python -c "...print(lines[400:420])..."` means you have forgotten
  file_read exists.
- **IMPORTANT**: Do NOT start long-running servers (Flask, uvicorn, etc.) as they block forever.
- For web apps, verify with `python -c "import <module>"` instead of running the server.
- **NEVER** run `python app.py` for web servers - they block forever. Just verify imports work.
- **WINDOWS CRITICAL**: Do NOT use Linux syntax like `mkdir -p` or paths with forward slashes.
- Use file_write to create NEW files ONLY (it auto-creates parent directories).
- Use python <file>.py --test 2>&1 for (exit code) or it will run forever.

RULES:
- **NEVER** use bash for mkdir; file_write already creates parent directories automatically.
- **NEVER** guess what code looks like - always verify with file_read first.
- If str_replace returns "String not found", your old_str does not exist in
  that file. Do NOT retry with a guessed variant - that is the single most
  common way a run stalls out. file_read the region and copy old_str from
  what is actually on disk. Two failures in a row means STOP and file_read.
- **NEVER** write `except: pass` / `except Exception: pass` around feature
  code. A swallowed error makes a DEAD feature look alive and your --test
  still passes. At minimum print the exception; better, let it raise.
- **NEVER WEAKEN A TEST TO MAKE IT PASS.** If --test fails, the default
  assumption is that the CODE is wrong, not the test. You may edit the test
  only if you can state in one sentence what it asserted that the task never
  required. Deleting an assertion, loosening a pattern, or lowering a
  threshold so the run goes green is not a fix - it converts a real failure
  into a false success that nothing downstream can catch.
- **IF YOUR OWN COMMENT SAYS THE LINE IS WRONG, DELETE THE LINE.** Writing
  `doThing(x); // but this needs to iterate the collection` and leaving it
  in ships a defect you had already found. This is the cheapest bug in the
  world to prevent and one of the most expensive to locate later.
- **CROSS-SECTION NAME CHECK**: when one file is built in sections across
  many separate calls, a name DEFINED in an early section and CALLED in a
  later one is a contract that nothing enforces. Before you verify,
  grep_search the file for the functions and objects your later sections
  call, and confirm the earlier sections actually define them under that
  EXACT name. Defining `updateAudio()` and calling `A.update()` is a build
  error; if you do not catch it here you will meet it as a runtime crash
  many iterations later, with no clue where it came from.
- **SAME-CLASS SWEEP**: after fixing any defect, immediately
  grep_search the SAME FILE for the same pattern (grep_search accepts a
  file path) and fix EVERY instance in the same pass. One patched copy of
  a bug with six live siblings is not a fix.
- **THERE IS NOBODY TO ASK.** This is a one-shot run: no human will read a
  question and reply. Never end by asking what to do next, offering a menu
  of things you could do, or saying you are ready to continue when the user
  is. If work remains, DO IT. If you truly cannot proceed, say so with
  VERDICT: BROKEN and state what blocked you.
- Your FINAL SUMMARY must OPEN with a one-line verdict, before anything
  else: `VERDICT: WORKING` or `VERDICT: BROKEN - <one sentence why>`. Only
  claim features your verification actually PROVED; label everything else
  "written but unverified". If any deliverable still has a known unresolved
  defect, the verdict is BROKEN even if most of the work succeeded.

AVAILABLE TOOLS:
- file_read: Read file contents.
- file_write: Create new files ONLY. 
- str_replace: SUBSTITUTION - replaces old_str with new_str. **old_str is DELETED**.
- list_dir: List directory contents.
- bash: Execute shell commands.
- grep_search: Search a pattern in ONE FILE (pass its path) or recursively in a directory.

=== CRITICAL: str_replace SEMANTICS ===
- str_replace is DESTRUCTIVE SUBSTITUTION, not insertion!
- old_str gets DELETED and new_str takes its place
- old_str must match the file EXACTLY and must appear EXACTLY ONCE
- To ADD lines while KEEPING existing ones, include what you want to keep in new_str

WRONG - this DELETES "import pygame" and replaces it:
  old_str: "import pygame"
  new_str: "from game import Snake"
  Result: "import pygame" is GONE, only "from game import Snake" remains

CORRECT - to add a line while keeping the original:
  old_str: "import pygame"
  new_str: "import pygame\\nfrom game import Snake"
  Result: both lines are now in the file (swap the order to insert BEFORE)

WRONG - never use empty old_str:
  old_str: ""  <-- NEVER DO THIS (matches everywhere)

=== ANCHOR INTEGRITY - the #1 cause of stalled runs ===
old_str must be COPIED from a file_read of the target region. It must NEVER
be RECALLED from memory of what you wrote earlier. In a long build your
memory of your own output drifts, and each failed retry drifts FURTHER from
the file rather than closer to it - you will rewrite the same anchor three
times, each version more wrong than the last, and burn the run.
- Before your first str_replace on a file you have not read this session,
  file_read the region. Not the whole file - the region.
- After "String not found", file_read the SAME region you just failed on.
  Do not retype old_str, do not shorten it, do not nudge the whitespace and
  try again. Read it, then paste exactly what you read.
- TWO failures on the same anchor means STOP. file_read a WIDER range and
  find out what is actually on disk before touching it again.
- If str_replace instead reports MULTIPLE matches, that is the opposite
  problem: add surrounding lines to old_str until it is unique.

RECOVERY: If file gets corrupted, use `file_read` to see current state, then craft a sophisticated `str_replace` that fixes ALL issues in one operation. Include enough context lines to make old_str unique.
=== END str_replace SEMANTICS ===

WORKFLOW:
1. Do NOT re-probe the environment - the working directory and everything in it are listed in ENVIRONMENT FACTS above.
2. Use `file_read` (with start_line/end_line) to examine any existing file before you edit it.
3. Use `file_write` to create new files only OR `str_replace` to edit existing files.
4. **VERIFY**: Run `python -c "import <module>"` to check imports.
5. **VERIFY**: python <file>.py --test (exit code) to "test and fix it".
6. **VERIFY**: If a `SyntaxError`, `IndentationError`, `TabError`, or other parser error occurs, fix it first using `file_read` and `str_replace`, then re-run verification before attempting any other fixes.
7. Use bash to run the application (GUI apps: only ever via --test).
8. If errors occur, <think> of 3 intricate solutions and choose the best one and utilize `list_dir`, `file_read`, `str_replace` and re-verify with --test.

CRITICAL: Always use tools. Never just describe code - write it to new files using `file_write` or existing files using `str_replace`."""


PLAN_PROMPT = """You are a expert code analysis assistant with READ-ONLY access.

AVAILABLE TOOLS: `file_read`, `list_dir`, `grep_search`

You can analyze code but CANNOT modify files or run commands."""


# V21.1: explicit OS-specific rules (per the V21 review). Injected into the
# build prompt AND the reflection prompt so neither the agent nor its saved
# lessons can drift onto the wrong platform's commands.
PLATFORM_RULES_WINDOWS = """- This machine is WINDOWS.
- NEVER use or recommend: sudo, apt, apt-get, yum, dnf, chmod, chown, systemctl.
- NEVER use or recommend /home/... or /tmp/... paths.
- NEVER use or recommend 'python3' - the correct command here is 'python'.
- NEVER give Linux shell examples; every command must be valid on Windows."""


def get_platform_rules() -> str:
    """Return the hard platform rules. V25: Windows-only by design -
    PLATFORM_RULES_UNIX never existed (latent NameError on non-Windows)."""
    return PLATFORM_RULES_WINDOWS


def build_api_messages(system_prompt: str, messages, num_ctx: int = 0) -> list:
    """Assemble what the model actually sees, applying the V61.14a reasoning budget.

    Walks NEWEST to OLDEST accumulating reasoning characters. Once the budget
    is spent, every older turn is serialized WITHOUT its reasoning block. The
    newest turns therefore always keep theirs, which is the point: the failure
    this fixes is a model re-deriving the conclusion it reached one turn ago.

    Never truncates a block to fit - a half-block is worse than no block,
    because the operative decision lives at the end of it (70-98% through,
    measured). A block is either whole or absent.

    num_ctx <= 0 means "no ceiling known", and the budget does not bind.
    NEVER raises: if anything here goes wrong the caller still gets a valid
    message list, because a reasoning budget must not be able to stop a run.
    """
    out = [{"role": "system", "content": system_prompt}]
    msgs = list(messages or [])
    try:
        budget = 0
        if REFEED_THINKING and num_ctx and num_ctx > 0:
            budget = int(num_ctx * THINKING_REFEED_CTX_FRACTION
                         * THINKING_REFEED_CHARS_PER_TOKEN)
        drop_before = -1          # index; turns strictly BELOW this lose reasoning
        if budget:
            spent = 0
            kept_any = False
            for i in range(len(msgs) - 1, -1, -1):
                m = msgs[i]
                t = (getattr(m, "thinking", "") or "").strip()
                if not t or getattr(m, "role", "") != "assistant":
                    continue
                # The NEWEST block is kept unconditionally. Found by the
                # V61.14a test, not by reading: without this, a single block
                # larger than the whole budget fails the first comparison and
                # evicts EVERY turn including itself - the budget deleting the
                # one piece of reasoning that matters most. On the booby run
                # the last block is 7,310 chars, so any window under ~5K
                # produced exactly that: 0 blocks kept.
                if not kept_any:
                    kept_any = True
                    spent += len(t)
                    drop_before = i
                    continue
                if spent + len(t) > budget:
                    drop_before = i + 1
                    break
                spent += len(t)
                drop_before = i
            # V61.14b: only report a drop that actually DROPS something. The
            # first cut logged whenever drop_before > 0, but drop_before lands
            # on the newest reasoning turn even when the budget is nowhere
            # near binding - so on the snake_game run of 2026-07-31 this line
            # fired on all 17 iterations announcing "dropping reasoning from
            # turns 0-0" while turn 0 was the user's task message, which has
            # no reasoning to drop. A monitoring line that cries wolf every
            # single iteration is worse than no line: it is exactly how the
            # real swallower warning got ignored for six edits in V61.9.
            dropped = sum(1 for k in range(drop_before)
                          if (getattr(msgs[k], "thinking", "") or "").strip()
                          and getattr(msgs[k], "role", "") == "assistant")
            if dropped:
                debug_print(f"REASONING BUDGET BOUND: {spent:,}/{budget:,} chars "
                            f"kept; reasoning dropped from {dropped} older "
                            f"turn(s) below index {drop_before}")
        for i, m in enumerate(msgs):
            out.append(m.to_dict(include_thinking=(i >= drop_before)))
        return out
    except Exception as e:
        debug_print(f"reasoning budget failed, sending everything: {e}")
        return [{"role": "system", "content": system_prompt}] + [
            m.to_dict() for m in msgs]


_REASONING_TAG_RE = re.compile(r"</?reasoning>\s*", re.I)


def _fold_reasoning(content: str, thinking: str) -> str:
    """Attach the model's own reasoning to its assistant turn, exactly once.

    V61.25: V61.14 folded thinking into content as `<reasoning>...</reasoning>`
    and I flagged at the time that the model might start imitating the block.
    It did. On the spongebob_shooter run of 2026-08-01, 26 of 143 thinking
    blocks contain a reasoning tag the model wrote itself, and assistant
    turns came back looking like this:

        <reasoning>
        The test fails because ... one call to move() only moves 5. Let me
        fix this by checking for >= PLAYER_SPEED ...
        <reasoning>
        The test fails because ... one move() call only moves 5. I need to
        fix this by checking for >= PLAYER_SPEED ...
        </reasoning>
        </reasoning>
        </reasoning>

    Two problems in one. The model now opens the tag in `content`, so the
    machine's own fold NESTS inside it and the markup comes out unbalanced -
    two opens, three closes. And the model restates in `content` what it
    already said in `thinking`, so the same paragraph is paid for twice in a
    context that reached 162,568 tokens.

    So: unwrap any reasoning tags the model emitted, keeping its words, then
    fold only if the thinking actually adds something. Similarity is measured
    on the normalised text - a restatement of the same point scores high even
    when the wording differs, which is exactly the case above.
    """
    content = (content or "")
    thinking = (thinking or "").strip()
    # unwrap the model's imitation, keep what it said
    clean = _REASONING_TAG_RE.sub("", content).strip()
    if not thinking:
        return clean
    inner = _REASONING_TAG_RE.sub("", thinking).strip()
    if not inner:
        return clean
    if clean and len(inner) >= REASONING_DEDUP_MIN_CHARS:
        # Fraction of the THINKING's distinct words already present in
        # content - "does this add anything", measured directly. Chosen over
        # SequenceMatcher, which scored the real duplicate from the log at
        # 0.52 and a harmless one-line stub at 0.51: no threshold separates
        # those. On word overlap the same cases are 63% and 50%, against 24%
        # for a turn that genuinely added an explanation and 6% for wholly
        # new reasoning. It is also length-robust, which a raw ratio is not.
        # Gated on length because dedup only pays on a big block, while a
        # short one is both cheap to keep and the likeliest false positive -
        # a terse "do NOT use file_write here" shares most of its words with
        # any content that mentions file_write.
        try:
            wt = set(inner.lower().split())
            wc = set(clean.lower().split())
            overlap = (len(wc & wt) / len(wt)) if wt else 1.0
        except Exception:
            overlap = 0.0
        if overlap >= REASONING_DEDUP_RATIO:
            # The model already said this out loud. Folding it again buys
            # nothing and reinforces the pattern that caused it.
            return clean
    note = inner
    cap = THINKING_REFEED_CHARS
    if cap and len(note) > cap:
        note = "...(earlier reasoning trimmed)...\n" + note[-cap:]
    return (f"{clean}\n<reasoning>\n{note}\n</reasoning>").strip()


@dataclass
class Message:
    role: str
    content: str
    tool_calls: list = None
    tool_name: str = None
    tool_call_id: str = None
    thinking: str = ""   # V61.14: the model's OWN reasoning for this turn, kept
    # so later turns can see it. See REFEED_THINKING and to_dict() below.

    def to_dict(self, include_thinking: bool = True) -> dict:
        # V61.14: THE MODEL WAS THINKING INTO A BUCKET WITH A HOLE IN IT.
        #
        # Measured on the booby_game run (2026-07-31, seed 103603307,
        # 17 iterations, 408,747 tokens): across iterations 8, 9, 10 and 11
        # the model reached the SAME conclusion four separate times -
        # "the simplest fix is to just set lives=0 directly instead of
        # relying on collision detection" - and acted on it zero times. It
        # then made five consecutive str_replace edits to one test block
        # with no verification between them, of which steps 10 and 11
        # differed only in whether it moved the shark onto the booby or the
        # booby onto the shark. That is not a model that cannot reason. Its
        # reasoning for step 9 alone is 1,813 characters and correctly
        # derives the bug from first principles ("I set booby_vy = 0 but
        # then in step(), self.booby_vy += 0.35 happens FIRST").
        #
        # The reason it repeated itself is that it could not see any of it.
        # `thinking` was captured into the episode for review and never put
        # back, so iteration 9 opened with no access to what iteration 8
        # concluded, and re-derived it. 24,306 characters of reasoning were
        # produced that run and 0 of them re-entered the context - while the
        # context sat at ~17K of a 256K window, 6.6% full. Nothing was
        # compacted and nothing was evicted. The forgetting was not pressure,
        # it was plumbing.
        #
        # WHY FOLDED INTO content INSTEAD OF SENT AS A `thinking` FIELD:
        # Ollama returns reasoning under message.thinking on the way OUT.
        # Whether 0.32.5 ACCEPTS a thinking field on an inbound assistant
        # message is not something this file has ever tested against
        # ornith-vision, and an unverified wire field that errors would kill
        # the run rather than degrade it. content is a plain string that
        # provably round-trips. If you later confirm the inbound field works,
        # this is the one place to change.
        #
        # PREFIX CACHE: the fold is computed only from state stored on this
        # message, so the bytes of turn N never change once appended.
        # api_messages stays a growing list behind a byte-identical prefix,
        # which is what V61.1 depends on.
        content = self.content
        if (REFEED_THINKING and include_thinking and self.role == "assistant"):
            # V61.25: one place decides how reasoning attaches to a turn -
            # unwrapping the model's own imitated tags and skipping the fold
            # when it has already said the same thing in content. The TAIL is
            # kept when a cap applies: measured on every reasoning block over
            # 600 chars in the booby run, the last operative decision phrase
            # sits at 70-98% through the text, so cutting the head loses the
            # reasoning and cutting the tail loses the DECISION.
            content = _fold_reasoning(content, self.thinking)
        d = {"role": self.role, "content": content}
        if self.role == "tool":
            if self.tool_call_id:
                d["tool_call_id"] = self.tool_call_id
            if self.tool_name:
                d["tool_name"] = self.tool_name
            return d


        if self.tool_calls:
            d["tool_calls"] = [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {"name": tc.name, "arguments": tc.arguments}
                }
                for tc in self.tool_calls
            ]
        return d


class Agent:
    # V61.29: how many times one task may recover from a stalled model
    # call before giving up. Bounded for the same reason every other gate
    # in this file is bounded - a recovery that can loop is a new hang.
    MAX_STALL_RECOVERIES = 20

    def __init__(self, name: str, system_prompt: str, client: OllamaClient, tools: dict, 
                 max_iterations: int = 1000000, memory: EpisodeMemory = None,
                 judge_client: OllamaClient = None, gen_params: dict = None):
        self.name = name
        self.system_prompt = system_prompt
        self.client = client
        # V45: the GRADING calls (reflection, grounding judge, lesson
        # validator) must not move when the builder's temperature moves -
        # otherwise the measuring instrument is part of the experiment.
        # Falls back to the builder client so nothing breaks if unset.
        self.judge_client = judge_client or client
        # V61.1: size num_keep from the REAL prompt this agent was given, so a
        # context shift cannot evict the build prompt off the front. This runs
        # AFTER both clients exist - the first version of this edit sat above
        # those two lines and would have raised AttributeError into a handler
        # that swallowed it, leaving num_keep silently unset forever.
        if self.client is not None:
            self.client.sync_prompt_cache(system_prompt)
        if self.judge_client is not None and self.judge_client is not self.client:
            self.judge_client.sync_prompt_cache(system_prompt)
        self.gen_params = gen_params or {}
        self.tools = tools
        self.tool_schemas = get_tool_schemas(tools) if tools else []
        self.executor = ToolExecutor(tools) if tools else None
        self.max_iterations = max_iterations
        self.messages = []
        self.iteration_count = 0
        self.memory = memory
        
        # Episode tracking (reset each process call)
        self.trajectory = []  # [(tool_name, args_summary, success), ...]
        self.thinking_log = []  # V30.9: [(step, thinking_text), ...] - the
        # model's reasoning channel per response, captured for episode review
        # only (never re-fed to the model). Parallel to trajectory so no
        # existing tuple consumer is affected.
        self.lessons_injected = []  # Episodes actually injected
        self.lessons_candidates = []  # Episodes found (for review)
        
        # REAL token tracking from Ollama
        self.total_prompt_tokens = 0      # Accumulated prompt tokens (task-level)
        self.total_completion_tokens = 0  # Accumulated completion tokens (task-level)
        self.last_prompt_tokens = 0       # Last response's prompt tokens
        self.last_completion_tokens = 0   # Last response's completion tokens
        
        # SESSION-level token tracking (persists across tasks within session)
        self.session_prompt_tokens = 0
        self.session_completion_tokens = 0
        self.session_task_count = 0
        
        # V61.11 coverage probe snapshot. Set by _coverage_message, which runs
        # at most once per run. Initialized here so the attribute always
        # EXISTS: before this line it came into being only if the self-test
        # surface happened to fire, so any reader added later would have hit
        # AttributeError on the runs where it did not - the exact call-site
        # defect V61.11a was written about. Diagnostic only; see the note in
        # _coverage_message before wiring anything to it.
        self._last_coverage = None

        # Injection control (default OFF - review mode)
        self.inject_enabled = False
        # V24: semantic reflection mode (default ON - /confidence off for
        # the V23 mechanical path: regex class, lexical gate, template fallback)
        self.confidence_enabled = True
    
    def reset(self):
        """Reset for new task, preserving session-level stats."""
        # Accumulate to session totals before resetting
        self.session_prompt_tokens += self.total_prompt_tokens
        self.session_completion_tokens += self.total_completion_tokens
        if self.trajectory:  # Only count if work was done
            self.session_task_count += 1
        
        # Reset task-level state
        self.messages = []
        self.iteration_count = 0
        self.trajectory = []
        self.thinking_log = []  # V30.9: per-task reset
        self.lessons_injected = []
        self.lessons_candidates = []
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.last_prompt_tokens = 0
        self.last_completion_tokens = 0
        # V25: clear the duplicate-guard signature - it must not leak into
        # the next task ("nothing has changed since" is false across tasks).
        self._last_call_sig = None
        self._last_call_ok = False
        self._dup_streak = 0
        self._ok_call_counts = {}  # V30.8: per-task set of successful sigs
    
    def _detect_tool_success(self, result_content: str, tool_name: str) -> bool:
        """
        Intelligent success detection that parses actual outcomes.
        
        Fixes the fake-success problem where agent claims success based only
        on output not starting with "Error:".
        """
        content = result_content

        # V61.24: A CALL THAT NEVER RAN IS NOT A SUCCESS. `CALL REJECTED`
        # (V61.15's reasoning gate) and `CALL INCOMPLETE` (V61.15a's missing
        # required argument) both start with neither "Error:" nor any other
        # recognised failure prefix, so they scored as SUCCESSES - the exact
        # V21 "BLOCKED:" defect, reintroduced by me two versions later.
        # Observed on the spongebob run of 2026-08-01: str_replace was
        # rejected at step 3, recorded as ok, and the identical retry at step
        # 4 came back "DUPLICATE CALL SUPPRESSED: this call already succeeded
        # earlier in this run and nothing has changed since". The model was
        # locked out of a legitimate one-line fix by a rejection that should
        # never have fired, then told its retry duplicated a success that
        # never happened. It also poisoned the trajectory and the reflection
        # evidence, which read "str_replace: OK (patched spongebob_run.py)"
        # for a call that changed nothing.
        if content.lstrip().startswith(("CALL REJECTED", "CALL INCOMPLETE")):
            return False

        # Check for explicit error markers
        # V21: "BLOCKED:" added - in V20, forbidden/not-allowed commands were
        # recorded as SUCCESSES in the trajectory because their messages did
        # not start with any recognized failure prefix.
        if content.startswith(("Error:", "❌", "Access Denied:", "BLOCKED:")):
            return False

        # V45.8: the GUI-timeout family is the one bash result with NO error
        # prefix AND no "Exit code:" line, so every exit-code check below is
        # blind to it. Run 2 hit it at steps 10 and 13: a 30-second hang was
        # recorded as a SUCCESSFUL command, which set last_ok_bash (defusing
        # the completion gate), satisfied the V41.1 unverified->partial test,
        # and handed _extract_verification a scolding to store as proof.
        # An app that blocked for the full timeout DESPITE being given
        # --test is a failure by any reading: the test never ran.
        # Plain "LAUNCHED OK" (no --test passed) is deliberately left as a
        # success - V21 added it because a windowed app that survives its
        # timeout really did launch.
        # V60.2: this marker only ever ships inside the bash LAUNCHED-OK
        # message, which always OPENS the result. Unanchored, it sat above
        # the `tool_name == "bash"` branch and therefore failed EVERY tool:
        # a clean 6,959-line file_read of a file that merely quotes the
        # string was recorded as a failure, and its trajectory note became
        # the last line of the file, stored as the error evidence. Both
        # conditions below are required; neither alone is sufficient
        # (bash can `type` a file that contains the phrase).
        if (tool_name == "bash"
                and content.lstrip().startswith("LAUNCHED OK")
                and "--test FLAG IS NOT WIRED" in content):
            return False
        
        # For bash commands, parse exit code and error patterns
        if tool_name == "bash":
            # Check exit code
            exit_match = re.search(r'Exit code: (\d+)', content)
            if exit_match and int(exit_match.group(1)) != 0:
                return False
            
            # Check for Python tracebacks and common errors in STDERR
            if "STDERR:" in content:
                stderr_section = content.split("STDERR:")[-1]
                if "Exit code:" in stderr_section:
                    stderr_section = stderr_section.split("Exit code:")[0]
                
                error_patterns = [
                    "Traceback (most recent call last):",
                    "ModuleNotFoundError:",
                    "ImportError:",
                    "SyntaxError:",
                    "NameError:",
                    "FileNotFoundError:",
                    "PermissionError:",
                    "AttributeError:",
                    "TypeError:",
                    "ValueError:",
                    "KeyError:",
                    "IndentationError:",
                    "RuntimeError:",
                    "AssertionError:",
                ]
                for pattern in error_patterns:
                    if pattern in stderr_section:
                        return False
        
        return True
    
    # =====================================================================
    # V21.1: EVIDENCE-BASED REFLECTION SYSTEM
    # (rewrite per the V21 review - the sudo-apt-get-on-Windows incident)
    # =====================================================================

    @staticmethod
    def _extract_error_evidence(content: str) -> str:
        """
        V21.1: pull the ACTUAL error out of a failed tool result.

        V21 stored only the first output line, which for bash is literally
        "STDOUT:" - reflections were generated from zero information, so the
        model invented lessons. This returns the real exception line, the
        deepest file:line frame, and the exit code.
        """
        text = (content or "").strip()
        if not text:
            return ""
        lines = text.splitlines()
        first = lines[0].strip()

        # V41.5: keep the WHOLE tool-level error, not just line 1.
        #
        # The premise this replaces - "Tool-level errors already state the
        # problem on line 1" - is false for exactly the errors that matter.
        # str_replace's whitespace error puts the SYMPTOM on line 1 and the
        # CAUSE on line 2: "most often tabs vs spaces, a trailing space, or a
        # non-breaking space. Line endings were already normalized, so it is
        # NOT CRLF." Storing only line 1 handed the reflection the word
        # "whitespace" with no cause, and the mario_snake run concluded CRLF -
        # writing a convert_to_lf.py that does only
        # data.replace(b'\r\n', b'\n') and cannot touch a trailing space. That
        # lesson was stored grounded=True at confidence 0.92, above the
        # injection filter, and would have taught every later run to run a
        # CRLF conversion for a trailing-space problem.
        #
        # This is NOT a truncation-limit problem: the full message is 548
        # chars and the cap below is 1500, so the cap never fired. lines[0]
        # dropped the diagnosis on its own. Raising a number fixes nothing.
        #
        # ❌ and ⚠️ are included because "❌ VERIFICATION FAILED:\n<real
        # error>" carries its entire payload on the FOLLOWING lines - it was
        # not recognised as a tool error at all and fell through to the
        # traceback path by accident.
        #
        # Structural previews are cut: the candidates engine appends a
        # file-structure dump (🔍 markers, [Lines a-b] headers, numbered
        # source lines). That is a navigation aid for the model in the moment,
        # not evidence about the cause, and it is large enough to swamp the
        # note and the reflection prompt.
        # A tool header wrapping a PYTHON TRACEBACK is not tool prose - the
        # body is subprocess output and the traceback extractor below reads it
        # far better ("ZeroDivisionError: ... | at app.py:3" instead of every
        # line joined by pipes). Detect a real frame line and fall through.
        # Checking for a File "...", line N frame specifically, NOT an
        # exception-shaped word: "Error:" itself matches an exception regex,
        # which would send every tool error down the wrong path.
        _frame_probe = re.compile(r'^\s*File\s+"[^"]+",\s+line\s+\d+', re.M)
        if (first.startswith(("Error:", "BLOCKED:", "Access Denied:", "❌", "⚠️"))
                and not _frame_probe.search(text)):
            # Both dump shapes are emitted UNDER a 🔍 header
            # (_generate_helpful_preview builds preview_parts starting with
            # one), so breaking at 🔍 already excludes the numbered source
            # lines beneath it. A bare `\d+:\s` pattern would be redundant AND
            # would false-break on legitimate error text like "404: Not Found"
            # or a compiler's "1: warning". [Lines is kept as a cheap second
            # anchor - no real error message starts with it.
            dump_re = re.compile(r'^(?:🔍|\[Lines\s)')
            kept = []
            for ln in lines:
                s = ln.strip()
                if dump_re.match(s):
                    break
                if s:
                    kept.append(s)
            # 3000 to match the traceback branch below. The ❌ payload is
            # unbounded subprocess stderr (no upstream slice), so a compiler
            # wall must not be halved on the way in.
            return (" | ".join(kept) or first)[:3000]

        pieces = []

        # Last exception-type line = the root error of a traceback
        exc_re = re.compile(r'^\s*([A-Za-z_][\w\.]*(?:Error|Exception|Interrupt|Exit))\b.*')
        exc_line = None
        for ln in lines:
            if exc_re.match(ln):
                exc_line = ln.strip()
        # Deepest 'File "...", line N' frame = closest to the error
        frame_line = None
        frame_re = re.compile(r'^\s*File\s+"([^"]+)",\s+line\s+(\d+)')
        for ln in lines:
            m = frame_re.match(ln)
            if m:
                # split on / and \ so the filename is short on every platform
                fname = re.split(r'[\\/]', m.group(1))[-1]
                frame_line = f'{fname}:{m.group(2)}'
        if exc_line:
            pieces.append(exc_line[:1500])
        if frame_line:
            pieces.append(f"at {frame_line}")

        # V41.2: capture the actual message even when an exit code is present.
        # Previously "exit code N" was appended FIRST and the message fallback
        # was gated on `if not pieces`, so the fallback was dead code for any
        # nonzero exit. Every non-Python failure - compilers, where, git, npm,
        # make: nonzero exit, real text in stderr, no traceback - collapsed to
        # the bare string "exit code 1" and the diagnostic was discarded. The
        # Dragonfly run reduced "INFO: Could not find files for the given
        # pattern(s)." to "exit code 1", and the reflection LLM correctly
        # reported it could not see a cause. Gate the message capture on
        # ABSENCE OF TRACEBACK STRUCTURE instead, and append the exit code
        # after it, so both survive.
        if not exc_line and not frame_line:
            for ln in reversed(lines):
                s = ln.strip()
                if s and s not in ("STDOUT:", "STDERR:") and not s.startswith("Exit code:"):
                    pieces.append(s[:1500])
                    break

        exit_m = re.search(r'Exit code:\s*(\d+)', text)
        if exit_m and exit_m.group(1) != "0":
            pieces.append(f"exit code {exit_m.group(1)}")

        return " | ".join(pieces)[:3000]

    @staticmethod
    def _extract_verification(content: str) -> str:
        """V21.1: for a successful bash run, return the proof line
        (e.g. 'SELF-TEST OK') plus the exit code."""
        text = content or ""
        # V45.8: never scrape a LAUNCHED-OK message. It carries no exit
        # line, so the reversed scan below returns its LAST line - which is
        # the instruction "Do NOT re-run '<file>' until --test is wired -
        # it will block again". Run 2 stored exactly that string as its
        # verification evidence. A launch proves nothing was tested; say so
        # rather than quoting a warning as if it were a result.
        if text.lstrip().startswith("LAUNCHED OK"):
            return ("launched only - the app opened and blocked until the "
                    "timeout; NO test was executed and nothing was verified")
        proof = ""
        for ln in reversed(text.splitlines()):
            s = ln.strip()
            if s and s not in ("STDOUT:", "STDERR:") and not s.startswith("Exit code:"):
                proof = s
                break
        exit_m = re.search(r'Exit code:\s*(\d+)', text)
        if exit_m:
            proof = f"{proof} (exit {exit_m.group(1)})" if proof else f"exit {exit_m.group(1)}"
        return proof[:32000]

    # V30.8: deterministic recognizer for the model's OWN success signal.
    # The mario_snake run hit "=== ALL SELF-TESTS PASSED ===" (exit 0) at
    # step 12 and then kept re-testing and re-patching to step 18 - it did
    # not register that its task's own criterion had already passed. This
    # is NOT an LLM reflection (no model call, cannot confabulate): it is a
    # string match on the canonical pass phrases the GUI protocol tells the
    # model to print, gated on a clean exit code. When it fires, the loop
    # surfaces one factual line into context so the model can SEE its own
    # green result instead of having to infer it.
    _PASS_SIGNALS = ("SELF-TEST OK", "SELF-TESTS PASSED", "ALL TESTS PASSED",
                     "ALL SELF-TESTS PASSED", "TESTS PASSED")

    # --- V38.1 negation / clause awareness (shared by the self-test surface
    # and the reflection grounding floor) ---------------------------------
    # Both were naive substring matchers: _is_test_pass fired on the
    # 'ALL TESTS PASSED' inside 'NOT ALL TESTS PASSED', and the grounding
    # floor rejected the correct lesson 'use python NOT python3' because the
    # token 'python3' was absent from the evidence - unable to tell an
    # assertion ('I ran python3') from a warning ('avoid python3'). This
    # helper reports whether a matched span sits in a clause that negates or
    # warns AGAINST it, so a warned-against token is KEPT as valid preventive
    # advice and a negated pass phrase is NOT read as a pass. Clause = the
    # span between the nearest clause delimiters on each side, so a negation
    # in a different clause ('do not use python, use python3') does not bleed.
    _CLAUSE_DELIM_RE = re.compile(r'[,.;:!?\n]|\b(?:and|but|then|however|so)\b',
                                  re.IGNORECASE)
    _NEG_CUE_RE = re.compile(
        r'\b(?:not|no|never|without|avoid|avoiding|cannot|cant|isnt|arent|'
        r'wasnt|werent|dont|doesnt|didnt|wont|shouldnt|couldnt|wouldnt|'
        r'unsupported|invalid|instead|rather|skip|skipping|forbidden|'
        r'unavailable)\b', re.IGNORECASE)

    @classmethod
    def _phrase_negated_in_clause(cls, text: str, start: int, end: int) -> bool:
        """True if text[start:end] is negated / warned-against within its
        clause (the span between the nearest clause delimiters on each side).
        Apostrophes are stripped so 'isn't'/'don't' match the cue set."""
        cs = 0
        for m in cls._CLAUSE_DELIM_RE.finditer(text, 0, start):
            cs = m.end()
        ce = len(text)
        m = cls._CLAUSE_DELIM_RE.search(text, end)
        if m:
            ce = m.start()
        prefix = text[cs:start].lower().replace("'", "").replace("\u2019", "")
        suffix = text[end:ce].lower().replace("'", "").replace("\u2019", "")
        return bool(cls._NEG_CUE_RE.search(prefix) or cls._NEG_CUE_RE.search(suffix))

    @classmethod
    def _is_test_pass(cls, content: str) -> bool:
        """True iff a bash result shows a task-level self-test passing:
        one of the canonical pass phrases AND exit code 0 (or no failing
        exit code present).

        V30.8a: instrumented. In the mario_snake V30.8 run the game printed
        'ALL TESTS PASSED! ✓' with exit 0 yet the SELF-AWARENESS surface
        produced no line in the captured log - while this function and the
        live-driven agent both fire on that exact content in isolation. A
        text log can't show the live is_success / test_pass_surfaced state
        at that step, so log the decision here: the next run's log will say
        outright whether the detector saw the pass, isolating a detector
        miss from a downstream (loop-state) bypass. Diagnostic only - the
        return values are unchanged."""
        text = content or ""
        up = text.upper()
        # V38.1: a canonical pass phrase counts only when at least one of its
        # occurrences is NOT negated in its clause - 'NOT ALL TESTS PASSED'
        # (or 'tests did not pass') no longer reads as a pass. Same lexical
        # class as the reflection grounding-floor fix below.
        matched = None
        for sig in cls._PASS_SIGNALS:
            idx = up.find(sig)
            while idx != -1:
                if not cls._phrase_negated_in_clause(up, idx, idx + len(sig)):
                    matched = sig
                    break
                idx = up.find(sig, idx + 1)
            if matched:
                break
        if matched is None:
            return False
        # V171 FIX 1: read EVERY exit code in the result, not re.search's
        # first. Measured on the mario_game run of 2026-08-04: the model
        # wrapped its own test in run_test.py, which PRINTS the child's
        # "Exit code: 1" and then exits 0 itself, so the bash result carries
        # two exit lines. A single re.search picks whichever came first and
        # the other one - the one that actually decides - is never read.
        # A pass now requires every exit code present to be 0, which is
        # correct in both wrapper directions.
        exits = re.findall(r'Exit code:\s*(\d+)', text)
        if exits:
            verdict = all(e == "0" for e in exits)
            debug_print(f"_is_test_pass: phrase '{matched}' found, "
                        f"exit code(s) {','.join(exits)} -> {verdict}")
            return verdict
        # No explicit exit line but a pass phrase present: treat as pass.
        debug_print(f"_is_test_pass: phrase '{matched}' found, "
                    f"no exit line -> True")
        return True

    @classmethod
    def _pass_proof(cls, content: str) -> str:
        """The line that PROVES the pass - the output line containing the
        matched pass phrase, trimmed. V30.8b: the surface must cite proof
        of SUCCESS, not run _extract_verification, which is an ERROR
        extractor: on a pass that also carries a stderr traceback (the
        exact case V30.8a fires on) it returns the traceback, so the
        message read 'your self-test just PASSED (struct.error: pack
        expected 6 items)' - a success announced with an error as its
        evidence, which a temp-0.6 model can read as 'still broken' and
        dive back into the loop the surface exists to end. Quote the real
        pass line instead."""
        text = content or ""
        up = text.upper()
        matched = next((sig for sig in cls._PASS_SIGNALS if sig in up), None)
        if matched is None:
            return "self-test passed"
        for line in text.splitlines():
            if matched in line.upper():
                # strip box-drawing borders / whitespace the panel adds
                clean = line.strip().strip("│").strip("|").strip()
                if clean:
                    return clean[:200]
        return matched.title()

    @classmethod
    def _is_test_fail(cls, content: str, command: str = "") -> bool:
        """V38.1: True iff a bash result shows a self-test FAILING - a strong,
        unambiguous failure marker (an assertion, a unittest failure summary,
        an explicit SELF-TEST FAIL), or a nonzero exit code from a run whose
        output is a test. Deliberately narrow: it drives the one-time
        SELF-AWARENESS retraction, so it must not fire on incidental uses of
        the word 'fail'. Zero-count / negated markers ('no tests failed') are
        excluded by the clause check.

        V171 FIX 1: THIS DETECTOR WAS BLIND TO THE FAILURE SHAPE THIS
        MACHINE'S OWN PROMPT PRODUCES, and that is the single defect that
        disarmed the most machinery in the mario_game run of 2026-08-04.

        The GUI/GAME VERIFICATION PROTOCOL hands the model
        `print("SELF-TEST OK")` as the PASS path and says nothing about the
        FAIL path, so the model invented one:

            if test_passed:  print("SELF-TEST OK - All features verified")
            else:            for err in errors: print(f"FAIL: {err}")
                             raise SystemExit(1)

        Seventeen `FAIL:` lines and exit code 1. Driven through the old
        detector, that returns False: no ASSERTIONERROR (the harness catches
        its own exceptions and prints them), no "SELF-TEST FAIL", and the
        exit-code fallback additionally required the literal token "TEST" in
        the output - which appears ONLY on the pass path, in "SELF-TEST OK".
        So the detector saw every pass and no failure. Downstream, all
        measured in that run's log: the red window closed at 23:02:52 and
        NEVER REOPENED across the next 52 minutes; the model deleted 8
        assertions at 23:04:53 and was told nothing ("TEST WEAKENED (not
        warned - no test failure open)"); and _saw_test_fail stayed unset, so
        every mechanism keyed on "a test has actually failed here" was
        inert while the artifact went from 0 failures to 19.

        Three changes, all evidence-widening, none of them loosening what
        counts as a TEST:
          1. line-anchored FAIL:/FAILED: markers - a line that STARTS with
             the token is a test result, whereas the word appearing mid-line
             ("failed to open config, using defaults") is not, which is why
             the old `strong` list could not simply add "FAIL".
          2. every exit code is read, not re.search's first - see the
             wrapper case documented on _is_test_pass above.
          3. the COMMAND is accepted as evidence of testhood, so
             `python mario_game.py --test` exiting nonzero is a test failure
             even when the output never says the word. The output-side
             "TEST" test is KEPT as a disjunct, so nothing that fired before
             stops firing.
        """
        text = content or ""
        up = text.upper()
        strong = ("ASSERTIONERROR", "SELF-TEST FAIL", "SELF-TESTS FAILED",
                  "FAILED (FAILURES=", "FAILED (ERRORS=")
        for s in strong:
            idx = up.find(s)
            while idx != -1:
                if not cls._phrase_negated_in_clause(up, idx, idx + len(s)):
                    return True
                idx = up.find(s, idx + 1)
        # (1) A line whose first token is FAIL:/FAILED: is a reported test
        # result. Anchored to the line start so prose cannot forge it.
        for ln in up.splitlines():
            probe = ln.strip().lstrip("|│>*-\u2022 \t")
            if probe.startswith(("FAIL:", "FAILED:", "FAIL -", "FAILED -",
                                 "[FAIL]", "\u274c FAIL")):
                if not cls._phrase_negated_in_clause(ln, 0, len(ln)):
                    return True
        # (2)+(3) nonzero exit from something that IS a test.
        exits = re.findall(r'Exit code:\s*(\d+)', text)
        if exits and any(e != "0" for e in exits):
            cmd_up = (command or "").upper()
            looks_like_test = (
                "TEST" in up                      # V38.1 behaviour, unchanged
                or "TEST" in cmd_up                # `python x.py --test`
                or "PYTEST" in cmd_up
                or "--SELFTEST" in cmd_up
                or "UNITTEST" in cmd_up
            )
            if looks_like_test:
                return True
        return False

    def _notify(self, msg: str):
        """V45.5: report a mechanism decision to the dashboard. Visible in
        normal mode via the ◈ prefix. Never raises - a notifier that
        explodes must not take the run with it."""
        # V61.27: also to the run log. These lines ARE the record of what
        # the machine decided - which gate fired, what it measured, why an
        # outcome changed - and they were going only to a live dashboard that
        # scrolls away. Auditing mario_game meant inferring gate behaviour
        # from its ABSENCE, because "COMPLETION GATE: bounced" appears nowhere
        # in a 10 MB log.
        debug_print(msg)
        try:
            cb = getattr(self, "_status_cb", None)
            if cb:
                cb("◈ " + msg)
        except Exception:
            pass

    # V60.2: the ONE place that decides whether a marker in a tool result was
    # put there by this machine or was merely READ OUT OF A FILE.
    #
    # Three locks, all required:
    #   (a) TOOL SCOPE - a write gate cannot come out of a file_read,
    #       grep_search or list_dir, so those tools can never raise one;
    #   (b) ANCHOR - the shared MARK_* constants carry the leading newlines
    #       the emitter appends, which no quoted copy and no numbered dump
    #       can reproduce;
    #   (c) for HINT, the result must also have FAILED - every HINT this
    #       machine emits rides on an error result, so a successful
    #       `bash type prompt.txt` can no longer trip the nudge.
    #
    # Returns a set of signal names; an empty set means the machine said
    # nothing about this result and only the model's own content is present.
    GATE_TOOLS = ("file_write", "str_replace")
    HINT_TOOLS = ("file_write", "str_replace", "bash")

    @staticmethod
    def _machine_gate_signals(tool_name: str, content: str,
                              is_success: bool = True) -> set:
        sig = set()
        c = content or ""
        if tool_name in Agent.GATE_TOOLS:
            if MARK_TRUNCATED_WRITE in c:
                sig.add("truncated")
            elif MARK_SYNTAX_ERROR in c:
                sig.add("syntax")
            if MARK_GATE_STALLED in c:
                sig.add("stalled")
        if (tool_name in Agent.HINT_TOOLS and not is_success
                and HINT_LINE_RE.search(c)):
            sig.add("hint")
        return sig

    def _annotate_result(self, tc, result, refused_overwrites) -> None:
        """V45.8: append write-time warnings to a tool result IN PLACE, before
        success detection and note-building, so a warning reaches the model, the
        trajectory note, episodes.jsonl and the reflection evidence by the one
        path the V45.3 syntax flags already use.

        Appended to a message that starts with "✅", so no success verdict is
        changed by annotating. Never raises: an annotator that explodes must not
        take the run with it, and it reports rather than swallowing.
        """
        try:
            content = str(result.get("content", ""))
            args = tc.arguments if isinstance(tc.arguments, dict) else {}

            # (a) remember every overwrite refusal, by basename
            if content.startswith("❌ Refusing to overwrite"):
                base = re.split(r"[\\/]", str(args.get("path", "") or ""))[-1]
                if base:
                    refused_overwrites[base] = len(self.trajectory) + 1
                return

            if not content.startswith("✅"):
                return

            # (b) test-scope change.
            #
            # V61.2 - HIS POINT, AND HE IS RIGHT: "silent is bad for logs."
            # V45.8 armed this on ONE condition, that the IMMEDIATELY previous
            # step failed. On his spongebob run the weakening happened to land
            # on an armed step, so it was caught - but the identical edit one
            # step later would have produced NOTHING, and a log that says
            # nothing cannot be told apart from a log that found nothing.
            #
            # Two changes, and the order matters:
            #   1. the detector now RUNS on every str_replace that touches
            #      assertions, unconditionally. Detection is never gated.
            #   2. arming decides only WHO HEARS IT. Inside the red window the
            #      warning is appended to the tool result, where the model
            #      reads it. Outside, it still goes to the operator log via
            #      _notify, so the run always records that it happened.
            #
            # The red window itself is the V45.11 shape, which never reached
            # this lineage: it opens on a failing self-test and stays open
            # until one actually PASSES, instead of closing the instant any
            # single successful step goes by. The V45.8 adjacent-step trigger
            # is kept as the first disjunct, so nothing that warned before
            # stops warning.
            if tc.name == "str_replace":
                w = test_edit_warning(str(args.get("old_str", "") or ""),
                                      str(args.get("new_str", "") or ""))
                if w:
                    adjacent = bool(self.trajectory) and not self.trajectory[-1][2]
                    armed = adjacent or getattr(self, "_test_fail_window_open", False)
                    # V61.4: WARN THE MODEL AT MOST ONCE PER OPEN WINDOW.
                    # V61.2 widened the trigger so the detector stays armed
                    # until a test actually PASSES. That is right, but the
                    # window only closes on a CANONICAL pass phrase - so a
                    # build whose tests print anything else keeps it open for
                    # the whole run, and EVERY later assertion edit would have
                    # appended this whole warning to the tool result. Twenty of
                    # those in a context is not a safety net, it is a model
                    # being talked over while it works. The first one carries
                    # the signal; the rest go to the log only.
                    already = getattr(self, "_weaken_warned", False)
                    if armed and not already:
                        self._weaken_warned = True
                        result["content"] = content + w
                        content = result["content"]
                        self._notify(
                            "TEST SCOPE CHANGED - an edit to a failing test "
                            "weakened what it checks"
                            + ("" if adjacent else " (red window still open "
                                                   "from an earlier failing test)"))
                    else:
                        # Never silent. The run records every one of them, and
                        # says which reason it was not injected, so the log can
                        # never be misread as "checked and found clean".
                        first = next((ln.strip(" -") for ln in w.splitlines()
                                      if ln.strip().startswith("-")), "")
                        why = ("already warned once this window" if already
                               else "no test failure open")
                        self._notify(
                            f"TEST WEAKENED (not warned - {why}): "
                            + (first or "assertion made weaker")
                            + f" [{args.get('path', '?')}]")

            # (c) deliverable split: a NEW file after a refusal on another one
            if tc.name == "file_write" and refused_overwrites:
                base = re.split(r"[\\/]", str(args.get("path", "") or ""))[-1]
                w = deliverable_split_warning(base, list(refused_overwrites))
                if w:
                    result["content"] = content + w
                    self._notify(f"DELIVERABLE SPLIT - {base} created after an "
                                 f"overwrite refusal on "
                                 f"{', '.join(k for k in refused_overwrites)}")
        except Exception as e:
            debug_print(f"_annotate_result failed (non-fatal): {e}")

    def _tool_note(self, name: str, arguments, content: str, ok: bool) -> str:
        """
        V21.1: one evidence note per trajectory step.
        Failures -> the real error (exception, file:line, exit code).
        Successes -> what changed or what was proven, so the reflection can
        cite the fix and the verification instead of guessing.
        """
        if not ok:
            err = self._extract_error_evidence(content)
            # V45.8: a BLOCKED note is this machine's OWN GUARD speaking,
            # but in the evidence block it is indistinguishable from a fact
            # about the world. Run 5 read "BLOCKED: command 'head' not in
            # allowed list" and stored "On Windows, avoid using 'head' in
            # piped commands" at 0.9 / grounded=True. Verified that neither
            # gate can catch it: 'head' is in no impossible/suspect regex,
            # and it DOES appear in the evidence, so the causality judge
            # sees support. Tag it where the evidence is made.
            # APPENDED, never prefixed - _classify_failure and the duplicate
            # guard call startswith() on this note for "BLOCKED:" and
            # "Access Denied", and a prefix would break both (V41.2).
            if err and content.startswith(("BLOCKED:", "Access Denied:")):
                err = (err + SANDBOX_POLICY_TAG)[:3000]
            # V41.2: a failed bash note omitted the command entirely - the
            # success path has always recorded it - so the reflection could
            # see THAT something failed but never WHAT. The Dragonfly run's
            # root_cause said outright that the trace "does not record the
            # executed command". APPENDED, never prefixed: _classify_failure
            # and the dedup logic call startswith() on this note for
            # "PROTOCOL ERROR", "BLOCKED:", "Access Denied" and
            # "DUPLICATE SUPPRESSED", and a prefix would break all four.
            if name == "bash":
                bargs = arguments if isinstance(arguments, dict) else {}
                bcmd = str(bargs.get("command", "") or "")
                bcmd = re.sub(r'^\s*cd\s+("[^"]*"|\'[^\']*\'|\S+)\s*&&\s*', '', bcmd)
                if bcmd:
                    return f"{err} [cmd: {bcmd[:300]}]"[:3000] if err else \
                           f"failed [cmd: {bcmd[:300]}]"[:3000]
            return err
        args = arguments if isinstance(arguments, dict) else {}
        path = str(args.get("path", "") or "")
        if name in ("file_write", "str_replace"):
            if not path:
                return ""
            verb = "wrote" if name == "file_write" else "patched"
            # V45.3: carry the write-time warnings into the trajectory.
            # Without this the note is just "wrote x.html" and neither
            # episodes.jsonl nor the reflection writer can ever see that
            # the file was left unparseable - the gate fires only into
            # the model's message history and nowhere else.
            flags = []
            # V60.2 same-class sweep: this one is already tool-scoped (it is
            # inside the file_write/str_replace branch) and reached only on
            # the SUCCESS path, so no echoed file content can arrive here -
            # but it is the identical predicate to the three the loop just
            # had fixed, so it gets the identical anchor rather than being
            # left as the last unanchored copy for someone to trip over.
            # The line-scan below is unchanged and still finds the text.
            if MARK_SYNTAX_ERROR in content:
                first = next((ln.strip() for ln in content.split("\n")
                              if "SYNTAX ERROR" in ln), "")
                flags.append("SYNTAX ERROR LEFT ON DISK - " + first[:220])
            if "silent exception swallower" in content:
                flags.append("silent exception swallower(s) introduced")
            # V45.8: same reasoning as the V45.3 syntax flags - without
            # this the warning fires only into the model's message history
            # and neither episodes.jsonl nor the reflection writer can ever
            # see that the run changed what it was testing, or that the
            # deliverable changed identity mid-run.
            if TEST_WEAKENED_MARK in content:
                flags.append("TEST SCOPE CHANGED - edit to a failing test "
                             "dropped the call it exercised")
            if DELIVERABLE_SPLIT_MARK in content:
                flags.append("DELIVERABLE SPLIT - new file created after an "
                             "overwrite refusal on a different file")
            return (f"{verb} {path}"
                    + ("" if not flags else " | " + " | ".join(flags)))[:800]
        if name == "bash":
            cmd = str(args.get("command", "") or "")
            # V22.1: strip a leading cd "..." && prefix so the informative
            # part survives the 200-char cut (every temple_dash bash note
            # began 'cd "C:\Users\...' with the real command lost).
            cmd = re.sub(r'^\s*cd\s+("[^"]*"|\'[^\']*\'|\S+)\s*&&\s*', '', cmd)
            proof = self._extract_verification(content)
            note = f"ran '{cmd[:600]}'"
            if proof:
                note += f" -> {proof}"
            return note[:1500]
        return ""

    # --- V22.1 duplicate-call breaker ------------------------------------
    # The temple_dash run repeated identical successful calls back to back
    # (the same byte-offset check 3x, the passing --test 3x, list_dir 2x),
    # burning iterations and ~full-context resends each time. If a call is
    # byte-identical to the immediately previous call AND that call
    # succeeded, nothing can have changed in between - the result would be
    # identical, so it is suppressed with an explanation instead of run.
    # A failed previous call may always be retried.

    @staticmethod
    def _call_signature(tc) -> str:
        try:
            args = json.dumps(tc.arguments, sort_keys=True, default=str)
        except Exception:
            args = str(tc.arguments)
        return f"{tc.name}::{args}"

    def _duplicate_guard(self, tc):
        """Return a suppression message if this call repeats a call that
        already succeeded, else None.

        V30.8: the single-slot version (only _last_call_sig) caught a
        duplicate ONLY when it directly followed its twin. The mario_snake
        run showed the blind spot: the model alternated patch->test->same
        patch->test, so every repeat was separated by a different call and
        _dup_streak reset to 0 each time - the LOOP-DETECTED escalation
        could never fire on an alternating pattern, only a literal stutter.
        Now a set of up to 100 successful signatures with a per-signature
        repeat count is kept, so a re-issue is caught however many other
        calls sit between it and its original, and escalation triggers on
        the TOTAL number of times a given call has been re-run, not just
        consecutive ones.
        """
        sig = self._call_signature(tc)
        seen = getattr(self, "_ok_call_counts", None)
        if seen is None:
            seen = self._ok_call_counts = {}

        # V61.6: A FAILED EDIT THAT CANNOT CHANGE ITS OWN OUTCOME.
        #
        # The guard below has always cached SUCCESSES only, so a repeated call
        # that worked is suppressed while a repeated "String not found" sails
        # through - backwards. A repeated success is wasted work; a repeated
        # str_replace that missed is GUARANTEED to miss again, because the file
        # it failed against has not been written since. Audited by execution:
        # four identical failing str_replace calls all ran, while two identical
        # successful bash calls were suppressed on the second.
        #
        # Scope is deliberately narrow - only the two tools whose failure is a
        # pure function of file state:
        #   str_replace: "String not found" / "appears N times" cannot resolve
        #     without a write, and a write purges this cache (see below).
        #   file_write: "Refusing to overwrite" cannot resolve while the file
        #     exists, and every route to deleting it is already blocked.
        # bash is EXCLUDED on purpose: a failing command can legitimately pass
        # after an edit somewhere else, and suppressing that would be worse
        # than the loop this fixes.
        failed = getattr(self, "_failed_call_sigs", None)
        if failed is None:
            failed = self._failed_call_sigs = {}
        if sig in failed:
            failed[sig] += 1
            return (
                f"ALREADY FAILED: this exact {tc.name} was tried "
                f"{failed[sig] + 1} times in this session and returned the same "
                f"error every time. Nothing has written to that file since, so "
                f"it cannot succeed now - the file still holds exactly what it "
                f"held when the first attempt missed.\n"
                f"   Repeating it is the one move guaranteed not to work. "
                f"file_read the region you are aiming at, copy old_str out of "
                f"what you actually see (not from memory of what you wrote), "
                f"and include enough surrounding lines to make it unique."
            )

        # Consecutive-stutter path (unchanged behavior): keep _dup_streak so
        # a rapid identical repeat still escalates fast.
        if sig == getattr(self, "_last_call_sig", None) and getattr(self, "_last_call_ok", False):
            self._dup_streak = getattr(self, "_dup_streak", 0) + 1
        else:
            self._dup_streak = 1 if sig in seen else 0

        if sig in seen:
            seen[sig] += 1
            total = seen[sig]  # how many times this exact call has now repeated a success
            # Escalate on EITHER a fast stutter (>=3 in a row) OR enough
            # total re-runs of the same successful call across the run.
            if self._dup_streak >= 3 or total >= 3:
                return (f"LOOP DETECTED: you have issued this exact {tc.name} "
                        f"call {total} times after it already succeeded"
                        + (f" ({self._dup_streak} in a row)" if self._dup_streak >= 3 else "")
                        + f". You are looping. STOP calling tools and write your "
                        f"final summary of what was built and how it was verified, NOW.")
            return (f"DUPLICATE CALL SUPPRESSED: this {tc.name} call already "
                    f"succeeded earlier in this run and nothing has changed since, "
                    f"so the result is identical. Do not repeat successful calls - "
                    f"move to the next step, or if the task is done, give your final "
                    f"summary now.")
        return None

    def _remember_call(self, tc, ok: bool):
        sig = self._call_signature(tc)
        self._last_call_sig = sig
        self._last_call_ok = bool(ok)
        # V61.6: remember the failures that cannot resolve on their own.
        if not ok and tc.name in ("str_replace", "file_write"):
            failed = getattr(self, "_failed_call_sigs", None)
            if failed is None:
                failed = self._failed_call_sigs = {}
            if sig not in failed:
                if len(failed) >= 100:
                    failed.pop(next(iter(failed)))
                failed[sig] = 0
        if ok:
            seen = getattr(self, "_ok_call_counts", None)
            if seen is None:
                seen = self._ok_call_counts = {}
            # V41.3: a successful WRITE invalidates every cached call that
            # touched that file. The guard's whole claim - "nothing has
            # changed in between, so the result would be identical" - is
            # simply FALSE once the file has been edited, and nothing here
            # ever purged the cache. In the mario_snake run str_replace
            # succeeded at step 42 and file_read of the same region was still
            # suppressed at steps 44 and 47 with "nothing has changed since".
            # Worse, str_replace's own error tells the model to "file_read the
            # target region and copy old_str byte-for-byte" - so the machine
            # was blocking the exact recovery it prescribed, and the model
            # spent 16 iterations unable to establish what the file contained.
            # Purge BEFORE recording this call, so an immediate identical
            # repeat of the write itself is still caught.
            # Basename match, so a cached call is cleared whether it named the
            # file relatively, absolutely, or inside a bash command string.
            if tc.name in ("file_write", "str_replace"):
                wargs = tc.arguments if isinstance(tc.arguments, dict) else {}
                wpath = str(wargs.get("path", "") or "").strip()
                base = re.split(r'[\\/]', wpath)[-1] if wpath else ""
                if base:
                    stale = [k for k in seen if base in k]
                    for k in stale:
                        del seen[k]
                    # V61.6: the failed-edit cache is purged by the SAME rule
                    # and for the same reason - once the file has been written,
                    # an edit that missed may now hit, so the guarantee that
                    # justified suppressing it is gone.
                    fseen = getattr(self, "_failed_call_sigs", None) or {}
                    fstale = [k for k in fseen if base in k]
                    for k in fstale:
                        del fseen[k]
                    if stale or fstale:
                        debug_print(f"Duplicate-guard: purged {len(stale)} cached call(s) "
                                    f"and {len(fstale)} failed-edit signature(s) "
                                    f"referencing '{base}' after a successful {tc.name}")
                    # A cached read of this file must not survive as the
                    # consecutive-stutter anchor either.
                    if base in (getattr(self, "_last_call_sig", "") or ""):
                        self._dup_streak = 0
            # Record the signature as a known success (count starts at 0 -
            # _duplicate_guard increments on each REPEAT). Bound the set to
            # the 100 most-recent successes so a very long run can't grow it
            # without limit; oldest entry is dropped when full.
            if sig not in seen:
                if len(seen) >= 100:
                    seen.pop(next(iter(seen)))
                seen[sig] = 0

    # Failure taxonomy from the V21 review, applied deterministically in
    # code BEFORE the reflection prompt - the model never picks the class.
    FAILURE_CLASSES = (
        "syntax_error", "runtime_exception", "dependency_missing",
        "environment_mismatch", "logic_bug", "tool_misuse", "test_failure",
        "protocol_error",  # V38.1: Ollama transport/template rejection, not a task fault
    )

    # V41.1: protocol markers a task prompt can mandate for an explicit
    # give-up. NOT natural-language inference - the marker must be
    # LINE-ANCHORED, so a mention inside a quoted instruction mid-sentence
    # will not match. The optional prefix is because the observed give-up in
    # the Dragonfly run printed a bare "**BLOCKED: Missing toolchain**"
    # rather than the "MISSION BLOCKED:" the prompt asked for - matching only
    # the mandated form would have missed the very case this exists for.
    # The negative lookahead excludes the BLOCKED: messages the TOOLS emit
    # ("BLOCKED: command '...' not in allowed list", "BLOCKED: shell
    # write-redirection...", etc), which a model may quote in a final reply
    # that is otherwise a legitimate success.
    # Case-SENSITIVE on BLOCKED: it is a shouted protocol token, and a
    # lowercase "blocked:" at line start is far likelier to be prose. The
    # optional prefix IS case-insensitive (scoped inline flag), so
    # "Mission BLOCKED:" matches while "mission blocked:" does not.
    _BLOCK_MARKER_RE = re.compile(
        r"(?m)^\s*(?:\W{0,4}\s*)?"
        r"(?:(?i:MISSION|TASK|CHECKPOINT|PHASE)\s*\d*\s+)?"
        r"BLOCKED\s*:"
        r"(?!\s*(?:'|\"|command\b|inline\b|shell\b))")

    # V45: BUILD_PROMPT v4 requires the final summary to OPEN with a
    # verdict line. Read it. In the V44 fracture run the agent's own
    # summary said 'incomplete (has syntax error)' and the episode was
    # still stored as SUCCESS - the confession was written and ignored.
    _VERDICT_BROKEN_RE = re.compile(r"(?mi)^\s*\W{0,4}\s*VERDICT\s*:\s*BROKEN\b")
    _VERDICT_OK_RE = re.compile(r"(?mi)^\s*\W{0,4}\s*VERDICT\s*:\s*WORKING\b")
    # Fallback for runs predating the verdict rule. Deliberately narrow:
    # phrases that assert a KNOWN DEFECT, not merely a gap in coverage.
    # 'written but unverified' is NOT here - BUILD_PROMPT mandates that
    # phrase for honestly-reported partial coverage, so matching it would
    # downgrade nearly every well-behaved run.
    # V45.7: a one-shot run has nobody to answer a question. A final
    # message that asks the operator what to do next, or offers a menu of
    # things it COULD do, is an abandoned task wearing a helpful face.
    _ABANDONED_RE = re.compile(
        r"(?i)(what would you like|what's the next step|which would you"
        r"|would you like me to|shall i (?:continue|proceed)"
        r"|let me know (?:if|what|which)|how would you like"
        r"|do you want me to (?:continue|proceed)"
        r"|ready (?:for|to proceed) when you)")
    _KNOWN_DEFECT_RE = re.compile(
        r"(?i)(known issues?\b|\bunresolved\b|still (?:fails|broken|has)\b"
        r"|does not (?:run|parse|work)\b|incomplete \(has\b)")


    @staticmethod
    def _classify_failure(note: str, tool_name: str = "", args_summary: str = "") -> str:
        """V21.1: classify a failure from its evidence note."""
        n = note or ""
        # V38.1: transport/template failure (Ollama 500 at render time) is not
        # a task fault - classify it first so it can never be mistaken for a
        # shell/tool error just because a later regex matches the payload echo.
        if (n.startswith("PROTOCOL ERROR") or "returned 500" in n
                or "expected element type" in n):
            return "protocol_error"
        if "SyntaxError" in n or "IndentationError" in n:
            return "syntax_error"
        if "ModuleNotFoundError" in n or "ImportError" in n or "No module named" in n:
            return "dependency_missing"
        if "AssertionError" in n or "SELF-TEST FAIL" in n:
            return "test_failure"
        if (n.startswith("BLOCKED:") or "not in allowed list" in n
                or "String not found" in n or "Must be unique" in n
                or "Refusing to overwrite" in n):
            return "tool_misuse"
        if n.startswith("Access Denied") or "timed out" in n.lower():
            return "environment_mismatch"
        if re.search(r'\b[A-Za-z_][\w\.]*(?:Error|Exception)\b', n):
            return "runtime_exception"
        if "exit code" in n.lower():
            return "test_failure" if "--test" in args_summary else "logic_bug"
        return "unknown"

    # --- V38.1 Ollama protocol-error recovery -----------------------------
    # A 500 at template-render time (prompt_eval_count 0) is a DETERMINISTIC
    # rejection of the replayed tool-call history - a blind resend 500s
    # identically (the fake iteration this machine exists to prevent). The
    # only real fix is to REPAIR the history: collapse the offending
    # assistant tool-call turn (and its tool results) into one plain-text
    # assistant message so the chat template has no <function> element to
    # choke on. Content is preserved as prose - nothing the model already saw
    # is lost, it is just no longer structured. Bounded, and walks back one
    # turn per attempt, so it always terminates.
    @staticmethod
    def _is_protocol_error(response) -> bool:
        """True for an Ollama transport/template failure that history repair
        can address (the 500 path, which sets raw_response={'error': ...}).
        Timeouts and other ⚠️ replies are excluded - flattening won't help."""
        return bool(
            response.content and response.content.startswith("⚠️")
            and isinstance(response.raw_response, dict)
            and "error" in response.raw_response
        )

    def _flatten_recent_toolcalls(self) -> bool:
        """Collapse the most recent assistant message that still carries
        tool_calls - together with its following tool-result messages - into a
        single plain-text assistant message. Interleaved system nudges are
        left in place. Returns False when there is no structured tool-call
        turn left to flatten."""
        idx = -1
        for i in range(len(self.messages) - 1, -1, -1):
            if self.messages[i].role == "assistant" and self.messages[i].tool_calls:
                idx = i
                break
        if idx == -1:
            return False
        asst = self.messages[idx]
        results = {}
        remove = []
        j = idx + 1
        while j < len(self.messages):
            mj = self.messages[j]
            if mj.role == "tool":
                results[mj.tool_call_id] = (mj.tool_name, mj.content)
                remove.append(j)
                j += 1
            elif mj.role == "system":
                j += 1  # keep interleaved system nudges where they are
            else:
                break    # next assistant/user turn - stop
        segs = []
        for tc in asst.tool_calls:
            _, tcontent = results.get(tc.id, ("", ""))
            try:
                args_str = (tc.arguments if isinstance(tc.arguments, str)
                            else json.dumps(tc.arguments))
            except Exception:
                args_str = str(tc.arguments)
            seg = f"[called {tc.name}({args_str[:4000]})"
            if tcontent:
                seg += f" -> {str(tcontent)[:4000]}"
            seg += "]"
            segs.append(seg)
        base = (asst.content or "").strip()
        new_content = (base + ("\n" if base and segs else "")
                       + "\n".join(segs)).strip() or "[tool call flattened]"
        self.messages[idx] = Message(role="assistant", content=new_content)
        for k in sorted(remove, reverse=True):
            del self.messages[k]
        return True

    async def _recover_protocol_error(self):
        """Flatten-and-retry the chat call, walking back one tool-call turn
        per attempt. Returns (response, True) on the first clean reply, or
        (None, False) once nothing is left to flatten or the cap is hit."""
        MAX_FLATTEN = 4
        for _ in range(MAX_FLATTEN):
            if not self._flatten_recent_toolcalls():
                break
            api_messages = build_api_messages(  # V61.14a
                self.system_prompt, self.messages,
                int(self.client.options.get("num_ctx", 0) or 0))
            resp = await self.client.chat(
                messages=api_messages,
                tools=self.tool_schemas if self.tools else None
            )
            if not (resp.content and resp.content.startswith("⚠️")):
                return resp, True
        return None, False

    # --- V21.1 lesson grounding validation --------------------------------
    # Install advice may appear in a lesson ONLY if it occurred in the run.
    _INSTALL_PHRASES = ("pip install", "pip3 install", "apt-get install",
                        "apt install", "conda install", "npm install",
                        "brew install", "ollama pull")
    # Commands the agent can NEVER run (BashTool.FORBIDDEN territory):
    # advice naming them is unusable, so it must be evidenced or rejected.
    _SUSPECT_TOKEN_RE = re.compile(
        r'\b(sudo|apt-get|apt|yum|dnf|chmod|chown|systemctl|powershell|regedit)\b',
        re.IGNORECASE)
    # V61.12: a lesson may not prescribe an operation this sandbox REFUSES.
    _BLOCKED_WRITE_RE = re.compile(
        r"\b(?:file_write|os\.remove|os\.unlink|os\.rename"
        r"|shutil\.(?:move|copy))\b|\bdel\s+\S+\.py\b", re.IGNORECASE)
    _SUBSTITUTION_RE = re.compile(
        r"\binstead\b|\brather than\b|\bin place of\b"
        r"|don'?t use str_replace|avoid str_replace|stop using str_replace",
        re.IGNORECASE)
    _WINDOWS_IMPOSSIBLE_RE = re.compile(
        r'(\b(?:sudo|apt-get|apt|yum|dnf|chmod|chown|systemctl)\b|/home/|/tmp/|\bpython3\b)',
        re.IGNORECASE)
    _UNIX_IMPOSSIBLE_RE = re.compile(
        r'(\b(?:powershell|regedit|findstr)\b|C:\\|%APPDATA%)',
        re.IGNORECASE)

    def _reflection_grounding_error(self, lesson: str, evidence: str,
                                    floor_only: bool = False) -> str:
        """
        V21.1: return "" if the lesson is grounded in the evidence and valid
        on this platform, else a rejection reason. This is the gate that
        stopped 'sudo apt-get' advice from being stored for a Windows run
        whose evidence contained no install command at all.

        V24: floor_only=True (semantic /confidence mode) keeps only the hard
        floor - platform-impossible and agent-forbidden commands - and skips
        the lexical install-phrase check, whose "phrase must appear in
        evidence" rule made every preventive install lesson unstorable.
        In semantic mode that check is replaced by the LLM causality judge.
        """
        low = (lesson or "").lower()
        ev_low = (evidence or "").lower()

        # V61.12: a lesson that prescribes an operation THIS SANDBOX REFUSES is
        # not weakly grounded, it is a trap being written into memory. The
        # horror_snake run of 2026-07-31 stored, at confidence 0.85 and with
        # the LLM auditor answering "supported": "When Python files exceed
        # ~1000 lines str_replace becomes unreliable due to string matching
        # failures; use file_write or targeted line-based editing instead."
        # file_write CANNOT overwrite an existing file - a hard guard in this
        # machine - so that lesson instructs the next run to walk straight into
        # the rewrite-the-whole-file spiral V30.7 exists to break, which this
        # run had already done (patch_test.py, fix_file.py).
        # The causal claim is refuted by the very evidence the auditor was
        # shown: str_replace SUCCEEDED eight times at the same 1029-1057 lines
        # it is accused of failing at. Correlation read as causation, and the
        # auditor's own instruction was "judge causality, not vocabulary".
        # Deterministic, no LLM.
        if self._BLOCKED_WRITE_RE.search(low) and self._SUBSTITUTION_RE.search(low):
            return ("prescribes a blocked operation as a substitute for "
                    "str_replace - file_write cannot overwrite an existing "
                    "file, and del/os.remove/rename are refused by this "
                    "sandbox, so storing this would teach the next run to "
                    "repeat the spiral")

        imp_re = (self._WINDOWS_IMPOSSIBLE_RE if sys.platform == "win32"
                  else self._UNIX_IMPOSSIBLE_RE)
        # V38.1: check EVERY impossible-token match (not just the first) and
        # keep a token that is WARNED AGAINST in its clause ('use python NOT
        # python3', 'avoid sudo') - reject only an unnegated, unevidenced one.
        # Fixes both the false-reject of correct preventive lessons and the
        # latent hole where 'avoid python3 but run sudo' passed on the first
        # match. Same lexical class as the _is_test_pass fix above.
        for m in imp_re.finditer(lesson):
            tok = m.group(0)
            if tok.lower() in ev_low:
                continue
            if self._phrase_negated_in_clause(lesson, m.start(), m.end()):
                continue
            return (f"mentions '{tok}', which is invalid on this "
                    f"platform and never occurred in the run")

        if not floor_only:
            for phrase in self._INSTALL_PHRASES:
                if phrase in low and phrase not in ev_low:
                    return (f"recommends '{phrase}' but no such command appears "
                            f"in the evidence")

        for m in self._SUSPECT_TOKEN_RE.finditer(lesson):
            tok = m.group(0)
            if tok.lower() in ev_low:
                continue
            if self._phrase_negated_in_clause(lesson, m.start(), m.end()):
                continue
            return (f"mentions '{tok}', which this agent cannot run "
                    f"and which never occurred in the run")
        return ""

    @staticmethod
    def _parse_reflection_json(raw: str) -> dict:
        """V21.1: extract the outermost JSON object from a model reply
        (tolerates thinking tags and markdown fences). {} on failure."""
        text = re.sub(r'<think>.*?</think>', '', raw or '', flags=re.DOTALL)
        text = re.sub(r'```(?:json)?', '', text).strip()
        start, end = text.find('{'), text.rfind('}')
        if start == -1 or end <= start:
            return {}
        try:
            obj = json.loads(text[start:end + 1])
            return obj if isinstance(obj, dict) else {}
        except Exception:
            return {}

    async def _judge_lesson_grounding(self, task: str, evidence: str,
                                      lesson: str) -> tuple:
        """
        V24: semantic grounding judge (/confidence on). Replaces the lexical
        install-phrase check with an LLM pass that audits CAUSALITY: does
        the evidence actually support the lesson? Unlike substring matching
        this accepts preventive lessons (advice about what the run
        correctly avoided) and can reject a lesson built from real
        in-evidence tokens stitched into a wrong causal story - the two
        blind spots of the V21.1 gate.

        Returns (supported: bool, reason: str). A judge reply that cannot
        be parsed counts as SUPPORTED - the regex hard floor has already
        passed, and a flaky judge must not destroy a valid semantic lesson.
        """
        judge_prompt = f"""You are auditing one lesson written by a coding agent, against the evidence of what actually happened in its run.

Task: {task[:1000000]}

EVIDENCE (what actually happened):
{evidence}

PROPOSED LESSON:
{lesson}

Is the lesson SUPPORTED by the evidence? Judge causality, not vocabulary:
- SUPPORTED if the events in the evidence make the lesson true and useful -
  including preventive advice about approaches the run deliberately and
  successfully avoided.
- UNSUPPORTED if it claims commands, packages, causes, fixes, or outcomes
  the evidence does not show, or draws a causal story the evidence
  contradicts.

Reply with ONLY a JSON object, no other text:
{{"supported": true, "reason": "..."}}"""
        response = await self.judge_client.chat(
            messages=[{"role": "user", "content": judge_prompt}],
            tools=None  # No tools for judging
        )
        parsed = self._parse_reflection_json(response.content or "")
        if not parsed or "supported" not in parsed:
            debug_print("Grounding judge reply unparseable - counting as supported")
            return True, ""
        supported = parsed.get("supported")
        if isinstance(supported, str):
            supported = supported.strip().lower() in ("true", "yes", "1")
        reason = str(parsed.get("reason", ""))[:32000]
        return bool(supported), reason

    @staticmethod
    def _fallback_reflection(failure_class: str, primary_error: str,
                             fix_note: str, verify_note: str, outcome: str) -> dict:
        """
        V21.1: deterministic, evidence-only reflection used when the model
        cannot produce a grounded one. A mechanical true lesson beats a
        fluent invented one. (V24: grounded=True by construction - every
        field is copied from the evidence.)
        """
        if primary_error:
            lesson = f"[{failure_class}] {primary_error}"
            if fix_note:
                lesson += f" - fixed by: {fix_note}"
            if verify_note:
                lesson += f"; verified: {verify_note}"
        else:
            lesson = f"Completed with outcome '{outcome}'"
            if verify_note:
                lesson += f"; verified: {verify_note}"
        return {
            "failure_class": failure_class,
            "root_cause": primary_error[:5000],
            "fix": fix_note[:5000],
            "verification": verify_note[:5000],
            "lesson": lesson[:5000],
            "confidence": 0.3,
            "grounded": True,
        }

    async def _generate_reflection(self, task: str, outcome: str) -> dict:
        """
        V21.1: evidence-based reflection (rewritten per the V21 review).

        1. Evidence is assembled from what actually ran: real error lines,
           the patches applied, and the output that proved success.
        2. The primary failure is classified deterministically in code
           BEFORE the model is asked anything.
        3. The prompt carries the evidence plus explicit platform rules and
           demands JSON (root_cause / fix / verification / lesson /
           confidence) traceable to that evidence. The V21 prompt's loaded
           pip/pygame example - which the model copied whenever evidence was
           thin - is gone.
        4. The lesson is validated for grounding. One corrective retry, then
           a deterministic evidence-only fallback. A hallucinated lesson can
           no longer reach the episode store.

        V24 (/confidence on, the default): semantic mode.
        - The model picks failure_class from the taxonomy; the code regex
          result is offered as a suggestion instead of a mandate (invalid
          picks fall back to the code class).
        - Grounding = hard regex floor (platform-impossible / forbidden
          commands, both modes, always) + LLM causality judge instead of
          the lexical install-phrase check.
        - A lesson the judge still rejects after the corrective retry is
          stored ANNOTATED (grounded=False, confidence capped at 0.25)
          rather than replaced by the template - fallback fires only when
          no valid lesson JSON exists at all.
        /confidence off restores the exact V23 mechanical path.

        Returns dict: failure_class, root_cause, fix, verification, lesson,
        confidence, grounded.
        """
        # ---- 1. assemble evidence from the WHOLE run ----
        # V22.1: no more 12-step tail window. (The temple_dash run had 49
        # steps; the tail meant the reflection never saw the run's true
        # first failure - a SyntaxError at step 2 - or its dominant
        # failure mode, four cp1252 UnicodeEncodeErrors. It classified
        # the run off a late str_replace miss instead.) Failures ARE the
        # story of a run: include every failure (capped), the repair that
        # followed each, and the final steps.
        MAX_FAILURES_SHOWN = 50
        TAIL_STEPS = 20
        traj = list(self.trajectory)
        n_steps = len(traj)
        picked = {}  # step index -> evidence line
        primary_error = ""
        primary_class = "none"
        primary_args = ""
        fix_note = ""
        verify_note = ""
        verify_pinned = False
        failures_total = 0
        prev_failed = False
        for i, t in enumerate(traj):
            name, args_summary, ok = t[0], t[1], t[2]
            note = t[3] if len(t) > 3 else ""
            if ok:
                # V25: suppression notices are not evidence - they leaked
                # into verify_note/fix_note ("verification: DUPLICATE
                # SUPPRESSED (...)") when they were the last unpinned note.
                if note.startswith("DUPLICATE SUPPRESSED"):
                    note = ""
                if name == "bash" and note:
                    # V23: pin the actual test proof - mario_snake stored the
                    # imports probe as verification merely because it was the
                    # LAST bash; SELF-TEST OK one step earlier was the real one.
                    if "SELF-TEST OK" in note or "TESTS PASSED" in note:
                        verify_note = note
                        verify_pinned = True
                    elif not verify_pinned:
                        verify_note = note
                if prev_failed and note and name in ("str_replace", "file_write"):
                    if not fix_note:
                        fix_note = note  # first repair after the first failure
                    if failures_total <= MAX_FAILURES_SHOWN:
                        picked.setdefault(i, f"- step {i + 1} {name}: OK ({note})  [repair]")
                prev_failed = False
            else:
                failures_total += 1
                prev_failed = True
                if failures_total <= MAX_FAILURES_SHOWN:
                    picked.setdefault(
                        i, f"- step {i + 1} {name}: FAILED ({note})" if note
                        else f"- step {i + 1} {name}: FAILED")
                if not primary_error and note:
                    primary_error = note
                    primary_args = args_summary
        # Always show how the run ended
        for i in range(max(0, n_steps - TAIL_STEPS), n_steps):
            name, ok = traj[i][0], traj[i][2]
            note = traj[i][3] if len(traj[i]) > 3 else ""
            if ok:
                line = f"- step {i + 1} {name}: OK" + (f" ({note})" if note else "")
            else:
                line = (f"- step {i + 1} {name}: FAILED ({note})" if note
                        else f"- step {i + 1} {name}: FAILED")
            picked.setdefault(i, line)
        if primary_error:
            primary_class = self._classify_failure(primary_error, "", primary_args)
        elif failures_total:
            primary_class = "unknown"
        # V38.1: if a transport/template 500 terminated the run, it is the
        # dominant fact - attribute the lesson to the protocol error instead
        # of whatever task step happened to fail first (which is why the
        # blocked-bash run was misread as a shell-syntax fault). Feeds both
        # the semantic suggested-class and the deterministic fallback.
        if getattr(self, "_terminal_protocol_note", ""):
            primary_error = self._terminal_protocol_note
            primary_args = ""
            primary_class = "protocol_error"
        header = f"(run summary: {n_steps} tool steps, {failures_total} failed)"
        if failures_total > MAX_FAILURES_SHOWN:
            header += f" - showing the first {MAX_FAILURES_SHOWN} failures plus the final steps"
        evidence = header + "\n" + "\n".join(picked[i] for i in sorted(picked))

        os_name = "Windows" if sys.platform == "win32" else "Linux/Mac"

        # V24: /confidence toggles between semantic and mechanical prompts.
        semantic = getattr(self, "confidence_enabled", True)
        if semantic:
            class_line = f"Failure class suggested by code analysis: {primary_class}"
            schema_line = ('{"failure_class": "...", "root_cause": "...", "fix": "...", '
                           '"verification": "...", "lesson": "...", "confidence": 0.0}')
            class_rule = ("- failure_class: one of "
                          + ", ".join(self.FAILURE_CLASSES)
                          + ", none, unknown. Keep the suggestion unless the\n"
                            "  EVIDENCE clearly shows a different class.\n")
            mention_rule = ("- Never mention a command, package, tool, or file that the "
                            "EVIDENCE or\n  the Task does not support.")
            install_rule = ("- Installation advice must be tied to what the run showed: "
                            "either an\n  install command that ran, or a documented pivot "
                            "away from one.")
        else:
            class_line = (f"Failure class (already determined from evidence - "
                          f"do not change it): {primary_class}")
            schema_line = ('{"root_cause": "...", "fix": "...", "verification": "...", '
                           '"lesson": "...", "confidence": 0.0}')
            class_rule = ""
            mention_rule = ("- Never mention a command, package, tool, or file that does "
                            "not appear in the\n  EVIDENCE or the Task.")
            install_rule = ("- Never give installation advice unless an install command "
                            "appears in the\n  EVIDENCE.")

        reflection_prompt = f"""A coding agent just finished a task. Produce its learning record.

Task: {task[:1000000]}
Outcome: {outcome}
Operating system: {os_name}
{class_line}

EVIDENCE (what actually happened across the run):
{evidence}

PLATFORM RULES:
{get_platform_rules()}

Reply with ONLY a JSON object, no other text:
{schema_line}

Field rules:
{class_rule}- root_cause: the underlying reason for the primary failure, taken from the
  EVIDENCE error lines. If nothing failed, use "".
- fix: what change repaired it, taken from the EVIDENCE. If nothing failed, "".
- verification: how success was proven (the command/output in the EVIDENCE).
- lesson: 1-2 sentences - the single most valuable lesson for a FUTURE run on
  THIS machine, concrete and traceable to the EVIDENCE above.
- confidence: 0.0-1.0, how certain you are the lesson is correct and useful.

HARD CONSTRAINTS:
{mention_rule}
{install_rule}
- Never write generic engineering advice ("test components separately").
- An evidence line marked [SANDBOX POLICY ...] is a rule of THIS AGENT, not
  a property of the operating system. Never turn one into a platform lesson
  ("on Windows, avoid X"). Say that this sandbox refuses it and name the
  substitute the tool message gave you.
- If the evidence is thin, state only what the evidence shows - do not invent."""

        meta = None
        last_error = ""
        for attempt in range(2):
            prompt = reflection_prompt if attempt == 0 else (
                reflection_prompt
                + f"\n\nYour previous reply was REJECTED because it {last_error}. "
                  "Base every field strictly on the EVIDENCE section.")
            response = await self.judge_client.chat(
                messages=[{"role": "user", "content": prompt}],
                tools=None  # No tools for reflection
            )
            parsed = self._parse_reflection_json(response.content or "")
            lesson = str(parsed.get("lesson", "")).strip() if parsed else ""
            if not lesson:
                last_error = "was not the required JSON object with a non-empty 'lesson'"
                continue
            # V24: in semantic mode only the hard floor applies here
            # (platform-impossible / forbidden commands); the install-phrase
            # check is handed to the causality judge below.
            grounding_error = self._reflection_grounding_error(
                lesson, evidence + "\n" + task, floor_only=semantic)
            if grounding_error:
                last_error = grounding_error
                debug_print(f"Reflection attempt {attempt + 1} rejected: {grounding_error}")
                self._notify(f"REFLECTION attempt {attempt + 1} rejected "
                             f"({grounding_error}) - regenerating")
                continue
            # V24: LLM causality judge (semantic mode). First rejection
            # feeds the corrective retry; a second rejection ANNOTATES the
            # lesson instead of discarding it for the template.
            judged_ok, judge_reason = True, ""
            if semantic:
                judged_ok, judge_reason = await self._judge_lesson_grounding(
                    task, evidence, lesson)
            if not judged_ok and attempt == 0:
                last_error = (f"is not supported by the EVIDENCE"
                              + (f" ({judge_reason})" if judge_reason else ""))
                debug_print(f"Reflection attempt 1 judged ungrounded: {judge_reason}")
                continue
            try:
                confidence = max(0.0, min(1.0, float(parsed.get("confidence", 0.25))))
            except (TypeError, ValueError):
                confidence = 0.25
            # V24: semantic mode lets the model pick the class; membership
            # in the taxonomy is the structural guard, code's class is the
            # fallback for invalid picks.
            picked_class = primary_class
            if semantic:
                model_class = str(parsed.get("failure_class", "")).strip().lower()
                if model_class in self.FAILURE_CLASSES or model_class in ("none", "unknown"):
                    picked_class = model_class
            grounded = True
            if not judged_ok:
                grounded = False
                confidence = min(confidence, 0.25)
                debug_print(f"Storing lesson ANNOTATED grounded=False: {judge_reason}")
                self._notify("LESSON stored but flagged UNGROUNDED - the "
                             "judge could not tie it to evidence")
            meta = {
                "failure_class": picked_class,
                "root_cause": str(parsed.get("root_cause", ""))[:5000],
                "fix": str(parsed.get("fix", ""))[:5000],
                "verification": str(parsed.get("verification", ""))[:5000],
                "lesson": lesson[:5000],
                "confidence": confidence,
                "grounded": grounded,
            }
            break

        if meta is None:
            debug_print(f"Reflection rejected twice ({last_error}); using evidence-only fallback")
            self._notify("REFLECTION rejected twice - falling back to an "
                         "evidence-only lesson")
            meta = self._fallback_reflection(
                primary_class, primary_error, fix_note, verify_note, outcome)

        # Keep code-derived fix/verification when the model left them blank
        if not meta.get("fix") and fix_note:
            meta["fix"] = fix_note[:5000]
        if not meta.get("verification") and verify_note:
            meta["verification"] = verify_note[:5000]
        # V30.2: a verification claim needs a verifying event. In the
        # snake_game run every bash failed, verify_note was empty, and the
        # reflection LLM WROTE "the final python run completed without
        # errors" anyway - and the grounding judge passed it (0.85,
        # grounded=True). Mechanical truth override: if zero commands
        # succeeded in the whole run, no wording gets to claim verification.
        if not any(t[0] == "bash" and t[2] for t in self.trajectory):
            if any(t[0] in ("file_write", "str_replace") and t[2] for t in self.trajectory):
                meta["verification"] = ("NONE - zero successful commands in this run; "
                                        "the final file state was never verified")
                meta["confidence"] = min(meta.get("confidence", 0.25), 0.5)
        return meta
    
    def _filter_candidates_by_quality(self, candidates: list) -> list:
        """
        V24 (/confidence on): drop episodes the reflection system itself
        flagged - grounded=False (judge could not tie lesson to evidence)
        or recorded confidence below 0.7. Confidence 0.0 means 'never
        recorded' (pre-V21.1 episodes and legacy stores) and passes, so
        old episodes.jsonl files keep injecting exactly as before.
        In mechanical mode (/confidence off) this is a no-op.
        """
        if not getattr(self, "confidence_enabled", True) or not candidates:
            return candidates
        kept = [(score, ep) for score, ep in candidates
                if getattr(ep, "grounded", True)
                and not (0.0 < getattr(ep, "confidence", 0.0) < 0.7)]
        if len(kept) != len(candidates):
            debug_print(f"Quality filter dropped {len(candidates) - len(kept)} "
                        f"episode(s) (ungrounded or confidence < 0.7)")
        return kept

    async def _validate_lessons(self, task: str, candidates: list[tuple[float, Episode]]) -> list[Episode]:
        """
        Use LLM to validate which candidate episodes are actually relevant.
        
        This is the 'smart filter' - embeddings find similar, LLM confirms relevant.
        """
        if not candidates:
            return []
        
        # Build validation prompt
        candidate_list = "\n".join([
            f"{i+1}. Task: \"{ep.task[:32000]}\" → Lesson: \"{ep.reflection[:32000]}\" (similarity: {score:.2f})"
            for i, (score, ep) in enumerate(candidates[:50])
        ])
        
        validation_prompt = f"""Current task: "{task[:1000000]}"

Found these past episodes that MIGHT be relevant:
{candidate_list}

Which episodes have lessons that would actually help with the current task?
Consider: Is the workflow pattern transferable? Is it about similar tools/problems?

Reply with ONLY the numbers of relevant episodes (e.g., "1, 3") or "none" if none are relevant.
Do not explain - just the numbers or "none"."""

        response = await self.judge_client.chat(
            messages=[{"role": "user", "content": validation_prompt}],
            tools=None
        )
        
        # Parse response
        content = response.content or ""
        content = re.sub(r'<think>.*?</think>', '', content, flags=re.DOTALL).strip().lower()
        
        # V25: whole-number parse, range-checked against the list actually
        # shown. The old substring test made "1" match "10", and any mention
        # of the word "none" discarded every selection. No numbers = none.
        nums = {int(n) for n in re.findall(r'\d+', content)}
        
        valid_episodes = [ep for i, (score, ep) in enumerate(candidates[:50])
                          if (i + 1) in nums]
        
        return valid_episodes
    
    async def _coverage_message(self, command: str):
        """System-message text if `command`'s --test left functions unrun.

        Returns None when there is nothing to say (no .py named, no --test,
        probe unusable, or full coverage). NEVER raises - a probe that cannot
        run must not take the agent down with it.

        Records the probe result on self._last_coverage. READ THAT FIELD AS A
        DEBUG SNAPSHOT ONLY - it is NOT wired into the completion gates, and
        the earlier version of this docstring claiming otherwise was wrong.
        Wiring it there as-is would be a bug, not a feature: the caller is
        guarded by `test_pass_surfaced`, which fires ONCE PER RUN, so this
        method runs exactly once and the snapshot is never refreshed. A model
        that OBEYS the message below - extends --test, calls the untouched
        functions, re-runs - would still be holding the pre-fix numbers at
        completion time and would be bounced for a defect it already fixed.
        Accusing from stale state is the failure this machine exists to
        prevent, so a real completion-path gate has to RE-PROBE at that
        moment rather than read this.
        """
        self._last_coverage = None
        try:
            wd = _tools_working_dir(getattr(self, "tools", None))
            for base in sorted(_scripts_named_in(command or "")):
                if not base.lower().endswith(".py"):
                    continue
                cov = await asyncio.to_thread(
                    test_coverage_probe, os.path.join(wd, base), wd)
                if not cov:
                    continue
                self._last_coverage = cov
                debug_print(f"COVERAGE PROBE {base}: {cov['executed']}/"
                            f"{cov['defined']} functions ran, "
                            f"{len(cov['never'])} never executed"
                            + ("" if cov.get("headless", True)
                               else " (headless retry was needed)"))
                # V61.13: THE INSTRUMENT MUST NOT REPORT A MEASUREMENT IT
                # COULD NOT TAKE. A non-zero exit here means the PROBE's run
                # died partway - and test_coverage_probe has already retried
                # without the headless drivers, so this is not our env. The
                # never-executed list is therefore truncated at the crash
                # point, not a coverage finding: every function below it is
                # named as untested when it may run perfectly in the model's
                # own environment, which by construction it just did (this
                # method is only reached from the _is_test_pass branch, i.e.
                # the model's own `--test` exited 0 with a canonical pass
                # phrase moments ago).
                # ABSTAIN, do not accuse. Deliberately silent to the model
                # rather than "your test crashed under my tracer": V61.9's
                # rule is that every warning must be ACTIONABLE, and the
                # model cannot fix this machine's probe. A warning it cannot
                # satisfy teaches it that the whole channel is noise, which
                # is exactly how the real swallower at line 1754 got ignored
                # for six edits. The discrepancy is real and worth seeing, so
                # it goes to the debug channel and to _last_coverage, where
                # it costs the run nothing and lies to no one.
                if cov.get("exit"):
                    debug_print(
                        f"COVERAGE PROBE {base}: ABSTAINING - the probe's own "
                        f"run exited {cov['exit']}"
                        + (f" ({cov['error']})" if cov.get("error") else "")
                        + f", after a non-headless retry, so its "
                        f"{len(cov['never'])} never-executed name(s) are "
                        f"truncated at the crash and are NOT a finding. The "
                        f"model's own run of this same --test passed.")
                    continue
                # V61.19: skipped assertions are reported here too, at the
                # FIRST passing self-test rather than only at completion -
                # the earlier the model learns its test body is being cut
                # short, the less work it builds on top of the illusion.
                # This branch is reached even at FULL function coverage,
                # because 21/21 functions can run while 17 of 31 assertions
                # are skipped: that is exactly what the snake_game artifact
                # of 2026-08-01 did.
                skipped = cov.get("asserts_never") or []
                if skipped:
                    tot = cov.get("asserts_total") or len(skipped)
                    lines_txt = "\n".join(
                        f"   line {ln}: {t}" for ln, t in skipped[:8])
                    return (
                        f"\u26d4 YOUR SELF-TEST PASSED WITH {len(skipped)} OF "
                        f"ITS {tot} ASSERTIONS NEVER EXECUTED.\n"
                        f"I traced every line of {base} while your own --test "
                        f"ran. These assertion lines were never reached:\n"
                        + lines_txt
                        + (f"\n   ... and {len(skipped) - 8} more"
                           if len(skipped) > 8 else "")
                        + f"\n\nAn assertion that does not run cannot fail. "
                          f"The features these name are UNTESTED, and the "
                          f"pass message printed anyway - so nothing you can "
                          f"see reports it. Usual causes: an exception "
                          f"handler wrapped around the test body (a game "
                          f"loop's sys.exit() raises SystemExit, so "
                          f"`except SystemExit: pass` there ends the test at "
                          f"the first scenario), an early return, or the pass "
                          f"message printed outside the block meant to guard "
                          f"it. Read those lines, make them execute, and "
                          f"re-run before doing anything else.")
                if not cov["never"]:
                    return None
                names = ", ".join(f"{n}() [line {ln}]"
                                  for n, ln in cov["never"][:12])
                more = ("" if len(cov["never"]) <= 12
                        else f" ... and {len(cov['never']) - 12} more")
                return (
                    f"\u26d4 YOUR TEST PASSED AND PROVED LESS THAN YOU THINK. "
                    f"I re-ran `{base} --test` under a call tracer. Of the "
                    f"{cov['defined']} functions defined in that file, "
                    f"{cov['executed']} executed and {len(cov['never'])} "
                    f"NEVER RAN AT ALL:\n  {names}{more}\n"
                    f"These are not weakly tested, they are untested - their "
                    f"bodies could be replaced with `return` and your suite "
                    f"would still print its ticks and exit 0. If any of them "
                    f"is a feature the task named, your test does not cover "
                    f"the task.\n"
                    f"DO NOT write your final summary yet, and do NOT list any "
                    f"of these under verified features. Extend --test to CALL "
                    f"them with real inputs and ASSERT on what they return or "
                    f"change - values the test did not itself assign a line "
                    f"earlier. For a game loop, drive update() for N frames and "
                    f"assert the state actually moved. Then run --test again."
                )
        except Exception as e:
            debug_print(f"COVERAGE PROBE skipped: {type(e).__name__}: {e}")
        return None

    async def process(self, user_message: str, on_tool_call=None, on_tool_result=None, 
                      on_status=None, on_lessons_found=None, on_lessons_injected=None, 
                      on_episode_saved=None, on_tokens=None) -> str:
        """
        Process user message with optional episode memory integration.
        
        Callbacks:
        - on_lessons_found(candidates): Called when embedding search finds candidates
        - on_lessons_injected(episodes): Called when lessons are actually injected (if enabled)
        - on_episode_saved(episode): Called after episode is saved
        - on_tokens(prompt_tokens, completion_tokens): Called after each Ollama response with REAL token counts
        """
        # Reset trajectory and tokens for this task
        self.trajectory = []
        self.thinking_log = []  # V30.9: per-task reset
        self._terminal_protocol_note = ""  # V38.1: set only if a 500 ends the run
        self.lessons_injected = []
        self.lessons_candidates = []
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        # V25: duplicate-guard must start clean per task (the cross-task
        # leak suppressed real re-runs as "already succeeded").
        self._last_call_sig = None
        self._last_call_ok = False
        self._dup_streak = 0
        self._ok_call_counts = {}  # V30.8: per-task set of successful sigs
        
        # ═══════════════════════════════════════════════════════════════════
        # LESSON SEARCH - Find semantically similar past experiences
        # ═══════════════════════════════════════════════════════════════════
        if self.memory:
            if on_status:
                on_status("Searching memory...")
            
            # Step 1: Embedding search (fast, finds candidates)
            candidates = await self.memory.search(user_message, top_k=50)
            # V24: semantic mode consumes the stored quality signals -
            # before this, confidence and grounded were written and never
            # read. Legacy episodes (confidence 0.0 = unrecorded) pass.
            candidates = self._filter_candidates_by_quality(candidates)
            self.lessons_candidates = candidates
            
            if candidates and on_lessons_found:
                on_lessons_found(candidates)
            
            # Step 2: LLM validation (smart, filters irrelevant)
            if candidates and self.inject_enabled:
                if on_status:
                    on_status("Validating relevance...")
                
                validated = await self._validate_lessons(user_message, candidates)
                
                if validated:
                    self.lessons_injected = validated
                    lessons_text = "LESSONS FROM RELEVANT PAST TASKS:\n"
                    for ep in validated:
                        lessons_text += f"• {ep.reflection}\n"
                    lessons_text += "\nApply these workflow patterns to the current task.\n"
                    
                    # Inject as system context
                    self.messages.append(Message(role="system", content=lessons_text))
                    
                    if on_lessons_injected:
                        on_lessons_injected(validated)
                    debug_print(f"Injected {len(validated)} validated lessons")
        
        # Add user message
        self.messages.append(Message(role="user", content=user_message))
        # V61.2: now that the TASK is known, widen the pin to cover it.
        if self.client is not None:
            self.client.sync_prompt_cache(self.system_prompt, user_message)
        self.iteration_count = 0
        
        # ═══════════════════════════════════════════════════════════════════
        # MAIN AGENT LOOP
        # ═══════════════════════════════════════════════════════════════════
        final_response = None
        outcome = "success"
        empty_streak = 0  # V25: consecutive contentless, tool-less replies
        # V30.2: verification-debt tracking for the one-shot completion gate
        last_py_edit = None       # trajectory step of the latest successful .py edit
        self._test_fail_window_open = False   # V61.2: red window, see _annotate_result
        self._weaken_warned = False           # V61.4: warn once per window
        # V61.5: basename -> (trajectory step, did that run succeed). LAST run
        # wins, so a script that failed and was then fixed does not get flagged.
        self._script_runs = {}
        claims_nudged = False
        stall_recoveries = 0   # V61.29, see MAX_STALL_RECOVERIES
        last_py_edit_path = ""
        # V171 FIX 4: last_py_edit_path is "the file most recently WRITTEN
        # successfully", which is the right semantics for the verification-debt
        # gate and the WRONG one for the two consumers below.
        #
        # In the run of 2026-08-04 the model wrote run_test.py at step 54 - a
        # 19-line wrapper - and its next three str_replace calls, all on
        # mario_game.py, all missed. The spiral breaker then told it:
        #   "STOP - you are in a rewrite-the-whole-file loop on run_test.py ...
        #    Do NOT attempt file_write, del, or os.remove on run_test.py again."
        # It was not editing run_test.py. The one message whose entire job is
        # to name the trap named the wrong file, and told it to stop doing
        # something it was not doing.
        #
        # Two separate slots, because the two questions are different:
        #   last_failed_edit_path - what the model is actually FIGHTING WITH.
        #   edit_counts           - which file is the DELIVERABLE, i.e. the
        #                           one being built, not the one touched last.
        # The second matters beyond the message: the mutation gate mutates
        # os.path.join(wd, last_py_edit_path), so after step 54 it would have
        # planted its forty bugs in the 19-line test wrapper instead of the
        # 2,000-line game.
        last_failed_edit_path = ""
        edit_counts = {}             # path -> successful file_write/str_replace count
        built_deliverables = set()   # V61.28: basenames of every .py/.html
                                     # written or edited successfully
        last_ok_bash = None       # trajectory step of the latest successful bash
        # V178: what the VERIFICATION did, kept apart from what any
        # command did - see the completion gate for why the two are not
        # the same question.
        last_test_pass = None
        last_test_fail = None
        completion_nudged_sig = None
        # V179: the edit the entry-point smoke check last ran against,
        # so it re-runs on a change and stays quiet otherwise.
        smoke_checked_at = None
        completion_nudged = False
        # V61.17 / V61.18: mutation gate. NOT one-shot - see MUTATION_MAX_FIRES.
        mutation_fires = 0
        mutation_prev = None      # the previous measurement, for comparison
        # V171 FIX 5: set when a round bounces and promises a re-measure;
        # cleared when that re-measure happens or the budget is spent.
        mutation_remeasure_due = False
        # V172: what the last round actually measured, and how many edits
        # have landed on the target since. Both are needed before any
        # better/worse claim can honestly be made - see _mutation_progress.
        mutation_last_md5 = None
        mutation_edits_since = 0
        # V30.7: escalating breaker for the miss->overwrite->delete spiral.
        # Counts consecutive failed edits / blocked destructive writes; the
        # nudge gets firmer and names the spiral by name once it repeats.
        stuck_edit_streak = 0
        # V61.9: warnings ride on a ✅, so NOTHING in the reaction chain below
        # can see them - the failed-edit branch needs `not is_success` and the
        # HINT branch needs `not startswith("✅")`. Both miss, and the `else`
        # then RESETS the spiral counter. Measured on the fps_game run of
        # 2026-07-31: "2 silent exception swallower(s) at line(s) 1754, 2809"
        # was emitted on six consecutive successful edits, the model
        # file_read that exact region twice, and never touched it.
        # Keyed on the COUNT, not the line numbers: line numbers shift
        # whenever an edit above adds a line, which would reset a line-based
        # signature and hide the very stall this is here to catch. A count
        # that never falls across repeated edits to one file IS the stall.
        warn_floor = {}     # path -> lowest swallower count seen so far
        warn_streak = {}    # path -> edits since that count last improved
        # V45.8: basenames this run was refused an overwrite on, so that
        # creating a differently-named copy can be recognised as the
        # abandonment it is rather than recorded as "wrote <newfile>".
        refused_overwrites = {}
        # V30.8: fire the self-test-pass awareness surface only once per run.
        test_pass_surfaced = False
        # V38.1: allow ONE mechanical retraction of that surface if a later
        # self-test actually FAILS - a genuinely-passing shallow test no
        # longer leaves a stale 'criterion met' line that contradicting
        # evidence cannot correct.
        test_pass_retracted = False
        
        for iteration in range(self.max_iterations):
            self.iteration_count = iteration + 1
            
            if on_status:
                self._status_cb = on_status
                on_status(f"Iteration {self.iteration_count}/{self.max_iterations}")
            
            api_messages = build_api_messages(  # V61.14a
                self.system_prompt, self.messages,
                int(self.client.options.get("num_ctx", 0) or 0))
            
            debug_print(f"=== Iteration {iteration + 1} ===")
            
            response = await self.client.chat(
                messages=api_messages, 
                tools=self.tool_schemas if self.tools else None
            )
            
            # ═══════════════════════════════════════════════════════════════════
            # REAL TOKEN TRACKING - From Ollama's actual response
            # ═══════════════════════════════════════════════════════════════════
            self.last_prompt_tokens = response.prompt_tokens
            self.last_completion_tokens = response.completion_tokens
            self.total_prompt_tokens += response.prompt_tokens
            self.total_completion_tokens += response.completion_tokens
            
            if on_tokens and response.prompt_tokens > 0:
                on_tokens(response.prompt_tokens, response.completion_tokens)
            
            debug_print(f"Tokens: prompt={response.prompt_tokens}, completion={response.completion_tokens}")
            
            # Check for errors in response
            if response.content and response.content.startswith("⚠️"):
                # V61.29: A STALL IS NOT A VERDICT, IT IS AN OBSERVATION.
                # The old code appended the machine's own error text to
                # history AS AN ASSISTANT TURN and broke. Two defects in
                # four lines: the model's next task opened with a
                # fabricated turn in which it claimed to have timed out,
                # and a recoverable transport event ended the build. Now
                # the partial output goes back as the model's own turn,
                # the MEASUREMENT goes back as a user turn, and the loop
                # continues - bounded, so it cannot become a new hang.
                _stall = (response.raw_response or {}).get("stall") \
                    if isinstance(response.raw_response, dict) else None
                if _stall and stall_recoveries < self.MAX_STALL_RECOVERIES:
                    stall_recoveries += 1
                    probe = await self.client.probe_server()
                    debug_print(f"STALL RECOVERY {stall_recoveries}/"
                                f"{self.MAX_STALL_RECOVERIES}; server probe:",
                                probe)
                    self._notify(
                        f"STALL RECOVERY {stall_recoveries}/"
                        f"{self.MAX_STALL_RECOVERIES}: "
                        + (f"generation looped after "
                           f"{_stall['content_chars']:,} chars"
                           if _stall["kind"] == "degenerate-repetition"
                           else f"generation overran "
                                f"{_stall['elapsed_s']:.0f}s, "
                                f"{_stall['content_chars']:,} chars"
                           if _stall["kind"] == "overrun"
                           else f"model went silent for "
                                f"{_stall['silence_budget_s']:.0f}s after "
                                f"{_stall['content_chars']:,} chars"))
                    self.trajectory.append((
                        "chat", "", False,
                        f"STALL ({_stall['kind']}) after "
                        f"{_stall['elapsed_s']}s, {_stall['chunks']} chunks, "
                        f"{_stall['content_chars']} chars produced"))
                    _partial = (_stall.get("partial_content") or "").strip()
                    if _partial:
                        self.messages.append(Message(
                            role="assistant", content=_partial,
                            thinking=_stall.get("partial_thinking") or ""))
                    if _stall["kind"] == "overrun":
                        _where = (
                            "You did NOT stop - you were still producing text "
                            "when I cut it off. That means you were writing at "
                            "length instead of acting. Whatever you had written "
                            "is above as your own turn. Emit ONE tool call now, "
                            "with no preamble and no restatement of the plan.")
                    elif _stall.get("first_token_s") is None:
                        _where = (
                            "NOT ONE TOKEN ever arrived, so it stopped while "
                            "reading the prompt, not while writing. The "
                            "request itself is the problem, not your "
                            "reasoning. Make your next step ONE small tool "
                            "call - a narrow file_read or a single "
                            "str_replace - and do not restate the plan.")
                    else:
                        _where = (
                            f"Output was flowing (first token at "
                            f"{_stall['first_token_s']}s) and then stopped "
                            f"dead. Whatever you had written is above as your "
                            f"own turn. Do NOT start again from the top: "
                            f"finish the tool call you were building, or "
                            f"state the next single step in as few words as "
                            f"you can.")
                    _loop = (f"\n   I also measured your output going "
                             f"{self.client.STREAM_NOVELTY_STREAK} consecutive "
                             f"{self.client.STREAM_NOVELTY_WINDOW}-character "
                             f"windows with under "
                             f"{self.client.STREAM_NOVELTY_MIN:.0%} new content "
                             f"before the stall - you were restating, not "
                             f"progressing. The phrase you kept coming back to: "
                             f"{_stall['loop_line']!r}. Reasoning about it again "
                             f"cannot break the cycle; write the smallest "
                             f"program that PRINTS the value you are guessing "
                             f"at and run it."
                             if _stall.get("loop_line") else "")
                    _srv = ("reachable" if probe.get("reachable")
                            else f"NOT reachable ({probe.get('error')})")
                    self.messages.append(Message(role="user", content=(
                        f"⚠ YOUR LAST TURN DID NOT FINISH (recovery "
                        f"{stall_recoveries} of {self.MAX_STALL_RECOVERIES}). "
                        f"This is measured, not inferred:\n"
                        f"   - the connection carried {_stall['chunks']} "
                        f"chunk(s) over {_stall['elapsed_s']}s, then "
                        f"{_stall['silence_budget_s']:.0f}s of silence\n"
                        f"   - you had produced {_stall['content_chars']:,} "
                        f"chars of content, "
                        f"{_stall['thinking_chars']:,} of reasoning, "
                        f"{_stall['tool_calls_seen']} tool call(s)\n"
                        f"   - the ollama server is {_srv}\n"
                        f"{_where}{_loop}"
                    )))
                    continue
                # V38.1: an Ollama transport/template 500 is a deterministic
                # rejection of the replayed tool-call history, not a task
                # failure. Repair the history (flatten the offending tool-call
                # turn to prose) and retry before giving up - a blind resend
                # would 500 identically.
                if self._is_protocol_error(response):
                    debug_print("Protocol error detected; attempting history-repair recovery")
                    recovered_resp, ok = await self._recover_protocol_error()
                    if ok:
                        debug_print("Protocol error recovered via tool-call flattening")
                        response = recovered_resp
                        # account for the recovered call's real tokens
                        self.last_prompt_tokens = response.prompt_tokens
                        self.last_completion_tokens = response.completion_tokens
                        self.total_prompt_tokens += response.prompt_tokens
                        self.total_completion_tokens += response.completion_tokens
                        if on_tokens and response.prompt_tokens > 0:
                            on_tokens(response.prompt_tokens, response.completion_tokens)
                        # fall through to normal tool-call / final-answer handling
                    else:
                        note = ("PROTOCOL ERROR: Ollama rejected the replayed "
                                "tool-call history at template-render time "
                                "(transport failure, not a task/command error); "
                                "history repair by flattening prior tool calls "
                                "did not clear it. "
                                + str((response.raw_response or {}).get("error", ""))[:1500])
                        self.trajectory.append(("chat", "", False, note))
                        self._terminal_protocol_note = note
                        self.messages.append(Message(role="assistant", content=response.content))
                        final_response = response.content
                        outcome = "failure"
                        break
                else:
                    # V61.29: a STALL is the machine talking, not the
                    # model. Recording it as an assistant turn put words
                    # in the model's mouth that the next task then read
                    # back as its own. Everything else keeps the old
                    # behaviour.
                    if not _stall:
                        self.messages.append(Message(role="assistant", content=response.content))
                    else:
                        self.trajectory.append((
                            "chat", "", False,
                            f"STALL unrecovered after "
                            f"{self.MAX_STALL_RECOVERIES} attempts "
                            f"({_stall['kind']})"))
                    final_response = response.content
                    outcome = "failure"
                    break
            
            # V61.4: record the model's reasoning channel for this response,
            # keyed to the next step number. Episode-review only - deliberately
            # NOT added to self.messages, so it is never fed back to the model.
            #
            # HOISTED out of `if response.tool_calls:` below. Nested there, this
            # only fired for responses that called a tool, so the FINAL,
            # tool-less response - the one that declares the task done - had its
            # reasoning silently dropped. That is the single most diagnostic
            # response in a run: V30.9 added this channel precisely because the
            # mario_snake run showed the model asserting "the tests are passing"
            # in `thinking` before any evidence existed, and the closing claim is
            # exactly where that shows up.
            #
            # Placed HERE, not earlier in the loop, deliberately: the protocol-
            # error path above can REPLACE `response` with a recovered one, and
            # capturing before that would log the discarded 500's thinking (empty)
            # while missing the real reply's. Every path that reaches this line
            # has a final `response`, and the `break` paths above have already
            # exited, so this runs exactly once per surviving response.
            #
            # Step keying is unchanged from V30.9 (len(trajectory)+1) so existing
            # episodes.jsonl records stay comparable. Consequence: a tool-less
            # response does not grow the trajectory, so consecutive tool-less
            # responses can share a step number. It is a review label, not a key.
            if response.thinking:
                self.thinking_log.append(
                    (len(self.trajectory) + 1, response.thinking[:THINKING_STORE_CHARS])
                )

            if response.tool_calls:
                empty_streak = 0
                # Model wants to use tools
                self.messages.append(Message(
                    role="assistant", 
                    content=response.content or "",
                    tool_calls=response.tool_calls,
                    # V61.14: THIS is the append that matters. Every iteration
                    # of a build loop passes through here, so this is where
                    # the reasoning either survives or is lost. The booby run
                    # made five consecutive edits to one test block from this
                    # branch, re-deriving the same analysis each time because
                    # the previous turn arrived stripped.
                    thinking=response.thinking
                ))
                
                for tc in response.tool_calls:
                    if on_tool_call:
                        on_tool_call(tc.name, tc.arguments)
                    
                    # V22.1: suppress exact repeats of the previous
                    # successful call instead of re-running them.
                    dup_msg = self._duplicate_guard(tc)
                    if dup_msg is not None:
                        result = {"content": dup_msg}
                        is_success = True
                        note = "DUPLICATE SUPPRESSED (identical to previous successful call)"
                    else:
                        result = await self.executor.execute(tc)
                        # V45.8: annotate BEFORE the verdict and the note.
                        self._annotate_result(tc, result, refused_overwrites)
                        is_success = self._detect_tool_success(result["content"], tc.name)
                        # V21.1: capture REAL evidence, not the first output line.
                        # Failures record the actual exception + location + exit
                        # code; successes record what was patched / what output
                        # proved success, so reflections can cite fix and proof.
                        note = self._tool_note(tc.name, tc.arguments, result["content"], is_success)
                        self._remember_call(tc, is_success)
                    # V30.1: 250 was too small (it cut file_write evidence
                    # mid-defect), but V30's 10000 detonates downstream: the
                    # whole trajectory is serialized into every episode
                    # (episodes.jsonl grows ~40x per run and is loaded +
                    # embedded at startup), and primary_args feeds the
                    # reflection prompt. 2000 keeps a whole function of
                    # evidence while staying bounded at both sinks.
                    args_summary = str(tc.arguments)[:TRAJECTORY_ARG_CHARS]
                    # V45.5: the syntax gate fires into the model's message
                    # history; without this the operator never sees it.
                    # V60.2: was three bare substring tests over the whole
                    # payload, so any file quoting this machine's own strings
                    # impersonated its gates. Same text, same messages, same
                    # order - the recogniser is now tool-scoped and anchored.
                    _rc = str(result.get("content", ""))
                    _sig = self._machine_gate_signals(tc.name, _rc, is_success)
                    if "truncated" in _sig:
                        _p = (tc.arguments or {}).get("path", "?")
                        self._notify(f"TRUNCATED WRITE: {_p} - generation was "
                                     f"cut off mid-string")
                    elif "syntax" in _sig:
                        _p = (tc.arguments or {}).get("path", "?")
                        self._notify(f"SYNTAX GATE: {_p} left unparseable by "
                                     f"this {tc.name}")
                    if "stalled" in _sig:
                        self._notify("GATE STALLED: same error 3+ writes in a "
                                     "row - the agent is not fixing it")
                    self.trajectory.append((tc.name, args_summary, is_success, note))
                    # V61.5: remember how the LAST run of each script ended.
                    # V180: ONLY IF IT ACTUALLY RAN. A command the sandbox
                    # refused never touched the script it names, so recording
                    # it as a failed run is a lie about the artifact.
                    #
                    # Measured, snake run of 2026-08-06 04:53 - the best run
                    # in this series and it was still marked partial:
                    #   msg 81  python snake_game.py --test    -> exit 0, PASS
                    #   msg 83  timeout 3 python snake_game.py -> BLOCKED
                    #           ('timeout' is not in the allowlist)
                    # The blocked command names snake_game.py, so the ledger
                    # overwrote a genuine pass with a failure for a run that
                    # never happened, and outcome check (a3) downgraded
                    # success -> partial on it. The self-test passed, the
                    # entry smoke passed, the mutation gate passed at 50% -
                    # and the episode says partial.
                    #
                    # Same class as the V61.7 duplicate-suppression fix
                    # (`executed = dup_msg is None`): the ledger must record
                    # what RAN, and a suppressed duplicate and a refused
                    # command are both "did not run". That fix covered one of
                    # the two; this covers the rest.
                    if tc.name == "bash" and _command_executed(
                            str(result.get("content", ""))):
                        try:
                            _cmd = str((tc.arguments or {}).get("command", ""))
                            for _b in _scripts_named_in(_cmd):
                                self._script_runs[_b] = (len(self.trajectory),
                                                         bool(is_success))
                        except Exception as e:
                            debug_print(f"script-run bookkeeping failed: {e}")
                    elif tc.name == "bash":
                        debug_print(
                            "SCRIPT LEDGER: not recorded - the command did "
                            "not execute, so it says nothing about the "
                            "script it names")
                    # V61.2: the red window (V45.11 shape, ported). It opens on
                    # a bash result that is a recognised test FAILURE and stays
                    # open until one actually PASSES - not until the next
                    # successful command of any kind, which is what made the
                    # V45.8 adjacent-step gate blind one step after a failure.
                    if tc.name == "bash":
                        _rcw = str(result.get("content", ""))
                        # V171 FIX 1: the command is evidence of testhood -
                        # `python game.py --test` exiting nonzero is a test
                        # failure even when the output never says the word.
                        _cmdw = str((tc.arguments or {}).get("command", ""))
                        if self._is_test_fail(_rcw, _cmdw):
                            if not getattr(self, "_test_fail_window_open", False):
                                self._test_fail_window_open = True
                                # a NEW failing test earns a fresh warning
                                self._weaken_warned = False
                                self._notify("TEST FAILURE WINDOW OPEN - edits to "
                                             "assertions will be checked until a "
                                             "test actually passes")
                        elif self._is_test_pass(_rcw):
                            if getattr(self, "_test_fail_window_open", False):
                                self._test_fail_window_open = False
                                self._notify("TEST FAILURE WINDOW CLOSED - a test "
                                             "passed")
                            # V171 FIX 5: a green self-test is the moment the
                            # bounced round promised to re-measure at. Waiting
                            # for the next COMPLETION ATTEMPT meant that on
                            # 2026-08-04 the promise was never kept: bounced at
                            # 8%, 29 more steps of work, no second attempt to
                            # finish, one round fired out of a budget of three,
                            # and the rewrite that made the test worse was
                            # never compared against anything.
                            if (mutation_remeasure_due
                                    and mutation_fires < MUTATION_MAX_FIRES
                                    and last_py_edit_path):
                                mutation_remeasure_due = False
                                mutation_fires += 1
                                _mt = last_py_edit_path
                                if edit_counts:
                                    _b = max(edit_counts.items(),
                                             key=lambda kv: (kv[1], kv[0]))
                                    if _b[1] > edit_counts.get(last_py_edit_path, 0):
                                        _mt = _b[0]
                                _wd = _tools_working_dir(getattr(self, "tools", None))
                                # V172: same no-change skip as the completion
                                # site. Fix 5 made this trigger more often,
                                # which without the hash check would mean MORE
                                # measurements of an unchanged file, not fewer.
                                _skip = False
                                try:
                                    _p2 = os.path.join(_wd, _mt)
                                    if mutation_last_md5 and os.path.exists(_p2):
                                        _skip = (hashlib.md5(
                                            open(_p2, "rb").read()).hexdigest()
                                            == mutation_last_md5
                                            and mutation_edits_since == 0)
                                except Exception as e:
                                    debug_print(f"MUTATION GATE: hash check "
                                                f"failed ({e})")
                                if _skip:
                                    mutation_fires -= 1
                                    mutation_remeasure_due = True
                                    self._notify(
                                        f"MUTATION GATE: re-measure skipped - "
                                        f"{_mt} unchanged since my last check")
                                    _mut = None
                                else:
                                    _mut = await asyncio.to_thread(
                                        run_mutation_gate, os.path.join(_wd, _mt),
                                        _wd, MUTATION_MAX_MUTANTS, 60, 180,
                                        mutation_fires)
                                try:
                                    _hist = self._mutation_history
                                except AttributeError:
                                    _hist = self._mutation_history = []
                                if _mut:
                                    _hist.append({
                                        "round": mutation_fires,
                                        "trigger": "test-pass",
                                        "flaky": bool(_mut.get("flaky")),
                                        "killed": _mut.get("killed"),
                                        "tested": _mut.get("tested"),
                                        "rate": round(_mut.get("rate") or 0.0, 4),
                                        "survivors": len(_mut.get("survivors") or []),
                                        "asserts_never": len(_mut.get("asserts_never") or []),
                                        "file": _mt,
                                    })
                                    debug_print(f"MUTATION RECORD round "
                                                f"{mutation_fires} (test-pass): "
                                                + json.dumps(_hist[-1]))
                                _n, _t, _last = mutation_round_message(
                                    _mut, _mt, mutation_prev, mutation_fires,
                                    mutation_edits_since)
                                if _mut and _mut.get("file_md5"):
                                    mutation_last_md5 = _mut["file_md5"]
                                    mutation_edits_since = 0
                                if _mut and not _mut.get("unrunnable") \
                                        and not _mut.get("flaky") \
                                        and _mutation_scored(_mut)[0] \
                                            < MUTATION_MIN_KILL_RATE:
                                    mutation_prev = _mut
                                if _t:
                                    self._notify(_n)
                                    self.messages.append(
                                        Message(role="user", content=_t))
                                    if _last:
                                        mutation_fires = MUTATION_MAX_FIRES
                                    else:
                                        mutation_remeasure_due = True
                                elif _mut:
                                    self._notify(
                                        f"MUTATION GATE: {_mt} caught "
                                        f"{_mut['killed']}/{_mut['tested']} "
                                        f"({_mut['rate']:.0%}) - passed on "
                                        f"re-measure")
                    # V30.2: verification-debt bookkeeping for the completion
                    # gate - which came later, the last .py edit or the last
                    # successful command?
                    step_no = len(self.trajectory)
                    # V171 FIX 4: remember WHICH file an edit failed on. The
                    # spiral breaker below used to borrow last_py_edit_path,
                    # which is a different question and gave a different file.
                    if (not is_success) and tc.name in ("file_write", "str_replace"):
                        _fp = str((tc.arguments or {}).get("path", ""))
                        if _fp:
                            last_failed_edit_path = _fp
                    if is_success and tc.name in ("file_write", "str_replace"):
                        p = str(tc.arguments.get("path", ""))
                        # V45.7: the gate's principle is "you edited a
                        # file and never ran anything after it" - that was
                        # never about Python. An .html build that quits
                        # mid-way used to sail straight through.
                        if p.lower().endswith(VERIFIABLE_EXT):
                            last_py_edit = step_no
                            last_py_edit_path = p
                            # V171 FIX 4: the file being BUILT is the one that
                            # keeps getting edited, not the one edited most
                            # recently. 30+ edits to mario_game.py against one
                            # write of run_test.py is not a close call.
                            edit_counts[p] = edit_counts.get(p, 0) + 1
                            # V172: edits since the last mutation measurement.
                            mutation_edits_since += 1
                            # V61.28: EVERY deliverable, not just the newest.
                            # last_py_edit_path is a single slot, so a run
                            # that produces two files only ever guards one.
                            built_deliverables.add(
                                re.split(r"[\\/]", p)[-1] or p)
                    if is_success and tc.name == "bash":
                        last_ok_bash = step_no
                    # V178: "did anything succeed" is not "was it verified".
                    # The completion gate below asked the first question and
                    # let a throwaway diagnostic answer it. On the snake run
                    # of 2026-08-06 03:20 the last edit was step N, then
                    # `python snake_game.py --test` FAILED, then two
                    # `python -c` probes exited 0 - which set last_ok_bash
                    # past the edit and disarmed the gate completely. The run
                    # finished at iteration 111 with a red self-test and a
                    # game that will not start. These two record what the
                    # VERIFICATION did, separately from what any command did.
                    if tc.name == "bash":
                        _bc = str(result.get("content", ""))
                        _bcmd = str((tc.arguments or {}).get("command", ""))
                        if self._is_test_pass(_bc):
                            last_test_pass = step_no
                        elif self._is_test_fail(_bc, _bcmd):
                            last_test_fail = step_no
                    # V30.8a: self-result-awareness, now OUTSIDE the
                    # is_success gate. ROOT CAUSE of the mario_snake surface
                    # miss (found by execution): the model's --test printed
                    # 'ALL TESTS PASSED! ✓' and exited 0, but earlier
                    # subtests had thrown a struct.error whose traceback sat
                    # in the STDERR section - and _detect_tool_success
                    # returns is_success=False whenever STDERR contains
                    # 'Traceback', EVEN with exit 0. That skipped this branch
                    # before _is_test_pass ran. _is_test_pass already has the
                    # authoritative, stricter gate (a canonical pass phrase
                    # AND exit code 0), so it is the right and sufficient
                    # condition here - is_success is not needed and was
                    # actively wrong. Still fires once per run.
                    if (tc.name == "bash" and not test_pass_surfaced
                            and self._is_test_pass(result["content"])):
                        test_pass_surfaced = True
                        proof = self._pass_proof(result["content"])
                        debug_print(f"SELF-AWARENESS surface FIRED (step {step_no})")

                        # V61.11: BEFORE endorsing the pass, measure it.
                        # This branch used to say "your success criterion is
                        # now met... write your final summary now" on the
                        # strength of a phrase the model prints itself. On the
                        # horror_snake run that sentence ended a build whose
                        # test never called update(), and the frozen game
                        # shipped with VERDICT: WORKING.
                        # V61.11a: the body of this lives in _coverage_message
                        # so it can be CALLED BY A TEST. Shipped inline first
                        # time and it referenced two attributes that do not
                        # exist - self._scripts_named_in (module-level, no
                        # self) and self.executor.validator (ToolExecutor has
                        # only .tools) - which raised AttributeError the
                        # instant the branch fired and killed the run. The
                        # helpers had unit tests; the call site had none. That
                        # is the same defect this whole gate exists to catch.
                        _cov_msg = await self._coverage_message(
                            str((tc.arguments or {}).get("command", "")))
                        if _cov_msg:
                            self.messages.append(Message(role="system",
                                                         content=_cov_msg))
                        else:
                            self.messages.append(Message(
                                role="system",
                                content=(
                                    f"✅ SELF-AWARENESS: your own self-test just PASSED "
                                    f"(output: \"{proof}\"). Your task's built-in success criterion "
                                    f"is now met. Re-running the same passing test or re-applying "
                                    f"patches that already succeeded will not change this. If the "
                                    f"task is complete, write your final summary now; only keep "
                                    f"working if there is a specific, still-unmet requirement."
                                )
                            ))
                    # V38.1: a genuinely-passing shallow test can surface the
                    # 'criterion met' line above, then a DEEPER test can fail.
                    # If a self-test FAILS after the surface fired, retract it
                    # once - mechanical, evidence-based, and distinct from the
                    # KNOWN-OPEN claims-vs-evidence auditor (an LLM pass over
                    # the FINAL response, which is still your design call).
                    if (tc.name == "bash" and test_pass_surfaced
                            and not test_pass_retracted
                            and self._is_test_fail(
                                result["content"],
                                str((tc.arguments or {}).get("command", "")))):
                        test_pass_retracted = True
                        debug_print(f"SELF-AWARENESS retraction FIRED (step {step_no})")
                        self.messages.append(Message(
                            role="system",
                            content=(
                                "⚠️ SELF-AWARENESS UPDATE: a self-test just FAILED "
                                "after your earlier test passed. Your task's success "
                                "criterion is NOT currently met - the earlier green "
                                "result is superseded by this failure. Do not finalize; "
                                "fix the failing behavior and re-run the test that failed."
                            )
                        ))

                    # Add tool result as a message FIRST (so token count is accurate)
                    self.messages.append(Message(
                        role="tool",
                        content=result["content"],
                        tool_name=tc.name,
                        tool_call_id=tc.id
                    ))
                    
                    # Check for security boundary hit and inject reflection
                    if result["content"].startswith("Access Denied:"):
                        stuck_edit_streak = 0
                        self.messages.append(Message(
                            role="system", 
                            content=(
                                "⚠️ SECURITY BOUNDARY: You attempted to access a path outside the allowed "
                                "working directory. STOP and reconsider:\n"
                                "1. What file/directory were you trying to access?\n"
                                "2. Is there a valid path WITHIN the working directory?\n"
                                "3. Use list_dir to see what's actually available.\n"
                                "Do NOT retry the same path."
                            )
                        ))

                    # V30.7: the miss->overwrite->delete spiral breaker.
                    # In the V30.5 game-mission log the model's str_replace
                    # missed (old_str described code not in the file), then it
                    # tried file_write over game.py (Refusing to overwrite),
                    # then `del game.py`, then os.remove - and the machine
                    # stayed SILENT through all three, because the only
                    # in-loop nudge listened for "HINT:"/"Access Denied:" and
                    # none of those blocked-write messages carry either. The
                    # HINT reflection also never escalated: same gentle text
                    # forever. This branch (a) fires on the blocked-write /
                    # failed-edit family too, and (b) counts consecutive hits
                    # and gets firmer, naming the spiral once it repeats.
                    elif (not is_success) and (
                        result["content"].startswith("❌ Refusing to overwrite")
                        or (result["content"].startswith("BLOCKED:")
                            and any(k in result["content"] for k in (
                                "cannot be deleted", "overwritten", "renamed",
                                "'del'", "os.remove", "os.unlink", "shutil.")))
                        or (tc.name == "str_replace"
                            and result["content"].startswith("Error: String not found"))
                    ):
                        stuck_edit_streak += 1
                        if stuck_edit_streak >= 2:
                            # Name the trap explicitly - the model is fighting
                            # the sandbox to regenerate a whole file instead of
                            # editing it.
                            tgt = (last_failed_edit_path
                                   or str((tc.arguments or {}).get("path", ""))
                                   or last_py_edit_path or "the file")
                            self.messages.append(Message(
                                role="system",
                                content=(
                                    f"⛔ STOP - you are in a rewrite-the-whole-file loop on {tgt}. "
                                    f"You have now hit {stuck_edit_streak} failed edits / blocked "
                                    f"destructive writes in a row. The facts that will not change:\n"
                                    f"• file_write CANNOT overwrite an existing file. del / os.remove "
                                    f"/ rename are BLOCKED. There is no way to replace the file wholesale. "
                                    f"Stop trying.\n"
                                    f"• str_replace DOES work - it is failing because your old_str does "
                                    f"not match the file's ACTUAL bytes. You are almost certainly "
                                    f"retyping from memory of what you wrote, which has drifted.\n"
                                    f"THE ONLY WAY FORWARD: file_read the EXACT lines you want to change, "
                                    f"copy the anchor VERBATIM from what file_read returns (do not retype "
                                    f"it), and str_replace that. Change one small region at a time. "
                                    f"Do NOT attempt file_write, del, or os.remove on {tgt} again."
                                )
                            ))
                        else:
                            # First hit: the tool's own HINT is usually enough.
                            self.messages.append(Message(
                                role="system",
                                content=(
                                    "⚠️ That edit did not apply. You CANNOT overwrite or delete an "
                                    "existing file - only str_replace edits it. If str_replace said "
                                    "'String not found', your old_str doesn't match the file: file_read "
                                    "the exact region and copy the anchor verbatim, then retry. Do NOT "
                                    "try file_write / del / os.remove to get around it."
                                )
                            ))

                    # Check for HINT in tool output - trigger reflection to prevent blind retries
                    # V60.2: this was the ONE contaminated site that reached the
                    # MODEL rather than the dashboard. A deliberate file_read of
                    # a file containing 8 "HINT:" occurrences told the model its
                    # correct, instructed action had failed and not to repeat the
                    # command. Now tool-scoped, anchored to column 0, and gated on
                    # an actual failure - the three facts true of every HINT this
                    # machine emits. The startswith("✅") guard is kept as-is.
                    elif ("hint" in self._machine_gate_signals(
                              tc.name, result["content"], is_success)
                          and not result["content"].startswith("✅")):
                        self.messages.append(Message(
                            role="system",
                            content=(
                                "⚠️ The tool output above contains a HINT. Before your next action:\n"
                                "1. READ the HINT carefully - it explains WHY your approach failed\n"
                                "2. THINK about what the hint is suggesting\n"
                                "3. APPLY the hint to formulate a DIFFERENT approach\n"
                                "Do NOT repeat the same command with the same parameters."
                            )
                        ))
                    else:
                        # V30.7: any successful/neutral result breaks the spiral
                        # streak so a later unrelated miss starts fresh.
                        if is_success:
                            stuck_edit_streak = 0

                    # V61.9: the warning branch. Deliberately OUTSIDE the
                    # if/elif chain above - every arm of that chain requires a
                    # failure, and this fires only on success.
                    if is_success and tc.name in ("file_write", "str_replace"):
                        _wp = str(tc.arguments.get("path", ""))
                        _parsed = parse_swallow_warning(result["content"])
                        if _parsed is None:
                            warn_floor.pop(_wp, None)
                            warn_streak.pop(_wp, None)
                        else:
                            _wn, _wlines = _parsed
                            if _wn < warn_floor.get(_wp, 1 << 30):
                                warn_floor[_wp] = _wn      # real progress
                                warn_streak[_wp] = 0
                            else:
                                warn_streak[_wp] = warn_streak.get(_wp, 0) + 1
                            if warn_streak.get(_wp, 0) >= 3:
                                warn_streak[_wp] = 0       # re-arm
                                self.messages.append(Message(
                                    role="system",
                                    content=(
                                        f"⛔ You have edited {_wp} three more times and the "
                                        f"silent-swallower count has NOT gone down - still "
                                        f"{_wn}, at line(s) {_wlines}. Reading those lines "
                                        f"is not fixing them; if you already looked and "
                                        f"moved on, you moved on from a live defect.\n"
                                        f"Every one of those lines is a place where an "
                                        f"exception is discarded, so the feature inside it "
                                        f"can be completely dead while --test still reports "
                                        f"PASS. That is the exact failure this machine "
                                        f"exists to prevent, and it is currently in your "
                                        f"file.\n"
                                        f"BEFORE your next feature edit: str_replace each "
                                        f"of those lines so the handler prints the exception "
                                        f"(or re-raises), then re-run your test. If you "
                                        f"believe one of them is genuinely correct as "
                                        f"written, say WHICH line and WHY in your next "
                                        f"message - do not silently skip it."
                                    )
                                ))
                    
                    # THEN notify callback (finish_tool can now see accurate context size)
                    # V21: pass the SAME success verdict used for the trajectory, so the
                    # dashboard can never show ✓ for a result the agent recorded as ✗
                    if on_tool_result:
                        on_tool_result(tc.name, result["content"], is_success)
                
                # Continue loop to get next response
                continue
            else:
                # No tool calls
                if not response.content or not response.content.strip():
                    # V25: cap the spin - with max_iterations effectively
                    # unbounded, a model stuck on empty replies re-sent the
                    # full context forever. Five strikes ends the task
                    # (raised from three in V30).
                    empty_streak += 1
                    if empty_streak >= 5:
                        final_response = ("⚠️ Aborted: the model returned 5 "
                                          "consecutive empty responses (no text, "
                                          "no tool calls). It is stuck.")
                        outcome = "failure"
                        break
                    # V61.12: "resend same context" was a DETERMINISTIC FIXED
                    # POINT. Measured on the horror_snake run of 2026-07-31,
                    # iterations 35-39: message_count stuck at 74, prompt
                    # 32,177 and completion 75 IDENTICAL five times, and the
                    # model's `thinking` echoing this machine's own str_replace
                    # nudge back verbatim with no content and no tool calls.
                    # Nothing was appended, so the next call sent the same
                    # bytes and could only get the same answer - ~129,000
                    # prompt tokens spent re-asking a question that provably
                    # could not answer differently. Same principle as the
                    # V61.6 failed-edit cache: a repeat over an unchanged
                    # input is guaranteed to repeat.
                    # From the second strike the input CHANGES. role="user",
                    # not "system" - what it was parroting was a system
                    # injection, and the completion gate already uses the user
                    # role successfully at this same site.
                    if empty_streak >= 2:
                        self.messages.append(Message(role="user", content=(
                            f"You returned an empty response {empty_streak} "
                            f"times in a row - no text and no tool call. "
                            f"Nothing has changed since, so re-sending the same "
                            f"context cannot produce a different answer; this "
                            f"message is the only thing that is different.\n"
                            f"If you were repeating a warning back to me instead "
                            f"of acting on it: the warning is not the task. Take "
                            f"ONE concrete action now - file_read the region you "
                            f"were trying to edit, then a single str_replace with "
                            f"an anchor copied verbatim from what file_read "
                            f"returned. If you believe the work is finished, say "
                            f"so in a final summary beginning with VERDICT:. "
                            f"After {5 - empty_streak} more empty replies this "
                            f"run is aborted as stuck."
                        )))
                    continue
                # V30.2: one-shot untested-edit gate. In the snake_game run
                # the model's final patch was NEVER tested - all 7 bash calls
                # in the run failed - and it declared success anyway; the
                # episode then stored a fabricated "final run completed
                # without errors". Mechanical check, no LLM: if a successful
                # .py edit postdates the last successful bash (or no bash
                # ever succeeded), bounce ONCE with explicit instructions,
                # then accept the next completion regardless (loop-proof).
                # V178: TWO FACTS, NOT ONE, AND A SIGNATURE INSTEAD OF A FLAG.
                #
                # (a) The condition was "no command has SUCCEEDED since the
                #     edit". On the snake run of 2026-08-06 03:20 the last
                #     edit was followed by a FAILING `--test` and then two
                #     `python -c` diagnostics that exited 0. Those set
                #     last_ok_bash past the edit, so the gate never fired at
                #     all and the run finished at iteration 111 with a red
                #     self-test. A diagnostic is not a verification. The
                #     second disjunct below asks the question that matters:
                #     did the TEST fail since the last edit, and has it not
                #     passed since?
                #
                # (b) `completion_nudged` was a one-shot boolean, so a model
                #     that burned the bounce early could finish later with a
                #     red test and nothing could stop it - that is the mario
                #     run of 2026-08-05 16:37, bounced at 17:09 and finished
                #     unstoppably at 17:19. It is now a SIGNATURE of the
                #     facts the bounce was about. It re-fires only when one of
                #     those facts has changed, which is the same rule the
                #     duplicate guard and the V172 mutation skip already use:
                #     never repeat over an unchanged input. It therefore
                #     cannot loop - if the model changes nothing, the
                #     signature is identical and the gate stays silent.
                # V178: a PASSING TEST IS A RUN. Keying "never ran" on
                # last_ok_bash alone means a green self-test that this
                # machine did not happen to score as a successful bash still
                # reads as "you never ran it". Take the later of the two -
                # caught by B5 of the suite, which is the reason the two
                # facts are tracked separately in the first place.
                _ran_since = max((x for x in (last_ok_bash, last_test_pass)
                                  if x is not None), default=None)
                _never_ran = (_ran_since is None or _ran_since < last_py_edit) \
                    if last_py_edit is not None else False
                _test_red = (last_test_fail is not None
                             and (last_test_pass is None
                                  or last_test_pass < last_test_fail))
                _sig = (last_py_edit, last_test_fail, last_test_pass)
                if (last_py_edit is not None and (_never_ran or _test_red)
                        and _sig != completion_nudged_sig):
                    completion_nudged_sig = _sig
                    completion_nudged = True
                    _why = ("was edited but never run since" if _never_ran
                            else "has a FAILING self-test as its last result")
                    self._notify(f"COMPLETION GATE: bounced - "
                                 f"{last_py_edit_path or 'a .py file'} {_why}")
                    self.messages.append(Message(role="assistant", content=response.content,
                                                 thinking=response.thinking))  # V61.14
                    self.messages.append(Message(role="user", content=(
                        (f"⚠ COMPLETION CHECK: your latest edit to "
                         f"{last_py_edit_path or 'a .py file'} has NEVER been verified - "
                         f"no command has succeeded since that edit"
                         + (", and no command succeeded in this entire run"
                            if last_ok_bash is None else "")
                         + ". "
                         if _never_ran else
                         f"⚠ COMPLETION CHECK: the last time your self-test ran "
                         f"it FAILED, and it has not passed since. Commands "
                         f"that exited 0 after it were diagnostics, not "
                         f"verification - running `python -c` successfully "
                         f"says nothing about whether "
                         f"{last_py_edit_path or 'your file'} works. ")
                        + f"Run: python {last_py_edit_path or '<file>'} --test  "
                        f"and fix what fails. Only finish after it passes, or "
                        f"explicitly label the affected features 'written but "
                        f"unverified' in your final summary."
                    )))
                    continue
                # V179: DOES THE PROGRAM START? Every other gate here reads
                # the self-test, and a self-test can be satisfied by a
                # fixture. This starts the deliverable the way a person
                # starts it - no test flag, no fake input - and reports what
                # happens. It is the one question a fixture cannot answer,
                # and it is the question that was never asked while the same
                # AttributeError shipped three runs running.
                #
                # Keyed on the edit, so it re-runs when the file changes and
                # stays silent when it does not - the same no-repeat rule as
                # the V178 gate above and the V172 mutation skip.
                _smoke_wd = _tools_working_dir(getattr(self, "tools", None))
                _smoke_target = last_py_edit_path
                if edit_counts:
                    _b = max(edit_counts.items(), key=lambda kv: (kv[1], kv[0]))
                    if _b[1] > edit_counts.get(last_py_edit_path or "", 0):
                        _smoke_target = _b[0]
                if (_smoke_target and last_py_edit is not None
                        and last_py_edit != smoke_checked_at):
                    smoke_checked_at = last_py_edit
                    _sp = os.path.join(_smoke_wd, _smoke_target)
                    _has_entry = False
                    try:
                        _has_entry = has_plain_entry(
                            open(_sp, encoding="utf-8", errors="replace").read())
                    except Exception as e:
                        debug_print(f"ENTRY SMOKE: could not read {_smoke_target} "
                                    f"({e})")
                    if _has_entry:
                        _sm = await asyncio.to_thread(
                            entry_point_smoke, _sp, _smoke_wd, ENTRY_SMOKE_TIMEOUT_S)
                        if _sm.get("crashed"):
                            self._notify(f"ENTRY SMOKE: bounced - "
                                         f"{_smoke_target} DIED "
                                         f"{_sm['seconds']}s after start "
                                         f"(exit {_sm['returncode']})")
                            self.messages.append(Message(
                                role="assistant", content=response.content,
                                thinking=response.thinking))
                            self.messages.append(Message(role="user", content=(
                                f"\u26d4 THE PROGRAM DOES NOT START. I ran "
                                f"`python {_smoke_target}` - no test flag, "
                                f"exactly how someone would run it - and it "
                                f"died after {_sm['seconds']}s with exit "
                                f"{_sm['returncode']}:\n\n{_sm['error']}\n\n"
                                f"Your self-test passes. That means the test "
                                f"is exercising a path the real program does "
                                f"not take. The usual cause is a fixture: a "
                                f"fake object built to satisfy a check, and "
                                f"then production code adjusted to accept the "
                                f"fake instead of what the real caller "
                                f"actually passes. Read the traceback, find "
                                f"what the REAL caller hands that function, "
                                f"and make the production code correct for "
                                f"THAT - then change the test to match, never "
                                f"the other way round.\n"
                                f"When it starts cleanly this check times out "
                                f"instead of failing, and that is the pass."
                            )))
                            continue
                        else:
                            debug_print(
                                f"ENTRY SMOKE: {_smoke_target} "
                                + ("started and was still running at "
                                   f"{_sm['seconds']}s - pass"
                                   if _sm.get("timed_out") else
                                   f"exited {_sm['returncode']} in "
                                   f"{_sm['seconds']}s"))
                # V61.17: THE MUTATION GATE. Coverage asks "did the function
                # run"; this asks "would the test NOTICE if the function were
                # wrong", and they are not the same question. Measured on the
                # snake_game run of 2026-08-01: the coverage probe passed at
                # 20/21 functions executed, noop_assert_findings returned
                # nothing, and both were right - yet deleting the scoring, the
                # growth, the death and the food respawn from Game.run() each
                # still printed SELF-TEST OK. The test asserted against a
                # TRANSCRIPTION of the game loop that the model had pasted
                # into run_test, with its own comment saying so ("This is the
                # exact same logic from Game.run() lines 228-244"). Nothing
                # that reads the test's text can catch that. Planting a bug
                # and watching the test not flinch can.
                # One shot, like the two gates above: bounced or ignored, the
                # next completion is accepted, so it cannot loop.
                # V61.18: RE-MEASURE THE FIX. The gate was one-shot, so the
                # model's rewrite was never checked - and on the snake_game
                # run of 2026-08-01 that rewrite made things WORSE. Told its
                # 12% was too low, the model wrapped the whole test body in
                # `except SystemExit: pass`; Game.run() ends by calling
                # sys.exit(), so the handler fired on the first scenario, 31
                # assertions were skipped, and the artifact shipped printing
                # "passed_scenarios contains 0 items" followed by
                # "SELF-TEST OK". Deleting the scoring, the growth and the
                # collision from the game all survived. A gate that measures
                # once cannot see a regression it caused.
                # Bounded, and bounded on EVIDENCE, not just on a count: it
                # stops at MUTATION_MAX_FIRES, and stops early the moment a
                # round fails to improve - because repeating a move that did
                # not work is the one move guaranteed not to work.
                if (mutation_fires < MUTATION_MAX_FIRES and last_py_edit_path
                        and last_ok_bash is not None):
                    mutation_fires += 1
                    # V171 FIX 4: mutate the DELIVERABLE, not whatever was
                    # written last. The gate plants forty bugs in
                    # os.path.join(wd, <target>) and asks whether the model's
                    # --test notices; pointed at a 19-line subprocess wrapper
                    # it would be measuring the wrong file entirely, and in
                    # the run of 2026-08-04 that is exactly where
                    # last_py_edit_path was pointing after step 54. The file
                    # being BUILT is the one that keeps being edited.
                    mut_target = last_py_edit_path
                    if edit_counts:
                        _best = max(edit_counts.items(), key=lambda kv: (kv[1], kv[0]))
                        if _best[1] > edit_counts.get(last_py_edit_path, 0):
                            mut_target = _best[0]
                            debug_print(
                                f"MUTATION TARGET: {mut_target} "
                                f"({_best[1]} edits) chosen over last-written "
                                f"{last_py_edit_path} "
                                f"({edit_counts.get(last_py_edit_path, 0)} edits)")
                    wd = _tools_working_dir(getattr(self, "tools", None))
                    # V172: DO NOT RE-MEASURE A FILE THAT HAS NOT CHANGED.
                    # On the 2026-08-05 run all three rounds fired at three
                    # consecutive completion attempts with zero edits between
                    # them, cost three full gate runs, produced 10/20/10% on
                    # a byte-identical file, and ended by accusing the model
                    # of a regression. A hash settles it before a single
                    # mutant is planted: the round is skipped, the budget is
                    # NOT spent, and the model is told the truth instead.
                    # V178: the gate needs a PASSING baseline. Spending a
                    # round when the last test result was a failure buys
                    # three baseline runs and the message "cannot measure" -
                    # which happened on rounds 2 AND 3 of the 2026-08-06
                    # 03:20 run, and rounds 2 and 3 of 2026-08-05 16:37. The
                    # completion gate above has already told the model its
                    # test is red; a second voice saying "I could not
                    # measure" adds nothing and costs the budget.
                    _no_baseline = (last_test_fail is not None
                                    and (last_test_pass is None
                                         or last_test_pass < last_test_fail))
                    _same_file = False
                    try:
                        _tp = os.path.join(wd, mut_target)
                        if mutation_last_md5 and os.path.exists(_tp):
                            _cur_md5 = hashlib.md5(
                                open(_tp, "rb").read()).hexdigest()
                            _same_file = (_cur_md5 == mutation_last_md5
                                          and mutation_edits_since == 0)
                    except Exception as e:
                        debug_print(f"MUTATION GATE: hash check failed ({e}) "
                                    f"- measuring anyway")
                    if _same_file:
                        mutation_fires -= 1        # the round was not spent
                        self._notify(f"MUTATION GATE: skipped - {mut_target} "
                                     f"is byte-identical to my last check")
                        self.messages.append(Message(
                            role="assistant", content=response.content,
                            thinking=response.thinking))
                        self.messages.append(Message(role="user", content=(
                            f"\u26d4 NOTHING HAS CHANGED SINCE MY LAST CHECK. "
                            f"{mut_target} is byte-identical to the version I "
                            f"measured, so I did not measure it again - the "
                            f"number would only move because I drew different "
                            f"bugs, and that would tell you nothing.\n"
                            f"The survivors I listed are still survivors. "
                            f"Reading the file again will not change them; an "
                            f"assertion that fails when one of those "
                            f"behaviours is wrong will. Write one, run your "
                            f"self-test, and I will measure the result."
                        )))
                        continue
                    if _no_baseline:
                        # V178: the gate needs a PASSING baseline. Running it
                        # against a red test buys three baseline runs and the
                        # message "cannot measure" - which is what rounds 2
                        # AND 3 produced on 2026-08-06 03:20, and rounds 2
                        # and 3 on 2026-08-05 16:37. Six wasted rounds across
                        # two runs, each one spending budget to learn
                        # something the completion gate above has already
                        # said. Same principle as the V172 skip: do not do
                        # work whose answer you already have.
                        mutation_fires -= 1
                        self._notify(f"MUTATION GATE: not run - "
                                     f"{mut_target}'s self-test is failing, so "
                                     f"there is no baseline to measure against")
                        mut = None
                    else:
                        mut = await asyncio.to_thread(
                            run_mutation_gate, os.path.join(wd, mut_target),
                            wd, MUTATION_MAX_MUTANTS, 60, 180, mutation_fires)
                    # V61.26: RECORD WHAT THE MACHINE MEASURED. Nothing did,
                    # and the spongebob_shooter summary of 2026-08-01 claimed
                    # "Round 1: 8/40 caught (20%) / Round 2: 11/40 (28%) /
                    # Round 3: 18/40 (45%)". Only 28% and 45% appear anywhere
                    # in the 143 thinking blocks; "20%" appears once, in the
                    # turn that WROTE the summary. Whether a third firing
                    # happened is not answerable from the episode, because
                    # the gate's own numbers lived only in a chat message and
                    # a debug line. A measurement the machine cannot produce
                    # on request is a measurement the model can invent.
                    try:
                        hist = self._mutation_history
                    except AttributeError:
                        hist = self._mutation_history = []
                    if mut:
                        hist.append({
                            "round": mutation_fires,
                            "flaky": bool(mut.get("flaky")),
                            "killed": mut.get("killed"),
                            "tested": mut.get("tested"),
                            "rate": round(mut.get("rate") or 0.0, 4),
                            "survivors": len(mut.get("survivors") or []),
                            "asserts_never": len(mut.get("asserts_never") or []),
                            "file": mut_target,
                        })
                        debug_print(f"MUTATION RECORD round {mutation_fires}: "
                                    + json.dumps(hist[-1]))
                    # V171 FIX 5: the three outcome messages now come from
                    # mutation_round_message() so the mid-loop re-measure
                    # below cannot drift from this one.
                    _notify, _text, last_round = mutation_round_message(
                        mut, mut_target, mutation_prev, mutation_fires,
                        mutation_edits_since)
                    # V172: record WHAT was measured and reset the edit
                    # counter, so the next round knows whether the model has
                    # touched the file since.
                    if mut and mut.get("file_md5"):
                        mutation_last_md5 = mut["file_md5"]
                        mutation_edits_since = 0
                    if mut and _mutation_scored(mut)[0] < MUTATION_MIN_KILL_RATE \
                            and not mut.get("unrunnable") and not mut.get("flaky"):
                        mutation_prev = mut
                    if _text:
                        self._notify(_notify)
                        self.messages.append(Message(
                            role="assistant", content=response.content,
                            thinking=response.thinking))
                        self.messages.append(Message(role="user", content=_text))
                        if last_round:
                            mutation_fires = MUTATION_MAX_FIRES
                            mutation_remeasure_due = False
                        else:
                            # The message promises a re-measure on the next
                            # green test. This is what makes it true.
                            mutation_remeasure_due = True
                        continue
                    if mut:
                        mutation_remeasure_due = False
                        _sr, _sk, _sn, _sl = _mutation_scored(mut)
                        debug_print(f"MUTATION GATE: {mut_target} caught "
                                    f"{_sk}/{_sn} {_sl} "
                                    f"({_sr:.0%}) - passed")
                # V61.5: CLAIM vs the machine's OWN RECORD. One shot, like the
                # gate above - answered or ignored, the next completion is
                # accepted, so it can never loop. Deterministic: it compares
                # basenames in the final answer against this run's own bash
                # outcomes and nothing else. No model opinion involved.
                if not claims_nudged:
                    _broken = []
                    try:
                        for _b in sorted(_scripts_named_in(response.content or "")):
                            _rec = self._script_runs.get(_b)
                            if _rec and _rec[1] is False:
                                _broken.append((_b, _rec[0]))
                    except Exception as e:
                        debug_print(f"claim check failed: {e}")
                    if _broken:
                        claims_nudged = True
                        _lines = "".join(
                            f"\n     - {b}  (last run: step {st}, FAILED)"
                            for b, st in _broken)
                        self._notify(
                            "CLAIM CHECK: final answer cites "
                            + ", ".join(b for b, _ in _broken)
                            + " but the last run of it FAILED")
                        self.messages.append(Message(role="assistant",
                                                     content=response.content,
                                                     thinking=response.thinking))  # V61.14
                        self.messages.append(Message(role="user", content=(
                            "⚠ CLAIM CHECK (one-time). Your summary presents "
                            "output from a script whose LAST run in this session "
                            "did not succeed:" + _lines + "\n\n"
                            "   Whatever that script printed before it stopped is "
                            "partial. A run that dies at step 5 of 15 still prints "
                            "four cheerful lines first, and quoting those as "
                            "complete evidence is the one mistake that survives "
                            "every test you have.\n"
                            "   Two honest ways out, and only two. Fix it and run "
                            "it until it exits 0 - then the evidence is real and "
                            "you can cite all of it. Or state in the summary "
                            "exactly how far it got and which claims are therefore "
                            "unverified.\n"
                            "   Do not simply repeat the summary."
                        )))
                        continue
                # V30.1: RESTORED - this block was deleted in V30, which broke
                # every run: a real no-tool-call completion fell through to the
                # next loop iteration, so the model was re-prompted after its
                # final answer until max_iterations, final_response stayed None,
                # and every task ended as "⚠️ Reached maximum iterations".
                # Real content = valid completion
                self.messages.append(Message(role="assistant", content=response.content))
                final_response = response.content
                break

        # Check if we hit max iterations
        if final_response is None:
            final_response = f"⚠️ Reached maximum iterations ({self.max_iterations}). The model may be stuck in a loop."
            outcome = "failure"
        
        # ═══════════════════════════════════════════════════════════════════
        # EPISODE CAPTURE - Save learning for future
        # ═══════════════════════════════════════════════════════════════════
        if self.memory and self.trajectory:  # Only save if tools were used
            if on_status:
                on_status("Generating reflection...")
            
            # Determine outcome based on trajectory
            fail_count = sum(1 for t in self.trajectory if not t[2])
            if fail_count > len(self.trajectory) * 0.7:
                outcome = "partial" if outcome == "success" else outcome

            # V41.1: outcome must not contradict the evidence. `outcome` is
            # INITIALIZED to "success" and is only overwritten on the warning,
            # protocol and max-iteration paths - so a model that gives up and
            # explains why produces an ordinary no-tool-call completion and
            # keeps the default. Two mechanical corrections, both using
            # evidence already computed elsewhere:
            #
            # (a) UNVERIFIED IS NOT SUCCESS. This is the same test the V30.2
            #     verification truth override uses to force
            #     meta["verification"] = "NONE - zero successful commands...".
            #     That override was already firing while outcome still said
            #     "success", so a single episode asserted both that it
            #     succeeded and that nothing was ever verified.
            if outcome == "success" and not any(
                    t[0] == "bash" and t[2] for t in self.trajectory):
                outcome = "partial"
                self._notify("OUTCOME success -> partial: nothing was ever "
                             "verified (no bash command succeeded)")
            #
            # (a2) V61.27: NOR IS "VERIFIED, THEN CHANGED". The V30.2 gate
            #     already computes "a successful .py edit postdates the last
            #     successful bash", bounces ONCE on it, then accepts the next
            #     completion REGARDLESS - loop-proof by design, and therefore
            #     silent about a model that never went back and re-ran.
            #     mario_game, 2026-08-03: last passing test at step 41, then
            #     EIGHT successful edits, a --test that FAILED at step 51 with
            #     AttributeError on pygame.array, four more edits, and a stop.
            #     Episode: outcome success, confidence 0.95, grounded True.
            #     The delivered file fails its own --test 0 times out of 6, in
            #     every SDL configuration. The bounce stays one-shot - looping
            #     is worse - but the RECORD must not say success. Same
            #     evidence, same mechanical test, applied where the model
            #     cannot argue with it.
            #
            # (a3) V61.28: AN ABANDONED DELIVERABLE IS NOT SUCCESS EITHER.
            #     DELIVERABLE SPLIT has warned since V45 and never escalated -
            #     it is the last item still open from the original audit.
            #     super_mario, 2026-08-03: file_write super_mario.py, an
            #     overwrite refusal, then super_mario_bros.py created at step
            #     17, its --test failed at step 18, and the model went back to
            #     super_mario.py and never touched the second file again. Both
            #     ship broken. This run was already caught by (a) because NO
            #     bash succeeded, but the dangerous shape is one green file
            #     and one abandoned - outcome success, last_py_edit_path
            #     pointing at the good one, and nothing anywhere asking about
            #     the other. last_py_edit_path is a single slot; a split
            #     deliverable needs a set.
            #     TIGHTENED: only a file the model RAN and never got green is
            #     counted. "Written and never run at all" is ambiguous - the
            #     mario run wrote coverage_check.py purely to analyse its own
            #     file, and flagging that would downgrade an honest success.
            #     "Ran it, it failed, walked away" is not ambiguous. Files
            #     never run at all are still covered by (a) and (a2).
            if outcome == "success" and built_deliverables:
                runs = getattr(self, "_script_runs", {})
                orphans = sorted(b for b in built_deliverables
                                 if b in runs and not runs[b][1])
                if orphans:
                    outcome = "partial"
                    self._notify(
                        "OUTCOME success -> partial: " + ", ".join(orphans)
                        + (" was" if len(orphans) == 1 else " were")
                        + " built but never ran successfully")
            #
            if outcome == "success" and last_py_edit is not None and (
                    last_ok_bash is None or last_ok_bash < last_py_edit):
                outcome = "partial"
                self._notify(
                    f"OUTCOME success -> partial: "
                    f"{last_py_edit_path or 'a source file'} was edited after "
                    f"the last successful command and never run again")
            #
            # (b) A SELF-DECLARED BLOCK IS A FAILURE. Exact, line-anchored
            #     protocol markers only - not natural-language inference.
            if final_response and self._BLOCK_MARKER_RE.search(final_response):
                if outcome != "failure":
                    self._notify(f"OUTCOME {outcome} -> failure: the summary "
                                 f"declares itself BLOCKED")
                outcome = "failure"
            #
            # (c) V45: A SELF-DECLARED BROKEN DELIVERABLE IS NOT A SUCCESS.
            #     An explicit 'VERDICT: BROKEN' is the agent stating the
            #     build does not work; that is stronger evidence than any
            #     heuristic and outranks the default. The narrower
            #     known-defect fallback only downgrades to partial, and
            #     only when no explicit WORKING verdict was given.
            if outcome == "success" and final_response:
                if self._VERDICT_BROKEN_RE.search(final_response):
                    outcome = "failure"
                    self._notify("OUTCOME success -> failure: the summary "
                                 "opens with VERDICT: BROKEN")
                elif (self._ABANDONED_RE.search(final_response)
                      and not self._VERDICT_OK_RE.search(final_response)):
                    outcome = "partial"
                    self._notify("OUTCOME success -> partial: the run ended "
                                 "by asking the operator what to do - that "
                                 "is an abandoned task, not a finished one")
                elif (not self._VERDICT_OK_RE.search(final_response)
                      and self._KNOWN_DEFECT_RE.search(final_response)):
                    outcome = "partial"
                    self._notify("OUTCOME success -> partial: the summary "
                                 "reports a known unresolved defect")
            
            # Generate evidence-based reflection (V21.1: returns structured dict)
            meta = await self._generate_reflection(user_message, outcome)
            
            # Create and save episode (async for embedding generation)
            episode = Episode(
                task=user_message[:32000],
                trajectory=self.trajectory,
                outcome=outcome,
                reflection=meta["lesson"],
                iterations=self.iteration_count,
                # Use REAL token count from Ollama, fallback to estimate if unavailable
                token_cost=self.total_prompt_tokens + self.total_completion_tokens if self.total_prompt_tokens > 0 
                          else len(json.dumps([m.to_dict() for m in self.messages])) // 4,
                timestamp=datetime.now().isoformat(),
                embedding=None,  # Will be generated in save()
                failure_class=meta["failure_class"],
                root_cause=meta["root_cause"],
                fix=meta["fix"],
                verification=meta["verification"],
                confidence=meta["confidence"],
                grounded=meta.get("grounded", True),
                temperature=self.gen_params.get("temperature", -1.0),
                seed=self.gen_params.get("seed", -1),
                model=self.gen_params.get("model", ""),
                ollama_version=self.gen_params.get("ollama_version", ""),
                thinking_log=self.thinking_log or None,  # V30.9: review-only
                # V61.26: the gate's own numbers, so a summary's claims
                # about kill rates are checkable after the fact.
                mutation_history=getattr(self, "_mutation_history", None) or None
            )
            await self.memory.save(episode)
            
            if on_episode_saved:
                on_episode_saved(episode)
            
            debug_print(f"Saved episode: {outcome}, reflection: {meta['lesson'][:500]}...")
        
        return final_response

def probe_environment(working_dir: str = None) -> dict:
    """
    V21: One-time environment probe so the model starts each task knowing
    the facts it previously burned 4-6 iterations rediscovering (python
    version, which packages are importable, where it is, what files exist).

    Probes the same `python` the bash tool will invoke (falls back to the
    interpreter running this script). Every step is fail-safe: on any
    error the field reads "unknown" and the agent behaves exactly as V20.
    """
    info = {
        "python_version": "unknown",
        "available_packages": "unknown (probe failed)",
        "cwd_abs": str(Path(working_dir or os.getcwd()).resolve()),
        "dir_listing": "unknown",
    }

    # Top-level listing (names only, capped) - never recurses
    try:
        entries = sorted(
            e for e in os.listdir(info["cwd_abs"])
            if not is_machine_self(os.path.join(info["cwd_abs"], e))
        )[:150]  # V30.5: runtime hidden from startup facts too
        info["dir_listing"] = ", ".join(entries) if entries else "(empty)"
    except Exception:
        pass

    # Probe interpreter + importable packages in ONE subprocess call
    candidates = ["pygame", "numpy", "PIL", "requests", "flask", "matplotlib",
                  "pandas", "tkinter", "httpx", "rich"]
    probe_code = (
        "import sys, importlib.util as u; "
        "print(sys.version.split()[0]); "
        "print(','.join(m for m in ["
        + ",".join(repr(c) for c in candidates)
        + "] if u.find_spec(m)))"
    )
    for interpreter in ("python", sys.executable):
        try:
            proc = subprocess.run(
                [interpreter, "-c", probe_code],
                capture_output=True, text=True, timeout=10,
                # V61.8: same class as the node --check defect - text=True with
                # no encoding decodes the child's stdout with the console
                # codepage. Package names and paths are usually ASCII, so this
                # one has not bitten yet; it would on any non-ASCII path.
                encoding="utf-8", errors="replace",
                env=utf8_subprocess_env(),
                cwd=info["cwd_abs"],
            )
            if proc.returncode == 0:
                lines = proc.stdout.strip().splitlines()
                if lines:
                    info["python_version"] = lines[0].strip()
                if len(lines) > 1 and lines[1].strip():
                    info["available_packages"] = lines[1].strip()
                elif len(lines) > 1:
                    info["available_packages"] = "(none of the common packages found)"
                break
        except Exception:
            continue

    return info


# V61.29a: the placeholders BUILD_PROMPT is allowed to contain. Anything else
# between single braces is a typo, and .format() turns a typo into a crash
# before the machine starts.
BUILD_PROMPT_FIELDS = frozenset({
    "os_type", "shell_type", "allowed_commands", "python_version",
    "available_packages", "cwd_abs", "dir_listing", "platform_rules",
})


def _format_build_prompt(**values) -> str:
    """BUILD_PROMPT.format() with a diagnosis instead of a traceback.

    V61.29a. V61.29 added an example key dict to the GUI protocol -
    {{"left": False, "up": True}} - written with SINGLE braces. .format()
    read that as a replacement field and every run died at startup with
    `KeyError: '"left"'`, eight frames deep in create_agent, before a banner
    or a log line. The prompt is 12KB of hand-edited English with eight real
    placeholders in it; that will happen again.
    Braces in prose must be doubled. When they are not, say so, name the
    offender, and carry on with the placeholder left visible rather than
    refusing to start - a malformed sentence in the manual is a far smaller
    problem than a machine that will not run.
    """
    try:
        return BUILD_PROMPT.format(**values)
    except (KeyError, IndexError, ValueError) as e:
        import string as _string
        stray = sorted({f for _, f, _, _ in _string.Formatter().parse(BUILD_PROMPT)
                        if f and f not in BUILD_PROMPT_FIELDS})
        debug_print(f"BUILD_PROMPT is malformed: {e}. Unescaped brace(s) in "
                    f"prose - double them as {{{{ and }}}}. Offending "
                    f"placeholder(s): {stray or '(unknown)'}. Starting anyway "
                    f"with those left as literal text.")
        text = BUILD_PROMPT
        for k in stray:
            text = text.replace("{" + k + "}", "{{" + k + "}}")
        try:
            return text.format(**values)
        except Exception:
            # last resort: substitute only the fields we know, touch nothing else
            out = BUILD_PROMPT
            for k, v in values.items():
                out = out.replace("{" + k + "}", str(v))
            return out


def create_agent(agent_type: str, client: OllamaClient, working_dir: str = None, 
                 memory: EpisodeMemory = None, judge_client: OllamaClient = None,
                 gen_params: dict = None) -> Agent:
    all_tools = get_all_tools(working_dir)
    
    # Detect environment
    os_type = "Windows" if sys.platform == "win32" else "Linux/Mac"
    shell_type = "CMD" if sys.platform == "win32" else "Bash"
    allowed_commands = ", ".join(sorted(BashTool.get_allowed()))
    
    if agent_type == "build":
        # Inject environment into prompt (V21: includes live-probed facts)
        env = probe_environment(working_dir)
        formatted_prompt = _format_build_prompt(
            os_type=os_type,
            shell_type=shell_type,
            allowed_commands=allowed_commands,
            python_version=env["python_version"],
            available_packages=env["available_packages"],
            cwd_abs=env["cwd_abs"],
            dir_listing=env["dir_listing"],
            platform_rules=get_platform_rules()
        )
        return Agent("build", formatted_prompt, client, all_tools, memory=memory,
                     judge_client=judge_client, gen_params=gen_params)
    elif agent_type == "plan":
        read_only = {k: v for k, v in all_tools.items() if k in ["file_read", "list_dir", "grep_search"]}
        return Agent("plan", PLAN_PROMPT, client, read_only, memory=memory,
                     judge_client=judge_client, gen_params=gen_params)
    raise ValueError(f"Unknown agent: {agent_type}")

# =============================================================================
# CLI
# =============================================================================

def _banner_logo_row(logo_line: str) -> str:
    """Style the WHAT-IF face white and its line-art depth Matrix green."""
    content = ("  " + logo_line).ljust(78)
    styled = ["[bold bright_green]║[/]"]
    for char in content:
        if char == "█":
            styled.append("[bold bright_white]█[/]")
        elif char in "╔╗╚╝║═":
            styled.append(f"[bold bright_green]{char}[/]")
        else:
            styled.append(char)
    styled.append("[bold bright_green]║[/]")
    return "".join(styled)


BANNER = f"""
[bold bright_green]╔══════════════════════════════════════════════════════════════════════════════╗[/]
[bold bright_green]║[/]                                                                              [bold bright_green]║[/]
{_banner_logo_row("██╗    ██╗██╗  ██╗ █████╗ ████████╗    ██╗███████╗")}
{_banner_logo_row("██║    ██║██║  ██║██╔══██╗╚══██╔══╝    ██║██╔════╝")}
{_banner_logo_row("██║ █╗ ██║███████║███████║   ██║ █████╗██║█████╗")}
{_banner_logo_row("██║███╗██║██╔══██║██╔══██║   ██║ ╚════╝██║██╔══╝")}
{_banner_logo_row("╚███╔███╔╝██║  ██║██║  ██║   ██║       ██║██║")}
{_banner_logo_row(" ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝       ╚═╝╚═╝")}
[bold bright_green]║[/]                                                                              [bold bright_green]║[/]
[bold bright_green]║[/]              [bright_white]▀▄▀▄▀▄[/] [bold bright_cyan]M A C H I N E[/] [bright_white]▄▀▄▀▄▀[/]                                     [bold bright_green]║[/]
[bold bright_green]║[/]                                                                              [bold bright_green]║[/]
[bold bright_green]║[/]   [bold bright_cyan]◈[/] [dim white]Nested Learning[/] [bold bright_cyan]◈[/] [dim white]Recursive Self-Correction[/] [bold bright_cyan]◈[/] [dim white]T=0.6[/] [bold bright_cyan]◈[/]                    [bold bright_green]║[/]
[bold bright_green]║[/]                                                                              [bold bright_green]║[/]
[bold bright_green]╚══════════════════════════════════════════════════════════════════════════════╝[/]
"""

# Tool visualization configuration
TOOL_ICONS = {
    "file_read": "📖", "file_write": "📝", "str_replace": "🔄",
    "list_dir": "📁", "bash": "⚡", "grep_search": "🔍"
}
TOOL_COLORS = {
    "file_read": "cyan", "file_write": "green", "str_replace": "yellow",
    "list_dir": "blue", "bash": "magenta", "grep_search": "cyan"
}

# V45.9: ONE definition of a valid seed, used by both doors (--seed at
# startup and /seed mid-session). Domain is 1..2**31-1 - exactly the range
# the machine draws its own random seeds from, so every seed it hands out
# is a seed it takes back. -1 is REFUSED on the way in: it is the Episode
# "unrecorded" sentinel (Episode.seed default), so accepting it would let a
# real pinned run be indistinguishable from a pre-V45 record that never had
# one. Returns None on refusal; callers decide what to say about it.
SEED_MIN = 1
SEED_MAX = 2**31 - 1


def normalize_seed(value) -> int:
    """Coerce value to a usable Ollama seed, or None if it is not one."""
    try:
        n = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    if n < SEED_MIN or n > SEED_MAX:
        return None
    return n


TEST_AND_FIX_DIRECTIVE = "test and fix it"
_TEST_AND_FIX_AT_END_RE = re.compile(
    r"(?i)\btest\s+and\s+fix\s+it[.!?]*\s*\Z"
)


def apply_autotest_directive(message: str, enabled: bool) -> tuple:
    """Append the existing test-and-fix instruction exactly once.

    This intentionally performs no interpretation and activates no parallel
    mode. It reproduces what already happens when a person types the phrase at
    the end of a What-If question. Returning whether text was appended lets the
    CLI disclose the transformation without making callers compare strings.
    """
    if not enabled or not isinstance(message, str) or not message.strip():
        return message, False
    if _TEST_AND_FIX_AT_END_RE.search(message):
        return message, False
    return message.rstrip() + "\n\n" + TEST_AND_FIX_DIRECTIVE, True


COMMANDS = {
    "/help": "Show all commands and usage",
    "/models": "List available Ollama models",
    "/model": "Show/switch model (/model <name>)",
    "/agent": "Show/switch agent (/agent build|plan)",
    "/clear": "Clear conversation history (episode memory is preserved)",
    "/tools": "List every tool available to the current agent",
    "/memory": "Show episode memory or erase it (/memory clear)",
    "/inject": "Show/set lesson injection (/inject on|off; default OFF)",
    "/confidence": "Show/set semantic reflection (/confidence on|off; default ON)",
    "/autotest": "Show/set automatic test-and-fix (/autotest on|off)",
    "/seed": "Show/set builder seed (/seed <number> | /seed random)",
    "/temp": "Show/set builder temperature (/temp <0.0-2.0>)",
    "/verbose": "Toggle developer debug output",
    "/prompt": "Load and run a prompt file (/prompt <filename>)",
    "/quit": "Exit (aliases: /exit, /q)",
}


class CLI:
    def __init__(self, model: str, agent_type: str, base_url: str, working_dir: str,
                 verbose: bool = False, temperature: float = 0.6, seed: int = None,
                 autotest: bool = False):
        global VERBOSE
        VERBOSE = verbose
        
        self.model = model
        self.agent_type = agent_type
        self.working_dir = working_dir or os.getcwd()
        self.verbose = verbose
        # V180.1: CLI-owned so /agent switches and /clear preserve it. The
        # transformation itself happens once at process_message(), before all
        # rendering/fallback branches and before Agent.process sees the task.
        self.autotest_enabled = bool(autotest)
        # V45: seed is the reproducibility lever, not temperature. Random
        # per run unless pinned, but ALWAYS recorded on the episode - so a
        # run can be reproduced exactly by passing its seed back in.
        self.temperature = temperature
        # V45.9: third door onto the same value (--seed, /seed, and direct
        # construction). All three now share normalize_seed. An explicit bad
        # seed RAISES here rather than quietly becoming a random one - a
        # caller asking to replay seed X must never get an unrelated run.
        if seed is None:
            self.seed = random.randint(SEED_MIN, SEED_MAX)
        else:
            _pinned = normalize_seed(seed)
            if _pinned is None:
                raise ValueError(
                    f"seed must be a whole number {SEED_MIN}-{SEED_MAX} (got {seed!r}); "
                    f"-1 is the episode 'unrecorded' marker and is not a seed")
            self.seed = _pinned
        self.client = OllamaClient(base_url, model, {
            "num_ctx": 256000, # Default = 32768
            "temperature": self.temperature, # 0.6 default - see --temp
            "top_p": 0.95,
            "top_k": 20,
            "seed": self.seed,
        #   "repeat_penalty": 1.1,
        #   "num_predict": 4096,
        })
        # V45: graders are pinned and never move with the builder.
        self.judge_client = OllamaClient(base_url, model, {
            "num_ctx": 256000,
            "temperature": 0.0,
            "top_p": 0.95,
            "top_k": 20,
            "seed": 7,
        })
        self.gen_params = {"temperature": self.temperature,
                           "seed": self.seed, "model": model}
        self.agent = None
        self.console = Console() if RICH_AVAILABLE else None
        
        # Initialize episode memory for persistent learning
        self.memory = EpisodeMemory(self.working_dir)
    
    def print(self, *args, **kwargs):
        if self.console:
            self.console.print(*args, **kwargs)
        else:
            text = str(args[0]) if args else ""
            text = re.sub(r'\[.*?\]', '', text)
            print(text)

    @staticmethod
    def _toggle_badge(enabled: bool) -> str:
        """Return one unmistakable live-state badge for Rich and plain output."""
        return ("[bold bright_green]● ON[/]" if enabled else
                "[bold bright_red]● OFF[/]")

    def _build_session_panel(self):
        """Build the Session Configuration panel from current runtime state."""
        tool_count = len(self.agent.tools) if self.agent else (
            6 if self.agent_type == "build" else 3)
        mem_stats = self.memory.get_stats()

        config = Table(show_header=False, box=None, padding=(0, 1), expand=False)
        config.add_column(style="bold bright_cyan", width=14, justify="right")
        config.add_column(style="white", width=50)

        config.add_row("[bright_cyan]🤖 Model[/]", f"[bold bright_white]{self.model}[/]")
        config.add_row("[bright_green]⚡ Agent[/]", f"[bold bright_green]{self.agent_type.upper()}[/] [dim white]│ {tool_count} tools ready[/]")
        config.add_row("[bright_yellow]📊 Context[/]", f"[bold bright_yellow]{self.client.options.get('num_ctx', 256000):,}[/] [dim]tokens[/]")
        config.add_row("[bright_magenta]🎯 Temp[/]", f"[bold bright_magenta]{self.temperature:g}[/] [dim]stable creativity[/]")
        config.add_row("[bright_cyan]🎲 Seed[/]", f"[bold bright_cyan]{self.seed}[/] [dim]--seed {self.seed} to replay[/]")
        autotest_status = (f"{self._toggle_badge(True)} [dim]│ appends ‘test and fix it’[/]"
                           if self.autotest_enabled else
                           f"{self._toggle_badge(False)} [dim]│ /autotest on[/]")
        config.add_row("[bright_green]🧪 Auto-test[/]", autotest_status)
        config.add_row("[bright_blue]📁 Dir[/]", f"[dim bright_blue]{str(self.working_dir)[-45:]}[/]")

        if mem_stats["total"] > 0:
            config.add_row("[bright_cyan]🧠 Memory[/]", f"[bold green]{mem_stats['successes']}[/][dim]✓[/] [bold red]{mem_stats['failures']}[/][dim]✗[/] [dim]│ {mem_stats['total']} episodes[/]")
        else:
            config.add_row("[bright_cyan]🧠 Memory[/]", "[dim italic]empty ─ learning starts fresh[/]")

        return Panel(
            config,
            title="[bold bright_green]◈ Session Configuration ◈[/]",
            subtitle="[dim][ Neural Interface Active ][/]",
            border_style="bright_green",
            box=box.HEAVY
        )

    def _build_quick_commands_panel(self):
        """Build Quick Commands with current values rather than startup values."""
        inject_badge = self._toggle_badge(
            getattr(self.agent, "inject_enabled", False))
        confidence_badge = self._toggle_badge(
            getattr(self.agent, "confidence_enabled", True))
        autotest_badge = self._toggle_badge(self.autotest_enabled)

        cmd_grid = Table(show_header=False, box=None, padding=(0, 1), expand=True)
        cmd_grid.add_column(width=25)
        cmd_grid.add_column(width=25)
        cmd_grid.add_column(width=25)

        cmd_grid.add_row(
            "[bold #ffd700]/help[/] [dim]› commands[/]",
            "[bold green]/prompt[/] [dim]› load file[/]",
            "[bold bright_white]/tools[/] [dim]› list all[/]"
        )
        cmd_grid.add_row(
            "[bold magenta]/memory[/] [dim]› episodes[/]",
            f"[bold blue]/inject[/] [dim]›[/] {inject_badge}",
            "[bold #ff8700]/clear[/] [dim]› clear chat[/]"
        )
        cmd_grid.add_row(
            "[bold white]/model[/] [dim]› switch[/]",
            f"[bold bright_magenta]/temp[/] [dim]›[/] "
            f"[bold bright_magenta]{self.temperature:g}[/]",
            "[bold bright_red]/quit[/] [dim]› exit[/]"
        )
        cmd_grid.add_row(
            f"[bold bright_cyan]/confidence[/] [dim]›[/] {confidence_badge}",
            f"[bold bright_cyan]/seed[/] [dim]›[/] "
            f"[bold bright_cyan]{self.seed}[/]",
            f"[bold bright_green]/autotest[/] [dim]›[/] {autotest_badge}"
        )

        return Panel(
            cmd_grid,
            title="[bold bright_cyan]◈ Quick Commands ◈[/]",
            border_style="cyan",
            box=box.ROUNDED
        )

    def _status_hud(self):
        """Return the one idle-screen HUD rendered directly above the prompt."""
        return Group(self._build_session_panel(), self._build_quick_commands_panel())

    def _show_status_hud(self):
        """Draw one measurable HUD instance so it can be erased without copies."""
        status_render = LiveRender(self._status_hud(), vertical_overflow="visible")
        self.console.print(status_render)
        return status_render

    def _erase_status_hud(self, status_render, user_input: str = ""):
        """Erase the prompt line and its immediately preceding HUD in place.

        LiveRender records its exact rendered height, including any table rows
        added by terminal-width wrapping. The prompt is outside that renderable,
        so erase its one or more wrapped rows first, then use Rich's own cursor
        restoration for the measured HUD. This is the same terminal-safe erase
        primitive used by Rich Live; no screen clear and no guessed panel height.
        """
        prompt_cells = cell_len("◈>: " + (user_input or ""))
        prompt_rows = max(1, (prompt_cells + self.console.width - 1) // self.console.width)
        erase_prompt = Control(
            ControlType.CARRIAGE_RETURN,
            *((ControlType.CURSOR_UP, 1),
              (ControlType.ERASE_IN_LINE, 2)) * prompt_rows
        )
        self.console.control(erase_prompt)
        self.console.control(status_render.restore_cursor())

    def _print_plain_status(self):
        """Fallback status summary for terminals where Rich is unavailable."""
        inject_enabled = getattr(self.agent, "inject_enabled", False)
        confidence_enabled = getattr(self.agent, "confidence_enabled", True)
        mem_stats = self.memory.get_stats()
        print(
            f"Status: Model={self.model} | Agent={self.agent_type.upper()} | "
            f"Temp={self.temperature:g} | Seed={self.seed} | "
            f"Inject={'ON' if inject_enabled else 'OFF'} | "
            f"Confidence={'ON' if confidence_enabled else 'OFF'} | "
            f"Auto-test={'ON' if self.autotest_enabled else 'OFF'} | "
            f"Memory={mem_stats['total']}"
        )
    
    def print_banner(self):
        if self.console:
            import time
            import shutil
            
            # Get terminal size for full screen effect
            term_size = shutil.get_terminal_size((80, 24))
            # Panel border (2 cells) + its horizontal padding (2 cells) leave
            # exactly columns-4 cells for the rain. Cap only very wide windows
            # so the animation remains fast, while ordinary windows stay full.
            width = max(10, min(term_size.columns - 4, 160))
            height = max(4, min(term_size.lines - 6, 18))
            
            # The banner lines we'll reveal through the rain (all 75 chars wide)
            banner_lines = [
                "╔═════════════════════════════════════════════════════════════════════════╗",
                "║  ██╗    ██╗██╗  ██╗ █████╗ ████████╗    ██╗███████╗                     ║",
                "║  ██║    ██║██║  ██║██╔══██╗╚══██╔══╝    ██║██╔════╝                     ║",
                "║  ██║ █╗ ██║███████║███████║   ██║ █████╗██║█████╗                       ║",
                "║  ██║███╗██║██╔══██║██╔══██║   ██║ ╚════╝██║██╔══╝                       ║",
                "║  ╚███╔███╔╝██║  ██║██║  ██║   ██║       ██║██║                          ║",
                "║   ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝       ╚═╝╚═╝                          ║",
                "║              M A C H I N E                                              ║",
                "║                                                                         ║",
                "║    ◈ Nested Learning Agent ◈ Recursive Self-Correction ◈ T=0.6 ◈        ║",
                "╚═════════════════════════════════════════════════════════════════════════╝",
            ]
            banner_height = len(banner_lines)
            banner_width = len(banner_lines[0])
            
            # Center position for banner
            start_row = max(0, (height - banner_height) // 2)
            start_col = max(0, (width - banner_width) // 2)
            
            # Full screen matrix rain
            matrix = MatrixRain(width, height)
            
            try:
                with Live(console=self.console, refresh_per_second=20, transient=True, screen=True) as live:
                    # Phase 1: Full matrix rain builds up (fills screen)
                    for frame in range(30):
                        matrix.step()
                        text = Text(no_wrap=True, overflow="crop")
                        for y in range(height):
                            for x in range(width):
                                char = matrix.chars[y % matrix.height][x % matrix.width]
                                if char != ' ':
                                    if y == matrix.columns[x % matrix.width] % matrix.height:
                                        text.append(char, style="bold bright_white")
                                    elif y == (matrix.columns[x % matrix.width] - 1) % matrix.height:
                                        text.append(char, style="bright_green")
                                    else:
                                        text.append(char, style="dim green")
                                else:
                                    text.append(random.choice(' ') if random.random() > 0.05 else random.choice('01'), style="dim green")
                            if y < height - 1:
                                text.append('\n')
                        live.update(Panel(text, border_style="bright_green", box=box.DOUBLE, 
                                         title="[bold bright_green]◈ INITIALIZING ◈[/bold bright_green]"))
                        time.sleep(0.04)
                    
                    # Phase 2: Banner emerges through the rain (eye trick - center first)
                    for frame in range(45):
                        matrix.step()
                        reveal_progress = frame / 35.0  # Goes past 1.0 intentionally
                        
                        text = Text(no_wrap=True, overflow="crop")
                        for y in range(height):
                            for x in range(width):
                                # Check if this position is part of the banner
                                banner_y = y - start_row
                                banner_x = x - start_col
                                in_banner = (0 <= banner_y < banner_height and 
                                           0 <= banner_x < banner_width)
                                
                                if in_banner and banner_x < len(banner_lines[banner_y]):
                                    banner_char = banner_lines[banner_y][banner_x]
                                    
                                    # Reveal from center outward (eye trick effect)
                                    center_x = banner_width // 2
                                    center_y = banner_height // 2
                                    dist = ((banner_x - center_x)**2 + (banner_y - center_y)**2) ** 0.5
                                    max_dist = ((banner_width//2)**2 + (banner_height//2)**2) ** 0.5
                                    normalized_dist = dist / max_dist
                                    
                                    # Wave-like reveal threshold
                                    reveal_threshold = reveal_progress - (normalized_dist * 0.6)
                                    
                                    if random.random() < reveal_threshold:
                                        # Show banner character with styling
                                        if banner_char in '║╔╗╚╝═':
                                            text.append(banner_char, style="bold bright_green")
                                        elif banner_char == '█':
                                            text.append(banner_char, style="bold bright_white")
                                        elif banner_char == '◈':
                                            text.append(banner_char, style="bold bright_cyan")
                                        elif banner_char.upper() in 'MACHINE':
                                            text.append(banner_char, style="bold bright_cyan")
                                        elif banner_char in '0123456789.v':
                                            text.append(banner_char, style="dim white")
                                        elif banner_char == ' ':
                                            text.append(' ')
                                        else:
                                            text.append(banner_char, style="white")
                                    else:
                                        # Matrix rain bleeding through (glitch effect)
                                        m_char = matrix.chars[y % matrix.height][x % matrix.width]
                                        if m_char != ' ' and random.random() < (1 - reveal_threshold * 0.5):
                                            text.append(m_char, style="dim green")
                                        else:
                                            text.append(' ')
                                else:
                                    # Outside banner - matrix rain fading to black
                                    fade = max(0, 1 - (reveal_progress * 0.8))
                                    m_char = matrix.chars[y % matrix.height][x % matrix.width]
                                    if m_char != ' ' and random.random() < fade:
                                        if y == matrix.columns[x % matrix.width] % matrix.height:
                                            text.append(m_char, style="bright_green" if fade > 0.5 else "dim green")
                                        else:
                                            text.append(m_char, style="dim green")
                                    else:
                                        text.append(' ')
                            if y < height - 1:
                                text.append('\n')
                        
                        live.update(Panel(text, border_style="bright_green", box=box.DOUBLE))
                        time.sleep(0.04)
                    
                    # Phase 3: Solid banner with subtle shimmer (settling)
                    for frame in range(20):
                        text = Text(no_wrap=True, overflow="crop")
                        for y in range(height):
                            for x in range(width):
                                banner_y = y - start_row
                                banner_x = x - start_col
                                in_banner = (0 <= banner_y < banner_height and 
                                           0 <= banner_x < banner_width)
                                
                                if in_banner and banner_x < len(banner_lines[banner_y]):
                                    banner_char = banner_lines[banner_y][banner_x]
                                    if banner_char in '║╔╗╚╝═':
                                        text.append(banner_char, style="bold bright_green")
                                    elif banner_char == '█':
                                        # Subtle pulse effect on the main text
                                        pulse = "bold bright_white" if (frame + banner_x) % 10 < 5 else "bright_white"
                                        text.append(banner_char, style=pulse)
                                    elif banner_char == '◈':
                                        text.append(banner_char, style="bold bright_cyan")
                                    elif banner_char.upper() in 'MACHINE':
                                        text.append(banner_char, style="bold bright_cyan")
                                    else:
                                        text.append(banner_char, style="white")
                                else:
                                    # Rare background shimmer
                                    if random.random() < 0.008:
                                        text.append(random.choice('01ｱｲ'), style="dim green")
                                    else:
                                        text.append(' ')
                            if y < height - 1:
                                text.append('\n')
                        
                        live.update(Panel(text, border_style="bright_green", box=box.DOUBLE))
                        time.sleep(0.05)
                        
            except Exception as e:
                # Fallback if Live screen mode fails
                pass
            
            # After animation, print the static banner. The status panels are
            # a single transient HUD owned by run(), immediately above input.
            self.console.print(BANNER)
        else:
            print(BANNER)
            self._print_plain_status()
            print(f"Dir: {self.working_dir}")
            print("/help commands | /autotest on|off | /prompt load file | /tools list | /quit exit\n")
    
    async def initialize(self) -> bool:
        self.print("[dim bright_cyan]⟳ Connecting to Ollama...[/dim bright_cyan]")
        
        if not HTTPX_AVAILABLE:
            self.print("[red]✗ Error: httpx not installed![/red]")
            self.print("[yellow]  Run: pip install httpx rich[/yellow]")
            return False
        
        if not await self.client.check_connection():
            self.print("[bold red]✗ Cannot connect to Ollama![/bold red]")
            self.print("[yellow]  Make sure Ollama is running: [bold]ollama serve[/bold][/yellow]")
            return False
        
        self.print("[bold bright_green]✓ Connected to Ollama[/bold bright_green]")
        # V45.1: probe once; gen_params is read at episode-save time.
        self.gen_params["ollama_version"] = await self.client.get_version()
        self.agent = create_agent(self.agent_type, self.client, self.working_dir, self.memory,
                                  judge_client=self.judge_client,
                                  gen_params=self.gen_params)

        # V21: the memory system is useless without an embedding model, and it
        # failed SILENTLY in V20 (episodes saved without vectors can never be
        # retrieved). Say it loudly, once, at startup.
        embeddings_ok = await self.memory.check_embeddings_available()
        mem_stats = self.memory.get_stats()
        # V45.8: a damaged store used to shrink memory in silence. Say it
        # as loudly as the missing-embedding-model warning below.
        _errs = getattr(self.memory, "load_errors", [])
        if _errs:
            self.print(
                f"[bold red]! EPISODE STORE DAMAGED:[/bold red] "
                f"{len(_errs)} line(s) in {self.memory.filepath.name} could "
                f"not be parsed and were SKIPPED "
                f"(loaded {mem_stats['total']}).\n"
                f"  First bad line: {_errs[0][0]} - {_errs[0][1][:120]}\n"
                f"  Those lessons are NOT available this session. Embedding "
                f"backfill is disabled while the file is damaged, so nothing "
                f"will overwrite them - repair or delete the bad line(s)."
            )
        if not embeddings_ok:
            self.print(
                "[bold yellow]! MEMORY DISABLED IN PRACTICE:[/bold yellow] no embedding "
                "model found in Ollama.\n"
                "  Episodes will be [bold]saved[/bold] but can [bold red]never be "
                "retrieved[/bold red] by future tasks.\n"
                "  Fix once with: [bold bright_white]ollama pull nomic-embed-text[/bold bright_white] "
                "(existing episodes will be backfilled automatically)."
            )
        elif mem_stats["total"] > 0 and mem_stats.get("with_embeddings", 0) < mem_stats["total"]:
            missing = mem_stats["total"] - mem_stats.get("with_embeddings", 0)
            self.print(
                f"[yellow]! {missing} stored episode(s) have no embedding - they will be "
                f"backfilled automatically on the next memory search.[/yellow]"
            )
        
        # Show tools with individual icons and colors
        tool_icons = {
            "file_read": ("📖", "cyan"),
            "file_write": ("📝", "green"),
            "str_replace": ("🔄", "yellow"),
            "bash": ("⚡", "bright_magenta"),
            "list_dir": ("📁", "blue"),
            "grep_search": ("🔍", "bright_cyan"),
        }
        
        tool_parts = []
        for name in self.agent.tools.keys():
            icon, color = tool_icons.get(name, ("🔧", "white"))
            tool_parts.append(f"[{color}]{icon} {name}[/{color}]")
        
        self.print(f"[bold bright_green]✓ {self.agent_type.title()} Agent Online[/bold bright_green]")
        self.print(f"  [dim]Tools:[/dim] {' '.join(tool_parts)}")
        
        # Show a beautiful tip box
        if self.console:
            tip_text = Text()
            if self.autotest_enabled:
                tip_text.append("🧪 ", style="bright_green")
                tip_text.append("AUTO-TEST ON: ", style="bold bright_green")
                tip_text.append('Every question will end with ', style="dim")
                tip_text.append('"test and fix it"', style="bold bright_cyan")
            else:
                tip_text.append("💡 ", style="bright_yellow")
                tip_text.append("PRO TIP: ", style="bold bright_yellow")
                tip_text.append('End prompts with ', style="dim")
                tip_text.append('"test and fix it"', style="bold bright_cyan")
                tip_text.append(' for automatic test→fix cycles', style="dim")
            self.console.print(Panel(
                tip_text,
                border_style="green" if self.autotest_enabled else "dim yellow",
                box=box.ROUNDED,
                padding=(0, 1)
            ))
        else:
            if self.autotest_enabled:
                self.print("[green]🧪 AUTO-TEST ON: every question will end with \"test and fix it\"[/green]")
            else:
                self.print("[dim]◈ Tip: End prompts with \"test and fix it\" for auto test→fix cycles[/dim]")
        
        # Ready indicator
        self.print("[bold bright_green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold bright_green]")
        self.print("[bold bright_white]      ◈ You pose it a What-If Build Request and it generates it... ◈[/bold bright_white]")
        self.print("[bold bright_green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold bright_green]\n")
        return True
    
    async def handle_command(self, cmd: str) -> bool:
        global VERBOSE
        # V25: lowercase only the command token - args keep their case
        # (/model Ornith:35B and /prompt MyTask.txt were silently mangled).
        raw_parts = cmd.split()
        c = raw_parts[0].lower()
        args = raw_parts[1:] if len(raw_parts) > 1 else []
        
        if c == "/help":
            self.print("\n[bold]Commands:[/bold]")
            for k, v in COMMANDS.items():
                self.print(f"  [cyan]{k}[/cyan] - {v}")
        elif c == "/models":
            await self._show_models()
        elif c == "/model":
            if args:
                self.model = args[0]
                self.client.model = args[0]
                self.agent.client.model = args[0]
                # V45.9: same defect class as the seed - a generation param
                # lived in four places and this command moved two, so the
                # episode named a model that did not do the work and the
                # graders kept running on the old one. Listed KNOWN-OPEN in
                # the V45.8 header; closed here because /seed fixed its twin.
                self.judge_client.model = args[0]
                self.gen_params["model"] = args[0]
                self.print(f"[green]✅ Switched to model: {args[0]}[/green]")
                self.print(f"[dim]   Builder, graders and episode record all moved.[/dim]")
            else:
                self.print(f"Current model: {self.model}")
                self.print("Usage: /model <model_name>")
                self.print("Recommended: ornith:35b")
        elif c == "/agent":
            if args and args[0].lower() in ["build", "plan"]:
                self.agent_type = args[0].lower()
                # V25: preserve /inject and /confidence across agent switches
                # (create_agent returns a fresh Agent with default toggles).
                prev_inject = self.agent.inject_enabled
                prev_conf = self.agent.confidence_enabled
                self.agent = create_agent(self.agent_type, self.client, self.working_dir, self.memory,
                                  judge_client=self.judge_client,
                                  gen_params=self.gen_params)
                self.agent.inject_enabled = prev_inject
                self.agent.confidence_enabled = prev_conf
                self.print(f"[green]✅ Switched to {self.agent_type} agent[/green]")
            else:
                self.print(f"Current: {self.agent_type}. Usage: /agent build|plan")
        elif c == "/clear":
            # Capture stats before clearing
            msg_count = len(self.agent.messages)
            tool_count = len(self.agent.trajectory)
            task_tokens = self.agent.total_prompt_tokens + self.agent.total_completion_tokens
            
            self.agent.reset()
            
            self.print(f"[green]✅ Conversation cleared[/green]")
            self.print(f"[dim]   Cleared: {msg_count} messages, {tool_count} tool calls, {task_tokens:,} task tokens[/dim]")
            session_total = self.agent.session_prompt_tokens + self.agent.session_completion_tokens
            self.print(f"[dim]   Session total: {session_total:,} tokens across {self.agent.session_task_count} tasks[/dim]")
            self.print(f"[dim]   Episode memory: preserved (use /memory clear to reset)[/dim]")
        elif c == "/tools":
            self.print("\n[bold bright_green]◈ Available Tools ◈[/bold bright_green]")
            for name, tool in self.agent.tools.items():
                icon = TOOL_ICONS.get(name, "🔧")
                color = TOOL_COLORS.get(name, "white")
                self.print(f"  [{color}]{icon} {name}[/{color}] - {tool.description[:200]}...")
        elif c == "/memory":
            stats = self.memory.get_stats()
            if args and args[0].lower() == "clear":
                # Clear memory
                if self.memory.filepath.exists():
                    self.memory.filepath.unlink()
                self.memory.episodes = []
                self.print("[yellow]⚠️ Episode memory cleared[/yellow]")
            else:
                # Show memory stats
                self.print("\n[bold magenta]◈ Episode Memory ◈[/bold magenta]")
                self.print(f"  [cyan]Location:[/cyan] {self.memory.filepath}")
                self.print(f"  [cyan]Total Episodes:[/cyan] {stats['total']}")
                self.print(f"  [cyan]Successes:[/cyan] [green]{stats['successes']}[/green]")
                self.print(f"  [cyan]Failures:[/cyan] [red]{stats['failures']}[/red]")
                self.print(f"  [cyan]With Embeddings:[/cyan] {stats.get('with_embeddings', 0)}")
                if self.memory.episodes:
                    self.print("\n  [dim]Recent episodes:[/dim]")
                    for ep in self.memory.episodes[-5:]:
                        outcome_color = "green" if ep.outcome == "success" else "yellow" if ep.outcome == "partial" else "red"
                        has_embed = "🧠" if ep.embedding else "  "
                        self.print(f"    {has_embed}[{outcome_color}]●[/{outcome_color}] {escape(ep.task[:200])}...")
                self.print("\n  [dim]Use /memory clear to reset[/dim]")
        elif c == "/inject":
            if args and args[0].lower() in ["on", "off"]:
                self.agent.inject_enabled = (args[0].lower() == "on")
                status = "[green]ON[/green]" if self.agent.inject_enabled else "[yellow]OFF (review mode)[/yellow]"
                self.print(f"[magenta]📚 Lesson injection: {status}[/magenta]")
                if self.agent.inject_enabled:
                    self.print("[dim]   Lessons will be validated by LLM and injected automatically[/dim]")
                else:
                    self.print("[dim]   Candidates will be shown for review but NOT injected[/dim]")
            else:
                status = "[green]ON[/green]" if self.agent.inject_enabled else "[yellow]OFF (review mode)[/yellow]"
                self.print(f"\n[bold magenta]◈ Lesson Injection ◈[/bold magenta]")
                self.print(f"  [cyan]Status:[/cyan] {status}")
                self.print(f"\n  [dim]Usage: /inject on|off[/dim]")
                self.print(f"  [dim]When OFF: Shows what WOULD be injected (for review)[/dim]")
                self.print(f"  [dim]When ON: LLM validates relevance, then injects[/dim]")
        elif c == "/confidence":
            if args and args[0].lower() in ["on", "off"]:
                self.agent.confidence_enabled = (args[0].lower() == "on")
                status = ("[green]ON (semantic)[/green]" if self.agent.confidence_enabled
                          else "[yellow]OFF (mechanical / V23)[/yellow]")
                self.print(f"[magenta]Semantic reflection: {status}[/magenta]")
                if self.agent.confidence_enabled:
                    self.print("[dim]   Model picks failure_class; LLM judge audits lesson causality;[/dim]")
                    self.print("[dim]   ungrounded lessons stored annotated (grounded=false), never templated;[/dim]")
                    self.print("[dim]   injection skips ungrounded and low-confidence (<0.7) lessons[/dim]")
                else:
                    self.print("[dim]   V23 behavior: regex classifies (model may not change it),[/dim]")
                    self.print("[dim]   lexical grounding gate, template fallback, confidence ignored[/dim]")
            else:
                status = ("[green]ON (semantic)[/green]" if self.agent.confidence_enabled
                          else "[yellow]OFF (mechanical / V23)[/yellow]")
                self.print(f"\n[bold magenta]Semantic Reflection[/bold magenta]")
                self.print(f"  [cyan]Status:[/cyan] {status}")
                self.print(f"\n  [dim]Usage: /confidence on|off[/dim]")
                self.print(f"  [dim]ON:  model-picked failure_class + LLM causality judge +[/dim]")
                self.print(f"  [dim]     annotate-don't-template + quality-filtered injection[/dim]")
                self.print(f"  [dim]OFF: V23 mechanical path (regex class, lexical gate, template)[/dim]")
        elif c == "/autotest":
            if args and args[0].lower() in ["on", "off"]:
                self.autotest_enabled = (args[0].lower() == "on")
                status = "[green]ON[/green]" if self.autotest_enabled else "[yellow]OFF[/yellow]"
                self.print(f"[bright_green]🧪 Auto-test: {status}[/bright_green]")
                if self.autotest_enabled:
                    self.print("[dim]   Every question will receive the literal phrase "
                               "‘test and fix it’ at its end before the agent sees it.[/dim]")
                else:
                    self.print("[dim]   Questions now pass to the agent unchanged.[/dim]")
            else:
                status = "[green]ON[/green]" if self.autotest_enabled else "[yellow]OFF[/yellow]"
                self.print("\n[bold bright_green]◈ Automatic Test → Fix ◈[/bold bright_green]")
                self.print(f"  [cyan]Status:[/cyan] {status}")
                self.print("\n  [dim]Usage: /autotest on|off[/dim]")
                self.print("  [dim]ON:  appends ‘test and fix it’ to each question[/dim]")
                self.print("  [dim]OFF: sends each question unchanged[/dim]")
                self.print("  [dim]The phrase is never duplicated when already present.[/dim]")
        elif c == "/seed":
            # V45.9: a seed lives in THREE places and they must move together
            # or the machine lies about itself:
            #   self.seed                  -> what the session panel reports
            #   client.options["seed"]     -> what Ollama actually samples with
            #                                 (OllamaClient.chat reads options
            #                                  live per request, so this takes
            #                                  effect on the very next call)
            #   gen_params["seed"]         -> what the episode records for replay
            # Moving one and not the others is the /model defect this pass also
            # fixes: an episode that names a coordinate nothing ran at.
            # judge_client is DELIBERATELY not touched - it stays pinned at
            # seed 7 / temp 0.0 so the measuring instrument never moves with
            # the experiment (the V45 contract).
            if not args:
                self.print(f"\n[bold bright_cyan]Builder Seed[/bold bright_cyan]")
                self.print(f"  [cyan]Current:[/cyan] [bold bright_cyan]{self.seed}[/bold bright_cyan]")
                live_seed = self.client.options.get("seed")
                rec_seed = self.gen_params.get("seed")
                if live_seed != self.seed or rec_seed != self.seed:
                    # Should be unreachable - say it loudly if it ever is.
                    self.print(f"  [bold red]! DESYNC:[/bold red] sampling with {live_seed}, "
                               f"recording {rec_seed}")
                self.print(f"  [cyan]Grader:[/cyan] [dim]7 (pinned, never moves)[/dim]")
                self.print(f"\n  [dim]Usage: /seed <number>   pin to an exact seed[/dim]")
                self.print(f"  [dim]       /seed random     draw a new one[/dim]")
                self.print(f"  [dim]Range: {SEED_MIN}-{SEED_MAX}. Same seed + same clean "
                           f"workspace + same Ollama build = same run.[/dim]")
                return True

            if args[0].lower() in ("random", "rand", "new"):
                new_seed = random.randint(SEED_MIN, SEED_MAX)
            else:
                new_seed = normalize_seed(args[0])
                if new_seed is None:
                    self.print(f"[red]Not a usable seed: {escape(args[0])}[/red]")
                    self.print(f"[dim]   Must be a whole number {SEED_MIN}-{SEED_MAX}, "
                               f"or 'random'. (-1 is the episode 'unrecorded' "
                               f"marker and is refused on purpose.)[/dim]")
                    return True

            old_seed = self.seed
            self.seed = new_seed
            self.client.options["seed"] = new_seed
            self.gen_params["seed"] = new_seed

            self.print(f"[green]🎲 Seed: [bold]{old_seed}[/bold] -> "
                       f"[bold bright_cyan]{new_seed}[/bold bright_cyan][/green]")
            self.print(f"[dim]   Applies to the next model call; recorded on the "
                       f"next episode. Graders stay at 7.[/dim]")
            # A seed only reproduces a run from the same starting state. If
            # history is already loaded, the next call's prompt is not the
            # prompt the seed was measured against - say so rather than let
            # him believe he pinned a replay he did not.
            if self.agent and self.agent.messages:
                self.print(f"[yellow]   ⚠ {len(self.agent.messages)} message(s) already in "
                           f"history - a seed reproduces a run from a CLEAN start. "
                           f"Use /clear first for a true replay.[/yellow]")
        elif c == "/temp":
            # Builder-only control. The judge deliberately remains pinned at
            # temperature 0.0 so changing the experiment does not also change
            # the measuring instrument. Keep the display, live Ollama options,
            # and episode record synchronized just like /seed does.
            if not args:
                self.print("\n[bold bright_magenta]Builder Temperature[/bold bright_magenta]")
                self.print(f"  [magenta]Current:[/magenta] "
                           f"[bold bright_magenta]{self.temperature:g}[/bold bright_magenta]")
                self.print("  [magenta]Grader:[/magenta] [dim]0.0 (pinned, never moves)[/dim]")
                self.print("\n  [dim]Usage: /temp <number>[/dim]")
                self.print("  [dim]Range: 0.0-2.0. Applies to the next builder call.[/dim]")
                return True

            if len(args) != 1:
                self.print("[red]Usage: /temp <number> (example: /temp 0.6)[/red]")
                return True

            try:
                new_temp = float(args[0])
            except (TypeError, ValueError):
                new_temp = -1.0

            # This comparison also rejects NaN and infinities.
            if not (0.0 <= new_temp <= 2.0):
                self.print(f"[red]Not a usable temperature: {escape(args[0])}[/red]")
                self.print("[dim]   Enter one number from 0.0 through 2.0.[/dim]")
                return True

            old_temp = self.temperature
            self.temperature = new_temp
            self.client.options["temperature"] = new_temp
            self.gen_params["temperature"] = new_temp

            self.print(f"[bright_magenta]🎯 Temperature: [bold]{old_temp:g}[/bold] -> "
                       f"[bold bright_magenta]{new_temp:g}[/bold bright_magenta][/bright_magenta]")
            self.print("[dim]   Applies to the next builder call and next episode. "
                       "Grader stays pinned at 0.0.[/dim]")
        elif c == "/verbose":
            self.verbose = not self.verbose
            VERBOSE = self.verbose
            self.print(f"[green]Verbose mode: {'ON' if self.verbose else 'OFF'}[/green]")
        elif c == "/prompt":
            if not args:
                self.print("[yellow]Usage: /prompt <filename>[/yellow]")
                self.print("[dim]   Load and execute a prompt from a text file[/dim]")
                self.print("[dim]   Example: /prompt task.txt[/dim]")
                return True
            
            filepath = Path(" ".join(args))  # Handle filenames with spaces
            if not filepath.exists():
                # Try relative to working dir
                filepath = Path(self.working_dir) / filepath
            
            if not filepath.exists():
                self.print(f"[red]❌ File not found: {args[0]}[/red]")
                return True
            
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    prompt_content = f.read().strip()
                
                if not prompt_content:
                    self.print("[yellow]⚠️ File is empty[/yellow]")
                    return True
                
                # Show what we're loading
                preview = prompt_content[:32000] + "..." if len(prompt_content) > 32000 else prompt_content
                self.print(f"[cyan]📄 Loading prompt from {filepath.name}:[/cyan]")
                self.print(f"[dim]{preview}[/dim]\n")
                
                # Process the loaded prompt
                await self.process_message(prompt_content)
                
            except Exception as e:
                self.print(f"[red]❌ Error reading file: {e}[/red]")
            
            return True
        elif c in ["/quit", "/exit", "/q"]:
            return False
        else:
            self.print(f"[red]Unknown: {c}[/red]. Type /help")
        return True
    
    async def _show_models(self):
        models = await self.client.list_models()
        self.print("\n[bold]Available Models:[/bold]")
        for m in models:
            marker = "✓" if m == self.model else " "
            self.print(f"  {marker} {m}")
    
    async def process_message(self, message: str):
        """
        Process a user message with persistent live dashboard.
        
        The dashboard stays at the bottom of the screen, continuously updating,
        while tool outputs print above it. This gives real-time visibility into
        what the agent is doing.
        """
        # V180.1: ONE shared transformation, before every rendering/fallback
        # branch and before Agent.process() performs memory search, task pinning,
        # iteration, reflection or episode capture. The agent therefore receives
        # exactly the message it would have received if the operator had typed
        # the phrase manually at the end. Slash commands never reach this method
        # (except /prompt's loaded task, which is intentionally a real question).
        message, autotest_appended = apply_autotest_directive(
            message, self.autotest_enabled)
        if autotest_appended:
            self.print("[bright_green]🧪 Auto-test appended: "
                       "[bold bright_cyan]test and fix it[/bold bright_cyan][/bright_green]")
        
        # Initialize the dashboard with REAL token tracking and memory stats
        dashboard = AgentStatusDisplay(
            max_iterations=self.agent.max_iterations,
            max_tokens=256000, # Default = 32768
            messages_getter=lambda: self.agent.messages,  # Real message access
            system_prompt_getter=lambda: self.agent.system_prompt,  # System prompt for accurate counting
            memory_stats=self.memory.get_stats().copy(),  # Copy current memory stats
            inject_enabled=self.agent.inject_enabled,  # Show inject status
            confidence_enabled=self.agent.confidence_enabled  # V24: show semantic mode
        )
        dashboard.log_activity("Starting processing")
        
        # Shared state for the refresh loop
        processing_complete = False
        final_response = None
        processing_error = None
        
        # ═══════════════════════════════════════════════════════════════════
        # CALLBACKS - These update the dashboard state
        # ═══════════════════════════════════════════════════════════════════
        
        def on_status(status_text):
            """Called when agent reports status (iteration changes)"""
            if "Iteration" in status_text:
                parts = status_text.split()
                for p in parts:
                    if "/" in p:
                        try:
                            current, total = p.split("/")
                            dashboard.start_iteration(int(current))
                        except:
                            pass
            # V45.5: "◈" marks a decision the MACHINE made on its own -
            # an outcome downgrade, a gate, a self-correction. Those are
            # exactly what an operator needs and were verbose-only.
            if self.verbose or status_text.startswith("◈"):
                dashboard.log_activity(status_text)
        
        def on_tool_call(name: str, args: dict):
            """Called when a tool is about to be executed"""
            dashboard.start_tool(name, args)
            
            # Print tool call panel ABOVE the dashboard
            icon = TOOL_ICONS.get(name, "🔧")
            color = TOOL_COLORS.get(name, "white")
            
            args_str = json.dumps(args, indent=2) if args else "{}"
            # V61.16: was `if len > 10000: args_str = args_str[:32000] + "..."`
            # - an ellipsis on anything over 10k even though nothing was cut
            # until 32k. The "..." on your snake file_write panel was that:
            # cosmetic, not a truncation. Trigger and cut are now the same
            # number and the message says how much is missing.
            if len(args_str) > PANEL_ARG_CHARS:
                args_str = (args_str[:PANEL_ARG_CHARS]
                            + f"\n... [{len(args_str) - PANEL_ARG_CHARS:,} more chars]")
            # V22.1: escape so JSON arrays / code in args keep their
            # [brackets] instead of Rich eating them as markup.
            args_str = escape(args_str)
            
            # FORCE dashboard refresh to show "Executing Tool" before tool blocks the event loop
            if hasattr(self, '_live') and self._live:
                self._live.update(dashboard.make_layout())
            
            # Use live.console.print to print above the live area
            if hasattr(self, '_live') and self._live:
                self._live.console.print(f"\n[bold {color}]{icon} [{len(dashboard.tool_history) + 1}] {name}[/bold {color}]")
                self._live.console.print(Panel(
                    f"[{color}]{args_str}[/{color}]", 
                    border_style=color, 
                    box=box.ROUNDED
                ))
            elif self.console:
                self.console.print(f"\n[bold {color}]{icon} [{len(dashboard.tool_history) + 1}] {name}[/bold {color}]")
                self.console.print(Panel(f"[{color}]{args_str}[/{color}]", border_style=color, box=box.ROUNDED))
        
        def on_tool_result(name: str, result: str, success: bool = None):
            """Called when a tool execution completes.

            V21: `success` now arrives from Agent._detect_tool_success (the same
            verdict recorded in the trajectory). The old prefix check remains only
            as a fallback for callers that do not pass it.
            """
            if success is None:
                is_error = (
                    result.startswith("Error:") or
                    result.startswith("❌") or
                    result.startswith("Access Denied:")
                )
                success = not is_error
            
            # Update dashboard
            result_preview = result[:5000] + "..." if len(result) > 5000 else result
            dashboard.finish_tool(name, success, result_preview)
            
            # FORCE dashboard refresh to show result status
            if hasattr(self, '_live') and self._live:
                self._live.update(dashboard.make_layout())
            
            # Prepare display preview (don't truncate file_read too much for model)
            if name == "file_read":
                display_preview = result
            elif name == "str_replace" and result.startswith("Error:"):
                display_preview = result
            else:
                display_preview = result[:10000] + "..." if len(result) > 10000 else result
            # V22.1: escape - file/bash content full of [brackets] was
            # swallowed as Rich markup in these panels (logs showed lines
            # like 'self.obstacles =' with the comprehension invisible),
            # and an orphan closing tag like [/i] in output would CRASH.
            display_preview = escape(display_preview)
            
            # Print result panel ABOVE the dashboard
            icon = "✓" if success else "✗"
            border_color = "green" if success else "red"
            
            if hasattr(self, '_live') and self._live:
                self._live.console.print(Panel(
                    display_preview,
                    title=f"[{border_color}]{icon} {name}[/{border_color}]",
                    border_style=border_color,
                    box=box.ROUNDED
                ))
            elif self.console:
                self.console.print(Panel(
                    display_preview,
                    title=f"[{border_color}]{icon} {name}[/{border_color}]",
                    border_style=border_color,
                    box=box.ROUNDED
                ))
        
        def on_lessons_found(candidates: list):
            """Called when embedding search finds candidates (before LLM validation)"""
            dashboard.set_lessons_found(candidates)
            
            # Print candidates panel - this is REVIEW mode, shows what's available
            if hasattr(self, '_live') and self._live:
                inject_status = "[green]will validate & inject[/green]" if self.agent.inject_enabled else "[yellow]review only (injection OFF)[/yellow]"
                candidates_text = f"[bold magenta]🔍 Found {len(candidates)} candidate episodes[/bold magenta]\n"
                candidates_text += f"[dim]Mode: {inject_status}[/dim]\n\n"
                for score, ep in candidates[:50]:
                    sim_pct = int(score * 100)
                    candidates_text += f"[dim]{sim_pct}%[/dim] {escape(ep.task[:150])}...\n"
                    candidates_text += f"    [italic dim]→ {escape(ep.reflection[:300])}...[/italic dim]\n"
                
                if not self.agent.inject_enabled:
                    candidates_text += "\n[dim]💡 Use /inject on to enable auto-injection[/dim]"
                
                self._live.console.print(Panel(
                    candidates_text.strip(),
                    title="[magenta]◈ Memory Search ◈[/magenta]",
                    border_style="magenta",
                    box=box.ROUNDED
                ))
            
            # Force refresh
            if hasattr(self, '_live') and self._live:
                self._live.update(dashboard.make_layout())
        
        def on_lessons_injected(episodes: list):
            """Called when lessons are actually injected (after LLM validation)"""
            dashboard.set_lessons_injected(episodes)
            
            # Print injection confirmation
            if hasattr(self, '_live') and self._live:
                inject_text = f"[bold green]✓ LLM validated {len(episodes)} lessons for injection[/bold green]\n\n"
                for ep in episodes:
                    inject_text += f"[green]•[/green] {escape(ep.reflection[:500])}...\n"
                
                self._live.console.print(Panel(
                    inject_text.strip(),
                    title="[green]◈ Lessons Injected ◈[/green]",
                    border_style="green",
                    box=box.ROUNDED
                ))
            
            # Force refresh
            if hasattr(self, '_live') and self._live:
                self._live.update(dashboard.make_layout())
        
        def on_episode_saved(episode):
            """Called when episode is saved after task completion"""
            dashboard.set_episode_saved(episode)
            
            # Print episode saved panel - token cost is now REAL (no tilde)
            if hasattr(self, '_live') and self._live:
                outcome_color = "green" if episode.outcome == "success" else "yellow" if episode.outcome == "partial" else "red"
                # Show real token count (no tilde) if we have real data
                token_label = f"Token cost: {episode.token_cost:,}" if dashboard.using_real_tokens else f"Token cost: ~{episode.token_cost:,}"
                self._live.console.print(Panel(
                    f"[bold {outcome_color}]Outcome: {episode.outcome.upper()}[/bold {outcome_color}]\n"
                    f"[dim]Reflection:[/dim] {escape(episode.reflection[:300])}...\n"
                    f"[dim]Iterations: {episode.iterations} | {token_label}[/dim]",
                    title="[cyan]◈ Episode Saved ◈[/cyan]",
                    border_style="cyan",
                    box=box.ROUNDED
                ))
        
        def on_tokens(prompt_tokens: int, completion_tokens: int):
            """Called after each Ollama response with REAL token counts"""
            dashboard.set_real_tokens(prompt_tokens, completion_tokens)
        
        # ═══════════════════════════════════════════════════════════════════
        # BACKGROUND REFRESH TASK - Keeps dashboard animating
        # ═══════════════════════════════════════════════════════════════════
        
        async def refresh_dashboard(live: Live):
            """Background task that refreshes the dashboard at ~10fps"""
            # V30.1: re-applied the V26 resize fix - it never made it into
            # the V28/V30 lineage, so the stacked ◈ WHAT-IF MACHINE ◈ frames
            # came back. Clear once per terminal size change so Live repaints
            # from a clean screen instead of scroll-stacking frames.
            last_size = live.console.size
            while not processing_complete:
                try:
                    if live.console.size != last_size:
                        last_size = live.console.size
                        live.console.clear()
                    live.update(dashboard.make_layout())
                    await asyncio.sleep(0.1)  # 10fps refresh
                except Exception:
                    break
        
        # ═══════════════════════════════════════════════════════════════════
        # MAIN PROCESSING WITH LIVE DASHBOARD
        # ═══════════════════════════════════════════════════════════════════
        
        if self.console:
            self.console.print("")  # Blank line before dashboard
            
            try:
                # Create Live context - dashboard stays at bottom
                with Live(
                    dashboard.make_layout(),
                    console=self.console,
                    refresh_per_second=10,
                    transient=False,  # Keep visible, don't clear
                    # V30.1: "visible" scroll-reprints every frame the moment
                    # the dashboard is taller than the terminal - that alone
                    # stacks banner frames in a short window, no resize
                    # needed. "crop" is the V26 fix, re-applied.
                    vertical_overflow="crop"
                ) as live:
                    # Store reference for callbacks to use
                    self._live = live
                    
                    # Start background refresh task
                    refresh_task = asyncio.create_task(refresh_dashboard(live))
                    
                    try:
                        # Run the actual agent processing
                        dashboard.set_phase("Processing", "sending to agent...")
                        final_response = await self.agent.process(
                            message,
                            on_tool_call=on_tool_call,
                            on_tool_result=on_tool_result,
                            on_status=on_status,
                            on_lessons_found=on_lessons_found,
                            on_lessons_injected=on_lessons_injected,
                            on_episode_saved=on_episode_saved,
                            on_tokens=on_tokens  # REAL token tracking
                        )
                        dashboard.set_complete()
                        
                    except Exception as e:
                        dashboard.set_error(str(e))
                        processing_error = e
                        
                    finally:
                        # Stop the refresh task
                        processing_complete = True
                        refresh_task.cancel()
                        try:
                            await refresh_task
                        except asyncio.CancelledError:
                            pass
                        
                        # Final dashboard update
                        live.update(dashboard.make_layout())
                    
                    # Clear live reference
                    self._live = None
                
                # ═══════════════════════════════════════════════════════════
                # EXECUTION SUMMARY - Printed after Live context ends
                # ═══════════════════════════════════════════════════════════
                
                if processing_error:
                    self.console.print(Panel(
                        f"[bold red]{escape(str(processing_error))}[/bold red]",
                        title="[red]◈ Error ◈[/red]",
                        border_style="red",
                        box=box.DOUBLE
                    ))
                    if self.verbose:
                        import traceback
                        traceback.print_exc()
                else:
                    # Success summary
                    success_count = sum(1 for _, s, _ in dashboard.tool_history if s)
                    fail_count = len(dashboard.tool_history) - success_count
                    
                    # Build episode info line - show candidates found vs injected
                    episode_line = ""
                    if dashboard.lessons_candidates > 0:
                        if dashboard.lessons_injected > 0:
                            episode_line += f"[green]📚 {dashboard.lessons_injected}/{dashboard.lessons_candidates} injected[/green] "
                        else:
                            episode_line += f"[magenta]📚 {dashboard.lessons_candidates} found[/magenta] "
                    if dashboard.episode_saved:
                        episode_line += f"[cyan]💾 saved[/cyan]"
                    if not episode_line:
                        episode_line = "[dim]No memory activity[/dim]"
                    
                    # Token summary - show REAL if available
                    total_toks = dashboard.get_total_tokens()
                    if dashboard.using_real_tokens:
                        token_line = f"[green]{total_toks:,}[/green] [dim](prompt: {dashboard.total_prompt_tokens:,} + completion: {dashboard.total_completion_tokens:,})[/dim]"
                    else:
                        token_line = f"[dim]~{total_toks:,} (estimated)[/dim]"
                    
                    summary_content = (
                        f"[bold bright_cyan]◈ Tools Used:[/bold bright_cyan] {len(dashboard.tool_history)}\n"
                        f"[bold bright_cyan]◈ Iterations:[/bold bright_cyan] {self.agent.iteration_count}\n"
                        f"[bold bright_cyan]◈ Results:[/bold bright_cyan] [green]✓ {success_count}[/green] [red]✗ {fail_count}[/red]\n"
                        f"[bold bright_cyan]◈ Tokens:[/bold bright_cyan] {token_line}\n"
                        f"[bold bright_cyan]◈ Memory:[/bold bright_cyan] {episode_line}\n"
                        f"[bold bright_cyan]◈ Time:[/bold bright_cyan] {dashboard.get_elapsed()}\n"
                        f"[bold bright_cyan]◈ Status:[/bold bright_cyan] [bright_green]Complete[/bright_green]"
                    )
                    
                    self.console.print(Panel(
                        summary_content,
                        title="[bold bright_green]◈ Execution Summary ◈[/bold bright_green]",
                        border_style="bright_green",
                        box=box.DOUBLE
                    ))
                    
                    # Print response
                    self.console.print("\n[bold bright_white]◈ Response:[/bold bright_white]")
                    self.console.print(Markdown(final_response))
                    
            except Exception as e:
                # Fallback if Live fails entirely
                self.console.print(f"[red]Dashboard error: {e}[/red]")
                self.console.print("[yellow]Falling back to simple mode...[/yellow]")
                
                # Simple fallback processing
                response = await self.agent.process(
                    message,
                    on_tool_call=lambda n, a: self.console.print(f"[cyan]Tool: {n}[/cyan]"),
                    on_tool_result=lambda n, r, s=None: self.console.print(f"[{'green' if (s is None or s) else 'red'}]Result: {r[:5000]}...[/{'green' if (s is None or s) else 'red'}]"),
                    on_status=lambda s: None,
                    on_lessons_found=lambda c: self.console.print(f"[magenta]Found {len(c)} candidates[/magenta]"),
                    on_lessons_injected=lambda e: self.console.print(f"[green]Injected {len(e)} lessons[/green]"),
                    on_episode_saved=lambda ep: self.console.print(f"[cyan]Episode saved: {ep.outcome}[/cyan]"),
                    on_tokens=lambda p, c: self.console.print(f"[dim]Tokens: {p:,} prompt + {c:,} completion[/dim]")
                )
                self.console.print(Markdown(response))
        
        else:
            # Non-Rich fallback (no console)
            self.print("[dim]Processing...[/dim]")
            
            def simple_tool_call(name, args):
                print(f"Tool: {name}")
            
            def simple_tool_result(name, result, success=None):
                marker = "" if success is None else ("[OK] " if success else "[FAIL] ")
                print(f"{marker}Result: {result[:5000]}...")
            
            def simple_tokens(prompt_toks, completion_toks):
                print(f"Tokens: {prompt_toks:,} prompt + {completion_toks:,} completion")
            
            response = await self.agent.process(
                message,
                on_tool_call=simple_tool_call,
                on_tool_result=simple_tool_result,
                on_status=lambda s: None,
                on_lessons_found=lambda c: print(f"Found {len(c)} candidate episodes"),
                on_lessons_injected=lambda e: print(f"Injected {len(e)} lessons"),
                on_episode_saved=lambda ep: print(f"Episode saved: {ep.outcome}"),
                on_tokens=simple_tokens
            )
            print(f"\nAssistant: {response}")
    
    async def run(self, prompt: str = None):
        if prompt:
            await self.process_message(prompt)
            return
        
        while True:
            status_render = None
            hud_visible = False
            user_input = ""
            try:
                if self.console:
                    # V180.5: there is exactly one idle HUD. It is measured as
                    # it renders, then removed together with the submitted input
                    # line before any command output or task dashboard begins.
                    status_render = self._show_status_hud()
                    hud_visible = True
                    user_input = Prompt.ask(
                        "[bold bright_green]◈>[/bold bright_green]",
                        console=self.console)
                    self._erase_status_hud(status_render, user_input)
                    hud_visible = False
                else:
                    user_input = input("\n> ")

                if not user_input.strip():
                    continue

                # The terminal already echoed this line inside the transient
                # HUD. Reprint it once after erasing that HUD so command/task
                # history remains readable without retaining a stale panel.
                if self.console:
                    self.print(f"[bold bright_green]◈>:[/] {escape(user_input)}")

                if user_input.startswith("/"):
                    if not await self.handle_command(user_input):
                        break
                    continue
                await self.process_message(user_input)
            except KeyboardInterrupt:
                if hud_visible and status_render is not None:
                    self._erase_status_hud(status_render, user_input)
                self.print("\n[yellow]Use /quit to exit[/yellow]")
            except EOFError:
                if hud_visible and status_render is not None:
                    self._erase_status_hud(status_render, user_input)
                break
        
        # Goodbye with matrix fade
        if self.console:
            import time
            matrix = MatrixRain(40, 3)
            try:
                with Live(console=self.console, refresh_per_second=15, transient=True) as live:
                    for i in range(12):
                        matrix.step()
                        live.update(Panel(
                            Group(
                                Align.center(matrix.render()),
                                Align.center(Text("◈ DISCONNECTING ◈", style="bold bright_cyan"))
                            ),
                            border_style="dim green",
                            box=box.SIMPLE
                        ))
                        time.sleep(0.06)
            except Exception:
                pass
            self.console.print("\n[bold bright_green]◈ What-if Machine terminated ◈[/bold bright_green]")
        else:
            self.print("\n[cyan]Goodbye! 👋[/cyan]")


async def main():
    parser = argparse.ArgumentParser(description="What-if Machine - Nested Learning Agent, Evidence-Tuned")
    parser.add_argument("prompt", nargs="?", help="Single prompt (non-interactive)")
    parser.add_argument("--model", "-m", default="ornith:35b", help="Ollama model")
    parser.add_argument("--agent", "-a", choices=["build", "plan"], default="build", help="Agent type")
    parser.add_argument("--url", "-u", default="http://localhost:11434", help="Ollama URL")
    parser.add_argument("--dir", "-d", default=None, help="Working directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show debug info")
    parser.add_argument("--autotest", action="store_true",
                        help="Append 'test and fix it' to every question in this session")
    parser.add_argument("--log", default=None, metavar="FILE",
                        help="Write the uncapped run log here instead of "
                             "whatif_logs/ beside this script")
    parser.add_argument("--no-log", action="store_true",
                        help="Disable the uncapped run log (it is ON by default)")
    parser.add_argument("--temp", "-t", type=float, default=0.6,
                        help="Builder temperature (default 0.6). Graders stay pinned at 0.0.")
    # V45.9: same guard as /seed. Was type=int and nothing else, so
    # `--seed -1` pinned the builder to the Episode "unrecorded" sentinel and
    # every episode of that run claimed it had no seed. Raise rather than
    # fall back to random - a typo'd seed must not silently become a
    # different run than the one he asked to replay.
    def _seed_arg(v):
        n = normalize_seed(v)
        if n is None:
            raise argparse.ArgumentTypeError(
                f"seed must be a whole number {SEED_MIN}-{SEED_MAX} (got {v!r}); "
                f"-1 is the episode 'unrecorded' marker and is not a seed")
        return n

    parser.add_argument("--seed", type=_seed_arg, default=None,
                        help=f"Builder seed ({SEED_MIN}-{SEED_MAX}). Omit for a random one "
                             "(still recorded on the episode). Pass a past episode's seed "
                             "to replay that run - requires the same clean workspace and "
                             "Ollama build. Changeable mid-session with /seed.")
    
    args = parser.parse_args()

    # V61.20: on by default. Started BEFORE the CLI so startup, connection
    # failures and the banner are in the file too - a run that dies during
    # initialize() is exactly the one worth having a log of.
    _logpath = init_run_log(args.log, enabled=not args.no_log)
    if _logpath:
        # printed unconditionally, not via debug_print: the operator needs the
        # path whether or not -v is on, and "where is the log" should never be
        # a question.
        print(f"📝 Run log: {_logpath}")
        debug_print(f"RUN LOG: {_logpath} (uncapped; screen capped at "
                    f"{DEBUG_MAX_CHARS:,} chars per entry)")

    cli = CLI(args.model, args.agent, args.url, args.dir, args.verbose,
              temperature=args.temp, seed=args.seed, autotest=args.autotest)
    
    if not args.prompt:
        cli.print_banner()
    
    if not await cli.initialize():
        sys.exit(1)
    
    await cli.run(args.prompt)


if __name__ == "__main__":
    asyncio.run(main())
