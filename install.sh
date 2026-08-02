#!/usr/bin/env bash
# Install the skill-grader skill into ~/.claude/skills/skill-grader/
set -euo pipefail

SKILL_DIR="$HOME/.claude/skills/skill-grader"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "Installing skill-grader skill..."
echo "  from: $SCRIPT_DIR"
echo "  to:   $SKILL_DIR"

# Remove previous installation. Handles the symlink left by earlier setups.
if [ -L "$SKILL_DIR" ]; then
  rm -f "$SKILL_DIR"
elif [ -d "$SKILL_DIR" ]; then
  rm -rf "$SKILL_DIR"
fi

mkdir -p "$SKILL_DIR"

# Skill payload. README ships too: a deployed skill with no orientation doc
# is hard to re-understand months later.
cp "$SCRIPT_DIR/SKILL.md" "$SKILL_DIR/"
cp "$SCRIPT_DIR/README.md" "$SKILL_DIR/"
cp -R "$SCRIPT_DIR/scripts" "$SKILL_DIR/"
cp -R "$SCRIPT_DIR/references" "$SKILL_DIR/"
cp -R "$SCRIPT_DIR/assets" "$SKILL_DIR/"
cp -R "$SCRIPT_DIR/config" "$SKILL_DIR/"

# evals/ ships but tests/ does not: evals define correctness for the deployed
# skill, whereas unit tests cover the source. This is why D11 moves between an
# installed target and a checkout while D12 does not.
cp -R "$SCRIPT_DIR/evals" "$SKILL_DIR/"

# score.py resolves weights from config/profiles.yaml at runtime, and the
# scripts run under `uv run`, so the project manifest ships as well.
cp "$SCRIPT_DIR/pyproject.toml" "$SKILL_DIR/"
[ -f "$SCRIPT_DIR/uv.lock" ] && cp "$SCRIPT_DIR/uv.lock" "$SKILL_DIR/"

# Drop build artifacts that cp carried along.
find "$SKILL_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$SKILL_DIR" -name "*.pyc" -delete 2>/dev/null || true

# Stamp with git hash. scan.py reads this to tell an installed skill from a
# source checkout, which changes how it scores resource hygiene and testability.
GIT_HASH=$(git -C "$SCRIPT_DIR" rev-parse --short HEAD 2>/dev/null || echo "unknown")
echo "$GIT_HASH" > "$SKILL_DIR/.installed-from"

echo "Installed from commit $GIT_HASH. Run again after making changes to update the live skill."
