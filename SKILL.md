---
name: distill-session
description: Use when the user wants to capture what a Claude Code work session taught into the durable knowledge graph ("distill this session", "save what I learned", "add to palace", "make dots from what I did", end-of-session capture). Distills past sessions into atomic linked "dots" (motivation, guess->method->result, on-going items, keywords) stored as markdown in ~/.claude/palace/dots and viewable in the palace graph. Also use when reviewing or relinking existing dots.
---

# Distill Session — sessions into knowledge dots

## What this is

Turn the reasoning of a Claude Code session into durable, linked **dots** — atomic
notes in a personal knowledge graph ("the palace"). Each dot is one idea: its
motivation, the guess->method->result logic line, what is still open, keywords,
and typed links to other dots. Dots live as markdown in `~/.claude/palace/dots/`,
are git-managed, and are browsed/edited in the palace web viewer.

This is the generalized, standalone version of the session-mining logic that
`my-slides` uses to build decks. `my-slides` reads sessions to make a talk and
throws the structure away; **this skill keeps the structure**.

## Never read raw jsonl

Session `.jsonl` is ~40x noise (tool dumps, file snapshots, metadata). Never Read
it into context. Use the bundled extractor:

```bash
~/.claude/skills/distill-session/extract-session.sh -p <work-dir> -n 3   # latest 3 sessions
~/.claude/skills/distill-session/extract-session.sh -a -p <work-dir>     # assistant text only (densest)
```

Project dir -> slug: `/` -> `-` (e.g. `/home/you/proj/foo` ->
`-home-you-proj-foo`). Sessions live at `~/.claude/projects/<slug>/*.jsonl`
(the extractor honors `$CLAUDE_CONFIG_DIR` if you set one).

## Workflow

1. **Extract.** Run the extractor for the target session(s). For a long session,
   delegate the read to an Explore/general subagent so the main context only
   receives the distilled result, not the transcript.

2. **Identify dots.** From the conversation, find the *atomic ideas* worth
   keeping. One dot = one idea (Zettelkasten atomicity). A single session usually
   yields 1–5 dots, not one giant dump. Split when a note covers two things.
   Prefer capturing:
   - a **method** that worked (or failed, and why),
   - a **result** with numbers / figure paths,
   - an **insight** (a realization that changes future decisions),
   - a **question** left open,
   - a **milestone** (a real checkpoint — a passing validation, a merged MR).

3. **Write each dot** with the schema below into `~/.claude/palace/dots/<id>.md`.
   `id` = `YYYYMMDD-slug` (date-prefixed, unique, stable — it is the filename
   stem and the wikilink target). Use the session's actual date; if summarizing
   several, use the latest. Never invent figure paths — use the real ones the
   session produced.

4. **Link.** Grep existing dot ids (`ls ~/.claude/palace/dots/`) and add typed
   edges in the `## Links` section connecting the new dot to prior ones. This is
   the point of the graph — an unlinked dot is nearly worthless. Propose links,
   don't force them.

5. **Reindex.** Regenerate `INDEX.md`:
   `cd ~/.claude/palace && python3 viewer/serve.py --reindex` (or the viewer
   rebuilds it on load). Commit: `git -C ~/.claude/palace add -A && git ... commit`.

Also check the project's own memory dir (`MEMORY.md`) for standing context before
distilling — it tells you what the user already considers known.

## Dot schema

```markdown
---
id: 20240112-retry-with-backoff
title: Exponential backoff on the flaky test client
type: method           # insight | method | result | question | milestone | project
project: demo          # work stream / repo short name
date: 2024-01-12
status: done            # open | done | parked   (open+ => "on-going item")
milestone: false        # true => real checkpoint, tagged in git & starred in viewer
keywords: [retry, backoff, jitter]
---
## Motivation
One or two sentences: why this came up, what problem it serves.
## Guess -> Method -> Result
- Guess: the hypothesis / expectation going in.
- Method: what was actually done (algorithm, tool, command, derivation).
- Result: the outcome — numbers, plots (real paths), pass/fail, surprise.
## On-going
- [ ] anything still open (omit the section if nothing is open)
## Links
- motivates:: [[<id>]]
- next:: [[<id>]]
```

### Fields

- **type** — `insight` (changes decisions), `method` (a technique), `result`
  (a measured outcome), `question` (open problem), `milestone` (checkpoint),
  `project` (a hub node for a work stream).
- **status** — `open` (still active), `done`, `parked`. `status: open` is how the
  palace surfaces on-going items across all projects.
- **milestone** — `true` marks a real checkpoint; the viewer stars it and it can
  be `git tag`-ged.
- **keywords** — lowercase, a handful; the search/filter axis.

### Typed edges (in `## Links`)

`- <reltype>:: [[<id>]]` — one per line. Reltypes:

| reltype | meaning | draws |
|---|---|---|
| `next` | roadmap forward step | timeline arrow |
| `motivates` | this dot is why that one exists | why-edge |
| `method` | uses this technique | how-edge |
| `part-of` | belongs to a project/milestone hub | grouping |
| `related` | loose association | plain edge |

Keep the `[[id]]` exact — it must equal an existing filename stem (or a dot you
are creating in the same pass).

## Quality bar

- Atomic: one idea per dot. If the title needs "and", split it.
- Self-contained: readable in a year without the session open.
- Linked: at least one typed edge unless it is a brand-new island.
- Honest: record failed guesses too — a dead end is knowledge.
- Terse: fragments, numbers, real paths. Not prose.

## Red flags — you are doing it wrong if

- You Read a raw `.jsonl` instead of using the extractor.
- One session became one 40-line mega-dot instead of 2–4 atomic ones.
- No `## Links` / every dot is an island.
- Figure paths are placeholders instead of the session's real outputs.
- Frontmatter YAML is malformed (breaks the viewer parser) — keep it flat,
  `keywords` is the only list, in `[a, b, c]` flow form.
