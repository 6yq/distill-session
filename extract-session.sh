#!/usr/bin/env bash
# extract-session.sh — strip Claude Code session jsonl to conversation text.
# Raw jsonl is ~40x larger than the useful text (tool dumps, file snapshots,
# attachments, metadata). Never read raw jsonl into context; pipe through this.
#
# Usage:
#   extract-session.sh <session.jsonl> [...]     # named sessions
#   extract-session.sh -p <project-dir> [-n N]   # N latest sessions of project
#   extract-session.sh -a <session.jsonl>        # assistant text only (densest)
#
# Project dir -> slug: / -> -   e.g. /home/you/proj -> -home-you-proj
# Sessions live at ${CLAUDE_CONFIG_DIR:-~/.claude}/projects/<slug>/*.jsonl

set -euo pipefail

ROLES='"user","assistant"'
NUM=1
PROJ=""
FILES=()

while [[ $# -gt 0 ]]; do
  case "$1" in
    -a) ROLES='"assistant"'; shift ;;
    -n) NUM="$2"; shift 2 ;;
    -p) PROJ="$2"; shift 2 ;;
    *) FILES+=("$1"); shift ;;
  esac
done

if [[ -n "$PROJ" ]]; then   # resolved after parsing so -n takes effect regardless of order
  slug=$(realpath -m "$PROJ" | tr '/' '-')   # -m: dir may only exist on another synced machine
  base=""
  for cand in "${CLAUDE_CONFIG_DIR:-$HOME/.claude}/projects" "$HOME/.claude/projects"; do
    [[ -d "$cand/$slug" ]] && base="$cand/$slug" && break
  done
  [[ -z "$base" ]] && { echo "no sessions for $PROJ (slug $slug)" >&2; exit 1; }
  while IFS= read -r f; do FILES+=("$f"); done \
    < <(ls -t "$base"/*.jsonl 2>/dev/null | head -n "$NUM")
fi

[[ ${#FILES[@]} -eq 0 ]] && { grep -E '^# ' "$0" | sed 's/^# //' >&2; exit 1; }

for f in "${FILES[@]}"; do
  echo "===== ${f##*/} ====="
  # Keep only real conversation turns; drop tool_result blocks, snapshots,
  # attachments, system events. Content is either a string or a block array;
  # take .text blocks only. Prefix each turn with its role.
  jq -r --argjson roles "[$ROLES]" '
    select(.type as $t | $roles | index($t))
    | .type as $role
    | .message.content
    | if type == "string" then .
      else ([.[]? | select(.type == "text") | .text] | join("\n"))
      end
    | select(length > 0)
    | "[\($role)] \(.)"
  ' "$f"
done
