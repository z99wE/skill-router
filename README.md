# Claude Skill Router v9

Intelligent prompt-to-skill matcher for Claude Code. Analyzes your prompts and suggests the best matching skills from your global library — automatically.

## 🚀 Quick Start

### Installation (One Command)

```bash
git clone https://github.com/YOUR_USERNAME/claude-skill-router.git ~/.claude/skills/skill-router
python3 ~/.claude/skills/skill-router/scripts/scan-skills.py
```

That's it. The router will now auto-fire on every prompt (debounced to every 30 seconds).

---

## 🤕 The Problem: You Have 500+ Skills, But Can't Find the Right One

### Sound familiar?

- **You install a bunch of skills** from GitHub repos — video tools, code reviewers, marketing agents, design helpers — and forget half of them
- **You remember there's a skill for this**… but not *which* skill. You spend 5 minutes scrolling through `~/.claude/skills/` just to find it
- **You type `/` and pray** — scroll through hundreds of slash commands until you find the right one (if you remember it exists)
- **You waste time mid-flow** — stop your actual work to search for "what's the command for X?" when you could just keep going
- **Skills sit unused** — you have powerful tools installed but never use them because discovering them requires conscious effort

### The Core Irritation

**Claude Code skills are powerful but invisible.** You can install 568 skills, but without an intelligent matcher, you're essentially hoarding tools you don't know how to reach. Every time you struggle to remember "is it `/hero-video` or `/product-launch`?", you're fighting your own setup.

The Skill Router fixes this by **bringing skills to you** instead of forcing you to hunt for them. It watches your prompts, understands what you're trying to do, and surfaces the exact skill you need — with a preview of what it does, so you can pick confidently.

---

---

## 📖 How to Use

### Mode 1: Auto-Match (Default)

Just type any prompt normally. After ~30 seconds, the router fires and suggests relevant skills:

```
> Create a product launch video

┌─────────────────────────────────────────────────────┐
│  🎯 Relevant Skills                                 │
└─────────────────────────────────────────────────────┘

  🎬  1. remotion-to-hyperframes  (73%)
       Translate an existing Remotion video compositi...
       ▶ HTML is the source of truth for video...
       ⚡ auto-hooks configured

  💡 Type /skill-name to invoke directly
```

**What you see:**
- **Category badge** — 🎬 Video | 🔍 Code Review | 🎨 Design | 📣 Marketing | etc.
- **Confidence score** — how well this skill matches your prompt
- **First action preview** — what happens when you invoke this skill
- **Hook indicator** — ⚡ means this skill has auto-hooks that fire on invocation

**To invoke a suggested skill:** Just type `/skill-name` (e.g., `/remotion`)

---

### Mode 2: Explicit Query

Search for skills without waiting for the auto-hook:

```bash
/skill-router security audit
```

Or using the CLI directly:
```bash
python3 ~/.claude/skills/skill-router/scripts/auto-match.py "security audit"
```

This bypasses the 30-second debounce and gives you instant results.

---

### Mode 3: Interactive Selection (NEW!)

Browse skills with full context before picking one:

```bash
/skill-router marketing --interactive
```

Or via CLI:
```bash
python3 ~/.claude/skills/skill-router/scripts/auto-match.py "marketing strategy" --interactive
```

You'll see a numbered list like this:

```
=======================================================
  🎯 Found 4 relevant skills for: "marketing strategy"
=======================================================

  [1] 📣 marketing-demand-acquisition (63%)
      Creates demand generation campaigns, optimizes paid ad spe...
      ▶ Acquisition playbook for Series A+ startups scaling internationally (EU/US/
      ⚡ auto: SessionStart

  [2] 📣 marketing-skills (55%)
      Directory and router for the marketing skills library. ...
      ▶ This is the index skill for the marketing plugin...

  What would you like to do?
    Type a number [1-4] to preview & invoke that skill
    Press Enter to accept all suggestions above
    Type 'q' to quit

> 1
🚀 Invoking /marketing-demand-acquisition ...
   Watching for the skill to activate...
✅ Skill 'marketing-demand-acquisition' ready to use.
   Type /marketing-demand-acquisition to invoke it now.
```

**Benefits:**
- See exactly what each skill does before picking
- Choose which one to invoke instead of guessing
- Preview hook behavior (auto-triggers)

---

### Mode 4: Verbose Explanation

Understand WHY each skill matched:

```bash
/skill-router code review --verbose
```

Output shows the matching keywords:

```
  🔍  1. zen-review              (53%)
       Expert code reviewer...
       ↳ matches: review, security audit
```

Perfect for learning what the router is looking for and tuning your prompts.

---

### Mode 5: Manual Index Refresh

When you add or remove skills, regenerate the index:

```bash
python3 ~/.claude/skills/skill-router/scripts/scan-skills.py
```

Preview what would be indexed (without writing):
```bash
python3 ~/.claude/skills/skill-router/scripts/scan-skills.py --dry-run
```

The router auto-detects changes and refreshes silently (<5ms), but manual refresh is useful after bulk installs.

---

## 🎯 Domains & Examples

The router recognizes **10 domains**. Here's what triggers each:

