#!/usr/bin/env python3
"""Generate Amazon byNara (formerly CodeWhisperer) compatible skill rules.

Kiro uses .byNara/rules/ directory similar to Cursor.
"""

import argparse
import csv
from pathlib import Path


def load_skills(csv_path):
    skills = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            skills.append(row)
    return skills


def generate_kiro_rules(skills, output_dir):
    """Generate Kiro-compatible skill rules."""
    rules_dir = Path(output_dir) / ".byNara" / "rules"
    rules_dir.mkdir(parents=True, exist_ok=True)
    
    # Main index file
    index_file = rules_dir / "skills.md"
    lines = [
        "# byNara Skills Index",
        f"# Auto-generated from {len(skills)} Claude skills",
        f"# Generated: {Path.home()}/.claude/skills/skill-router",
        "",
        "## Quick Reference",
        "",
    ]
    
    # Group by category
    categories = {
        "🎬 Video & Animation": [],
        "🔍 Code Review": [],
        "🎨 Design & UI": [],
        "📣 Marketing": [],
        "🔬 Research": [],
        "🐍 Coding": [],
        "🌐 Web Development": [],
    }
    
    for skill in skills[:100]:
        name = skill['name']
        desc = skill.get('description', '')[:80]
        triggers = skill.get('triggers', '').lower()
        
        # Simple categorization
        if any(k in triggers for k in ['video', 'animation', 'render', 'film']):
            cat = "🎬 Video & Animation"
        elif any(k in triggers for k in ['review', 'pr', 'code review']):
            cat = "🔍 Code Review"
        elif any(k in triggers for k in ['design', 'ui', 'landing']):
            cat = "🎨 Design & UI"
        elif any(k in triggers for k in ['marketing', 'seo', 'content']):
            cat = "📣 Marketing"
        elif any(k in triggers for k in ['research', 'paper', 'study']):
            cat = "🔬 Research"
        elif any(k in triggers for k in ['python', 'code', 'script']):
            cat = "🐍 Coding"
        elif any(k in triggers for k in ['web', 'html', 'css', 'react']):
            cat = "🌐 Web Development"
        else:
            cat = "Other"
        
        if cat in categories:
            categories[cat].append((name, desc))
    
    for cat, skills_list in categories.items():
        if skills_list:
            lines.append(f"### {cat}")
            lines.append("")
            for name, desc in skills_list[:10]:
                lines.append(f"- `/{name}` — {desc}")
            lines.append("")
    
    lines.append("---")
    lines.append("## Usage")
    lines.append("")
    lines.append("Run `/skill-router <query>` to find relevant skills.")
    lines.append("Add `--interactive` to browse and select from a numbered list.")
    
    index_file.write_text('\n'.join(lines))
    
    # Generate individual skill files for top skills
    generated = [index_file]
    for skill in skills[:15]:
        skill_file = rules_dir / f"{skill['name']}.md"
        content = f"""# {skill['name']}

{skill.get('description', '')}

## Triggers
{skill.get('triggers', 'None')}

## Hooks
{skill.get('hook_types', 'None')}

## First Action
{skill.get('first_action', 'See SKILL.md')}
"""
        skill_file.write_text(content)
        generated.append(skill_file)
    
    print(f"  ✓ byNara: {len(generated)} files in {rules_dir}")
    return generated


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=str(Path.home()/".claude/skills/skill-router/references/skill_index.csv"))
    parser.add_argument("--output", default=str(Path.home()))
    args = parser.parse_args()
    
    skills = load_skills(args.source)
    generate_kiro_rules(skills, args.output)
