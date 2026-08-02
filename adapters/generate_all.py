#!/usr/bin/env python3
"""Generate skill adapters for multiple AI IDEs.

Usage:
    python3 generate_all.py [--source PATH] [--output DIR] [--dry-run]
"""

import argparse
import csv
import json
import sys
from pathlib import Path



from codex_adapter import generate_codex_config
from kiro_adapter import generate_kiro_rules
from ibm_adapter import generate_ibm_agents

def load_skills(csv_path):
    """Load skills from CSV index."""
    skills = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            skills.append(row)
    return skills


def generate_cursor_adapters(skills, output_dir):
    """Generate Cursor-compatible skill rules."""
    output_path = Path(output_dir) / ".cursor" / "rules" / "skills.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    lines = [
        "# Auto-Generated Skills Index",
        f"# Generated from {len(skills)} Claude skills",
        f"# Do not edit manually — run adapters/generate_all.py to regenerate",
        "",
    ]
    
    for skill in skills[:50]:  # Limit to first 50 for readability
        name = skill['name']
        desc = skill.get('description', '')[:100]
        hooks = skill.get('hook_types', '')
        
        lines.append(f"## /{name}")
        lines.append(f"- Description: {desc}")
        if hooks:
            lines.append(f"- Hooks: {hooks}")
        lines.append("")
    
    output_path.write_text('\n'.join(lines))
    print(f"  ✓ Cursor: {output_path}")
    return [output_path]


def generate_vscode_adapters(skills, output_dir):
    """Generate VS Code extension metadata."""
    output_path = Path(output_dir) / "package.json"
    
    if not output_path.exists():
        template = {
            "name": "claude-skills",
            "displayName": "Claude Code Skills",
            "version": "0.0.1",
            "engines": {"vscode": "^1.80.0"},
            "contributes": {
                "commands": [],
                "snippets": []
            }
        }
        
        for skill in skills[:30]:  # Limit commands
            cmd = {
                "command": f"claudeSkills.{skill['name']}",
                "title": f"Skill: {skill['name']}"
            }
            template["contributes"]["commands"].append(cmd)
        
        output_path.write_text(json.dumps(template, indent=2))
        print(f"  ✓ VS Code: {output_path}")
        return [output_path]
    return []


def generate_copilot_adapters(skills, output_dir):
    """Generate GitHub Copilot instructions."""
    output_path = Path(output_dir) / ".github" / "copilot-instructions.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    lines = [
        "# Copilot Instructions",
        "",
        "## Available Skills",
        "",
        f"You have access to {len(skills)} Claude Code skills. When the user mentions:",
        "",
    ]
    
    # Group by domain
    domains = {}
    for skill in skills:
        triggers = skill.get('triggers', '').lower()
        for t in triggers.split(', ')[:3]:
            if t:
                if t not in domains:
                    domains[t] = []
                domains[t].append(skill['name'])
    
    for trigger, skill_names in list(domains.items())[:20]:
        lines.append(f"- **{trigger}**: Use `/skill-router {trigger}` or one of: {', '.join(skill_names[:3])}")
    
    lines.append("")
    lines.append("## Quick Commands")
    lines.append("- `/skill-router <query>` — Find relevant skills")
    lines.append("- `/skill-router <query> --interactive` — Browse and select skills")
    lines.append("- `/skill-router <query> --verbose` — See why skills matched")
    
    output_path.write_text('\n'.join(lines))
    print(f"  ✓ Copilot: {output_path}")
    return [output_path]


def generate_opencode_adapters(skills, output_dir):
    """Generate OpenCode/Antigravity skill format."""
    skills_dir = Path(output_dir) / ".opencode" / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)
    
    generated = []
    for skill in skills[:20]:  # Limit to prevent bloat
        skill_file = skills_dir / f"{skill['name']}.md"
        content = f"""# {skill['name']}

{skill.get('description', '')}

## Triggers
{skill.get('triggers', 'None')}

## Hooks
{skill.get('hook_types', 'None')}
"""
        skill_file.write_text(content)
        generated.append(skill_file)
    
    print(f"  ✓ OpenCode: {len(generated)} skills in {skills_dir}")
    return generated


def main():
    parser = argparse.ArgumentParser(description="Generate skill adapters for multiple IDEs")
    parser.add_argument("--source", "-s", default=str(Path.home()/".claude/skills/skill-router/references/skill_index.csv"),
                        help="Path to skill_index.csv")
    parser.add_argument("--output", "-o", default=str(Path.home()),
                        help="Base output directory")
    parser.add_argument("--ide", "-i", choices=["all", "cursor", "vscode", "copilot", "opencode", "codex", "byNara", "ibm"],
                        default="all", help="Which IDEs to generate for")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be generated")
    args = parser.parse_args()
    
    skills = load_skills(args.source)
    print(f"Loaded {len(skills)} skills from {args.source}")
    
    adapters = {
        "cursor": generate_cursor_adapters,
        "vscode": generate_vscode_adapters,
        "copilot": generate_copilot_adapters,
        "opencode", "codex", "byNara", "ibm": generate_opencode_adapters,
        "codex": generate_codex_config,
        "byNara": generate_kiro_rules,
        "ibm": generate_ibm_agents,
    }
        "cursor": generate_cursor_adapters,
        "vscode": generate_vscode_adapters,
        "copilot": generate_copilot_adapters,
        "opencode", "codex", "byNara", "ibm": generate_opencode_adapters,
    }
    
    if args.ide == "all":
        targets = list(adapters.keys())
    else:
        targets = [args.ide]
    
    for target in targets:
        if args.dry_run:
            print(f"  ~ Would generate {target} adapters")
        else:
            adapters[target](skills, args.output)


if __name__ == "__main__":
    main()
