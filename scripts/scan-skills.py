#!/usr/bin/env python3
"""Scan ~/.claude/skills/ and regenerate skill_index.csv.

Enhanced with metadata extraction:
  - description (one-line summary)
  - triggers (activation keywords)
  - has_hooks (whether skill has SessionStart/UserPromptSubmit hooks)
  - hook_types (comma-separated list of hook types)
  - first_action (first actionable step when invoked)

Usage:
    python3 scripts/scan-skills.py              # Regenerate in-place
    python3 scripts/scan-skills.py --dry-run    # Show what would be indexed
    python3 scripts/scan-skills.py --output path/to/skill_index.csv
"""

import argparse
import csv
import sys
import re
from pathlib import Path


def parse_frontmatter(content):
    """Extract YAML-like frontmatter from SKILL.md."""
    fm = {}
    in_fm = False
    current_key = None
    current_val = []
    
    for line in content.split('\n'):
        if line.strip() == '---':
            # Save previous key-value if any
            if current_key and current_val:
                fm[current_key] = ', '.join(current_val) if len(current_val) > 1 else current_val[0]
                current_key = None
                current_val = []
            in_fm = not in_fm
            continue
        if in_fm:
            # List item under current key
            m = re.match(r'^\s*-\s+(.+)$', line)
            if m and current_key:
                current_val.append(m.group(1).strip().strip('"').strip("'"))
                continue
            # New key
            m = re.match(r'^(\w+):\s*(.*)$', line)
            if m:
                if current_key and current_val:
                    fm[current_key] = ', '.join(current_val) if len(current_val) > 1 else current_val[0]
                current_key = m.group(1).strip()
                val = m.group(2).strip().strip('"').strip("'")
                if val:
                    current_val = [val]
                else:
                    current_val = []
    
    # Save last key
    if current_key and current_val:
        fm[current_key] = ', '.join(current_val) if len(current_val) > 1 else current_val[0]
    
    return fm


def extract_hook_info(content):
    """Extract hook information from SKILL.md using robust parsing."""
    hooks = {"has_hooks": False, "hook_types": [], "hook_commands": []}
    
    # Find hooks section in frontmatter
    in_hooks = False
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped == '---':
            in_hooks = not in_hooks
            continue
        if in_hooks and stripped == 'hooks:':
            hooks["has_hooks"] = True
            continue
        if in_hooks and hooks["has_hooks"]:
            # Hook type names (indented under hooks:)
            if re.match(r'^\s+-\s+\w', stripped) and stripped.replace('-', '').strip().title() in \
               ["Sessionstart", "Userpromptsubmit", "Pretooluse", "Posttooluse", "Complete"]:
                htype = stripped.replace('-', '').strip()
                hooks["hook_types"].append(htype)
            # Command pattern in hooks block
            m = re.search(r'command:\s*["\']?([^"\'\n]+)', line)
            if m:
                cmd = m.group(1).strip().rstrip('"').rstrip("\'")
                hooks["hook_commands"].append(cmd)
    
    # Fallback: just check if "hooks:" exists anywhere in frontmatter area
    if not hooks["has_hooks"] and "hooks:" in content[:500]:
        hooks["has_hooks"] = True
        # Try to find hook type names near hooks:
        for line in content.split('\n'):
            for htype in ["SessionStart", "UserPromptSubmit", "PreToolUse", "PostToolUse", "Complete"]:
                if htype in line:
                    if htype not in hooks["hook_types"]:
                        hooks["hook_types"].append(htype)
    
    return hooks


