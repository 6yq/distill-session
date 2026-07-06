# distill-session

A skill for AI coding agents (Claude Code and compatible) that distills a work
**session** into durable, atomic, linked knowledge notes — **dots**.

An agent session produces reasoning that normally dies with the session: a
motivation, a guess, the method tried, the result, and what's still open.
`distill-session` mines the session transcript and writes that structure out as
markdown dots you can keep, link, and grow.

Pairs with **[Mneme](https://github.com/6yq/Mneme)** — a zero-build web viewer
for browsing/editing the dots as a graph and roadmap. This skill is the
*distill* step; Mneme is the *store + view*.

## What it does

1. Extracts the conversation from a session's `.jsonl` with the bundled
   `extract-session.sh` (never reads raw jsonl into context — it is ~40× noise).
2. Identifies the atomic ideas worth keeping (one idea per dot).
3. Writes each as a markdown dot: YAML frontmatter + fixed body headers
   (`## Motivation`, `## Guess -> Method -> Result`, `## On-going`, `## Links`)
   + typed wikilink edges (`- next:: [[id]]`).
4. Links new dots to existing ones so the graph stays connected.

Full schema and rules: [`SKILL.md`](SKILL.md).

## Install

Copy this directory into your agent's skills dir:

```bash
git clone https://github.com/6yq/distill-session ~/.claude/skills/distill-session
```

Then, in a session, ask the agent to *"distill this session"* /
*"save what I learned into the Mneme"*. Requires `jq` for the extractor.

Dots default to `~/.claude/mneme/dots/` (clone Mneme there, or point elsewhere).

## Files

- `SKILL.md` — the skill instructions (schema, workflow, quality bar).
- `extract-session.sh` — session `.jsonl` → conversation text. Honors
  `$CLAUDE_CONFIG_DIR`.
- `dot-template.md` — a blank dot to copy by hand.

## License

MIT.
