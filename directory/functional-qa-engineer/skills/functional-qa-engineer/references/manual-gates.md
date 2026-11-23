# Manual gates and probes (no scripts)

Use this file when `scripts/` isn't available. It does the same job as each script, as steps you follow yourself. The rules are identical, so the result has to be identical too. Keep every file below in the **project you are testing**, never in the skill folder: a plugin update replaces the skill folder.

| Script | Manual equivalent |
|---|---|
| `kb.py` | §1 Knowledge graph |
| `coverage.py` | §2 Coverage matrix |
| `prereport.py` | §3 Pre-report gate |
| `testgen.py` | §4 Test values |
| `sentinel_*.js`, `surface_inventory.js`, `cta_destinations.js`, `raw_values.js`, `loading_sweep.js`, `flicker_scan.js`, `contrast_scan.js` | §5 Browser probes |
| `selftest/` | §6 Keeping lessons honest |

---

## 1. Knowledge graph

**Read it** before planning. The bundled graph is `knowledge/graph.json` (read-only here). Lessons learned in this project go in `./qa-knowledge/lessons.json`, with the same shape: `{"nodes": {}, "edges": []}`. The graph you use is both files together.

- **Mandatory checks:** every node with `"type": "check"` and `"mandatory": true`. The surfaces it applies to are the targets of its `applies_to` edges (`["check:X", "applies_to", "surface:cta"]`). A check with no `applies_to` edge applies everywhere.
- **Past misses:** every node with `"type": "bug"` and `"caught": false`. Follow `missed_because` → cause, `taught` → lesson, and that lesson's `enforced_by` → check.
- `knowledge/GRAPH.md` is the same graph as readable tables; use it to skim.

**Record a miss** (learning loop step 5) by adding to `./qa-knowledge/lessons.json`:

```json
{
  "nodes": {
    "bug:P-07": {"type": "bug", "title": "what was wrong", "product": "Web app", "found_by": "user", "caught": false, "date": "YYYY-MM-DD"},
    "lesson:short-slug": {"type": "lesson", "text": "the generalised rule"},
    "check:short-id": {"type": "check", "text": "the concrete, executable check", "mandatory": true}
  },
  "edges": [
    ["bug:P-07", "found_on", "surface:hidden-option"],
    ["bug:P-07", "missed_because", "cause:coverage-gap"],
    ["bug:P-07", "taught", "lesson:short-slug"],
    ["lesson:short-slug", "enforced_by", "check:short-id"],
    ["check:short-id", "applies_to", "surface:hidden-option"],
    ["check:short-id", "uses", "oracle:O18"]
  ]
}
```

- Causes: `coverage-gap`, `oracle-gap`, `baseline-gap`, `probe-error`, `instrument-gap`, `judgement`.
- If an existing check already covers it but wasn't applied, don't add a new check. Add an `applies_to` edge to the existing check id instead.
- **Record a bug you caught:** add the bug node with `"caught": true`, plus `found_on` and `caught_by` → the check that caught it.
- Keep the file valid JSON. Re-read it after writing.

## 2. Coverage matrix

Keep it in `./qa-coverage/<feature>.md` as one table:

| Item | Surface | Page / state | Check | Result | Evidence / reason | Build |
|---|---|---|---|---|---|---|

**Build it:**
1. **Feature-level items first,** one per surface: `overview`, `list`, `run-state`, `error-state`, `copy`, `actor`, `integration`, `theme`, `loading`, `live-view`, `api`, `settings`, `planning`, `signals`.
2. **Inventory every page × state** (§5 Inventory). Map each control to a surface:

   | Control | Surface |
   |---|---|
   | button, link, menu item | `cta` |
   | tab | `navigation` |
   | text box, text area, combo box, spin button, search box, radio | `form-field` |
   | checkbox, switch, option, checkable menu item | `hidden-option` |
   | repeated data rows | `list`, one row-type item (test first, last and one middle) |
