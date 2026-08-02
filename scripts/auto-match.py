#!/usr/bin/env python3
"""Skill Router v9 — Intelligent prompt-to-skill matcher.

Features:
  - Two-pass domain detection (primary + secondary domains)
  - Exclusive keyword bonuses for precise matching
  - Cross-domain disambiguation penalty
  - Auto-index refresh (detects new/removed skills silently)
  - Explicit query mode: /skill-router <query>
  - Category badges in output
  - "Why this skill" explanation on verbose mode
  - Context-aware boosting (reads package.json, .gitignore)
  - Session memory (avoids repeated suggestions)
  - Configurable thresholds, debounce, skip patterns
"""

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path


# ── Paths ───────────────────────────────────────────────────────────────
BASE_DIR      = Path.home() / ".claude" / "skills" / "skill-router"
SCRIPTS_DIR   = BASE_DIR / "scripts"
REFERENCES    = BASE_DIR / "references"
CSV_PATH      = REFERENCES / "skill_index.csv"
CACHE_FILE    = REFERENCES / "last_run.json"
MEMORY_FILE   = REFERENCES / "session_memory.json"
CONFIG_PATH   = BASE_DIR / "config.json"

DEBOUNCE_SECONDS = 30
INDEX_HASH_TTL   = 60  # Re-check index freshness every 60s


# ── Defaults ────────────────────────────────────────────────────────────
DEFAULT_CONFIG = {
    "min_confidence": 10,
    "max_suggestions": 4,
    "show_every": 5,
    "skip_patterns": ["_gstack-command", "pink-twill"],
    "auto_invoke": False,
    "verbose": False,
    "debounce_seconds": DEBOUNCE_SECONDS,
    "version": "9",
    "personal_favorites": [],   # skills to always surface
}


def load_config():
    """Load config, merge with defaults."""
    cfg = dict(DEFAULT_CONFIG)
    try:
        if CONFIG_PATH.exists():
            user_cfg = json.loads(CONFIG_PATH.read_text())
            cfg.update(user_cfg)
    except Exception:
        pass
    return cfg


CFG = load_config()


