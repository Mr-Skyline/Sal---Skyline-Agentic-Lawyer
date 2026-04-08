# Master Builder Playbook — Multi-Agent Project Builds

A reusable system for coordinating multiple AI coding agents to build, restructure, or ship a project fast. Drop this file into any repo and follow the pattern.

---

## How it works

You run **one coordinating agent** (the Master Builder) that never writes code directly. It assesses, plans, delegates, reviews, and integrates. The actual work is done by **specialized sub-agents** running in parallel Cursor chats (or sequential turns if limited to one).

```
                    ┌──────────────────┐
                    │  MASTER BUILDER  │
                    │  (Coordinator)   │
                    │                  │
                    │  Assess → Plan → │
                    │  Delegate →      │
                    │  Review →        │
                    │  Integrate       │
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
        ┌─────▼─────┐ ┌─────▼─────┐ ┌─────▼─────┐
        │  Agent 1  │ │  Agent 2  │ │  Agent 3  │
        │  (Lane A) │ │  (Lane B) │ │  (Lane C) │
        └───────────┘ └───────────┘ └───────────┘
```

### Why this works

- **No conflicts:** Each agent owns specific files/directories. No two agents edit the same file.
- **Parallel execution:** While Agent 1 restructures folders, Agent 2 hardens code, Agent 3 writes tests — simultaneously.
- **Quality gate:** The Master Builder reviews every deliverable before it's merged. Nothing ships unchecked.
- **Continuous momentum:** The moment one agent finishes, the next task is already queued.

---

## The 7-step cycle

Run this cycle repeatedly until the project is done:

### 1. Assess

Read the entire codebase. Understand what exists, what's broken, what's missing. Build a mental model of every file, every import, every dependency. You cannot delegate what you don't understand.

**What the Master Builder does:**
- Read every source file (not just headers — full content)
- Count files, check structure, identify clutter
- Run existing tests to see what passes/fails
- Check git status, branch, recent commits
- Read all documentation for accuracy

### 2. Plan

Create a numbered phase plan with clear milestones. Be honest about what's shipped vs. planned. Each phase should be completable in one agent cycle.

**Example plan:**
```
Phase 1: Folder structure + file moves (Repo Architect)
Phase 2: Import rewiring (Repo Architect + Workflow Engineer)
Phase 3: Missing code implementation (Workflow Engineer)
Phase 4: Documentation update (all agents)
Phase 5: Test coverage + security audit (Quality Inspector)
Phase 6: UI polish (Workflow Engineer)
Phase 7: Final integration + ship (Master Builder)
```

### 3. Delegate

