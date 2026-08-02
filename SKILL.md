---
name: skill-router
version: 1.0.0
description: Intelligent skill router that matches your prompts to the best skills from your global library of 568+ skills. Use when you want to discover relevant skills, auto-route to the right skill, or understand which skills apply to your task.
triggers:
  - which skill should I use
  - route this
  - find skill for
  - what skills apply
  - /skill-router
allowed-tools:
  - Bash
  - Read
  - Write
hooks:
  UserPromptSubmit:
    - matcher: "*"
      hooks:
        - type: command
          command: "bash ~/.claude/skills/skill-router/scripts/router.sh"
          timeout: 5
---

# Skill Router — Intelligent Prompt-to-Skill Matcher

## What It Does

The Skill Router analyzes your prompts and automatically suggests the **best matching skills** from your global library. It uses keyword matching, semantic understanding, and context awareness to recommend the most relevant skills.

## How to Use

### Explicit Invocation
Type `/skill-router` anytime to see current recommendations based on your recent prompts.

### Auto-Match (Passive)
The hook automatically runs after each prompt and prints skill suggestions in your session.

### Query Specific Skills
```
/skill-router web scraping
/skill-router video generation  
/skill-router security audit
```

## Matching Algorithm

1. **Keyword Extraction** — Identifies key terms from your prompt
2. **Trigger Matching** — Matches against skill trigger words
3. **Description Scoring** — Scores skills by relevance to prompt
4. **Context Awareness** — Considers project type, file types, and recent activity
5. **Deduplication** — Removes overlapping or redundant suggestions

## Output Format

```
🎯 Best Matches for Your Request:

1. /skill-name (95% match)
   Category: Engineering
   Why: Matches keywords: code review, PR, quality
   
2. /another-skill (87% match)
   Category: Productivity
   Why: Related to workflow automation
```

## Configuration

Edit `~/.claude/skills/skill-router/config.json` to customize:
- Minimum confidence threshold (default: 30%)
- Maximum suggestions (default: 5)
- Skip patterns (skills to always exclude)
