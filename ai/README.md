# AI Harness Configuration

This directory contains the actual, reproducible AI configuration used to
build the solution, per the brief's requirement to include custom rules,
system prompts, and agent configurations.

## What was used

- **Claude Code** (Anthropic CLI) running under the
  [Gentle AI](https://github.com/Gentleman-Programming/gentle-ai) harness as
  the orchestrator. The orchestrator delegates real work to specialized
  sub-agents and keeps a thin coordination thread.
- **SDD (spec-driven development) skills**: each change flows through
  explore → propose → spec → design → tasks → apply → verify → archive,
  with one dedicated sub-agent per phase (`sdd-*` agents).
- **Bounded review agents**: risk/reliability/readability/resilience lenses
  (`review-*`) plus an adversarial dual-judge protocol (`jd-*`) for
  higher-risk diffs.
- **Engram persistent memory** (MCP server): decisions, conventions, and
  discoveries persist across sessions and compactions.
- **Strict-TDD execution mode**: behavior changes require a failing test
  first (RED), then the minimal implementation (GREEN).
- **Model family**: Claude (Anthropic) — orchestrator and sub-agents run on
  Claude models (per-agent model tiers are declared in each agent's
  frontmatter).

## Layout

- `agents/` — all 18 sub-agent definitions (`sdd-*`, `review-*`, `jd-*`),
  verbatim as used.
- `skills/sdd/` — the 10 `sdd-*` phase skills (each `SKILL.md` plus its
  reference modules), verbatim as used. They are orchestrator-loaded and
  delegate-only by design (`user-invocable: false` in their frontmatter):
  the orchestrator loads them and delegates the actual work to the
  matching sub-agent in `agents/`.
- `skills/sdd-workflow/` — the SDD orchestrator workflow plus the shared
  conventions and contracts the skills reference (`sdd-phase-common.md`,
  `sdd-status-contract.md`, `openspec-convention.md`,
  `engram-convention.md`, `skill-resolver.md`).

## Reproducing the setup

1. Install [Claude Code](https://docs.anthropic.com/en/docs/claude-code)
   (optionally under the Gentle AI harness, which supplies the orchestrator
   rules and review lifecycle).
2. Copy the agent definitions:

   ```bash
   cp ai/agents/*.md ~/.claude/agents/
   ```

3. Copy the invocable `sdd-*` skills:

   ```bash
   cp -r ai/skills/sdd/* ~/.claude/skills/
   ```

4. Copy the workflow docs so the orchestrator can lazy-load them:

   ```bash
   mkdir -p ~/.claude/skills/_shared
   cp ai/skills/sdd-workflow/*.md ~/.claude/skills/_shared/
   ```

5. Run Claude Code in the repository; the `sdd-*` skills drive the workflow
   and the agents in `~/.claude/agents/` are picked up automatically.

Notes: the skill and agent files reference optional MCP servers (Engram
memory, CodeGraph code intelligence); without those servers they still run,
minus persistent memory and graph lookups. Files are committed as used, with personal data (none was present
beyond home-directory paths, already generalized to `~/...`) scrubbed.
