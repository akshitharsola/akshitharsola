#!/usr/bin/env python3
"""Generate a "which projects use this tech" list for the README Tech Stack
section, and splice it into README.md between the TECH_MAP marker comments.

Matches each declared skill against repos by primary `language` and by
keyword search over each repo's name + description (topics are mostly
unset on this account, so description text is the more reliable signal).

Requires env var GH_TOKEN (a token with public_repo read access is enough).
"""
import os
import sys
import json
import re
import urllib.request

USERNAME = "akshitharsola"
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

API = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": USERNAME,
}

README_PATH = os.path.join(os.path.dirname(__file__), "..", "README.md")
MARKER_START = "<!-- TECH_MAP:START -->"
MARKER_END = "<!-- TECH_MAP:END -->"

# name -> (display label, language match, keyword patterns to search in name+description)
SKILLS = {
    "python": ("Python", "Python", []),
    "cpp": ("C++", "C++", []),
    "kotlin": ("Kotlin", "Kotlin", []),
    "swift": ("Swift", "Swift", []),
    "ts": ("TypeScript", "TypeScript", []),
    "js": ("JavaScript", "JavaScript", []),
    "pytorch": ("PyTorch", None, [r"pytorch"]),
    "tensorflow": ("TensorFlow", None, [r"tensorflow"]),
    "opencv": ("OpenCV", None, [r"opencv"]),
    "raspberrypi": ("Raspberry Pi", None, [r"raspberry\s*pi"]),
    "arduino": ("Arduino", None, [r"arduino"]),
    "fastapi": ("FastAPI", None, [r"fastapi"]),
    "docker": ("Docker", None, [r"docker"]),
    "git": ("Git", None, []),
    "github": ("GitHub", None, []),
    "linux": ("Linux", None, [r"\blinux\b"]),
    "androidstudio": ("Android Studio", None, [r"android"]),
    "react": ("React", None, [r"\breact\b"]),
    "gradle": ("Gradle", None, [r"gradle"]),
}


def gh_get(path):
    url = path if path.startswith("http") else f"{API}{path}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def fetch_repos():
    repos = gh_get(f"/users/{USERNAME}/repos?per_page=100&type=owner")
    return [r for r in repos if not r.get("fork")]


def build_tech_map(repos):
    tech_map = {}
    for key, (label, lang, patterns) in SKILLS.items():
        matches = []
        for repo in repos:
            haystack = f"{repo['name']} {repo.get('description') or ''}".lower()
            hit = False
            if lang and repo.get("language") == lang:
                hit = True
            for pat in patterns:
                if re.search(pat, haystack, re.IGNORECASE):
                    hit = True
                    break
            if hit:
                matches.append(repo["name"])
        tech_map[key] = (label, sorted(set(matches)))
    return tech_map


ROWS = [
    ("Languages", ["python", "cpp", "kotlin", "swift", "ts", "js"]),
    ("ML · Robotics · Vision", ["pytorch", "tensorflow", "opencv", "raspberrypi", "arduino"]),
    ("Backend · Infra · Tools", ["fastapi", "docker", "git", "github", "linux"]),
    ("Mobile & Frontend", ["androidstudio", "swift", "react", "gradle"]),
]


def render_markdown(tech_map):
    lines = [MARKER_START, "", "<details>", "<summary><b>📂 Projects by technology</b></summary>", ""]
    for section, keys in ROWS:
        lines.append(f"**{section}**")
        lines.append("")
        for key in keys:
            label, repos = tech_map[key]
            if repos:
                repo_links = ", ".join(f"[{r}](https://github.com/{USERNAME}/{r})" for r in repos)
                lines.append(f"- **{label}**: {repo_links}")
            else:
                lines.append(f"- **{label}**: _no public repos yet_")
        lines.append("")
    lines.append("</details>")
    lines.append("")
    lines.append(MARKER_END)
    return "\n".join(lines)


def splice_into_readme(block):
    with open(README_PATH) as f:
        content = f.read()

    if MARKER_START not in content or MARKER_END not in content:
        sys.exit("TECH_MAP markers not found in README.md — add them manually first")

    pattern = re.compile(re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END), re.DOTALL)
    content = pattern.sub(block, content)

    with open(README_PATH, "w") as f:
        f.write(content)


def main():
    if not TOKEN:
        sys.exit("GH_TOKEN/GITHUB_TOKEN env var required")

    repos = fetch_repos()
    tech_map = build_tech_map(repos)
    block = render_markdown(tech_map)
    splice_into_readme(block)
    print("Updated README.md Tech Stack project map")


if __name__ == "__main__":
    main()