3. **Add what the UI can't show:** every baseline claim, lifecycle state, actor, entry surface (UI/CLI/API), environment and end-to-end flow, each as an item.
4. **Required cells:** for each item, one row per mandatory check that applies to its surface (§1). Re-derive them whenever a lesson is added: new lessons apply retroactively to the whole matrix.

**Results:**

| Result | Meaning | Counts as tested? |
|---|---|---|
| `pass` | correct | yes |
| `fail` | a bug; Evidence = bug id | yes |
| `na` | doesn't apply here, with why | yes |
| `intermittent` | behaves inconsistently; file it as an intermittent bug | yes, and listed under "intermittent" |
| `blocked` | can't be tested now. **Reason is required:** what blocks it and who unblocks it | no |
| `excluded` | out of scope, with a written reason | yes |
| *(empty)* | untested | no: a gap |

**Report** (paste this line into the summary):
`coverage <feature>: <done>/<total> required cells = <pct>%  (<items> items)`. If any cell is blocked, add `of the testable cells: <done>/<total − blocked> = <pct>% · blocked: <n>`. Then list failing, intermittent and blocked cells.

**Verdict:**
- Any gap → **NOT COMPLETE**. Don't call the feature tested.
- No gaps, but some cells blocked → **COMPLETE EXCEPT BLOCKED**. Sign off only as Go-with-conditions, list each blocked cell with its blocker, and retest them when unblocked.
- No gaps and nothing blocked → **COMPLETE**.

## 3. Pre-report gate

Record bugs in `./qa-bugs/<feature>.json`, one object per bug:

```json
{
  "id": "B-01", "title": "One sentence: the wrong behaviour, with the number that proves it",
  "severity": "High", "status": "open",
  "steps": "Numbered steps from a named project/page", "expected": "...", "actual": "... measured",
  "evidence": {"screenshots": ["img/b01.png"], "backend": "API response / log line that confirms it", "ids": {}},
  "repro": {"count": 2, "attempts": 2, "real_action": true, "screenshot_checked": true, "conditions": ""},
  "user_path": "ui", "reachability_note": "", "verified_build": "", "status_history": ["open"],
  "confirmed_by": "", "blocked_by": "", "forced_trigger": false, "user_approved_force": false,
  "root_cause": {"text": "", "proven": false}
}
```

- **Severity:** `Critical`, `High`, `Medium`, `Low`.
- **Status:** `open`, `intermittent`, `blocked`, `fixed`, `partly`, `not-fixed`, `not-reproduced`, `not-retested`, `expected`, `duplicate`.

Before reporting, go through every bug. **Any FAIL blocks the report.**

| Rule | FAIL when |
|---|---|
| R1 | `id`, `title`, `severity`, `status`, `steps`, `expected` or `actual` is missing, or severity/status isn't in the lists above |
| R2 | status is open / not-fixed / partly / intermittent and there's no screenshot (for intermittent: one of a failing occurrence), or no backend confirmation (API, session state, log) |
| R3 | status is open / not-fixed / partly and `repro.count` < 2. If it's flaky, file it as `intermittent` instead |
| R4 | status is open / not-fixed / partly / intermittent and it wasn't re-checked with a real mouse/keyboard action, or the screenshot wasn't looked at |
| R5 | `user_path` is `api-only` or `race` and severity is Critical/High, or `reachability_note` is empty |
| R6 | status is fixed / partly / not-fixed without `verified_build`; or it went `not-reproduced` → `fixed` without `confirmed_by` (only the user/dev closes it) |
| R7 | `forced_trigger` without `user_approved_force` |
| R10 | status `intermittent` and: `repro.count` < 1, `repro.attempts` < 5, or count > attempts. (count = attempts is a WARN: not intermittent, use `open`) |
| R11 | status `blocked` and `blocked_by` is empty |

**Warnings** (fix or justify):
- **R8:** two titles are near-duplicates.
- **R9:** a root cause is stated as fact without proof; call it a hypothesis.

