#!/usr/bin/env python3
"""Generate a "which projects use this tech" list for the README Tech Stack
section, and splice it into README.md between the TECH_MAP marker comments.

Unlike a naive language/description match, this uses GitHub's code search
API to look for real signal inside each repo (dependency manifests, config
files) so frameworks/tools actually used but not mentioned in the repo
description or captured by the primary `language` field still get credit.

Requires env var GH_TOKEN (a token with public_repo + code search access —
a normal GITHUB_TOKEN in Actions is enough for public repos).
"""
import os
import sys
import json
import time
import urllib.request
import urllib.parse

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


def gh_get(path):
    url = path if path.startswith("http") else f"{API}{path}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def code_search(query, retries=4):
    """Run a GitHub code search query, return set of matching repo names.
    Retries with backoff on rate limiting instead of silently swallowing
    failures (a swallowed error would render as a false "not used")."""
    q = urllib.parse.quote(f"{query} user:{USERNAME}")
    url = f"{API}/search/code?q={q}&per_page=50"
    for attempt in range(retries):
        try:
            return {item["repository"]["name"] for item in gh_get(url).get("items", [])}
        except urllib.error.HTTPError as e:
            if e.code in (403, 429) and attempt < retries - 1:
                wait = int(e.headers.get("Retry-After", 15))
                print(f"  rate limited on '{query}', waiting {wait}s...", file=sys.stderr)
                time.sleep(wait)
                continue
            raise


def fetch_owned_repos():
    repos = gh_get(f"/users/{USERNAME}/repos?per_page=100&type=owner")
    return {r["name"] for r in repos if not r.get("fork")}


# label -> list of code-search queries (results are unioned); language-based
# skills fall back to the repo's primary `language` field instead of search.
SKILL_QUERIES = {
    "python": {"label": "Python", "language": "Python"},
    "cpp": {"label": "C++", "language": "C++"},
    "kotlin": {"label": "Kotlin", "language": "Kotlin"},
    "swift": {"label": "Swift", "language": "Swift"},
    "ts": {"label": "TypeScript", "language": "TypeScript"},
    "js": {"label": "JavaScript", "language": "JavaScript"},
    "pytorch": {"label": "PyTorch", "queries": ["torch in:file filename:requirements.txt"]},
    "tensorflow": {"label": "TensorFlow", "queries": ["tensorflow in:file filename:requirements.txt"]},
    "opencv": {"label": "OpenCV", "queries": ["opencv in:file filename:requirements.txt"]},
    "raspberrypi": {"label": "Raspberry Pi", "queries": ["raspberry in:readme"]},
    "arduino": {"label": "Arduino", "queries": ["arduino in:readme", "filename:*.ino"]},
    "fastapi": {"label": "FastAPI", "queries": ["fastapi in:file filename:requirements.txt"]},
    "docker": {"label": "Docker", "queries": ["filename:Dockerfile", "filename:docker-compose.yml"]},
    "git": {"label": "Git", "queries": ["filename:.gitignore"]},
    "github": {"label": "GitHub", "queries": ["path:.github/workflows"]},
    "linux": {"label": "Linux", "queries": ["filename:requirements.txt", "filename:build.gradle.kts", "filename:Dockerfile"]},
    "androidstudio": {"label": "Android Studio", "language": "Kotlin", "queries": ["filename:build.gradle.kts", "filename:AndroidManifest.xml"]},
    "react": {"label": "React", "queries": ["react in:file filename:package.json"]},
    "gradle": {"label": "Gradle", "queries": ["filename:build.gradle.kts", "filename:build.gradle"]},
}

ROWS = [
    ("Languages", ["python", "cpp", "kotlin", "swift", "ts", "js"]),
    ("ML · Robotics · Vision", ["pytorch", "tensorflow", "opencv", "raspberrypi", "arduino"]),
    ("Backend · Infra · Tools", ["fastapi", "docker", "git", "github", "linux"]),
    ("Mobile & Frontend", ["androidstudio", "swift", "react", "gradle"]),
]


def build_tech_map(owned_repos, repo_languages):
    tech_map = {}
    for key, spec in SKILL_QUERIES.items():
        matches = set()

        lang = spec.get("language")
        if lang:
            matches |= {name for name, l in repo_languages.items() if l == lang}

        for q in spec.get("queries", []):
            matches |= code_search(q)
            time.sleep(2)  # code search is rate-limited to ~10 req/min

        matches &= owned_repos
        tech_map[key] = (spec["label"], sorted(matches))
    return tech_map


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

    import re
    pattern = re.compile(re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END), re.DOTALL)
    content = pattern.sub(block, content)

    with open(README_PATH, "w") as f:
        f.write(content)


def main():
    if not TOKEN:
        sys.exit("GH_TOKEN/GITHUB_TOKEN env var required")

    owned_repos_list = gh_get(f"/users/{USERNAME}/repos?per_page=100&type=owner")
    owned_repos_list = [r for r in owned_repos_list if not r.get("fork")]
    owned_repos = {r["name"] for r in owned_repos_list}
    repo_languages = {r["name"]: r.get("language") for r in owned_repos_list}

    tech_map = build_tech_map(owned_repos, repo_languages)
    block = render_markdown(tech_map)
    splice_into_readme(block)
    print("Updated README.md Tech Stack project map")


if __name__ == "__main__":
    main()
