# Functional QA Engineer (script-free edition)

A functional QA engineer for Claude Code that learns from every bug it misses. It tests features end to end (functional, UI/UX, exploratory, edge, negative, regression and retests), won't sign off below 100% coverage of every page, state and control, and won't file a bug until it's confirmed against the backend.

This edition contains only instructions: every gate and probe is a step-by-step procedure in `skills/functional-qa-engineer/references/manual-gates.md`, and lessons it learns are saved in your project under `qa-knowledge/`. Browser testing uses the Playwright MCP server if you have it.

The full edition, with scripts for the gates, generators and browser probes, and its self-test, is at https://github.com/Akansh09/functional-qa-engineer. Install it from its marketplace inside Claude Code:

```text
/plugin marketplace add Akansh09/functional-qa-engineer
/plugin install functional-qa-engineer@akansh09
```

This is a functional QA tool, not a penetration-testing or bug-bounty tool. Licensed under MIT.