Print the result as `pre-report gate <feature>: <n> bugs, <f> failures, <w> warnings`, list each FAIL/WARN as `<id> <rule>: <why>`, and note each intermittent rate (e.g. 2/10) and each blocker.

## 4. Test values

- **Boundaries (BVA)** for a range min..max (text length in chars, or a number):
  - empty / 0, min, min+1, max−1, max, max+1, far above max
  - for text: whitespace only, leading/trailing spaces, and a multi-byte character exactly at the boundary (count in the product's unit: chars, bytes or UTF-16)
  - check each in the UI, in the API directly, and after reload
- **Partitions (EP):** one valid value per valid sub-type, and one invalid value per invalid reason. Use one invalid input per case.
- **Pairwise:**
  1. List the parameters and their values.
  2. Start with the two parameters that have the most values; write one case per pair of their values.
  3. Fill each other parameter's column, choosing for each case the value that covers the most not-yet-covered pairs.
  4. Add cases for any pair still uncovered.
  5. **Verify:** for every pair of parameters, every value pair appears in at least one case. State "all pairs covered: yes" only after checking.
  6. Add the known-risky full combinations on top.
- **State transitions:** list states and events. Test every valid transition once, consecutive pairs on critical paths, and every event in every state where it should be refused (the UI must block it and the API must refuse it). Note what the UI shows *during* each transition.

## 5. Browser probes (Playwright MCP tools)

- **Sentinel (all session):** after each state you test, call `browser_console_messages` and `browser_network_requests`. Log every console error/warning, page error, HTTP ≥ 400 and failed request, with the state you were in. Before sign-off, triage each group: bug, known bug, or expected (with the reason).
- **Inventory (per page × state):** use `browser_snapshot`. List every visible link, button, tab, menu item, form field, checkbox/switch and option. Open every "More actions", "Columns", "Filter", "View" or "Sort" menu, and list what's inside too. Collapse repeated rows into one row-type item.
- **CTA destinations:** wait until the page has fully loaded, then click each link/button (skip destructive ones). Record the URL and the first heading it lands on, and compare with the label.
  - **BLANK:** the page has almost no text, or an HTTP error.
  - **MISMATCH:** the heading doesn't match the label.
  - Confirm every flag with a real click after full load. Early clicks and hidden duplicates give false flags.
- **Raw values:** turn on every hidden column/option first. Then flag:
  - placeholders (`{n}`, `%s`)
  - CLI flags (`--name`)
  - SNAKE_CASE or raw codes
  - `undefined`, `null`, `NaN`, `[object Object]`
  - numbers-only cells in columns named priority, status, severity, type, state, level, kind or category
- **Loading:** for each entry (tab click from another section, direct URL, reload, first open after ~15 min idle), take screenshots about every 0.5 s for up to 12 s (25 s on a throttled network), until a control that only appears with content is visible. Look at the frames yourself: any blank or half-built frame lasting more than about 1 s without a visible loader is a bug.
- **Flicker:** while the update is happening (live run, polling), take a burst of screenshots of the region, as fast as the tool allows, for about 10 s. A frame that changes and then returns to the previous look within a few frames is a blink. Show that you can see a blink first (a positive control) before you call something "no flicker".
- **Contrast:** in light and dark mode, use `browser_evaluate` on each view, tab, drawer and dialog to compute the WCAG contrast of each visible text element against its effective background. It fails below 4.5:1, or 3:1 for large text (≥ 24 px, or ≥ 18.7 px bold). Then look at non-text elements (icons, toggles, avatars, graph lines) yourself.

## 6. Keeping lessons honest

There's no automated self-test here. After adding a lesson:
1. Re-derive the coverage matrix (§2): the new check must appear on every matching item.
2. Run it on the current feature, and report any siblings.
3. For a judgement or status lesson, re-check the open bugs against §3 with the new rule.