| Domain | Emoji | Example Prompt |
|--------|-------|----------------|
| Video/Animation | 🎬 | "Create a product launch video" |
| Code Review | 🔍 | "Review my PR for security issues" |
| Design/UI | 🎨 | "Design a landing page with animations" |
| Marketing | 📣 | "Write SEO content for our SaaS" |
| Research | 🔬 | "Research AI papers and write literature review" |
| Product | 🗺️ | "Create a product roadmap for Q4" |
| Finance/Business | 💰 | "Analyze revenue metrics and create business plan" |
| Testing | 🧪 | "Set up Playwright E2E tests" |
| Coding/Python | 🐍 | "Write Python code to scrape websites" |
| Coding/Web | 🌐 | "Build a Next.js app with TypeScript" |

---

## ⚙️ Configuration

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

| Setting | Default | Description |
|---------|---------|-------------|
| `min_confidence` | 10 | Minimum score (0-100) to show a skill |
| `max_suggestions` | 4 | How many skills to display |
| `debounce_seconds` | 30 | Cooldown between auto-fires |
| `skip_patterns` | `["_gstack-command", "pink-twill"]` | Always hide these skills |
| `personal_favorites` | `[]` | Always boost these skills to top |
| `verbose` | `false` | Show match explanations by default |

---


## 🔌 Cross-IDE Compatibility

Works with all major AI coding environments:

| IDE | Status | Adapter |
|-----|--------|---------|
| **Claude Code** | ✅ Native | Built-in hooks |
| **Cursor** | ✅ Tested | `.cursor/rules/skills.md` |
| **VS Code** | ✅ Tested | Extension manifest |
| **GitHub Copilot** | ✅ Tested | `.github/copilot-instructions.md` |
| **OpenCode / Antigravity** | ✅ Tested | `.opencode/skills/` |
| **Codex CLI** | 🔄 Beta | `codex.yaml` (unverified) |
| **Amazon byNara** | ⚠️ Experimental | Format assumed, not verified |
| **IBM Watsonx** | ⚠️ Experimental | Format assumed, not verified |

### Generate For Your IDE

```bash
# For all supported IDEs
python3 adapters/generate_all.py --output ~/.your-ide-config

# Verified IDEs
python3 adapters/generate_all.py --ide cursor --output ~/.cursor
python3 adapters/generate_all.py --ide vscode --output ~/your-project
python3 adapters/generate_all.py --ide copilot --output .
python3 adapters/generate_all.py --ide opencode --output ~/.opencode

# Beta (untested format assumptions)
python3 adapters/generate_all.py --ide codex --output ~/.codex
python3 adapters/generate_all.py --ide bynara --output ~/.byNara
python3 adapters/generate_all.py --ide ibm --output ~/.watsonx
```

### How It Works

1. **Read** the canonical `skill_index.csv` (557+ skills)
2. **Transform** each skill into the target IDE's format
3. **Output** files in the correct location
4. **Sync** automatically when you add/remove skills

See [`adapters/README.md`](./adapters/README.md) for full details.

---

## 🔧 Troubleshooting

### Skills not showing up?

1. Check if the skill is installed: `ls ~/.claude/skills/`
2. Rebuild the index: `python3 ~/.claude/skills/skill-router/scripts/scan-skills.py`
3. Test manually: `python3 ~/.claude/skills/skill-router/scripts/auto-match.py "your query"`

### Hook error "No such file or directory"?

The hook path changed in v9. Update your SKILL.md:
```
Old: bash ~/.claude/skills/skill-router/hooks-handlers/auto-match.sh
New: bash ~/.claude/skills/skill-router/scripts/router.sh
```

### Want to see more/fewer skills?

Adjust in `config.json`:
- `max_suggestions: 6` for more results
- `min_confidence: 20` for higher precision only

---

## 📂 Repository Structure

```
claude-skill-router/
├── README.md                 # This file
├── SKILL.md                  # Hook definition for Claude Code
├── config.json               # Your configuration
├── scripts/
│   ├── auto-match.py         # v9 matching engine (647 lines)
│   ├── router.sh             # Shell entry point
│   └── scan-skills.py        # Regenerates skill_index.csv
└── references/
    └── skill_index.csv       # Generated index of your skills
```

---

## 🎓 How It Works

1. **Domain Detection** — Scans your prompt for keywords across 10 domains
2. **Two-Pass Scoring** — Finds primary domain first, then ranks within it
3. **Exclusive Bonuses** — Skills with domain-specific names get +25 boost
4. **Cross-Domain Penalty** — Ambiguous skills get downweighted
5. **Context Boosting** — Reads project files (`package.json`, `.gitignore`) to bias results
6. **Auto-Refresh** — Detects when you add/remove skills and rebuilds index silently

---

## 🧪 Testing

Run all test scenarios:
```bash
# Test different domains
python3 scripts/auto-match.py "create a video" --verbose
python3 scripts/auto-match.py "design a landing page" --interactive
python3 scripts/auto-match.py "review my PR" --verbose
python3 scripts/auto-match.py "write marketing copy" --interactive

# Test scan
python3 scripts/scan-skills.py --dry-run
```

---

## 📝 License

MIT