def extract_first_action(content, fm):
    """Extract what the skill does — look for imperative instructions."""
    in_body = False
    seen_heading = False
    for line in content.split('\n'):
        stripped = line.strip()
        if stripped == '---':
            in_body = True
            continue
        if not in_body:
            continue
        # Skip frontmatter-derived content like "name:" etc
        if re.match(r'^(name|version|description|triggers|allowed-tools|hooks):', stripped):
            continue
        # First real section heading
        if stripped.startswith('#'):
            if not seen_heading:
                seen_heading = True
                continue
        # Look for actionable patterns
        if any(kw in stripped.lower() for kw in ['use when', 'run ', 'type ', 'invoke', 
                                                  'call /', 'execute', 'to create', 
                                                  'when you want', 'when asked']):
            # Get the command or slash-command reference
            cmds = re.findall(r'(?:`([^`]+)`|(/\w+))', stripped)
            if cmds:
                return cmds[0][0] or cmds[0][1]
            return stripped[:75]
        # If we hit the first content line after headings, grab it
        if seen_heading and stripped and len(stripped) > 10:
            return stripped[:75]
    return ""


def scan_skills(skills_dir, dry_run=False, output_path=None):
    """Scan all skills and return list of enriched tuples."""
    skills = []
    skipped = []
    stats = {"with_hooks": 0, "without_hooks": 0}
    
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
        
        content = skill_md.read_text(encoding="utf-8")
        fm = parse_frontmatter(content)
        hook_info = extract_hook_info(content)
        
        desc = fm.get("description", "")
        triggers_raw = fm.get("triggers", "")
        
        # Clean up triggers (remove leading /)
        triggers_clean = []
        if triggers_raw:
            for t in triggers_raw.replace(", ", ",").split(","):
                t = t.strip().lstrip("/")
                if t and len(t) > 2:
                    triggers_clean.append(t)
        
        # Determine first action
        first_action = extract_first_action(content, fm)
        
        # Mark if has hooks
        has_hooks = hook_info["has_hooks"]
        hook_types = "|".join(hook_info["hook_types"]) if hook_info["hook_types"] else ""
        
        if has_hooks:
            stats["with_hooks"] += 1
        else:
            stats["without_hooks"] += 1
        
        # Build enhanced trigger string
        trigger_str = ", ".join(triggers_clean)
        if hook_types:
            trigger_str += f" |hooks:{hook_types}"
        
        if desc:
            skills.append((
                skill_name,
                desc,
                trigger_str,
                str(has_hooks),
                hook_types,
                first_action[:80],
            ))
        else:
            skipped.append((skill_name, "No description"))
    
    return skills, skipped, stats


def write_csv(skills, output_path):
    """Write enriched skills to CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "name", "description", "triggers",
            "has_hooks", "hook_types", "first_action"
        ])
        for row in skills:
            writer.writerow(row)
    return len(skills)


def main():
    parser = argparse.ArgumentParser(description="Scan Claude skills and generate enhanced index CSV")
    parser.add_argument("--dry-run", action="store_true", help="Show without writing")
    parser.add_argument("--output", "-o", help="Output CSV path")
    args = parser.parse_args()

    skills_dir = Path.home() / ".claude" / "skills"
    output_path = Path(args.output) if args.output else Path.home() / ".claude/skills/skill-router/references/skill_index.csv"

    print(f"Scanning {skills_dir}...")
    skills, skipped, stats = scan_skills(skills_dir, dry_run=args.dry_run)

    if args.dry_run:
        print(f"\n📊 Would index {len(skills)} skills ({stats['with_hooks']} with hooks, {stats['without_hooks']} without)")
        print(f"⚠️  Skipped {len(skipped)} skills\n")
        print("Top 10 by score:")
        for name, desc, triggers, has_h, hooks, action in skills[:10]:
            hook_mark = "🪝" if has_h == "True" else "  "
            print(f"  {hook_mark} {name}: {desc[:55]}...")
            print(f"      triggers: {triggers[:60]}")
            print(f"      action:   {action}")
            print()
        if skipped:
            print(f"\n⚠️  Skipped {len(skipped)} skills:")
            for name, reason in skipped[:5]:
                print(f"  - {name}: {reason}")
        return

    count = write_csv(skills, output_path)
    print(f"✅ Indexed {count} skills → {output_path}")
    print(f"   {stats['with_hooks']} with hooks | {stats['without_hooks']} without")
    if skipped:
        print(f"⚠️  Skipped {len(skipped)} skills (no SKILL.md or description)")


if __name__ == "__main__":
    main()
