# Claude Skill Router

Intelligent prompt-to-skill matcher for Claude Code. Analyzes your prompts and suggests the best matching skills from your global library — automatically.

## ✨ Features

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Two-pass domain detection** | Identifies primary + secondary domains from your prompt before ranking |
| 2 | **Exclusive keyword bonuses** | Skills with domain-specific names get +25 boost |
| 3 | **Cross-domain disambiguation** | Penalizes skills that score well across multiple domains |
| 4 | **Auto-index refresh** | Detects when you add/remove skills and silently regenerates the index |
| 5 | **Explicit query mode** | `/skill-router web scraping` — browse skills without triggering a hook |
| 6 | **Category badges** | 🎬🔍🎨📣🔬🗺️💰🧪🐍🌐 — instant visual category recognition |
| 7 | **"Why this skill" explanations** | `--verbose` shows exact keywords that triggered each match |
| 8 | **Context-aware boosting** | Reads `package.json`, `.gitignore`, etc. to boost relevant domains |
| 9 | **Session memory** | Won't show the same skill twice in one session |
| 10 | **Configurable thresholds** | Min confidence, max suggestions, skip patterns — all in `config.json` |
| 11 | **Debounced execution** | 30s cooldown prevents hook spam (configurable) |
| 12 | **Personal favorites** | Pin certain skills to always appear first |
| 13 | **Manual scan command** | `python3 scripts/scan-skills.py --dry-run` to preview indexing |
| 14 | **Multi-domain ranking** | Shows skills from both primary AND secondary matching domains |
| 15 | **Trigger column matching** | Checks skill trigger words for higher precision |
| 16 | **Name partial matching** | Matches multi-word input against skill names (e.g. "landing page" → `landing-page-generator`) |
| 17 | **Long description penalty** | Generic long descriptions get downweighted to reduce noise |
| 18 | **Silent background refresh** | Index regeneration happens in <5ms, invisible to user |
| 19 | **Per-session deduplication** | Tracks shown skills per session to avoid repetition |
| 20 | **Plugin-structured install** | Drop into `~/.claude/skills/` and hooks auto-register |

## Installation

### One-command install

```bash
# Clone the repo into your Claude skills directory
git clone https://github.com/<yourusername>/claude-skill-router.git ~/.claude/skills/skill-router

# Scan your existing skills to build the index
cd ~/.claude/skills/skill-router && python3 scripts/scan-skills.py
```

That's it. The `UserPromptSubmit` hook will now fire on every prompt.

### What gets installed

```
~/.claude/skills/skill-router/
├── SKILL.md                    # Hook definition (auto-registers with Claude Code)
├── config.json                 # Your configuration
├── scripts/
│   ├── auto-match.py           # v9 matching engine
│   ├── router.sh               # Shell entry point
│   └── scan-skills.py          # Regenerates skill_index.csv
└── references/
    └── skill_index.csv         # Generated index of all your skills
```

## Usage

### Auto-mode (default)

Just type any prompt. After ~30 seconds since the last run, the router will suggest relevant skills:

```
> Create a product launch video for my SaaS app

┌─────────────────────────────────────────────────────┐
│  🎯 Relevant Skills                                 │
└─────────────────────────────────────────────────────┘

  🎬  remotion-to-hyperframes  (82%)
       Translate an existing Remotion video composition...

  🎬  remotion                 (60%)
       Remotion CLI integration...
```

### Explicit mode

Type `/skill-router <query>` anytime to browse skills without waiting for a hook:

```
> /skill-router security audit

🔍  zen-review          (75%)
🔍  adversarial-reviewer (72%)
🔍  cso                 (72%)
```

### Verbose mode

Add `--verbose` or set `"verbose": true` in config to see why each skill matched:

```
🔍  adversarial-reviewer  (72%)
   ↳ matches: code review, review, [trigger] code, [trigger] review
```

### Manual index refresh

When you add or remove skills, regenerate the index:

```bash
python3 ~/.claude/skills/skill-router/scripts/scan-skills.py
```

Preview what would be indexed without writing:

```bash
python3 ~/.claude/skills/skill-router/scripts/scan-skills.py --dry-run
```

## Configuration

Edit `~/.claude/skills/skill-router/config.json`:

```json
{
  "min_confidence": 10,
  "max_suggestions": 4,
  "show_every": 5,
  "skip_patterns": ["_gstack-command", "pink-twill"],
  "auto_invoke": false,
  "verbose": false,
  "debounce_seconds": 30,
  "version": "9",
  "personal_favorites": ["remotion", "zen-review"]
}
```

| Field | Default | Description |
|-------|---------|-------------|
| `min_confidence` | 10 | Minimum score to show a skill |
| `max_suggestions` | 4 | How many skills to display |
| `debounce_seconds` | 30 | Cooldown between auto-runs |
| `skip_patterns` | `["_gstack-command", "pink-twill"]` | Skip these skill names |
| `personal_favorites` | `[]` | Always boost these skills |
| `verbose` | `false` | Show matching explanations by default |

## Domains

The router recognizes 10 domains and scores skills within each:

| Domain | Emoji | Key Signals |
|--------|-------|-------------|
| Video/Animation | 🎬 | video, animation, render, hyperframes, remotion |
| Code Review | 🔍 | code review, pr review, debug, vulnerability |
| Design/UI | 🎨 | ui design, landing page, tailwind, figma |
| Marketing | 📣 | seo, copywriting, lead generation, funnel |
| Research | 🔬 | literature review, dossier, competitive analysis |
| Product | 🗺️ | sprint planning, backlog, agile, roadmap |
| Finance/Business | 💰 | revenue, profit, mrr, burn rate, pitch deck |
| Testing | 🧪 | playwright, e2e test, tdd, cypress |
| Coding/Python | 🐍 | python, django, fastapi, pandas |
| Coding/Web | 🌐 | typescript, react, nextjs, tailwind |

## How It Works

1. **Detect**: Scans your prompt for domain keywords (strong + weak signals)
2. **Rank**: Scores each skill using exclusive keywords, trigger matches, name overlap, and description word intersection
3. **Disambiguate**: Applies cross-domain penalty if a skill scores well in multiple domains
4. **Boost**: Context-aware weighting from project files (`package.json`, `.gitignore`, etc.)
5. **Refresh**: Silently checks if your skill library changed and regenerates the index if needed
6. **Output**: Shows top N skills with category emoji badges and optional explanation trails

## Requirements

- Python 3.8+
- Claude Code (for hook registration)
- Any Claude Code skills installed at `~/.claude/skills/`

## Contributing

Contributions welcome! Feel free to:
- Add new domain definitions to `DOMAINS` in `auto-match.py`
- Improve keyword lists for better matching
- Submit issues and pull requests

## License

MIT
