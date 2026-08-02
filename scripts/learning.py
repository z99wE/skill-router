#!/usr/bin/env python3
"""Learning layer for skill router - tracks what you actually use vs ignore.

Usage:
    from learning import LearningTracker
    tracker = LearningTracker()
    
    # Record that we showed these skills
    tracker.record_impression("user-prompt-id", ["remotion", "zen-review"])
    
    # Record that user picked this skill
    tracker.record_selection("remotion")
    
    # Get learned preferences
    preferences = tracker.get_preferences()
"""

import json
import time
from pathlib import Path
from datetime import datetime, timedelta


class LearningTracker:
    """Tracks skill usage patterns to learn user preferences over time."""
    
    def __init__(self, data_dir=None):
        if data_dir is None:
            data_dir = Path.home() / ".claude/skills/skill-router/references"
        self.data_dir = Path(data_dir)
        self.data_file = self.data_dir / "learning_data.json"
        self.data = self._load()
        
    def _load(self):
        """Load learning data from disk."""
        if self.data_file.exists():
            try:
                return json.loads(self.data_file.read_text())
            except:
                pass
        return {
            "impressions": [],  # [session_id, timestamp, skill_names]
            "selections": {},   # {skill_name: count}
            "ignores": {},      # {skill_name: count}
            "boosted": [],      # Skills that got +boost from frequent use
            "demoted": [],      # Skills that got -penalty from ignores
            "last_reset": None
        }
    
    def _save(self):
        """Persist learning data to disk."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.data_file.write_text(json.dumps(self.data, indent=2))
    
    def record_impression(self, session_id, skill_names):
        """Record that we showed these skills to the user."""
        self.data["impressions"].append({
            "session_id": session_id,
            "timestamp": time.time(),
            "skills": skill_names
        })
        
        # Keep only last 100 impressions to prevent bloat
        if len(self.data["impressions"]) > 100:
            self.data["impressions"] = self.data["impressions"][-100:]
        
        self._save()
    
    def record_selection(self, skill_name):
        """Record that the user actually invoked this skill."""
        self.data["selections"][skill_name] = self.data["selections"].get(skill_name, 0) + 1
        
        # Boost recently used skills (last 7 days)
        recent_uses = self._recent_selections(days=7)
        if skill_name in recent_uses and recent_uses[skill_name] >= 3:
            if skill_name not in self.data["boosted"]:
                self.data["boosted"].append(skill_name)
                print(f"  📈 Skill '{skill_name}' boosted - used frequently!")
        
        self._save()
    
    def record_ignore(self, skill_name):
        """Record that the user ignored this suggestion."""
        self.data["ignores"][skill_name] = self.data["ignores"].get(skill_name, 0) + 1
        
        # Demote persistently ignored skills
        total_shown = self.data["selections"].get(skill_name, 0) + self.data["ignores"].get(skill_name, 0)
        if total_shown >= 5 and self.data["ignores"].get(skill_name, 0) >= 4:
            if skill_name not in self.data["demoted"]:
                self.data["demoted"].append(skill_name)
                print(f"  ⬇️  Skill '{skill_name}' demoted - rarely used")
        
        self._save()
    
    def _recent_selections(self, days=7):
        """Get selection counts for recent period."""
        cutoff = time.time() - (days * 86400)
        recent = {}
        for impression in self.data["impressions"]:
            if impression["timestamp"] > cutoff:
                for skill in impression.get("skills", []):
                    recent[skill] = recent.get(skill, 0) + 1
        return recent
    
    def get_boost(self, skill_name):
        """Get learning-based boost for a skill (0-20 points)."""
        # Base boost from frequency
        total_uses = self.data["selections"].get(skill_name, 0)
        total_shown = total_uses + self.data["ignores"].get(skill_name, 0)
        
        if total_shown == 0:
            return 0
        
        # Calculate ratio: more uses = higher boost
        usage_ratio = total_uses / total_shown
        base_boost = int(usage_ratio * 15)  # Max 15 points from frequency
        
        # Extra boost if in boosted list
        if skill_name in self.data["boosted"]:
            base_boost += 5
        
        # Penalty if in demoted list
        if skill_name in self.data["demoted"]:
            base_boost -= 10
        
        return max(0, base_boost)
    
    def get_preferences(self):
        """Get summary of learned preferences."""
        return {
            "top_skills": sorted(
                self.data["selections"].items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:10],
            "ignored_skills": sorted(
                [(k, v) for k, v in self.data["ignores"].items() if v >= 2],
                key=lambda x: x[1],
                reverse=True
            )[:10],
            "total_impressions": len(self.data["impressions"]),
            "total_selections": sum(self.data["selections"].values()),
            "boosted": self.data["boosted"],
            "demoted": self.data["demoted"]
        }
    
    def reset(self):
        """Reset all learning data."""
        self.data = {
            "impressions": [],
            "selections": {},
            "ignores": {},
            "boosted": [],
            "demoted": [],
            "last_reset": datetime.now().isoformat()
        }
        self._save()
        print("✅ Learning data reset")


if __name__ == "__main__":
    import sys
    tracker = LearningTracker()
    
    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "stats":
            prefs = tracker.get_preferences()
            print(f"\n📊 Learning Stats:")
            print(f"   Total impressions: {prefs['total_impressions']}")
            print(f"   Total selections: {prefs['total_selections']}")
            if prefs['top_skills']:
                print(f"\n   Top skills:")
                for skill, count in prefs['top_skills']:
                    print(f"      ✓ {skill}: {count}x used")
            if prefs['ignored_skills']:
                print(f"\n   Ignored skills:")
                for skill, count in prefs['ignored_skills']:
                    print(f"      ✗ {skill}: {count}x ignored")
        elif cmd == "reset":
            tracker.reset()
        else:
            print(f"Unknown command: {cmd}")
    else:
        print("Usage: python3 learning.py [stats|reset]")
