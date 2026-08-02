#!/usr/bin/env python3
"""Generate Codex CLI compatible skill configuration.

Codex CLI uses a yaml-based configuration with rules.
Docs: https://github.com/openai/codex
"""

import argparse
import csv
import yaml
from pathlib import Path


def load_skills(csv_path):
    skills = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            skills.append(row)
    return skills


def generate_codex_config(skills, output_dir):
    """Generate codex.yaml configuration file."""
    output_path = Path(output_dir) / "codex.yaml"
    
    # Group skills by domain for rules
    rules = []
    for skill in skills[:30]:  # Limit to prevent bloat
        name = skill['name']
        desc = skill.get('description', '')[:200]
        triggers = [t.strip() for t in skill.get('triggers', '').split(', ') if t.strip()]
        
        if triggers:
            rule = {
                "name": f"skill-{name}",
                "description": desc,
                "trigger_keywords": triggers[:5],
                "action": f"/{name}"
            }
            rules.append(rule)
    
    config = {
        "version": 1,
        "skills": {
            "count": len(skills),
            "index_file": "~/.claude/skills/skill-router/references/skill_index.csv",
            "router_command": "bash ~/.claude/skills/skill-router/scripts/router.sh",
            "rules": rules
        },
        "modes": {
            "auto": {
                "debounce_seconds": 30,
                "max_suggestions": 4
            },
            "interactive": {
                "enabled": True,
                "show_confidence": True
            }
        }
    }
    
    output_path.write_text(yaml.dump(config, default_flow_style=False))
    print(f"  ✓ Codex CLI: {output_path}")
    return [output_path]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default=str(Path.home()/".claude/skills/skill-router/references/skill_index.csv"))
    parser.add_argument("--output", default=str(Path.home()))
    args = parser.parse_args()
    
    skills = load_skills(args.source)
    generate_codex_config(skills, args.output)
