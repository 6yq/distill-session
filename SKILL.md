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

## Distilling from a repo, not a session

Sometimes the input is a **project directory / old repo**, not a session jsonl
("organize what I've done", back-filling the palace from years of work). Then read
**backbones first**, never plough the source or data. This is a fan-out job — one
subagent per work stream returning a structured digest, then synthesize the taxonomy
and write dots yourself. Hard-won rules:

- **Backbone read order** (stop when purpose is clear): `README*`/`.org`, `Makefile`
  targets, `CLAUDE.md`/`AGENTS.md`, then narrative docs — `HANDOFF*`, `methodology_*`,
  `why_*`, `proof_scheme_*`, `debate_*`, `RESULTS.md`, `record.md`, `note.md`,
  `compare*.md`, any `## Results` section — plus stray `*.log`, entry-point docstrings,
  and `__init__`/`setup.py` exports when a README is absent or was deleted.
- **CLAUDE.md and HANDOFF/record docs are first-class truth**, often richer than git
  log; the newest, most substantive work may be *deliberately uncommitted* (read the
  result `.md` even when git history looks stale). Chinese commit messages carry
  milestone/date signal — keep them.
- **Never read** `.h5/.hdf5/.parquet/.pq/.root/.rtraw/.npz`, big `.csv`, `.pdf`/`.png`
  figures, framework source trees (JUNOsw/TAOsw internals), or full `.ipynb`. Measured
  numbers usually live in those gitignored artifacts, so a backbone-only pass **cannot**
  recover them: be honest — cite the artifact `path` (and page) or leave `results: []`
  rather than inventing. Skip machine-generated blocks (`#+begin_example`, NUTS/sampler
  logs) in `.org` notes.
- **Dedup by (remote-url, branch), not by directory.** Sibling worktrees/checkouts of
  the same origin are ONE stream — merge them.
- **Cloned ≠ worked on — gate on authorship FIRST.** Before distilling a repo at all,
  confirm the user actually committed to it: `git shortlog -sne --all` (or
  `git log --all --pretty='%an|%ae' | grep -iE '<their identities>'`). Zero of their
  commits — or a lone stray commit in a repo whose real files are authored by others —
  means it's a **clone, not a work stream**: skip it, or drop the lane if you already
  made one. Map the user's several identities (name + every email) before counting.
- **Attribute honestly.** Group/framework repos are multi-author; credit only the user's
  commits. For an official-framework repo the contribution may be a data payload committed
  by a maintainer, or a topic branch with no merge commits — cross-reference
  symlinks/artifacts and sibling dots for MR ids, not just `git log` authorship. Weight a
  shared repo's dots to the user's actual slice, not its whole history.
- **Dates:** non-git working dirs → take the date from the filename/mtime; otherwise
  trust git *author* dates over checkout mtimes.
- **Don't inherit a guess.** If the prompt guesses an acronym/experiment, verify it —
  flag unresolved, and reconcile the experiment prefix from concrete in-repo tokens.
- **A thin repo yields no dots.** Placeholder/data-staging/clone repos with no user
  commits and no numbers: say so and move on rather than padding.

See `docs/naming.md` (the `Scope:Subject` pattern) and the palace `CLAUDE.md` for the
project vocabulary. Reuse existing lanes; `Calib` is the umbrella for detector
calibration (bench tests, commissioning, param-DB all fold in), and waveform-level
work is `FSMP`, never `Reco` (which is event vertex/energy reconstruction).

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

## Replay the logic chain — the point of the links

A dot is atomic, but a *study* is a **chain of reasoning**, and the palace earns its
keep only if you can walk a work stream start-to-finish and **replay that chain** —
the same arc you'd stand up and present. That arc is fixed (it's the `my-slides` deck
skeleton): **problem → guess/theory → method → result (numbers) → cross-check →
summary → open question**. So distilling a stream is not "drop N atomic notes next to
a hub"; it is *laying the story's spine as typed edges*:

- The **hub** (`type: project`) reads as the talk's opening **and** summary in one
  short paragraph: the problem, the approach, the headline number, the current state.
  If someone read only the hub they should get the abstract.
- A **`next` chain** orders the dots the way the study actually unfolded
  (theory → method → result → cross-check → outlook). Following `next` from the first
  step *is* the roadmap the viewer draws — make it walkable, not a bag of siblings.
- **`motivates`** carries the *why*: a problem or a **negative result** points to the
  fix it triggered. Keep dead-ends in the graph — a biased result that `motivates` its
  correction is exactly the reasoning a reader needs, and it's what a good talk shows.
- **`method`** binds each applied step to the shared-toolbox dot instead of re-deriving
  it; **`part-of`** only groups. `part-of` alone is a star with no story.

Litmus test: can you narrate the project in one breath by following its edges —
"needed X *(hub)* → tried Y, came out biased *(result)* → because Z *(insight)* →
so did W *(method)* → gave N *(result)* → cross-checked by V → next is U *(question)*"?
If the edges don't let you say that sentence, the spine is missing; add the ordering.
A well-linked project exports to a deck almost directly: hub → opening, the `next`
spine → body sections, `question`/`open` dots → outlook.

## Quality bar

- Atomic: one idea per dot. If the title needs "and", split it.
- Self-contained: readable in a year without the session open.
- Linked: at least one typed edge unless it is a brand-new island.
- Honest: record failed guesses too — a dead end is knowledge.
- Terse: fragments, numbers, real paths. Not prose.
- Walkable: a project's dots form a `next`/`motivates` spine you can narrate
  end-to-end, not a `part-of` star. If you can't replay the logic chain, it isn't done.

## Red flags — you are doing it wrong if

- You Read a raw `.jsonl` instead of using the extractor.
- One session became one 40-line mega-dot instead of 2–4 atomic ones.
- No `## Links` / every dot is an island.
- A project is a `part-of` star with no `next`/`motivates` spine — you can't replay
  its logic chain, so it reads as trivia, not a study.
- Figure paths are placeholders instead of the session's real outputs.
- Frontmatter YAML is malformed (breaks the viewer parser) — keep it flat,
  `keywords` is the only list, in `[a, b, c]` flow form.
- (repo mode) You opened data/figure artifacts or framework source, invented numbers a
  backbone can't show, credited a multi-author branch entirely to the user, or padded a
  placeholder repo into dots instead of skipping it.
