#!/usr/bin/env python3
"""Scan ~/.claude/skills/ and regenerate skill_index.csv.

Usage:
    python3 scripts/scan-skills.py              # Regenerate in-place
    python3 scripts/scan-skills.py --dry-run    # Show what would be indexed
    python3 scripts/scan-skills.py --output path/to/skill_index.csv
"""

import argparse
import csv
import sys
from pathlib import Path


def scan_skills(skills_dir, dry_run=False, output_path=None):
    """Scan all skills and return list of (name, description, triggers) tuples."""
    skills = []
    skipped = []

    for skill_dir in sorted(skills_dir.iterdir()):
        if not skill_dir.is_dir():
            continue

        skill_name = skill_dir.name
        if skill_name.startswith("_"):
            continue

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            if not dry_run:
                skipped.append((skill_name, "No SKILL.md"))
            continue

        # Parse frontmatter
        content = skill_md.read_text(encoding="utf-8")
        desc = ""
        triggers = []

        # Extract description from frontmatter
        in_frontmatter = False
        for line in content.split("\n"):
            if line.strip() == "---":
                in_frontmatter = not in_frontmatter
                continue
            if in_frontmatter:
                if line.startswith("description:"):
                    desc = line.split(":", 1)[1].strip().strip('"').strip("'")
                elif line.startswith("  - "):
                    trigger = line.strip("- ").strip().strip('"').strip("'")
                    triggers.append(trigger)

        # Fallback: extract first non-frontmatter paragraph
        if not desc:
            in_body = False
            for line in content.split("\n"):
                if line.strip() == "---":
                    in_body = True
                    continue
                if in_body and line.startswith("#"):
                    continue
                if in_body and line.strip():
                    desc = line.strip()
                    break

        if desc:
            skills.append((skill_name, desc, ", ".join(triggers)))
        else:
            skipped.append((skill_name, "No description"))

    return skills, skipped


def write_csv(skills, output_path):
    """Write skills to CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["name", "description", "triggers"])
        for name, desc, triggers in skills:
            writer.writerow([name, desc, triggers])
    return len(skills)


def main():
    parser = argparse.ArgumentParser(description="Scan Claude skills and generate index CSV")
    parser.add_argument("--dry-run", action="store_true", help="Show without writing")
    parser.add_argument("--output", "-o", help="Output CSV path (default: references/skill_index.csv)")
    args = parser.parse_args()

    skills_dir = Path.home() / ".claude" / "skills"
    output_path = Path(args.output) if args.output else Path.home() / ".claude/skills/skill-router/references/skill_index.csv"

    print(f"Scanning {skills_dir}...")
    skills, skipped = scan_skills(skills_dir, dry_run=args.dry_run)

    if args.dry_run:
        print(f"\n📊 Would index {len(skills)} skills ({len(skipped)} skipped)")
        print("\nTop 10 by name:")
        for name, desc, triggers in skills[:10]:
            print(f"  {name}: {desc[:60]}...")
        if skipped:
            print(f"\n⚠️  Skipped {len(skipped)} skills:")
            for name, reason in skipped[:5]:
                print(f"  - {name}: {reason}")
        return

    count = write_csv(skills, output_path)
    print(f"✅ Indexed {count} skills → {output_path}")
    if skipped:
        print(f"⚠️  Skipped {len(skipped)} skills (no SKILL.md or description)")


if __name__ == "__main__":
    main()
