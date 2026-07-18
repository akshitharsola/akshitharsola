#!/usr/bin/env python3
"""Generate static GitHub stats + top-languages SVG cards without relying on
any third-party rendering service (github-readme-stats.vercel.app has been
returning 503s). Uses the GitHub REST/GraphQL API directly and writes plain
SVGs that render on GitHub with no external image dependency.

Requires env var GH_TOKEN (a token with public_repo read access is enough).
"""
import os
import sys
import json
import urllib.request

USERNAME = "akshitharsola"
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")

API = "https://api.github.com"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "User-Agent": USERNAME,
}


def gh_get(path):
    url = path if path.startswith("http") else f"{API}{path}"
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def gh_graphql(query, variables):
    req = urllib.request.Request(
        f"{API}/graphql",
        data=json.dumps({"query": query, "variables": variables}).encode(),
        headers={**HEADERS, "Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def fetch_stats():
    user = gh_get(f"/users/{USERNAME}")

    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar { totalContributions }
          totalCommitContributions
          restrictedContributionsCount
        }
        repositories(first: 100, ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC) {
          totalCount
          nodes {
            stargazers { totalCount }
            forkCount
          }
        }
        pullRequests(first: 1) { totalCount }
        issues(first: 1) { totalCount }
      }
    }
    """
    data = gh_graphql(query, {"login": USERNAME})["data"]["user"]

    total_stars = sum(r["stargazers"]["totalCount"] for r in data["repositories"]["nodes"])
    total_commits = (
        data["contributionsCollection"]["totalCommitContributions"]
        + data["contributionsCollection"]["restrictedContributionsCount"]
    )

    return {
        "stars": total_stars,
        "commits": total_commits,
        "prs": data["pullRequests"]["totalCount"],
        "issues": data["issues"]["totalCount"],
        "repos": data["repositories"]["totalCount"],
        "followers": user.get("followers", 0),
    }


def fetch_top_langs(limit=8):
    repos = gh_get(f"/users/{USERNAME}/repos?per_page=100&type=owner")
    totals = {}
    for repo in repos:
        if repo.get("fork"):
            continue
        langs = gh_get(repo["languages_url"])
        for lang, count in langs.items():
            totals[lang] = totals.get(lang, 0) + count
    ranked = sorted(totals.items(), key=lambda kv: kv[1], reverse=True)[:limit]
    grand_total = sum(v for _, v in ranked) or 1
    return [(lang, count / grand_total) for lang, count in ranked]


LANG_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Jupyter Notebook": "#DA5B0B",
    "Shell": "#89e051",
    "C++": "#f34b7d",
    "C": "#555555",
    "Java": "#b07219",
    "Swift": "#F05138",
    "Kotlin": "#A97BFF",
    "Dart": "#00B4AB",
    "Go": "#00ADD8",
    "Rust": "#dea584",
}
DEFAULT_COLOR = "#8e8e8e"

BG = "#0d1117"
BORDER = "#30363d"
TITLE = "#58a6ff"
TEXT = "#c9d1d9"
ICON = "#58a6ff"


def render_stats_svg(stats):
    rows = [
        ("Total Stars", stats["stars"], "★"),
        ("Total Commits", stats["commits"], "●"),
        ("Total PRs", stats["prs"], "⚡"),
        ("Total Issues", stats["issues"], "◈"),
        ("Public Repos", stats["repos"], "▣"),
    ]
    height = 60 + len(rows) * 30
    lines = []
    lines.append(f'<svg width="420" height="{height}" viewBox="0 0 420 {height}" xmlns="http://www.w3.org/2000/svg">')
    lines.append(f'<rect x="0.5" y="0.5" rx="6" width="419" height="{height-1}" fill="{BG}" stroke="{BORDER}"/>')
    lines.append(f'<text x="25" y="35" fill="{TITLE}" font-family="Segoe UI, Ubuntu, sans-serif" font-size="18" font-weight="600">{USERNAME}\'s GitHub Stats</text>')
    y = 70
    for label, value, icon in rows:
        lines.append(f'<text x="30" y="{y}" fill="{ICON}" font-family="Segoe UI, sans-serif" font-size="14">{icon}</text>')
        lines.append(f'<text x="50" y="{y}" fill="{TEXT}" font-family="Segoe UI, Ubuntu, sans-serif" font-size="14">{label}:</text>')
        lines.append(f'<text x="380" y="{y}" fill="{TEXT}" font-family="Segoe UI, Ubuntu, sans-serif" font-size="14" font-weight="600" text-anchor="end">{value}</text>')
        y += 30
    lines.append("</svg>")
    return "\n".join(lines)


def render_top_langs_svg(langs):
    height = 60 + len(langs) * 28
    lines = []
    lines.append(f'<svg width="380" height="{height}" viewBox="0 0 380 {height}" xmlns="http://www.w3.org/2000/svg">')
    lines.append(f'<rect x="0.5" y="0.5" rx="6" width="379" height="{height-1}" fill="{BG}" stroke="{BORDER}"/>')
    lines.append(f'<text x="25" y="35" fill="{TITLE}" font-family="Segoe UI, Ubuntu, sans-serif" font-size="18" font-weight="600">Most Used Languages</text>')

    bar_x = 25
    bar_y = 55
    bar_w = 330
    bar_h = 10
    xcur = bar_x
    lines.append(f'<g>')
    for lang, frac in langs:
        color = LANG_COLORS.get(lang, DEFAULT_COLOR)
        w = max(bar_w * frac, 2)
        lines.append(f'<rect x="{xcur:.1f}" y="{bar_y}" width="{w:.1f}" height="{bar_h}" fill="{color}"/>')
        xcur += w
    lines.append("</g>")

    y = 95
    col = 0
    x0 = 25
    for i, (lang, frac) in enumerate(langs):
        color = LANG_COLORS.get(lang, DEFAULT_COLOR)
        x = x0 + (col % 2) * 170
        row_y = y + (i // 2) * 26
        lines.append(f'<circle cx="{x}" cy="{row_y-5}" r="5" fill="{color}"/>')
        lines.append(f'<text x="{x+14}" y="{row_y}" fill="{TEXT}" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13">{lang} {frac*100:.1f}%</text>')
        col += 1
    lines.append("</svg>")
    return "\n".join(lines)


def main():
    if not TOKEN:
        sys.exit("GH_TOKEN/GITHUB_TOKEN env var required")

    out_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
    os.makedirs(out_dir, exist_ok=True)

    stats = fetch_stats()
    langs = fetch_top_langs()

    with open(os.path.join(out_dir, "github-stats.svg"), "w") as f:
        f.write(render_stats_svg(stats))

    with open(os.path.join(out_dir, "top-langs.svg"), "w") as f:
        f.write(render_top_langs_svg(langs))

    print("Generated assets/github-stats.svg and assets/top-langs.svg")


if __name__ == "__main__":
    main()
