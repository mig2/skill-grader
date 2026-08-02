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

# tests/ and evals/ are deliberately excluded. The payload is what the skill
# reads or executes while running; nothing consults either at runtime. Grade
# the source checkout, not the install, to say anything about verification.

# score.py resolves weights from config/profiles.yaml at runtime, and the
# scripts run under `uv run`, so the project manifest ships as well.
cp "$SCRIPT_DIR/pyproject.toml" "$SKILL_DIR/"
[ -f "$SCRIPT_DIR/uv.lock" ] && cp "$SCRIPT_DIR/uv.lock" "$SKILL_DIR/"

# Drop build artifacts that cp carried along.
find "$SKILL_DIR" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
find "$SKILL_DIR" -name "*.pyc" -delete 2>/dev/null || true

# Provenance stamp. scan.py reads this to tell an installed skill from a source
# checkout, and to report drift against the source. A bare hash is not enough:
# hashes only resolve inside a known repo, so the source location is recorded
# too. `dirty` matters most — installing from an uncommitted tree makes the
# commit describe something other than what was actually copied.
COMMIT=$(git -C "$SCRIPT_DIR" rev-parse HEAD 2>/dev/null || echo "unknown")
BRANCH=$(git -C "$SCRIPT_DIR" rev-parse --abbrev-ref HEAD 2>/dev/null || echo "unknown")
REMOTE=$(git -C "$SCRIPT_DIR" remote get-url origin 2>/dev/null || echo "")
if [ -n "$(git -C "$SCRIPT_DIR" status --porcelain 2>/dev/null)" ]; then
  DIRTY=true
else
  DIRTY=false
fi

cat > "$SKILL_DIR/.installed-from" <<JSON
{
  "source_path": "$SCRIPT_DIR",
  "source_remote": "$REMOTE",
  "commit": "$COMMIT",
  "branch": "$BRANCH",
  "dirty": $DIRTY,
  "installed_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
JSON

echo "Installed from ${COMMIT:0:7} on $BRANCH. Run again after making changes to update the live skill."
if [ "$DIRTY" = true ]; then
  echo "WARNING: source tree had uncommitted changes — the recorded commit does not fully describe this payload."
fi