# ── Domains ─────────────────────────────────────────────────────────────
DOMAINS = {
    "video/animation": {
        "strong": ["video", "animation", "render", "film", "movie", "hyperframes",
                   "remotion", "motion graphics", "studio", "timeline", "scene"],
        "weak":   ["clip", "compose", "frame", "composition"],
        "exclusive": ["hyperframes", "remotion", "webcodecs", "producer",
                      "product-launch-video", "faceless-explainer", "pr-to-video",
                      "embedded-captions", "talking-head-recut", "music-to-video",
                      "slideshow", "general-video", "remotion-to-hyperframes"],
    },
    "code/review": {
        "strong": ["code review", "pr review", "pull request", "debug", "vulnerability",
                   "static analysis", "lint", "refactor", "quality gate", "code smell",
                   "technical debt", "semgrep", "sast", "dast", "security audit",
                   "review this pr", "adversarial review"],
        "weak":   ["review", "check", "analyze"],
        "exclusive": ["zen-review", "adversarial-reviewer", "karpathy-coder",
                      "code-smell-detective", "security-pen-testing", "cso",
                      "md-review", "|review"],
    },
    "design/ui": {
        "strong": ["ui design", "ux design", "interface design", "landing page",
                   "website design", "visual design", "brand identity", "graphic design",
                   "color palette", "typography", "accessibility", "responsive design",
                   "design system", "wireframe", "prototype", "figma",
                   "apple hig", "material design", "creative direction",
                   "css animation", "gsap", "tailwind", "component library",
                   "artifacts builder", "canvas design", "frontend design", "html css"],
        "weak":   ["layout", "style", "theme", "modern", "beautiful"],
        "exclusive": ["apple-hig-expert", "frontend-design", "landing-page-generator",
                      "canvas-design", "artifacts-builder", "design-html"],
    },
    "marketing": {
        "strong": ["marketing", "seo", "aeo", "copywriting", "content strategy",
                   "social media", "email marketing", "lead generation", "conversion",
                   "growth hacking", "funnel", "campaign", "advertising",
                   "brand awareness", "demand gen", "demand generation"],
        "weak":   ["write copy", "social post"],
        "exclusive": ["marketing-skills", "cs-demand-gen-specialist",
                      "content-production", "copywriting", "marketing-ideas",
                      "marketing-psychology", "seo-audit"],
    },
    "research": {
        "strong": ["literature review", "academic research", "study methodology",
                   "survey design", "interview guide", "user research",
                   "competitive analysis", "market research", "dossier",
                   "entity research", "due diligence", "lit review"],
        "weak":   ["research", "read paper"],
        "exclusive": ["dossier", "content-research-writer", "literature-review",
                      "research-finance", "cs-content-creator"],
    },
    "product": {
        "strong": ["product roadmap", "product strategy", "agile", "sprint planning",
                   "backlog grooming", "epic", "user story", "jtbd",
                   "pmf", "product market fit", "okrs", "feature prioritization",
                   "roadmap planning", "sprint"],
        "weak":   ["product plan"],
        "exclusive": ["cs-agile-product-owner", "cpo-review", "scrum-master",
                      "agile-product-owner", "sprint-plan"],
    },
    "finance/business": {
        "strong": ["revenue", "profit", "finance", "accounting", "budget",
                   "financial model", "cfo", "ceo", "coo", "board meeting",
                   "investor deck", "fundraising", "valuation", "unit economics",
                   "arr", "mrr", "burn rate", "runway", "pitch deck", "cro",
                   "revenue operations"],
        "weak":   ["business", "sales", "metrics"],
        "exclusive": ["revenue-operations", "cro-review", "saas-metrics-coach",
                      "cs-growth-strategist", "finance-agent"],
    },
    "testing": {
        "strong": ["playwright", "e2e test", "integration test", "unit test",
                   "api test", "browser test", "qa", "test automation",
                   "selenium", "cypress", "jest", "pytest", "tdd", "bdd"],
        "weak":   ["test", "debug"],
        "exclusive": ["senior-qa", "api-test-suite-builder", "playwright",
                      "tdd-guide", "test-automation"],
    },
    "coding/python": {
        "strong": ["python", "django", "flask", "fastapi", "pandas", "numpy",
                   "scikit-learn", "tensorflow", "pytorch", "scripting",
                   "backend api", "rest api", "graphql", "database",
                   "web scraping", "automation script", "data pipeline",
                   "asyncio", "sqlalchemy", "postgresql", "mongodb"],
        "weak":   ["api", "scrape"],
        "exclusive": ["karpathy-coder", "python-tutor", "fullstack-python",
                      "senior-fullstack", "python-patterns"],
    },
    "coding/web": {
        "strong": ["javascript", "typescript", "react", "nextjs", "vue",
                   "angular", "node.js", "express", "webpack", "vite",
                   "frontend framework", "full stack", "spa", "ssr",
                   "csr", "tailwind", "bootstrap"],
        "weak":   ["web", "frontend", "app", "framework"],
        "exclusive": ["senior-fullstack", "artifacts-builder", "landing-page-generator",
                      "nextjs-boilerplate", "typescript-patterns"],
    },
}

_STRONG_SETS  = {d: set(c["strong"]) for d, c in DOMAINS.items()}
_WEAK_SETS    = {d: set(c["weak"])   for d, c in DOMAINS.items()}
_EXCL_SETS    = {d: set(c["exclusive"]) for d, c in DOMAINS.items()}


# ── Loading ─────────────────────────────────────────────────────────────

