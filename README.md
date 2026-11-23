<p align="center">
  <img src=".claude-plugin/icon.png" alt="Functional QA Engineer icon" width="120">
</p>

<h1 align="center">Functional QA Engineer</h1>

<p align="center">
  <a href="https://github.com/Akansh09/functional-qa-engineer/actions/workflows/selftest.yml"><img src="https://github.com/Akansh09/functional-qa-engineer/actions/workflows/selftest.yml/badge.svg" alt="self-test"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT"></a>
  <a href="#install"><img src="https://img.shields.io/badge/Claude%20Code-plugin-8A63D2" alt="Claude Code plugin"></a>
</p>

<p align="center"><b>A functional QA engineer for Claude Code that learns from every bug it misses.</b></p>

When you tell it about a bug it missed, it works out *why* it missed it and records the lesson in a knowledge graph. The lesson becomes a mandatory check on every feature it tests after that, so the same class of bug doesn't get missed twice.

It tests features the way a thorough functional QA engineer does:

- It decides what "correct" means before testing.
- It covers every page, state and control, not only the happy path, and won't sign off below 100% coverage.
- It won't file a bug until it's confirmed against the backend and reproduced twice.

> **Scope: functional QA.** Functional, UI/UX, exploratory, edge, negative, regression and retest testing of features across UI, API, CLI and background jobs. Deeper non-functional checks (API contracts, accessibility, performance, i18n, security) run only when you ask. This is **not** a penetration-testing or bug-bounty tool.

## What it looks like

**It won't file a weak bug report.** Here a bug was seen once by a script and never confirmed:

```text
$ prereport.py check checkout
pre-report gate checkout: 1 bugs, 4 failures, 0 warnings
  FAIL B-01 R2: no backend confirmation (API/session/log) — could be a probe artefact
  FAIL B-01 R3: reproduced fewer than 2 times
  FAIL B-01 R4: not re-checked with a real mouse/keyboard action
  FAIL B-01 R4: screenshot not looked at before filing
BLOCKED: fix the failures before reporting
```

**It won't say "tested" until the coverage matrix is complete** (output trimmed):

```text
$ coverage.py report checkout
coverage checkout: 0/40 required cells = 0.0%  (15 items)
NOT COMPLETE — 40 untested cells:
  GAP  feature/actor :: permission
  GAP  feature/api :: reachability
  GAP  feature/copy :: claims
  ...
```

**It generates test values instead of guessing them** (here for a coupon field limited to 50 characters; output trimmed):

```text
$ testgen.py bva --min 1 --max 50 --type text --unit chars
value | expected | why
---|---|---
0 chars | invalid | empty
1 chars | valid | min
50 chars | valid | max
51 chars | invalid | above max
49 chars + 1 emoji (multi-byte at the boundary) | decide (spec?) | ...
whitespace only | invalid | trimmed?
```

**It learns from a miss** (an example conversation):

```text
You:    You missed this: the hidden "Priority" column shows
        raw 3/2/0 instead of labels.
Claude: Reproduced. Cause: coverage-gap (optional columns were
        never turned on).
        Lesson added: turn on every hidden column, filter and
        toggle once, and check its values aren't raw.
        Re-ran it on this feature: found the same bug in the
        hidden "Owner" and "SLA" columns.
```

## Install

**As a Claude Code plugin (recommended).** Run this inside Claude Code:

```text
/plugin marketplace add Akansh09/functional-qa-engineer
/plugin install functional-qa-engineer@akansh09
```

**As a plain skill** (use this if you want lessons it learns to persist on your machine, because a plugin update replaces the plugin folder):

```sh
git clone https://github.com/Akansh09/functional-qa-engineer.git ~/functional-qa-engineer
ln -s ~/functional-qa-engineer/skills/functional-qa-engineer \
      ~/.claude/skills/functional-qa-engineer
```

Then just ask. It triggers on requests like:

- "Test the checkout flow on our stage URL"
- "Check if B-12, B-14 and B-15 are fixed"
- "Run a regression after today's deploy"
- "Is this a bug or expected?"
- "You missed this: …"

**Requirements:** Python 3.10+ (standard library only). Browser testing needs [Playwright MCP](https://github.com/microsoft/playwright-mcp).

## What's inside

| Feature | What it does |
|---|---|
| **Modes** | New feature, retest of fixes, regression after deploy, triage |
| **Test design by default** | Equivalence partitioning, boundary values, decision tables, state transitions, pairwise, classification tree, CRUD matrix, error guessing (`testgen.py`) |
| **100% coverage gate** | Page × state × control inventory, plus claims, actors, entry surfaces and flows. Cells that can't be tested are marked `blocked` with a reason, so the gate ends as "complete except blocked" instead of getting stuck (`coverage.py`) |
| **21 oracles** | Consistency, state truth, causality, round-trip, claim, recovery, loading, permission, destination, hidden options… each with a real bug it caught |
| **Pre-report gate** | Evidence, backend confirmation, 2 repros, real-action recheck, severity capped by how users reach it. Flaky bugs are filed as `intermittent` with their rate; bugs that can't be retested are `blocked` with the blocker (`prereport.py`) |
| **Browser probes** | Console/network sentinel, surface inventory, CTA destinations, raw-value leaks, loading sweep, flicker and contrast scans |
| **Knowledge graph** | bug → why it was missed → lesson → mandatory check → surface/oracle (`kb.py`, rendered to [`GRAPH.md`](skills/functional-qa-engineer/knowledge/GRAPH.md)) |
| **Self-test** | A browser fixture for each learned UI miss, plus checks of the gates, generators and knowledge graph; the non-browser half runs in CI |

```
.claude-plugin/          plugin + marketplace manifests, icon
skills/functional-qa-engineer/
  SKILL.md               entry point: rules, modes, workflow
  references/            techniques, test design, oracles, reporting
  knowledge/             graph.json + generated GRAPH.md
  scripts/               browser probes (.js), gates (.py)
  selftest/              fixtures and the skill's own tests
```

## Self-test

```sh
cd skills/functional-qa-engineer
python3 selftest/selftest.py        # non-browser half (also runs in CI)
sh selftest/selftest.sh             # stages fixtures + browser harness, serves on :3101
# then in Claude Code with Playwright MCP, run .playwright-mcp/qa/selftest.js
sh selftest/selftest.sh stop
```

## Starting with an empty knowledge graph

The bundled graph holds 27 lessons drawn from 34 real misses on real projects, with the product names made generic. Its checks apply to any product. To start from scratch, set `knowledge/graph.json` to `{"nodes": {}, "edges": []}` and run `python3 scripts/kb.py render`.

## Contributing

The most valuable contribution is **a bug you found that the skill missed.** Open a [missed-bug issue](https://github.com/Akansh09/functional-qa-engineer/issues/new?template=missed_bug.yml); it becomes a lesson and a check for everyone. False alarms ([report one](https://github.com/Akansh09/functional-qa-engineer/issues/new?template=false_alarm.yml)), new oracles and script fixes are welcome too. Run the self-test before opening a PR.

## License

[MIT](LICENSE)
