#!/usr/bin/env python
"""
What-if Machine v25 - Nested Learning Agent for the Terminal
Enhanced with Matrix-themed visuals, recursive self-correction, and episode memory

NEW IN V61.6 - THE TWO str_replace DEFECTS FOUND BY AUDIT
(this file: WHAT-IF_MACHINE_V61_3.py)

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
import re
import json
import difflib          # V61.1: was imported inside two functions only; the
                        # assertion-relaxation detector needs it at module scope.
import asyncio
import argparse
import subprocess
import random
import time
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

def debug_print(msg, data=None):
    """Print debug info when verbose mode is on"""
    if VERBOSE:
        print(f"\n[DEBUG] {msg}")
        if data:
            if isinstance(data, (dict, list)):
                print(json.dumps(data, indent=2, default=str)[:5000])
            else:
                print(str(data)[:500])

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
    
    CHARS = "アイウWオNキクHコMシスTソタFツテトナ-ヌネノAヒフCホマミムメモヤユEラIルレAワン01"
    
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
        text = Text()
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
        self.set_phase("Error", message[:100])
        
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
    try:
        return Path(p).resolve() == MACHINE_SELF
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


def _assert_bodies(text: str) -> list:
    """Every assert in `text`, message stripped, whitespace normalised."""
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
    old_a, new_a = _assert_bodies(old_str), _assert_bodies(new_str)
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
    if "assert" not in (old_str or ""):
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
        r = subprocess.run(["node", "--check"], input=source,
                           capture_output=True, text=True, timeout=30)
    except Exception:
        return None
    if r.returncode == 0:
        return None
    err = (r.stderr or r.stdout).strip()
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
EXPERIMENTAL = {
    # Ollama options. Reasoned from the API docs, NEVER exercised against
    # ornith-vision on your box. If a run started behaving differently after
    # V61.1, this is the first thing to suspect and it is why it is off.
    "ollama_keep_alive": False,   # pin the model in VRAM between turns
    "ollama_num_keep": False,     # protect the prompt head from context shift

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
    )
    if not hits:
        return syn
    where = ", ".join(str(n) for n in hits[:25]) + (" ..." if len(hits) > 25 else "")
    return syn + (
        f"\n⚠ WARNING: {len(hits)} silent exception swallower(s) at line(s) {where} "
        f"(`except ...: pass` / suppress). Errors inside them are INVISIBLE to you and "
        f"to --test: a feature can die in there and the self-test still passes. "
        f"file_read those lines; print the exception or let it raise, and make your "
        f"--test assert the swallowed feature actually works. (They span two lines, "
        f"so a line-based grep_search for 'except.*pass' will find NOTHING - use "
        f"these line numbers instead.)"
    )


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
                    + swallow_warning(path, content))

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

                        return (
                            f"✅ Successfully replaced (indent-tolerant) line in {path} "
                            f"(matched by stripped equality)."
                            + swallow_warning(path, new_content)
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

                    prefix, rel = "", 0
                    shifted = []
                    for k, l in enumerate(new_block):
                        if k < nlines and k < len(old_lines_n):
                            fl = c_lines[i + k]
                            prefix = fl[:len(fl) - len(fl.lstrip())]
                            rel = _cols(l) - _cols(old_lines_n[k])
                        if not l.strip():
                            shifted.append(l)
                        else:
                            shifted.append(prefix + " " * max(0, rel) + l.lstrip())
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
                    return (
                        f"✅ Successfully replaced block in {path} at line {i + 1} "
                        f"(matched ignoring per-line leading/trailing whitespace - your "
                        f"old_str differed only by invisible whitespace, most often a "
                        f"trailing space). Each new line was re-indented to match the "
                        f"line it replaced, so a block spanning two indent levels keeps "
                        f"both"
                        + (f", re-indented by {delta:+d} spaces to match the file."
                           if delta else ".")
                        + swallow_warning(path, new_content)
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
            
            return (f"✅ Successfully replaced string in {path}"
                    + swallow_warning(path, new_content))
        except SecurityError as e:
            return str(e)
        except Exception as e:
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
            return output.strip() or "(No output)"
        except Exception as e:
            return f"Error: {str(e)}"


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


def get_tool_schemas(tools: dict) -> list:
    return [tool.to_schema() for tool in tools.values()]


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
            thinking_log=d.get("thinking_log")
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
    NUM_KEEP_MAX = 32768
    NUM_KEEP_CTX_FRACTION = 0.25
    # 30 min for complex generations. The timeout message quotes THIS.
    REQUEST_TIMEOUT_S = 1800.0

    def __init__(self, base_url: str = "http://localhost:11434", model: str = "ornith-vision", options: dict = None):
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
            f"Messages: showing last 200 of {len(messages)}"
            + (f" ({len(messages) - 200} earlier hidden):" if len(messages) > 200 else ":"),
            messages[-200:] if len(messages) > 200 else messages)
        
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
                thinking=(msg.get("thinking") or "")  # V30.9: capture, don't drop
            )
        
        return ChatResponse(
            content="", 
            raw_response=data,
            prompt_tokens=data.get("prompt_eval_count", 0),
            completion_tokens=data.get("eval_count", 0)
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
    
    async def execute(self, tool_call: ToolCall) -> dict:
        if tool_call.name not in self.tools:
            return {"tool_name": tool_call.name, "content": f"Unknown tool: {tool_call.name}"}
        try:
            tool = self.tools[tool_call.name]
            # V23: filter arguments to the tool's declared schema. Models
            # trained on richer tool APIs attach extras - ornith:35b passed
            # a 'description' kwarg to bash, which crashed the call with
            # "unexpected keyword argument" and burned an iteration.
            args = tool_call.arguments if isinstance(tool_call.arguments, dict) else {}
            declared = set(tool.parameters.get("properties", {}).keys())
            dropped = sorted(set(args) - declared)
            if dropped:
                args = {k: v for k, v in args.items() if k in declared}
                debug_print(f"Dropped unsupported {tool_call.name} argument(s): {dropped}")
            result = await tool.execute(**args)
            return {"tool_name": tool_call.name, "content": str(result)}
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
3. Verify with: python <file>.py --test  (fast, exit code tells the truth)
4. Only after --test passes, you can continue with task.
5. PARSING IS NOT RUNNING, AND THIS IS THE MOST COMMON WAY A BUILD SHIPS
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


@dataclass
class Message:
    role: str
    content: str
    tool_calls: list = None
    tool_name: str = None
    tool_call_id: str = None
    
    def to_dict(self) -> dict:
        d = {"role": self.role, "content": self.content}
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
        exit_m = re.search(r'Exit code:\s*(\d+)', text)
        if exit_m:
            verdict = exit_m.group(1) == "0"
            debug_print(f"_is_test_pass: phrase '{matched}' found, "
                        f"exit code {exit_m.group(1)} -> {verdict}")
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
    def _is_test_fail(cls, content: str) -> bool:
        """V38.1: True iff a bash result shows a self-test FAILING - a strong,
        unambiguous failure marker (an assertion, a unittest failure summary,
        an explicit SELF-TEST FAIL), or a nonzero exit code from a run whose
        output is a test. Deliberately narrow: it drives the one-time
        SELF-AWARENESS retraction, so it must not fire on incidental uses of
        the word 'fail'. Zero-count / negated markers ('no tests failed') are
        excluded by the clause check."""
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
        m = re.search(r'Exit code:\s*(\d+)', text)
        if m and m.group(1) != "0" and "TEST" in up:
            return True
        return False

    def _notify(self, msg: str):
        """V45.5: report a mechanism decision to the dashboard. Visible in
        normal mode via the ◈ prefix. Never raises - a notifier that
        explodes must not take the run with it."""
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
            api_messages = ([{"role": "system", "content": self.system_prompt}]
                            + [m.to_dict() for m in self.messages])
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
        last_py_edit_path = ""
        last_ok_bash = None       # trajectory step of the latest successful bash
        completion_nudged = False
        # V30.7: escalating breaker for the miss->overwrite->delete spiral.
        # Counts consecutive failed edits / blocked destructive writes; the
        # nudge gets firmer and names the spiral by name once it repeats.
        stuck_edit_streak = 0
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
            
            api_messages = [{"role": "system", "content": self.system_prompt}] + [m.to_dict() for m in self.messages]
            
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
                    self.messages.append(Message(role="assistant", content=response.content))
                    final_response = response.content
                    outcome = "failure"
                    break
            
            if response.tool_calls:
                empty_streak = 0
                # V30.9: record the model's reasoning channel for this
                # response BEFORE its tool steps, keyed to the next step
                # number. Episode-review only - deliberately NOT added to
                # self.messages, so it is never fed back to the model.
                if response.thinking:
                    self.thinking_log.append(
                        (len(self.trajectory) + 1, response.thinking[:8000])
                    )
                # Model wants to use tools
                self.messages.append(Message(
                    role="assistant", 
                    content=response.content or "",
                    tool_calls=response.tool_calls
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
                    args_summary = str(tc.arguments)[:32000]
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
                    if tc.name == "bash":
                        try:
                            _cmd = str((tc.arguments or {}).get("command", ""))
                            for _b in _scripts_named_in(_cmd):
                                self._script_runs[_b] = (len(self.trajectory),
                                                         bool(is_success))
                        except Exception as e:
                            debug_print(f"script-run bookkeeping failed: {e}")
                    # V61.2: the red window (V45.11 shape, ported). It opens on
                    # a bash result that is a recognised test FAILURE and stays
                    # open until one actually PASSES - not until the next
                    # successful command of any kind, which is what made the
                    # V45.8 adjacent-step gate blind one step after a failure.
                    if tc.name == "bash":
                        _rcw = str(result.get("content", ""))
                        if self._is_test_fail(_rcw):
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
                    # V30.2: verification-debt bookkeeping for the completion
                    # gate - which came later, the last .py edit or the last
                    # successful command?
                    step_no = len(self.trajectory)
                    if is_success and tc.name in ("file_write", "str_replace"):
                        p = str(tc.arguments.get("path", ""))
                        # V45.7: the gate's principle is "you edited a
                        # file and never ran anything after it" - that was
                        # never about Python. An .html build that quits
                        # mid-way used to sail straight through.
                        if p.lower().endswith(VERIFIABLE_EXT):
                            last_py_edit = step_no
                            last_py_edit_path = p
                    if is_success and tc.name == "bash":
                        last_ok_bash = step_no
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
                            and self._is_test_fail(result["content"])):
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
                            tgt = last_py_edit_path or "the file"
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
                    # Model failed to act - resend same context (don't pollute history)
                    continue
                # V30.2: one-shot untested-edit gate. In the snake_game run
                # the model's final patch was NEVER tested - all 7 bash calls
                # in the run failed - and it declared success anyway; the
                # episode then stored a fabricated "final run completed
                # without errors". Mechanical check, no LLM: if a successful
                # .py edit postdates the last successful bash (or no bash
                # ever succeeded), bounce ONCE with explicit instructions,
                # then accept the next completion regardless (loop-proof).
                if (not completion_nudged and last_py_edit is not None
                        and (last_ok_bash is None or last_ok_bash < last_py_edit)):
                    completion_nudged = True
                    self._notify(f"COMPLETION GATE: bounced - "
                                 f"{last_py_edit_path or 'a .py file'} was "
                                 f"edited but never run since")
                    self.messages.append(Message(role="assistant", content=response.content))
                    self.messages.append(Message(role="user", content=(
                        f"⚠ COMPLETION CHECK (one-time): your latest edit to "
                        f"{last_py_edit_path or 'a .py file'} has NEVER been verified - "
                        f"no command has succeeded since that edit"
                        + (", and no command succeeded in this entire run"
                           if last_ok_bash is None else "")
                        + f". Run: python {last_py_edit_path or '<file>'} --test  "
                        f"and fix what fails. Only finish after it passes, or "
                        f"explicitly label the affected features 'written but "
                        f"unverified' in your final summary."
                    )))
                    continue
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
                                                     content=response.content))
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
                thinking_log=self.thinking_log or None  # V30.9: review-only
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
        formatted_prompt = BUILD_PROMPT.format(
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

BANNER = """
[bold bright_green]╔══════════════════════════════════════════════════════════════════════════════╗[/]
[bold bright_green]║[/]                                                                              [bold bright_green]║[/]
[bold bright_green]║[/]  [bold bright_white]██╗    ██╗[/][bold green]██╗  ██╗[/][bold bright_cyan] █████╗ [/][bold cyan]████████╗[/]    [bold bright_magenta]██╗[/][bold magenta]███████╗[/]               [bold bright_green]║[/]
[bold bright_green]║[/]  [bold bright_white]██║    ██║[/][bold green]██║  ██║[/][bold bright_cyan]██╔══██╗[/][bold cyan]╚══██╔══╝[/]    [bold bright_magenta]██║[/][bold magenta]██╔════╝[/]               [bold bright_green]║[/]
[bold bright_green]║[/]  [bold bright_white]██║ █╗ ██║[/][bold green]███████║[/][bold bright_cyan]███████║[/][bold cyan]   ██║[/] [bold yellow]█████╗[/][bold bright_magenta]██║[/][bold magenta]█████╗[/]                [bold bright_green]║[/]
[bold bright_green]║[/]  [bold bright_white]██║███╗██║[/][bold green]██╔══██║[/][bold bright_cyan]██╔══██║[/][bold cyan]   ██║[/] [bold yellow]╚════╝[/][bold bright_magenta]██║[/][bold magenta]██╔══╝[/]                [bold bright_green]║[/]
[bold bright_green]║[/]  [bold bright_white]╚███╔███╔╝[/][bold green]██║  ██║[/][bold bright_cyan]██║  ██║[/][bold cyan]   ██║[/]       [bold bright_magenta]██║[/][bold magenta]██║[/]                   [bold bright_green]║[/]
[bold bright_green]║[/]   [bold bright_white]╚══╝╚══╝ [/][bold green]╚═╝  ╚═╝[/][bold bright_cyan]╚═╝  ╚═╝[/][bold cyan]   ╚═╝[/]       [bold bright_magenta]╚═╝[/][bold magenta]╚═╝[/]                   [bold bright_green]║[/]
[bold bright_green]║[/]                                                                              [bold bright_green]║[/]
[bold bright_green]║[/]              [bold bright_cyan]▀▄▀▄▀▄[/] [bold bright_white]M A C H I N E[/] [bold bright_cyan]▄▀▄▀▄▀[/]   [bold yellow]v30.0[/]                    [bold bright_green]║[/]
[bold bright_green]║[/]                                                                              [bold bright_green]║[/]
[bold bright_green]║[/]   [bright_cyan]◈[/] [dim]Nested Learning[/] [bright_green]◈[/] [dim]Recursive Self-Correction[/] [bright_yellow]◈[/] [dim]T=0.6[/] [bright_magenta]◈[/]          [bold bright_green]║[/]
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