def load_skill_db():
    """Load skills from CSV. Returns list of dicts."""
    skills = []
    if not CSV_PATH.exists():
        return skills
    with open(CSV_PATH, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader, None)  # skip header
        for row in reader:
            if len(row) >= 2:
                name   = row[0].strip()
                desc   = row[1].strip()
                triggers = row[2].strip() if len(row) > 2 else ""
                if name.startswith("_") or name in ("name", "skill-router"):
                    continue
                if not name or not desc:
                    continue
                skills.append({
                    "name":          name,
                    "desc":          desc.lower(),
                    "triggers":      triggers.lower(),
                    "original_desc": desc,
                })
    return skills


def _compute_index_hash(skills):
    """Create a fingerprint of the current skill set for staleness detection."""
    h = hashlib.sha256()
    for s in sorted(skills, key=lambda x: x["name"]):
        h.update(s["name"].encode())
        h.update(s["original_desc"][:80].encode())
    return h.hexdigest()[:16]


def _get_session_id():
    """Unique per-session ID to avoid cross-session memory pollution."""
    sid = os.environ.get("CLAUDE_SESSION_ID", "")
    if not sid:
        sid = str(os.getpid())
    return sid


def load_session_memory():
    """Load per-session memory (recently shown skills, ignored skills)."""
    try:
        if MEMORY_FILE.exists():
            return json.loads(MEMORY_FILE.read_text())
    except Exception:
        pass
    return {"sessions": {}, "personal_favorites": CFG.get("personal_favorites", [])}


def save_session_memory(mem):
    try:
        MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        MEMORY_FILE.write_text(json.dumps(mem))
    except Exception:
        pass


# ── Index Refresh ──────────────────────────────────────────────────────

def check_and_refresh_index(config):
    """Silently re-scan if skills directory has changed since last index."""
    cache = {}
    try:
        if CACHE_FILE.exists():
            cache = json.loads(CACHE_FILE.read_text())
    except Exception:
        pass

    now = time.time()
    last_check = cache.get("last_check", 0)

    # Only re-check TTL seconds apart
    if now - last_check < INDEX_HASH_TTL:
        return

    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    cache["last_check"] = now
    CACHE_FILE.write_text(json.dumps(cache))

    # Compute current hash from disk
    current_hash = _scan_skills_for_hash()
    cached_hash  = cache.get("index_hash", "")

    if current_hash != cached_hash:
        # Index is stale — regenerate
        _build_index_csv()
        cache["index_hash"] = current_hash
        CACHE_FILE.write_text(json.dumps(cache))


def _scan_skills_for_hash():
    """Compute hash of all installed skills without loading descriptions."""
    h = hashlib.sha256()
    skills_dir = Path.home() / ".claude" / "skills"
    for d in sorted(skills_dir.iterdir()):
        if d.is_dir() and (d / "SKILL.md").exists():
            h.update(d.name.encode())
    return h.hexdigest()[:16]


def _build_index_csv():
    """Scan ~/.claude/skills/ and regenerate skill_index.csv."""
    import subprocess
    # Run the scan script
    scan_script = SCRIPTS_DIR / "scan-skills.py"
    if scan_script.exists():
        try:
            subprocess.run([sys.executable, str(scan_script)], capture_output=True, timeout=30)
        except Exception:
            pass


# ── Context Boosting ───────────────────────────────────────────────────

_DOMAIN_BOOSTS = {
    "video/animation": ["remotion.config.", "hyperframes", "video/", "*.mp4", "*.mov"],
    "code/review":     [".github/workflows/", "review-", "*test*", "SECURITY.md"],
    "design/ui":       ["tailwind.config", "components/", "*.css", "*.scss", "figma"],
    "marketing":       ["content/", "blog/", "marketing/", "newsletter"],
    "research":        ["papers/", "research/", "analysis/", "dossier"],
    "product":         ["ROADMAP.md", "product/", "sprint-board"],
    "finance/business": ["finance/", "revenue.md", "board/", "pitch"],
    "testing":         ["playwright.config", "cypress.config", "*.test.", "*.spec."],
    "coding/python":   ["requirements.txt", "pyproject.toml", "Dockerfile", "*.py"],
    "coding/web":      ["package.json", "next.config", "tsconfig.json", "vite.config"],
}


