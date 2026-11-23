#!/usr/bin/env python3
"""Build the script-free edition of the skill for the Claude plugin directory.

The directory accepts only Markdown, text, JSON, YAML and images from unverified organizations, so this edition
drops scripts/ and selftest/ and points every script step at references/manual-gates.md instead.

  python3 tools/build_directory_edition.py           write directory/functional-qa-engineer/
  python3 tools/build_directory_edition.py --check   exit 1 if the committed edition is out of date (CI)

Every replacement must match exactly once, so a change to SKILL.md that breaks the edition fails the build.
"""
import filecmp, json, os, shutil, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, 'skills', 'functional-qa-engineer')
NAME = 'functional-qa-engineer'
ALLOWED = {'.md', '.json', '.png', '.txt'}
MG = '`references/manual-gates.md`'

NOTE = ('> **Script-free edition.** Where this file names `scripts/…`, `kb.py`, `coverage.py`, `prereport.py`, '
        '`testgen.py`, a `.js` probe or `selftest/`, follow the matching section of `references/manual-gates.md` instead.\n\n')

SKILL_SUBS = [
    ("`scripts/testgen.py` computes the values (BVA, EP, all-pairs with a coverage self-check, state-transition and invalid-event lists).",
     f"Derive the values with {MG} §4."),
    ("Grows with every miss. Edit only through `scripts/kb.py`.",
     f"Read-only in this edition: lessons you learn go in `./qa-knowledge/lessons.json` in the project ({MG} §1)."),
    ("- `references/manual-gates.md` — the same gates and probes as step-by-step instructions, for when the scripts can't run (no Python, no file access, or the script-free directory edition).\n",
     f"- {MG} — **this edition has no scripts.** It gives the manual equivalent of every gate and probe: knowledge graph, coverage matrix, pre-report gate, test values, and browser probes through Playwright MCP tools. Wherever a reference file names a script, follow the matching section there.\n"),
    ("Run `python3 <skill>/scripts/kb.py checks` and `kb.py misses`; every mandatory check goes into the plan.",
     f"Read the mandatory checks and past misses ({MG} §1), including this project's `./qa-knowledge/lessons.json`; every mandatory check goes into the plan."),
    ("you may not call a feature \"tested\" until `coverage.py report` exits 0 — every required cell tested or excluded with a written reason.",
     f"you may not call a feature \"tested\" until the coverage report ({MG} §2) says COMPLETE — every required cell tested or excluded with a written reason."),
    ("generalise, `kb.py add-miss`, apply the new check",
     "generalise, record it in `./qa-knowledge/lessons.json`, apply the new check"),
    ("Run `sentinel_start.js` before the first page and label states as you go; before sign-off, triage every group from `sentinel_report.js` (bug, known bug, or expected with reason).",
     f"Read console messages and network requests after every state ({MG} §5, Sentinel); before sign-off, triage every group (bug, known bug, or expected with reason)."),
    ("Record bugs in `./qa-bugs/<feature>.json` and run `prereport.py check <feature>`:",
     f"Record bugs in `./qa-bugs/<feature>.json` and run the gate in {MG} §3:"),
    ("After any change to this skill, and after every learning-loop update, run the self-test (`selftest/selftest.sh` + `selftest.js`). A lesson that its fixture doesn't catch is not learned yet.",
     f"After every learning-loop update, follow {MG} §6: the new check must appear on every matching item and be run on the current feature."),
    ("never improvise boundary or combination values; generate them with `scripts/testgen.py` (bva / ep / pairwise / states) and keep the output as the test list.",
     f"never improvise boundary or combination values; derive them with {MG} §4 and keep the result as the test list."),
    ("When you record a bug you caught, also run `kb.py add-caught --bug … --surface … --check <check that caught it>` so the graph knows which checks earn their keep.",
     f"When you record a bug you caught, also add it to `./qa-knowledge/lessons.json` with `caught_by` the check that caught it ({MG} §1), so the graph knows which checks earn their keep."),
]
SKILL_DROP = ["- `scripts/` — browser (Playwright MCP", "- `selftest/` — the skill's own test suite:"]
COVERAGE_START, COVERAGE_END = "Work in the project directory (the matrix lives in `./qa-coverage/<feature>.json`):", "\n## 3. Run it, and judge with oracles"
COVERAGE_NEW = f"""Work in the project directory. Build and keep the matrix exactly as {MG} §2 describes, in `./qa-coverage/<feature>.md`:
1. Feature-level items for every global surface (actor, integration, theme, loading, live-view, api…), so global checks can't be skipped.
2. **Inventory every page × every state** (empty, queued, running, stopped, failed, drawer open, dark mode, other user…) with `browser_snapshot`, including every menu's contents ({MG} §5, Inventory). Repeated data rows collapse into one row-type item (test first, last and one middle).
3. **Add what the UI can't show:** every baseline claim, lifecycle state, actor, entry surface (UI/CLI/API), environment and end-to-end flow.
4. **Mark as you test:** pass, fail, na, `intermittent` (inconsistent behaviour), or `blocked` with a reason saying what blocks it and who unblocks it. Don't leave such cells as gaps.
5. **Exclude only with a reason**, e.g. an external link; the reason shows in review.
6. **Gate:** any gap means NOT COMPLETE. If only blocked cells remain, it's **complete except blocked**: sign off only as Go-with-conditions, list every blocked cell with its blocker, and retest them when unblocked. Re-derive the required cells whenever a lesson is added, so lessons learned mid-project apply to the whole matrix immediately.
"""

def sub_once(text, old, new, where):
    n = text.count(old)
    if n != 1:
        sys.exit(f'{where}: expected exactly 1 match, found {n}: {old[:70]!r}')
    return text.replace(old, new)

