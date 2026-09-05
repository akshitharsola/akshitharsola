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
import datetime
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
        result = json.load(resp)
    if result.get("errors"):
        sys.exit(f"GraphQL errors: {json.dumps(result['errors'])}")
    if result.get("data", {}).get("user") is None:
        sys.exit(f"GraphQL returned null user (check token scopes): {json.dumps(result)}")
    return result


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


def fetch_contribution_calendar():
    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays { date contributionCount }
            }
          }
        }
      }
    }
    """
    data = gh_graphql(query, {"login": USERNAME})["data"]["user"]
    calendar = data["contributionsCollection"]["contributionCalendar"]
    days = [
        (d["date"], d["contributionCount"])
        for week in calendar["weeks"]
        for d in week["contributionDays"]
    ]
    days.sort(key=lambda dc: dc[0])
    return calendar["totalContributions"], days


def compute_streaks(days):
    today = datetime.date.today().isoformat()
    longest = 0
    longest_run = (None, None)
    run_start = None
    run_len = 0

    for date, count in days:
        if count > 0:
            if run_len == 0:
                run_start = date
            run_len += 1
            if run_len > longest:
                longest = run_len
                longest_run = (run_start, date)
        else:
            run_len = 0

    # Current streak: walk backwards from the most recent day, allowing
    # today to be contribution-free (day not over yet) without breaking it.
    current = 0
    current_end = None
    current_start = None
    for date, count in reversed(days):
        if count > 0:
            current += 1
            current_start = date
            if current_end is None:
                current_end = date
        else:
            if date == today:
                continue
            break

    return {
        "current": current,
        "current_range": (current_start, current_end),
        "longest": longest,
        "longest_range": longest_run,
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


def fmt_range(range_pair):
    start, end = range_pair
    if not start:
        return "N/A"
    fmt = lambda s: datetime.date.fromisoformat(s).strftime("%b %-d")
    if start == end:
        return fmt(start)
    return f"{fmt(start)} - {fmt(end)}"


def render_streak_svg(total_contributions, streaks):
    width, height = 495, 195
    col_w = width / 3
    lines = []
    lines.append(f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">')
    lines.append(f'<rect x="0.5" y="0.5" rx="8" width="{width-1}" height="{height-1}" fill="{BG}" stroke="{BORDER}"/>')
    lines.append(f'<line x1="{col_w:.1f}" y1="30" x2="{col_w:.1f}" y2="{height-30}" stroke="{BORDER}"/>')
    lines.append(f'<line x1="{col_w*2:.1f}" y1="30" x2="{col_w*2:.1f}" y2="{height-30}" stroke="{BORDER}"/>')

    columns = [
        ("Total Contributions", total_contributions, None),
        ("Current Streak", streaks["current"], fmt_range(streaks["current_range"])),
        ("Longest Streak", streaks["longest"], fmt_range(streaks["longest_range"])),
    ]
    for i, (label, value, subrange) in enumerate(columns):
        cx = col_w * i + col_w / 2
        lines.append(f'<text x="{cx:.1f}" y="80" fill="{TITLE}" font-family="Segoe UI, Ubuntu, sans-serif" font-size="34" font-weight="700" text-anchor="middle">{value}</text>')
        lines.append(f'<text x="{cx:.1f}" y="110" fill="{TEXT}" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13" text-anchor="middle">{label}</text>')
        if subrange:
            lines.append(f'<text x="{cx:.1f}" y="130" fill="{TEXT}" font-family="Segoe UI, Ubuntu, sans-serif" font-size="11" text-anchor="middle" opacity="0.7">{subrange}</text>')
    lines.append("</svg>")
    return "\n".join(lines)


def render_activity_graph_svg(days):
    """Weekly-aggregated area chart of contributions over the last ~52 weeks,
    styled to resemble github-readme-activity-graph without depending on it."""
    weeks = []
    week_dates = []
    week = []
    for date, count in days:
        week.append(count)
        if len(week) == 7:
            weeks.append(sum(week))
            week_dates.append(date)
            week = []
    if week:
        weeks.append(sum(week))
        week_dates.append(days[-1][0])

    width, height = 800, 260
    pad_l, pad_r, pad_t, pad_b = 45, 25, 45, 45
    plot_w = width - pad_l - pad_r
    plot_h = height - pad_t - pad_b
    max_val = max(weeks) or 1
    n = len(weeks)
    step = plot_w / max(n - 1, 1)

    points = []
    for i, v in enumerate(weeks):
        x = pad_l + i * step
        y = pad_t + plot_h - (v / max_val) * plot_h
        points.append((x, y))

    def smooth_path(pts):
        if len(pts) < 3:
            return "M " + " L ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
        d = [f"M {pts[0][0]:.1f},{pts[0][1]:.1f}"]
        for i in range(len(pts) - 1):
            x0, y0 = pts[i]
            x1, y1 = pts[i + 1]
            mx = (x0 + x1) / 2
            d.append(f"C {mx:.1f},{y0:.1f} {mx:.1f},{y1:.1f} {x1:.1f},{y1:.1f}")
        return " ".join(d)

    line_path = smooth_path(points)
    area_path = (
        line_path
        + f" L {points[-1][0]:.1f},{pad_t + plot_h:.1f}"
        + f" L {points[0][0]:.1f},{pad_t + plot_h:.1f} Z"
    )

    # Horizontal gridlines at 25/50/75/100% of max, with value labels.
    grid_lines = []
    for frac in (0.25, 0.5, 0.75, 1.0):
        gy = pad_t + plot_h - frac * plot_h
        grid_lines.append(f'<line x1="{pad_l}" y1="{gy:.1f}" x2="{width-pad_r}" y2="{gy:.1f}" stroke="{BORDER}" stroke-width="1" stroke-dasharray="3,3" opacity="0.5"/>')
        grid_lines.append(f'<text x="{pad_l-8}" y="{gy+4:.1f}" fill="{TEXT}" font-family="Segoe UI, Ubuntu, sans-serif" font-size="10" text-anchor="end" opacity="0.6">{round(frac*max_val)}</text>')

    # Month labels along the x-axis, deduplicated.
    month_labels = []
    seen_months = set()
    for i, d in enumerate(week_dates):
        month = d[:7]
        if month not in seen_months:
            seen_months.add(month)
            x = pad_l + i * step
            label = datetime.date.fromisoformat(d).strftime("%b")
            month_labels.append(f'<text x="{x:.1f}" y="{height-pad_b+18}" fill="{TEXT}" font-family="Segoe UI, Ubuntu, sans-serif" font-size="10" text-anchor="middle" opacity="0.6">{label}</text>')

    # Highlight peak week.
    peak_i = weeks.index(max(weeks))
    peak_x, peak_y = points[peak_i]

    lines = []
    lines.append(f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">')
    lines.append('<defs>')
    lines.append(f'<linearGradient id="areaFill" x1="0" y1="0" x2="0" y2="1">')
    lines.append(f'<stop offset="0%" stop-color="{ICON}" stop-opacity="0.45"/>')
    lines.append(f'<stop offset="100%" stop-color="{ICON}" stop-opacity="0.02"/>')
    lines.append('</linearGradient>')
    lines.append('</defs>')
    lines.append(f'<rect x="0.5" y="0.5" rx="8" width="{width-1}" height="{height-1}" fill="{BG}" stroke="{BORDER}"/>')
    lines.append(f'<text x="20" y="26" fill="{TITLE}" font-family="Segoe UI, Ubuntu, sans-serif" font-size="16" font-weight="700">Contribution Activity</text>')
    lines.append(f'<text x="20" y="42" fill="{TEXT}" font-family="Segoe UI, Ubuntu, sans-serif" font-size="11" opacity="0.6">Weekly contributions over the last year</text>')
    lines.extend(grid_lines)
    lines.extend(month_labels)
    lines.append(f'<path d="{area_path}" fill="url(#areaFill)" stroke="none"/>')
    lines.append(f'<path d="{line_path}" fill="none" stroke="{ICON}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>')
    lines.append(f'<circle cx="{peak_x:.1f}" cy="{peak_y:.1f}" r="4" fill="{BG}" stroke="{ICON}" stroke-width="2"/>')
    lines.append(f'<text x="{peak_x:.1f}" y="{peak_y-12:.1f}" fill="{ICON}" font-family="Segoe UI, Ubuntu, sans-serif" font-size="11" font-weight="600" text-anchor="middle">{weeks[peak_i]}</text>')
    lines.append("</svg>")
    return "\n".join(lines)


def main():
    if not TOKEN:
        sys.exit("GH_TOKEN/GITHUB_TOKEN env var required")

    out_dir = os.path.join(os.path.dirname(__file__), "..", "assets")
    os.makedirs(out_dir, exist_ok=True)

    stats = fetch_stats()
    langs = fetch_top_langs()
    total_contributions, days = fetch_contribution_calendar()
    streaks = compute_streaks(days)

    with open(os.path.join(out_dir, "github-stats.svg"), "w") as f:
        f.write(render_stats_svg(stats))

    with open(os.path.join(out_dir, "top-langs.svg"), "w") as f:
        f.write(render_top_langs_svg(langs))

    with open(os.path.join(out_dir, "streak-stats.svg"), "w") as f:
        f.write(render_streak_svg(total_contributions, streaks))

    with open(os.path.join(out_dir, "activity-graph.svg"), "w") as f:
        f.write(render_activity_graph_svg(days))

    print("Generated assets/github-stats.svg, assets/top-langs.svg, assets/streak-stats.svg, assets/activity-graph.svg")


if __name__ == "__main__":
    main()