def compute_context_boost(project_root):
    """Read project files to boost relevant domains. Returns domain → weight map."""
    boosts = {}
    cwd = Path(project_root) if project_root else Path.cwd()

    # Check common project files
    pattern_files = [
        cwd / "package.json",
        cwd / "requirements.txt",
        cwd / "pyproject.toml",
        cwd / "Cargo.toml",
        cwd / "go.mod",
        cwd / "Makefile",
        cwd / ".gitignore",
        cwd / "README.md",
    ]

    context_text = ""
    for pf in pattern_files:
        if pf.exists():
            try:
                context_text += pf.read_text()[:2000] + "\n"
            except Exception:
                pass

    for domain, patterns in _DOMAIN_BOOSTS.items():
        score = sum(1 for p in patterns if p.replace("*", "") in context_text.lower())
        if score > 0:
            boosts[domain] = score

    return boosts


# ── Session Memory ─────────────────────────────────────────────────────

def get_session_key(sid):
    return f"{sid}:{time.strftime('%Y%m%d')}"


def recently_shown(mem, skill_name, window=12):
    """Check if this skill was shown in the last N seconds."""
    sk = get_session_key(_get_session_id())
    shown = mem.get("shown", {}).get(sk, [])
    now = time.time()
    # Prune old entries
    shown = [t for t in shown if now - t < window * 60]
    if skill_name in [n for n, _ in shown[-5:]]:
        return True
    return False


def record_shown(mem, skill_name):
    sk = get_session_key(_get_session_id())
    if "shown" not in mem:
        mem["shown"] = {}
    if sk not in mem["shown"]:
        mem["shown"][sk] = []
    mem["shown"][sk].append((skill_name, time.time()))
    # Keep only last 20
    mem["shown"][sk] = mem["shown"][sk][-20:]
    save_session_memory(mem)


# ── Scoring ─────────────────────────────────────────────────────────────

def detect_primary_domains(input_lower, context_boosts=None):
    """Detect which domain(s) the input targets. Returns ordered list."""
    scores = {}
    for domain, strong in _STRONG_SETS.items():
        s = sum(1 for kw in strong if kw in input_lower)
        w = sum(1 for kw in _WEAK_SETS[domain] if kw in input_lower)
        # Apply context boost
        ctx = (context_boosts or {}).get(domain, 0)
        if s > 0 or w > 0 or ctx > 0:
            scores[domain] = (s * 2 + w) + (ctx * 3)
    return [d for d, s in sorted(scores.items(), key=lambda item: item[1], reverse=True) if s > 0]


def score_skill(skill, input_lower, primary_domains, context_boosts=None):
    """Score a skill considering domain, exclusives, context, and personal prefs."""
    if not primary_domains:
        return 0
    top_domain = primary_domains[0]
    other_domains = primary_domains[1:]
    top_config = DOMAINS[top_domain]
    ctx_boost  = (context_boosts or {}).get(top_domain, 0)

    def _domain_score(dom_cfg):
        strong  = dom_cfg["strong"]
        weak    = dom_cfg["weak"]
        excl    = dom_cfg.get("exclusive", [])
        in_s    = sum(1 for kw in strong if kw in input_lower)
        in_w    = sum(1 for kw in weak   if kw in input_lower)
        if in_s == 0 and in_w == 0:
            return 0
        sk = skill["desc"] + " " + skill["name"]
        sk_s  = sum(1 for kw in strong if kw in sk)
        sk_e  = sum(1 for kw in excl    if kw in skill["name"] or kw in skill["triggers"])
        if sk_s == 0 and sk_e == 0:
            return 0
        sc = in_s * 10 + in_w * 4 + sk_s * 5 + sk_e * 15
        for kw in strong:
            if kw in input_lower and kw in skill["triggers"]:
                sc += 8
        for word in re.findall(r"\b\w{4,}\b", input_lower):
            if word in skill["name"]:
                sc += 12
                break
        desc_long = set(re.findall(r"\b\w{4,}\b", skill["desc"]))
        input_long = set(re.findall(r"\b\w{4,}\b", input_lower))
        dw = set()
        for kw in strong + weak:
            dw.add(kw)
            for p in kw.split():
                if len(p) > 3:
                    dw.add(p)
        sc += min(len(desc_long & dw & input_long) * 3, 15)
        if len(desc_long) > 100 and sk_s == 0:
            sc -= 10
        return max(0, sc)

    total = _domain_score(top_config)
    if ctx_boost > 0:
        total *= (1 + ctx_boost * 0.1)  # Up to ~50% boost for strong context match
    for d in other_domains:
        total += _domain_score(DOMAINS[d]) * 0.6
    if skill["name"] in CFG.get("personal_favorites", []):
        total += 30
    return max(0, int(total))