def build_skill_md():
    t = open(os.path.join(SRC, 'SKILL.md'), encoding='utf-8').read()
    for old, new in SKILL_SUBS:
        t = sub_once(t, old, new, 'SKILL.md')
    lines = t.split('\n')
    for prefix in SKILL_DROP:
        hits = [i for i, l in enumerate(lines) if l.startswith(prefix)]
        if len(hits) != 1:
            sys.exit(f'SKILL.md: expected 1 line starting {prefix!r}, found {len(hits)}')
        del lines[hits[0]]
    t = '\n'.join(lines)
    a, b = t.find(COVERAGE_START), t.find(COVERAGE_END)
    if a < 0 or b < a:
        sys.exit('SKILL.md: coverage section markers not found')
    return t[:a] + COVERAGE_NEW + t[b:]

def build(out):
    sk = os.path.join(out, 'skills', NAME)
    os.makedirs(os.path.join(out, '.claude-plugin')); os.makedirs(os.path.join(sk, 'references')); os.makedirs(os.path.join(sk, 'knowledge'))
    open(os.path.join(sk, 'SKILL.md'), 'w', encoding='utf-8').write(build_skill_md())
    for f in sorted(os.listdir(os.path.join(SRC, 'references'))):
        t = open(os.path.join(SRC, 'references', f), encoding='utf-8').read()
        if f != 'manual-gates.md' and any(k in t for k in ('scripts/', '.py', '.js', 'selftest')):
            first, rest = t.split('\n', 1)
            t = first + '\n\n' + NOTE + rest.lstrip('\n')
        open(os.path.join(sk, 'references', f), 'w', encoding='utf-8').write(t)
    for f in ('graph.json', 'GRAPH.md'):
        shutil.copy(os.path.join(SRC, 'knowledge', f), os.path.join(sk, 'knowledge', f))
    shutil.copy(os.path.join(ROOT, '.claude-plugin', 'icon.png'), os.path.join(out, '.claude-plugin', 'icon.png'))
    shutil.copy(os.path.join(ROOT, 'LICENSE'), os.path.join(out, 'LICENSE'))
    pj = json.load(open(os.path.join(ROOT, '.claude-plugin', 'plugin.json')))
    pj['description'] = ('Functional QA engineer for Claude Code (script-free edition): tests features end to end, enforces a '
                         '100% coverage gate, blocks weak bug reports, and learns from every bug it misses.')
    json.dump(pj, open(os.path.join(out, '.claude-plugin', 'plugin.json'), 'w'), indent=2); open(os.path.join(out, '.claude-plugin', 'plugin.json'), 'a').write('\n')
    open(os.path.join(out, 'README.md'), 'w', encoding='utf-8').write(
        "# Functional QA Engineer (script-free edition)\n\n"
        "A functional QA engineer for Claude Code that learns from every bug it misses. It tests features end to end "
        "(functional, UI/UX, exploratory, edge, negative, regression and retests), won't sign off below 100% coverage of "
        "every page, state and control, and won't file a bug until it's confirmed against the backend.\n\n"
        "This edition contains only instructions: every gate and probe is a step-by-step procedure in "
        "`skills/functional-qa-engineer/references/manual-gates.md`, and lessons it learns are saved in your project "
        "under `qa-knowledge/`. Browser testing uses the Playwright MCP server if you have it.\n\n"
        "The full edition, with scripts for the gates, generators and browser probes, and its self-test, is at "
        "https://github.com/Akansh09/functional-qa-engineer. Install it from its marketplace inside Claude Code:\n\n"
        "```text\n/plugin marketplace add Akansh09/functional-qa-engineer\n/plugin install functional-qa-engineer@akansh09\n```\n\n"
        "This is a functional QA tool, not a penetration-testing or bug-bounty tool. Licensed under MIT.\n")
    check_allowed(out)

def check_allowed(out):
    bad = []
    for d, _, files in os.walk(out):
        for f in files:
            p = os.path.join(d, f); rel = os.path.relpath(p, out)
            ext = os.path.splitext(f)[1].lower()
            if ext not in ALLOWED and f != 'LICENSE':
                bad.append(f'{rel}: file type not allowed'); continue
            if ext == '.png':
                data = open(p, 'rb').read()
                if b'PK\x03\x04' in data: bad.append(f'{rel}: looks like it holds a zip archive')
                continue
            raw = open(p, 'rb').read()
            if b'\x00' in raw: bad.append(f'{rel}: NUL byte')
            try: s = raw.decode('utf-8')
            except UnicodeDecodeError: bad.append(f'{rel}: not UTF-8'); continue
            if s.startswith('#!'): bad.append(f'{rel}: starts with #!')
            if f.lower() in ('claude.md', 'claude.local.md', 'agents.md'): bad.append(f'{rel}: reserved name')
    if bad:
        sys.exit('directory edition has files the directory refuses:\n  ' + '\n  '.join(bad))

def same_tree(a, b):
    c = filecmp.dircmp(a, b)
    if c.left_only or c.right_only or c.diff_files or c.funny_files:
        return False
    return all(same_tree(os.path.join(a, s), os.path.join(b, s)) for s in c.common_dirs)

if __name__ == '__main__':
    dest = os.path.join(ROOT, 'directory', NAME)
    if '--check' in sys.argv:
        tmp = tempfile.mkdtemp(); out = os.path.join(tmp, NAME); build(out)
        ok = os.path.isdir(dest) and same_tree(out, dest)
        shutil.rmtree(tmp)
        if not ok:
            sys.exit('directory edition is out of date: run python3 tools/build_directory_edition.py')
        print('directory edition up to date')
    else:
        if os.path.isdir(dest): shutil.rmtree(dest)
        build(dest); print('built', os.path.relpath(dest, ROOT))
