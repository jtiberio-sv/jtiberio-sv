#!/usr/bin/env python3
"""Generate GitHub profile stats SVGs from GraphQL API data."""

import json
import sys
from datetime import datetime
from collections import defaultdict

data = json.loads(sys.argv[1])
user = data["data"]["user"]
cc = user["contributionsCollection"]
repos = user["repositories"]

year = datetime.now().year
total = cc["contributionCalendar"]["totalContributions"]
commits = cc["totalCommitContributions"]
prs = cc["totalPullRequestContributions"]
issues = cc["totalIssueContributions"]
reviews = cc["totalPullRequestReviewContributions"]
repo_count = repos["totalCount"]
private_repos = user["privateRepos"]["totalCount"]
public_repos = user["publicRepos"]["totalCount"]
stars = sum(n["stargazerCount"] for n in repos["nodes"])
followers = user["followers"]["totalCount"]

# --- Stats SVG ---
stats_svg = f'''<svg width="495" height="195" xmlns="http://www.w3.org/2000/svg">
  <rect width="495" height="195" rx="6" fill="#0d1117" stroke="#30363d" stroke-width="1"/>
  <text x="25" y="35" fill="#58A6FF" font-family="Segoe UI, Ubuntu, sans-serif" font-weight="600" font-size="18">GitHub Stats &#8212; {year}</text>
  <line x1="25" y1="48" x2="470" y2="48" stroke="#21262d" stroke-width="1"/>

  <text x="25" y="78" fill="#c9d1d9" font-family="Segoe UI, Ubuntu, sans-serif" font-size="14">&#9733; Total Contributions ({year})</text>
  <text x="280" y="78" fill="#58A6FF" font-family="Segoe UI, Ubuntu, sans-serif" font-weight="700" font-size="16">{total}</text>

  <text x="25" y="103" fill="#c9d1d9" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13">Commits</text>
  <text x="280" y="103" fill="#c9d1d9" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13">{commits}</text>
  <text x="370" y="103" fill="#8b949e" font-family="Segoe UI, Ubuntu, sans-serif" font-size="11">Repos: {repo_count}</text>

  <text x="25" y="125" fill="#c9d1d9" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13">Pull Requests</text>
  <text x="280" y="125" fill="#c9d1d9" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13">{prs}</text>
  <text x="370" y="125" fill="#8b949e" font-family="Segoe UI, Ubuntu, sans-serif" font-size="11">&#128274; Private: {private_repos}</text>

  <text x="25" y="147" fill="#c9d1d9" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13">Issues</text>
  <text x="280" y="147" fill="#c9d1d9" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13">{issues}</text>
  <text x="370" y="147" fill="#8b949e" font-family="Segoe UI, Ubuntu, sans-serif" font-size="11">Stars: {stars}</text>

  <text x="25" y="169" fill="#c9d1d9" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13">Code Reviews</text>
  <text x="280" y="169" fill="#c9d1d9" font-family="Segoe UI, Ubuntu, sans-serif" font-size="13">{reviews}</text>
  <text x="370" y="169" fill="#8b949e" font-family="Segoe UI, Ubuntu, sans-serif" font-size="11">Followers: {followers}</text>
</svg>'''

with open("dist/stats.svg", "w") as f:
    f.write(stats_svg)

# --- Languages SVG ---
lang_sizes = defaultdict(lambda: {"size": 0, "color": "#8b949e"})
for node in repos["nodes"]:
    for edge in node["languages"]["edges"]:
        name = edge["node"]["name"]
        lang_sizes[name]["size"] += edge["size"]
        lang_sizes[name]["color"] = edge["node"]["color"] or "#8b949e"

top_langs = sorted(lang_sizes.items(), key=lambda x: -x[1]["size"])[:8]
total_size = sum(v["size"] for _, v in top_langs) or 1

bars = ""
y = 68
for name, info in top_langs:
    pct = round(info["size"] / total_size * 100, 1)
    bar_w = max(int(pct * 2.5), 2)
    bars += f'  <rect x="25" y="{y - 10}" width="{bar_w}" height="14" rx="3" fill="{info["color"]}"/>\n'
    bars += f'  <text x="{bar_w + 35}" y="{y + 1}" fill="#c9d1d9" font-family="Segoe UI, Ubuntu, sans-serif" font-size="12">{name} ({pct}%)</text>\n'
    y += 24

height = y + 10

langs_svg = f'''<svg width="350" height="{height}" xmlns="http://www.w3.org/2000/svg">
  <rect width="350" height="{height}" rx="6" fill="#0d1117" stroke="#30363d" stroke-width="1"/>
  <text x="25" y="35" fill="#58A6FF" font-family="Segoe UI, Ubuntu, sans-serif" font-weight="600" font-size="16">Top Languages</text>
  <line x1="25" y1="48" x2="325" y2="48" stroke="#21262d" stroke-width="1"/>
{bars}</svg>'''

with open("dist/langs.svg", "w") as f:
    f.write(langs_svg)

print(f"Generated: Total={total}, Commits={commits}, PRs={prs}, Issues={issues}, Reviews={reviews}, Repos={repo_count} ({private_repos} private), Langs={len(top_langs)}")