def get_matched_keywords(skill, input_lower, primary_domains):
    """Return list of (keyword, domain) pairs that caused this match."""
    matched = []
    seen = set()
    for domain in primary_domains:
        config = DOMAINS[domain]
        for kw in config["strong"] + config["weak"]:
            if kw in input_lower and kw in skill["desc"] + " " + skill["name"]:
                pair = (kw, domain)
                if pair not in seen:
                    seen.add(pair)
                    matched.append(kw)
    # Also check trigger column
    for kw in input_lower.split():
        if len(kw) > 3 and kw in skill["triggers"]:
            matched.append(f"[trigger] {kw}")
    return matched[:5]  # Limit to top 5


# ── Debounce ────────────────────────────────────────────────────────────

def should_fire():
    """Debouncing with optimistic write."""
    prev_ts = None
    try:
        if CACHE_FILE.exists():
            prev_ts = json.loads(CACHE_FILE.read_text()).get("timestamp", None)
    except Exception:
        pass

    now = time.time()
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        CACHE_FILE.write_text(json.dumps({"timestamp": now}))
    except Exception:
        pass

    if prev_ts is not None:
        elapsed = now - prev_ts
        if elapsed < CFG.get("debounce_seconds", DEBOUNCE_SECONDS):
            try:
                CACHE_FILE.write_text(json.dumps({"timestamp": prev_ts}))
            except Exception:
                pass
            return False, round(CFG.get("debounce_seconds", DEBOUNCE_SECONDS) - elapsed)
    return True, 0


# ── Output ──────────────────────────────────────────────────────────────

CATEGORY_EMOJI = {
    "video/animation":  "🎬",
    "code/review":      "🔍",
    "design/ui":        "🎨",
    "marketing":        "📣",
    "research":         "🔬",
    "product":          "🗺️",
    "finance/business": "💰",
    "testing":          "🧪",
    "coding/python":    "🐍",
    "coding/web":       "🌐",
}


def print_header():
    print("")
    print("┌─────────────────────────────────────────────────────┐")
    print("│  🎯 Relevant Skills                                 │")
    print("└─────────────────────────────────────────────────────┘")
    print("")


def print_results(results, verbose=False):
    if not results:
        return
    print_header()
    for score, skill, domain, kw_list in results:
        conf  = min(95, int(score))
        badge = CATEGORY_EMOJI.get(domain, "📌")
        desc  = skill["original_desc"][:65].replace("\n", " ")
        print(f"  {badge}  {skill['name']:<23s}  ({conf}%)")
        print(f"       {desc}...")
        if verbose and kw_list:
            print(f"       ↳ matches: {', '.join(kw_list)}")
        print("")
    print("  💡 Type /skill-router <query> to search manually")
    print("     Or type /skill-name to invoke directly")
    print("")


