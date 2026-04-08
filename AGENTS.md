# Agents

## Before anything else

1. Read **AGENT_TEAM_CHECKLIST.md** (full file, or headers + **§2 Lanes** + **§7 Changelog** if timeboxed).
2. Obey the rules under `.cursor/rules/` — especially `agent-team-checklist.mdc` and `agent-autonomy.mdc`.

## Responsibilities

- **Lanes:** When parent + subagents or multiple agents could overlap, follow checklist **§2** (claim a lane, no duplicate research/edits).
- **Living doc:** Add durable operational steps to **AGENT_TEAM_CHECKLIST.md** and append a row to **§7 Changelog** when you do.
- **Handoff:** If you stop mid-task, use the **handoff block** in checklist **§6**.
- **Sal / Grok persona work:** When the user assigns **Sal** (prompt file, `sal_prompt.py`, Sal-related `analysis.py`) to **another agent**, stay out of that lane unless they explicitly move it here; keep the **checklist** current when team process changes.
- **Release checklist:** After substantive product changes, align **`docs/SKYLINE_BUILD_REVIEW.md`** (review pass + **Last reviewed**) with what the code actually does.

## Where things live


| What                       | Where                                     |
| -------------------------- | ----------------------------------------- |
| Full playbook              | `AGENT_TEAM_CHECKLIST.md`                 |
| Release / phase alignment  | `docs/SKYLINE_BUILD_REVIEW.md`            |
| Ops runbook (first run + troubleshooting) | `docs/OPERATIONS_ELITE.txt` |
| Cursor enforcement         | `.cursor/rules/agent-team-checklist.mdc`  |
| Execution / secrets policy | `.cursor/rules/agent-autonomy.mdc`        |
| Core Python package        | `src/sal/`                                |
| Sal system prompt          | `prompts/`                                |
| Scripts & CLI tools        | `scripts/`                                |
| Config templates           | `config/`                                 |
| Repo structure map         | `STRUCTURE.md`                            |
| PR merge-ready loop        | User **babysit** skill (see checklist §2) |


This file stays short; **AGENT_TEAM_CHECKLIST.md** is the source of truth for procedures.