Issue parallel tasks using the delegation format below. Each task must have:
- **Exact files** the agent owns (their "lane")
- **Exact files** the agent must NOT touch (other agents' lanes)
- **Measurable acceptance criteria** (not "make it better" — "all 14 tests pass")
- **Context** about recent changes they need to know

### 4. Review

When an agent reports back, verify:
- Acceptance criteria are met (run the tests yourself)
- No files outside their lane were modified
- Code quality meets your standards
- No regressions introduced

### 5. Integrate

Commit with professional messages. One logical change per commit.

### 6. Advance

Immediately queue the next round of tasks. Never let agents sit idle.

### 7. Report

Give the project owner a crisp status update after each cycle.

---

## Delegation format

Use this exact format every time. Copy the entire block and paste it into the agent's Cursor chat.

```
=== DELEGATION TO: [Agent Name] ===
Task: [one-line summary]
Acceptance Criteria:
- [measurable outcome 1]
- [measurable outcome 2]
- [measurable outcome 3]
Deadline: [immediate / next cycle]
```

Then below the block, provide a **Context** paragraph with:
- Current branch name
- What was recently changed and by whom
- Which files are in their lane (CAN touch)
- Which files are NOT in their lane (CANNOT touch)
- How to run tests
- Any gotchas or blockers

---

## Lane management (the critical rule)

**One agent per file per cycle.** This is non-negotiable.

### How to split lanes

**By directory** (cleanest for restructuring):
```
Agent 1: src/core/         — business logic
Agent 2: src/api/          — API layer
Agent 3: tests/ + docs/    — quality + documentation
Agent 4: infra/ + scripts/ — deployment + tooling
```

**By feature** (best for feature work):
```
Agent 1: authentication (all files related)
Agent 2: payments (all files related)
Agent 3: notifications (all files related)
Agent 4: shared utilities + tests for all features
```

**By layer** (good for full-stack):
```
Agent 1: backend/models + backend/services
Agent 2: backend/api + backend/middleware
Agent 3: frontend/components + frontend/pages
Agent 4: frontend/state + frontend/api-client
Agent 5: tests/ + CI/CD + docs/
```

### Shared files (the danger zone)

Some files are touched by everyone (`README.md`, config files, `__init__.py`). Options:

1. **Master Builder owns shared files** — agents propose changes, coordinator applies them
2. **One agent owns them per cycle** — rotate ownership each round
3. **Lock them** — nobody touches them until a dedicated "docs pass" cycle

---

## Scaling to more agents

### 3 agents (small project)

```
Agent 1: Repo Architect     — structure, config, packaging, CI
Agent 2: Workflow Engineer   — core logic, pipelines, integrations
Agent 3: Quality Inspector   — tests, security, docs, review
```

### 5 agents (medium project)

```
Agent 1: Repo Architect     — structure, packaging, CI/CD
Agent 2: Backend Engineer   — API, services, database
Agent 3: Frontend Engineer  — UI components, state, styling
Agent 4: Integration Engineer — API clients, auth, external services
Agent 5: Quality Inspector   — tests, security, docs, performance
```

### 8 agents (large project)

```
Agent 1: Repo Architect       — monorepo structure, build system, CI
Agent 2: Data Layer           — models, migrations, queries, caching
Agent 3: Business Logic       — services, domain rules, workflows
Agent 4: API Layer            — endpoints, middleware, serialization
Agent 5: Frontend Core        — components, routing, layouts
Agent 6: Frontend State       — state management, API client, real-time
Agent 7: Infrastructure       — Docker, deployment, monitoring, scripts
Agent 8: Quality & Security   — tests, audits, docs, compliance
```

### 12+ agents (monorepo / multi-service)

Split by **service boundary**:
```
Agent 1-2:  Service A (one for logic, one for API)
Agent 3-4:  Service B
Agent 5-6:  Service C
Agent 7:    Shared libraries
Agent 8:    API gateway / BFF
Agent 9:    Frontend
Agent 10:   Infrastructure / DevOps
Agent 11:   Testing & QA
Agent 12:   Documentation & Compliance
```

---

## How the Master Builder assessment works (step by step)

This is exactly what was done on the Sal project, generalized:

### Step 1: Read everything

```
1. Read EVERY file in the repo (not just a few)
2. Count files at root level vs. in subdirectories
3. Identify the "clutter ratio" — how many files are at root that shouldn't be
4. Map every import chain (who imports what)
5. Run existing tests — note what passes and what fails
6. Check for tests that reference code that doesn't exist yet
```

### Step 2: Classify every file

Put every file into one of these buckets:

| Bucket | Examples | Destination |
|--------|----------|-------------|
| Entry point | `main.py`, `app.py`, `manage.py` | Root |
| Core library | Business logic, models, services | `src/<pkg>/` |
| Configuration | `.env.example`, theme files | `config/` |
| Documentation | READMEs, guides, schemas | `docs/` |
| Scripts/tools | CLI helpers, batch files, setup | `scripts/` |
| Tests | Test files | `tests/` |
| CI/CD | GitHub Actions, Dockerfiles | `.github/`, root |
| Static assets | Images, fonts, templates | `assets/` or `static/` |
| Must stay at root | `.gitignore`, `requirements.txt`, `LICENSE` | Root |

### Step 3: Plan the moves

Use `git mv` to preserve history. Plan the import rewiring before you move anything.

### Step 4: Execute in order

```
1. Create directories
2. Move files (git mv)
3. Create __init__.py files
4. Rewrite imports (relative inside packages, absolute from entry points)
5. Fix scripts (sys.path, relative paths)
6. Run tests
7. Update documentation
8. Commit
```

---

## Prompt template for the Master Builder

Paste this into a new Cursor chat to activate the Master Builder on any project:

```
You are the Master Builder for this project. You coordinate multiple 
specialized agents to build/restructure this codebase rapidly.

Your job:
1. ASSESS — Read every file, understand the full codebase state
2. PLAN — Create a numbered phase plan with clear milestones
3. DELEGATE — Issue parallel tasks to sub-agents (I will paste them into 
   separate chats)
4. REVIEW — Inspect every deliverable ruthlessly
5. INTEGRATE — Direct clean commits
6. ADVANCE — Immediately queue next tasks
7. REPORT — Give me a crisp status update after each cycle

Rules:
- You do NOT write code. You read, plan, delegate, review, integrate.
- Every delegation specifies exact file lanes (what to touch, what not to)
- One agent per file per cycle — no conflicts
- Measurable acceptance criteria on every task
- All agents stay busy at all times

Begin by assessing the current repo state. Read every file. Then give me 
the plan and the first round of agent prompts.
```

---

## Prompt template for sub-agents

Each sub-agent gets a prompt like this in their own Cursor chat:

```
You are [Agent Name] working on branch [branch-name].

YOUR LANE (files you own this cycle):
- [list of files/directories]

DO NOT TOUCH (other agents' lanes):
- [list of files/directories]

TASK:
[specific task description]

ACCEPTANCE CRITERIA:
- [criterion 1]
- [criterion 2]
- [criterion 3]

CONTEXT:
- [recent changes]
- [how to run tests]
- [gotchas]

When done, report: "Task complete" + list of files changed + test results.
```

---

## Common pitfalls

### 1. Agents editing the same file
**Fix:** Explicit lane assignments. If two agents need the same file, one goes first, the other waits or works on something else.

### 2. Import breakage after moves
**Fix:** The Master Builder (or Repo Architect) handles all `git mv` + import rewiring in a single atomic commit before other agents start.

### 3. Tests reference code that doesn't exist
**Fix:** Read the test files during assessment. If tests import functions that don't exist, implementing them is a top-priority task.

### 4. Documentation drift
**Fix:** Every agent that changes behavior also updates the relevant doc. Quality Inspector verifies in their pass.

### 5. Agents going rogue (editing outside their lane)
**Fix:** Review `git diff` after each agent's work. Reject anything outside their lane.

### 6. Stale context (agent doesn't know about other agents' changes)
**Fix:** Each delegation prompt includes a Context section describing recent changes. After integration, update the context for the next round.

---

## Quick reference: file counts and agent allocation

| Root files | Status | Action |
|-----------|--------|--------|
| < 15 | Clean | Maintain |
| 15-30 | Cluttered | 1 agent: restructure |
| 30-60 | Messy | 2-3 agents: restructure + rewire |
| 60+ | War zone | 3-5 agents: full rebuild of structure |

| Total codebase files | Recommended agents |
|---------------------|-------------------|
| < 50 | 2-3 |
| 50-150 | 3-5 |
| 150-500 | 5-8 |
| 500+ | 8-12 (split by service/module) |

---

## Checklist for adding this to a new project

1. Copy this file to `docs/MASTER_BUILDER_PLAYBOOK.md` (or wherever docs live)
2. Activate the Master Builder using the prompt template above
3. Let it assess → plan → delegate
4. Paste each agent prompt into its own Cursor chat
5. Collect results → Master Builder reviews → integrate → repeat
6. Ship when all phases complete and tests pass

---

*This playbook was battle-tested on the Sal — Skyline Agentic Lawyer project: 55+ root files restructured into a clean package layout, 3 missing functions implemented, 14 tests passing, comprehensive documentation — executed across 5 phases with 3 parallel agents.*
