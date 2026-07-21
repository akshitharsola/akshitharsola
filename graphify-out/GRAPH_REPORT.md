# Graph Report - /Users/akshitharsola/Documents/TEMP/GitHub  (2026-07-21)

## Corpus Check
- 3 files · ~101,358 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 22 nodes · 38 edges · 5 communities detected
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]

## God Nodes (most connected - your core abstractions)
1. `main()` - 8 edges
2. `main()` - 5 edges
3. `gh_get()` - 4 edges
4. `code_search()` - 4 edges
5. `fetch_stats()` - 4 edges
6. `build_tech_map()` - 3 edges
7. `gh_get()` - 3 edges
8. `gh_graphql()` - 3 edges
9. `fetch_contribution_calendar()` - 3 edges
10. `fetch_top_langs()` - 3 edges

## Surprising Connections (you probably didn't know these)
- `fetch_stats()` --calls--> `gh_graphql()`  [EXTRACTED]
  /Users/akshitharsola/Documents/TEMP/GitHub/scripts/generate_stats.py → /Users/akshitharsola/Documents/TEMP/GitHub/scripts/generate_stats.py  _Bridges community 3 → community 2_
- `main()` --calls--> `fetch_stats()`  [EXTRACTED]
  /Users/akshitharsola/Documents/TEMP/GitHub/scripts/generate_stats.py → /Users/akshitharsola/Documents/TEMP/GitHub/scripts/generate_stats.py  _Bridges community 2 → community 1_
- `main()` --calls--> `fetch_contribution_calendar()`  [EXTRACTED]
  /Users/akshitharsola/Documents/TEMP/GitHub/scripts/generate_stats.py → /Users/akshitharsola/Documents/TEMP/GitHub/scripts/generate_stats.py  _Bridges community 3 → community 1_

## Communities

### Community 0 - "Community 0"
Cohesion: 0.42
Nodes (8): build_tech_map(), code_search(), fetch_owned_repos(), gh_get(), main(), Run a GitHub code search query, return set of matching repo names.     Retries w, render_markdown(), splice_into_readme()

### Community 1 - "Community 1"
Cohesion: 0.52
Nodes (6): compute_streaks(), fmt_range(), main(), render_stats_svg(), render_streak_svg(), render_top_langs_svg()

### Community 2 - "Community 2"
Cohesion: 0.67
Nodes (3): fetch_stats(), fetch_top_langs(), gh_get()

### Community 3 - "Community 3"
Cohesion: 1.0
Nodes (2): fetch_contribution_calendar(), gh_graphql()

### Community 4 - "Community 4"
Cohesion: 1.0
Nodes (0): 

## Knowledge Gaps
- **1 isolated node(s):** `Run a GitHub code search query, return set of matching repo names.     Retries w`
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 3`** (2 nodes): `fetch_contribution_calendar()`, `gh_graphql()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 4`** (1 nodes): `compose_about_me.py`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `main()` connect `Community 1` to `Community 2`, `Community 3`?**
  _High betweenness centrality (0.048) - this node is a cross-community bridge._
- **What connects `Run a GitHub code search query, return set of matching repo names.     Retries w` to the rest of the system?**
  _1 weakly-connected nodes found - possible documentation gaps or missing edges._