# ── Main ────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Skill Router v9")
    parser.add_argument("query", nargs="?", help="Optional explicit query (for /skill-router <query>)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show why each skill matched")
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without printing")
    args = parser.parse_args()

    # Get input text
    if args.query:
        input_text = args.query
    else:
        input_text = os.environ.get("CLAUDE_INPUT", "")
        if not input_text and not sys.stdin.isatty():
            input_text = sys.stdin.read().strip()
    if not input_text:
        sys.exit(0)

    # Debounce (only for auto-hook, not explicit invocation)
    if not args.query:
        ok, remaining = should_fire()
        if not ok:
            print(f"# Skill router: throttled ({remaining}s)")
            sys.exit(0)

    # Load & refresh index
    skills = load_skill_db()
    check_and_refresh_index(CFG)
    # Reload after potential refresh
    skills = load_skill_db()
    if not skills:
        print("# No skills found. Run: python3 scripts/scan-skills.py")
        sys.exit(0)

    input_lower = input_text.lower()

    # Detect primary domains
    context_boosts = compute_context_boost(None)
    primary_domains = detect_primary_domains(input_lower, context_boosts)
    if not primary_domains:
        sys.exit(0)

    # Score all skills
    mem = load_session_memory()
    max_suggestions = CFG.get("max_suggestions", 4)
    results = []
    for s in skills:
        if any(sp in s["name"] for sp in CFG.get("skip_patterns", [])):
            continue
        score = score_skill(s, input_lower, primary_domains, context_boosts)
        if score >= CFG.get("min_confidence", 10):
            # Find best matching domain
            best_domain = primary_domains[0]
            best_score  = score
            for d in primary_domains:
                ds = _domain_score_for_domain(s, input_lower, DOMAINS[d], context_boosts.get(d, 0))
                if ds > best_score:
                    best_score = ds
                    best_domain = d
            kws = get_matched_keywords(s, input_lower, primary_domains)
            if not recently_shown(mem, s["name"]):
                results.append((best_score, s, best_domain, kws))

    # Sort by score descending
    results.sort(key=lambda x: x[0], reverse=True)
    results = results[:max_suggestions]

    # Record shown
    for _, s, _, _ in results:
        record_shown(mem, s["name"])

    if not results:
        sys.exit(0)

    print_results(results, verbose=args.verbose or CFG.get("verbose", False))


def _domain_score_for_domain(skill, input_lower, config, ctx_boost):
    """Helper: raw score for a single domain."""
    strong  = config["strong"]
    weak    = config["weak"]
    excl    = config.get("exclusive", [])
    in_s    = sum(1 for kw in strong if kw in input_lower)
    in_w    = sum(1 for kw in weak   if kw in input_lower)
    if in_s == 0 and in_w == 0:
        return 0
    sk = skill["desc"] + " " + skill["name"]
    sk_s  = sum(1 for kw in strong if kw in sk)
    sk_e  = sum(1 for kw in excl    if kw in skill["name"] or kw in skill["triggers"])
    if sk_s == 0 and sk_e == 0:
        return 0
    sc = in_s * 10 + in_w * 4 + sk_s * 5 + sk_e * 15
    for kw in strong:
        if kw in input_lower and kw in skill["triggers"]:
            sc += 8
    for word in re.findall(r"\b\w{4,}\b", input_lower):
        if word in skill["name"]:
            sc += 12
            break
    desc_long = set(re.findall(r"\b\w{4,}\b", skill["desc"]))
    input_long = set(re.findall(r"\b\w{4,}\b", input_lower))
    dw = set()
    for kw in strong + weak:
        dw.add(kw)
        for p in kw.split():
            if len(p) > 3:
                dw.add(p)
    sc += min(len(desc_long & dw & input_long) * 3, 15)
    if len(desc_long) > 100 and sk_s == 0:
        sc -= 10
    if ctx_boost > 0:
        sc *= (1 + ctx_boost * 0.1)
    return max(0, sc)


if __name__ == "__main__":
    main()