COMMANDS = {
    "/help": "Show commands",
    "/models": "List Ollama models", 
    "/model": "Switch model (e.g., /model gemma4:12b)",
    "/agent": "Switch agent (build/plan)",
    "/clear": "Clear history",
    "/tools": "List available tools",
    "/memory": "Show/clear episode memory",
    "/inject": "Toggle lesson injection (on/off) - default OFF for review",
    "/confidence": "Toggle semantic reflection (on/off) - default ON",
    "/seed": "Show/set builder seed (/seed 12345 | /seed random)",
    "/verbose": "Toggle verbose mode",
    "/prompt": "Load prompt from file (e.g., /prompt task.txt)",
    "/quit": "Exit",
}


class CLI:
    def __init__(self, model: str, agent_type: str, base_url: str, working_dir: str,
                 verbose: bool = False, temperature: float = 0.6, seed: int = None):
        global VERBOSE
        VERBOSE = verbose
        
        self.model = model
        self.agent_type = agent_type
        self.working_dir = working_dir or os.getcwd()
        self.verbose = verbose
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
    
    def print_banner(self):
        if self.console:
            import time
            import shutil
            
            # Get terminal size for full screen effect
            term_size = shutil.get_terminal_size((80, 24))
            width = min(term_size.columns - 4, 90)
            height = min(term_size.lines - 6, 18)
            
            # The banner lines we'll reveal through the rain (all 75 chars wide)
            banner_lines = [
                "╔═════════════════════════════════════════════════════════════════════════╗",
                "║  ██╗    ██╗██╗  ██╗ █████╗ ████████╗    ██╗███████╗                   ║",
                "║  ██║    ██║██║  ██║██╔══██╗╚══██╔══╝    ██║██╔════╝                   ║",
                "║  ██║ █╗ ██║███████║███████║   ██║ █████╗██║█████╗                    ║",
                "║  ██║███╗██║██╔══██║██╔══██║   ██║ ╚════╝██║██╔══╝                    ║",
                "║  ╚███╔███╔╝██║  ██║██║  ██║   ██║       ██║██║                       ║",
                "║   ╚══╝╚══╝ ╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝       ╚═╝╚═╝                       ║",
                "║              M A C H I N E   v30.0                                   ║",
                "║                                                                         ║",
                "║    ◈ Nested Learning Agent ◈ Recursive Self-Correction ◈ T=0.6 ◈       ║",
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
                        text = Text()
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
                            text.append('\n')
                        live.update(Panel(text, border_style="bright_green", box=box.DOUBLE, 
                                         title="[bold bright_green]◈ INITIALIZING ◈[/bold bright_green]"))
                        time.sleep(0.04)
                    
                    # Phase 2: Banner emerges through the rain (eye trick - center first)
                    for frame in range(45):
                        matrix.step()
                        reveal_progress = frame / 35.0  # Goes past 1.0 intentionally
                        
                        text = Text()
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
                                            text.append(banner_char, style="bright_green")
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
                            text.append('\n')
                        
                        live.update(Panel(text, border_style="bright_green", box=box.DOUBLE))
                        time.sleep(0.04)
                    
                    # Phase 3: Solid banner with subtle shimmer (settling)
                    for frame in range(20):
                        text = Text()
                        for y in range(height):
                            for x in range(width):
                                banner_y = y - start_row
                                banner_x = x - start_col
                                in_banner = (0 <= banner_y < banner_height and 
                                           0 <= banner_x < banner_width)
                                
                                if in_banner and banner_x < len(banner_lines[banner_y]):
                                    banner_char = banner_lines[banner_y][banner_x]
                                    if banner_char in '║╔╗╚╝═':
                                        text.append(banner_char, style="bright_green")
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
                                        text.append(random.choice('01アイ'), style="dim green")
                                    else:
                                        text.append(' ')
                            text.append('\n')
                        
                        live.update(Panel(text, border_style="bright_green", box=box.DOUBLE))
                        time.sleep(0.05)
                        
            except Exception as e:
                # Fallback if Live screen mode fails
                pass
            
            # After animation, print static banner and session info
            self.console.print(BANNER)
            
            # ═══════════════════════════════════════════════════════════════════
            # VISUALLY STUNNING SESSION CONFIGURATION
            # ═══════════════════════════════════════════════════════════════════
            
            # Build a beautiful gradient-style config panel
            tool_count = 6 if self.agent_type == "build" else 3
            mem_stats = self.memory.get_stats()
            
            # Create styled config table
            config = Table(show_header=False, box=None, padding=(0, 1), expand=False)
            config.add_column(style="bold bright_cyan", width=14, justify="right")
            config.add_column(style="white", width=50)
            
            config.add_row("[bright_cyan]🤖 Model[/]", f"[bold bright_white]{self.model}[/]")
            config.add_row("[bright_green]⚡ Agent[/]", f"[bold bright_green]{self.agent_type.upper()}[/] [dim white]│ {tool_count} tools ready[/]")
            config.add_row("[bright_yellow]📊 Context[/]", f"[bold bright_yellow]{self.client.options.get('num_ctx', 256000):,}[/] [dim]tokens[/]")
            config.add_row("[bright_magenta]🎯 Temp[/]", f"[bold bright_magenta]{self.client.options.get('temperature', 0.6)}[/] [dim]stable creativity[/]")
            config.add_row("[bright_cyan]🎲 Seed[/]", f"[bold bright_cyan]{self.seed}[/] [dim]--seed {self.seed} to replay[/]")
            config.add_row("[bright_blue]📁 Dir[/]", f"[dim bright_blue]{str(self.working_dir)[-45:]}[/]")
            
            if mem_stats["total"] > 0:
                config.add_row("[bright_cyan]🧠 Memory[/]", f"[bold green]{mem_stats['successes']}[/][dim]✓[/] [bold red]{mem_stats['failures']}[/][dim]✗[/] [dim]│ {mem_stats['total']} episodes[/]")
            else:
                config.add_row("[bright_cyan]🧠 Memory[/]", "[dim italic]empty ─ learning starts fresh[/]")
            
            self.console.print(Panel(
                config,
                title="[bold bright_green]◈ Session Configuration ◈[/]",
                subtitle="[dim][ Neural Interface Active ][/]",
                border_style="bright_green",
                box=box.HEAVY
            ))
            
            # ═══════════════════════════════════════════════════════════════════
            # BEAUTIFUL COMMAND REFERENCE PANEL
            # ═══════════════════════════════════════════════════════════════════
            
            cmd_grid = Table(show_header=False, box=None, padding=(0, 1), expand=True)
            cmd_grid.add_column(width=25)
            cmd_grid.add_column(width=25)
            cmd_grid.add_column(width=25)
            
            # Row 1 - Primary commands
            cmd_grid.add_row(
                "[bold cyan]/help[/] [dim]› commands[/]",
                "[bold green]/prompt[/] [dim]› load file[/]",
                "[bold yellow]/tools[/] [dim]› list all[/]"
            )
            # Row 2 - Session commands
            cmd_grid.add_row(
                "[bold magenta]/memory[/] [dim]› episodes[/]",
                "[bold blue]/inject[/] [dim]› on│off[/]",
                "[bold red]/clear[/] [dim]› reset[/]"
            )
            # Row 3 - Config commands
            cmd_grid.add_row(
                "[bold white]/model[/] [dim]› switch[/]",
                "[bold bright_black]/verbose[/] [dim]› debug[/]",
                "[bold bright_red]/quit[/] [dim]› exit[/]"
            )
            # Row 4 - V24: semantic reflection toggle, V45.9: seed control
            cmd_grid.add_row(
                "[bold bright_cyan]/confidence[/] [dim]› on|off[/]",
                "[bold bright_cyan]/seed[/] [dim]› n|random[/]",
                ""
            )
            
            self.console.print(Panel(
                cmd_grid,
                title="[bold bright_cyan]◈ Quick Commands ◈[/]",
                border_style="cyan",
                box=box.ROUNDED
            ))
            
            self.console.print()  # Spacing
        else:
            print(BANNER)
            print(f"Model: {self.model} | Agent: {self.agent_type} | Verbose: {self.verbose}")
            print(f"Dir: {self.working_dir}")
            print("/help commands | /prompt load file | /tools list | /quit exit\n")
    
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
            tip_text.append("💡 ", style="bright_yellow")
            tip_text.append("PRO TIP: ", style="bold bright_yellow")
            tip_text.append('End prompts with ', style="dim")
            tip_text.append('"test and fix it"', style="bold bright_cyan")
            tip_text.append(' for automatic test→fix cycles', style="dim")
            self.console.print(Panel(
                tip_text,
                border_style="dim yellow",
                box=box.ROUNDED,
                padding=(0, 1)
            ))
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
                self.print("Recommended: qwen3:14b, ornith:35b, devstral:latest, gemma4:12b")
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
            if len(args_str) > 10000:
                args_str = args_str[:32000] + "\n..."
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
            try:
                user_input = Prompt.ask("\n[bold bright_green]◈>[/bold bright_green]") if self.console else input("\n> ")
                if not user_input.strip():
                    continue
                if user_input.startswith("/"):
                    if not await self.handle_command(user_input):
                        break
                    continue
                await self.process_message(user_input)
            except KeyboardInterrupt:
                self.print("\n[yellow]Use /quit to exit[/yellow]")
            except EOFError:
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
    parser = argparse.ArgumentParser(description="What-if Machine v30.0 - Nested Learning Agent, Evidence-Tuned")
    parser.add_argument("prompt", nargs="?", help="Single prompt (non-interactive)")
    parser.add_argument("--model", "-m", default="ornith-vision", help="Ollama model")
    parser.add_argument("--agent", "-a", choices=["build", "plan"], default="build", help="Agent type")
    parser.add_argument("--url", "-u", default="http://localhost:11434", help="Ollama URL")
    parser.add_argument("--dir", "-d", default=None, help="Working directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show debug info")
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
    
    cli = CLI(args.model, args.agent, args.url, args.dir, args.verbose,
              temperature=args.temp, seed=args.seed)
    
    if not args.prompt:
        cli.print_banner()
    
    if not await cli.initialize():
        sys.exit(1)
    
    await cli.run(args.prompt)


if __name__ == "__main__":
    asyncio.run(main())
