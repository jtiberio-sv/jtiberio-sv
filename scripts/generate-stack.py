#!/usr/bin/env python3
"""Gera dist/stack.svg: o que esta em uso agora, lido dos repositorios com push recente.

Nada aqui e lista fixa de tecnologias: o script varre os repos (inclusive privados, via PAT)
empurrados nos ultimos WINDOW_DAYS dias, detecta linguagens, arquivos de ferramenta e
dependencias, e agrupa em pilares que nao envelhecem. Nomes de repositorio nunca saem no SVG.
"""

import json
import os
import re
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from xml.sax.saxutils import escape

LOGIN = "jtiberio-sv"
WINDOW_DAYS = 90
MAX_PER_PILLAR = 7

PILLARS = [
    ("ai", "AI & Agents"),
    ("lang", "Languages"),
    ("app", "Apps & APIs"),
    ("infra", "Cloud & Infra"),
    ("ship", "Delivery & Quality"),
    ("data", "Data"),
]

# sinal -> (nome exibido, pilar, cor)
T = {
    "claude": ("Claude", "ai", "#D97757"),
    "claude-agent-sdk": ("Claude Agent SDK", "ai", "#D97757"),
    "claude-code": ("Claude Code", "ai", "#D97757"),
    "mcp": ("MCP", "ai", "#8B5CF6"),
    "openai": ("OpenAI", "ai", "#10A37F"),
    "gemini": ("Gemini", "ai", "#4285F4"),
    "langchain": ("LangChain", "ai", "#1C3C3C"),
    "langgraph": ("LangGraph", "ai", "#1C3C3C"),
    "ollama": ("Ollama", "ai", "#9CA3AF"),
    "llamacpp": ("llama.cpp", "ai", "#9CA3AF"),
    "mlx": ("MLX", "ai", "#9CA3AF"),
    "hf": ("Hugging Face", "ai", "#FFD21E"),
    "torch": ("PyTorch", "ai", "#EE4C2C"),
    "onnx": ("ONNX Runtime", "ai", "#5A6B7F"),
    "whisper": ("Whisper", "ai", "#10A37F"),
    "vercel-ai": ("Vercel AI SDK", "ai", "#9CA3AF"),
    "next": ("Next.js", "app", "#9CA3AF"),
    "react": ("React", "app", "#61DAFB"),
    "react-native": ("React Native", "app", "#61DAFB"),
    "expo": ("Expo", "app", "#9CA3AF"),
    "vue": ("Vue", "app", "#4FC08D"),
    "svelte": ("Svelte", "app", "#FF3E00"),
    "astro": ("Astro", "app", "#BC52EE"),
    "tailwind": ("Tailwind CSS", "app", "#06B6D4"),
    "vite": ("Vite", "app", "#646CFF"),
    "node": ("Node.js", "app", "#5FA04E"),
    "bun": ("Bun", "app", "#FBF0DF"),
    "fastapi": ("FastAPI", "app", "#009688"),
    "flask": ("Flask", "app", "#9CA3AF"),
    "django": ("Django", "app", "#44B78B"),
    "express": ("Express", "app", "#9CA3AF"),
    "fastify": ("Fastify", "app", "#9CA3AF"),
    "hono": ("Hono", "app", "#E36002"),
    "nest": ("NestJS", "app", "#E0234E"),
    "wordpress": ("WordPress", "app", "#21759B"),
    "laravel": ("Laravel", "app", "#FF2D20"),
    "swiftui": ("SwiftUI", "app", "#F05138"),
    "telegram": ("Telegram Bots", "app", "#26A5E4"),
    "discord": ("Discord Bots", "app", "#5865F2"),
    "docker": ("Docker", "infra", "#2496ED"),
    "compose": ("Docker Compose", "infra", "#2496ED"),
    "k8s": ("Kubernetes", "infra", "#326CE5"),
    "helm": ("Helm", "infra", "#0F1689"),
    "terraform": ("Terraform", "infra", "#844FBA"),
    "opentofu": ("OpenTofu", "infra", "#FFDA18"),
    "ansible": ("Ansible", "infra", "#EE0000"),
    "aws": ("AWS", "infra", "#FF9900"),
    "cdk": ("AWS CDK", "infra", "#FF9900"),
    "serverless": ("Serverless", "infra", "#FD5750"),
    "cloudflare": ("Cloudflare", "infra", "#F38020"),
    "vercel": ("Vercel", "infra", "#9CA3AF"),
    "nginx": ("Nginx", "infra", "#009639"),
    "caddy": ("Caddy", "infra", "#1F88C0"),
    "tailscale": ("Tailscale", "infra", "#9CA3AF"),
    "systemd": ("systemd", "infra", "#9CA3AF"),
    "gha": ("GitHub Actions", "ship", "#2088FF"),
    "playwright": ("Playwright", "ship", "#2EAD33"),
    "puppeteer": ("Puppeteer", "ship", "#40B5A4"),
    "vitest": ("Vitest", "ship", "#6E9F18"),
    "jest": ("Jest", "ship", "#C21325"),
    "pytest": ("pytest", "ship", "#0A9EDC"),
    "eslint": ("ESLint", "ship", "#4B32C3"),
    "biome": ("Biome", "ship", "#60A5FA"),
    "ruff": ("Ruff", "ship", "#D7FF64"),
    "phpunit": ("PHPUnit", "ship", "#3C9CD7"),
    "otel": ("OpenTelemetry", "ship", "#F5A800"),
    "sentry": ("Sentry", "ship", "#A78BFA"),
    "prometheus": ("Prometheus", "ship", "#E6522C"),
    "grafana": ("Grafana", "ship", "#F46800"),
    "postgres": ("PostgreSQL", "data", "#4169E1"),
    "mysql": ("MySQL", "data", "#4479A1"),
    "sqlite": ("SQLite", "data", "#44A8E0"),
    "redis": ("Redis", "data", "#DC382D"),
    "bullmq": ("BullMQ", "data", "#E0234E"),
    "prisma": ("Prisma", "data", "#5A67D8"),
    "drizzle": ("Drizzle", "data", "#C5F74F"),
    "supabase": ("Supabase", "data", "#3ECF8E"),
    "pgvector": ("pgvector", "data", "#4169E1"),
    "qdrant": ("Qdrant", "data", "#DC244C"),
    "duckdb": ("DuckDB", "data", "#FFF000"),
}

# dependencia (package.json / requirements / pyproject / composer) -> sinal
DEPS = [
    (r"^@anthropic-ai/claude-agent-sdk$|^claude[-_]agent[-_]sdk$", "claude-agent-sdk"),
    (r"^@anthropic-ai/sdk$|^anthropic$|^@ai-sdk/anthropic$", "claude"),
    (r"^@modelcontextprotocol/|^mcp$|^fastmcp$", "mcp"),
    (r"^openai$|^@ai-sdk/openai$", "openai"),
    (r"^@google/genai$|^google-genai$|^@google/generative-ai$|^google-generativeai$", "gemini"),
    (r"^langchain|^@langchain/", "langchain"),
    (r"^langgraph|^@langchain/langgraph$", "langgraph"),
    (r"^ollama$", "ollama"),
    (r"^llama[-_]cpp|^node-llama-cpp$", "llamacpp"),
    (r"^mlx", "mlx"),
    (r"^transformers$|^@huggingface/|^huggingface[-_]hub$", "hf"),
    (r"^torch$", "torch"),
    (r"^onnxruntime", "onnx"),
    (r"whisper", "whisper"),
    (r"^ai$", "vercel-ai"),
    (r"^next$", "next"),
    (r"^react$", "react"),
    (r"^react-native$", "react-native"),
    (r"^expo$", "expo"),
    (r"^vue$|^nuxt$", "vue"),
    (r"^svelte$|^@sveltejs/kit$", "svelte"),
    (r"^astro$", "astro"),
    (r"^tailwindcss$", "tailwind"),
    (r"^vite$", "vite"),
    (r"^fastapi$", "fastapi"),
    (r"^flask$", "flask"),
    (r"^django$", "django"),
    (r"^express$", "express"),
    (r"^fastify$", "fastify"),
    (r"^hono$", "hono"),
    (r"^@nestjs/core$", "nest"),
    (r"^johnpbloch/wordpress|^roots/bedrock|^wpackagist|^wp-cli/", "wordpress"),
    (r"^laravel/framework$", "laravel"),
    (r"^telegraf$|^grammy$|^node-telegram-bot-api$|^python-telegram-bot$|^aiogram$", "telegram"),
    (r"^discord\.js$|^discord\.py$|^discord$", "discord"),
    (r"^@aws-sdk/|^aws-sdk$|^boto3$", "aws"),
    (r"^aws-cdk", "cdk"),
    (r"^wrangler$|^@cloudflare/", "cloudflare"),
    (r"^playwright$|^@playwright/test$", "playwright"),
    (r"^puppeteer", "puppeteer"),
    (r"^vitest$", "vitest"),
    (r"^jest$", "jest"),
    (r"^pytest$", "pytest"),
    (r"^eslint$", "eslint"),
    (r"^@biomejs/biome$", "biome"),
    (r"^ruff$", "ruff"),
    (r"^phpunit/phpunit$", "phpunit"),
    (r"^@opentelemetry/|^opentelemetry", "otel"),
    (r"^@sentry/|^sentry-sdk$", "sentry"),
    (r"^prom-client$|^prometheus[-_]client$", "prometheus"),
    (r"^pg$|^postgres$|^psycopg|^asyncpg$", "postgres"),
    (r"^mysql2?$|^pymysql$|^mysqlclient$", "mysql"),
    (r"^better-sqlite3$|^sqlite3?$|^aiosqlite$", "sqlite"),
    (r"^redis$|^ioredis$", "redis"),
    (r"^bullmq$", "bullmq"),
    (r"^prisma$|^@prisma/client$", "prisma"),
    (r"^drizzle-orm$", "drizzle"),
    (r"^@supabase/|^supabase$", "supabase"),
    (r"^pgvector$", "pgvector"),
    (r"^qdrant", "qdrant"),
    (r"^duckdb$", "duckdb"),
]
DEPS = [(re.compile(p, re.I), s) for p, s in DEPS]

# arquivo/pasta na raiz -> sinal
FILES = [
    (r"^Dockerfile|\.dockerfile$", "docker"),
    (r"^(docker-)?compose(\.[\w-]+)?\.ya?ml$", "compose"),
    (r"\.tf$|^terraform$|^infra$", "terraform"),
    (r"^Chart\.yaml$|^charts?$", "helm"),
    (r"^k8s$|^kubernetes$|^manifests$|^kustomization\.ya?ml$", "k8s"),
    (r"^ansible\.cfg$|^playbooks?$", "ansible"),
    (r"^cdk\.json$", "cdk"),
    (r"^serverless\.ya?ml$", "serverless"),
    (r"^wrangler\.(toml|jsonc?)$", "cloudflare"),
    (r"^vercel\.json$", "vercel"),
    (r"^nginx(\.conf)?$", "nginx"),
    (r"^Caddyfile$", "caddy"),
    (r"\.service$|^systemd$", "systemd"),
    (r"^CLAUDE\.md$|^\.claude$", "claude-code"),
    (r"^\.mcp\.json$", "mcp"),
    (r"^playwright\.config\.", "playwright"),
    (r"^vitest\.config\.", "vitest"),
    (r"^bun\.lockb?$", "bun"),
    (r"^wp-content$|^wp-config(-sample)?\.php$|^style\.css$", "wordpress"),
    (r"^Package\.swift$|\.xcodeproj$", "swiftui"),
    (r"^grafana$|^dashboards$", "grafana"),
    (r"^prometheus(\.ya?ml)?$", "prometheus"),
]
FILES = [(re.compile(p, re.I), s) for p, s in FILES]

LANG_SKIP = {"HTML", "CSS", "SCSS", "Dockerfile", "Makefile", "Procfile", "Jinja", "Smarty",
             "Twig", "Blade", "Hack", "HCL", "Less", "Batchfile", "Roff", "Nix", "Mustache"}
LANG_ALIAS = {"Shell": "Bash", "PowerShell": "PowerShell"}


def gql(query, variables=None):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": variables or {}}).encode(),
        headers={"Authorization": f"bearer {os.environ['GH_TOKEN']}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        out = json.load(r)
    if out.get("errors") and not out.get("data"):
        sys.exit(f"graphql: {out['errors']}")
    return out["data"]


REPO_FIELDS = """
  pushedAt isFork isArchived
  owner { login }
  languages(first: 8, orderBy: {field: SIZE, direction: DESC}) { edges { size node { name color } } }
  repositoryTopics(first: 20) { nodes { topic { name } } }
  root: object(expression: "HEAD:") { ... on Tree { entries { name } } }
  wf: object(expression: "HEAD:.github/workflows") { ... on Tree { entries { name } } }
  pkg: object(expression: "HEAD:package.json") { ... on Blob { text } }
  req: object(expression: "HEAD:requirements.txt") { ... on Blob { text } }
  pyp: object(expression: "HEAD:pyproject.toml") { ... on Blob { text } }
  cmp: object(expression: "HEAD:composer.json") { ... on Blob { text } }
"""


def recent_repos():
    since = datetime.now(timezone.utc) - timedelta(days=WINDOW_DAYS)
    q = """query($cursor: String) { viewer { repositories(first: 25, after: $cursor,
      ownerAffiliations: [OWNER, COLLABORATOR, ORGANIZATION_MEMBER],
      orderBy: {field: PUSHED_AT, direction: DESC}) {
        pageInfo { hasNextPage endCursor } nodes { %s } } } }""" % REPO_FIELDS
    cursor = None
    while True:
        page = gql(q, {"cursor": cursor})["viewer"]["repositories"]
        for n in page["nodes"]:
            if not n["pushedAt"] or datetime.fromisoformat(n["pushedAt"].replace("Z", "+00:00")) < since:
                return
            if not n["isFork"] and not n["isArchived"]:
                yield n
        if not page["pageInfo"]["hasNextPage"]:
            return
        cursor = page["pageInfo"]["endCursor"]


def dep_names(n):
    names = set()
    for key in ("pkg", "cmp"):
        txt = (n.get(key) or {}).get("text")
        if not txt:
            continue
        try:
            j = json.loads(txt)
        except ValueError:
            continue
        for sec in ("dependencies", "devDependencies", "peerDependencies", "require", "require-dev"):
            names.update((j.get(sec) or {}).keys())
    for key in ("req", "pyp"):
        txt = (n.get(key) or {}).get("text") or ""
        names.update(m.group(1) for m in re.finditer(r'^\s*"?([A-Za-z0-9_.\-]+)\s*(?:[<>=~!\[;"]|$)', txt, re.M))
    return names


def signals(n):
    found = set()
    for name in dep_names(n):
        for rx, s in DEPS:
            if rx.search(name):
                found.add(s)
    for e in ((n.get("root") or {}).get("entries") or []):
        for rx, s in FILES:
            if rx.search(e["name"]):
                found.add(s)
    if (n.get("wf") or {}).get("entries"):
        found.add("gha")
    if (n.get("pkg") or {}).get("text"):
        found.add("node")
    for t in (n.get("repositoryTopics") or {}).get("nodes", []):
        name = t["topic"]["name"].lower()
        if name in T:
            found.add(name)
    return found


def main():
    now = datetime.now(timezone.utc)
    score = defaultdict(float)
    lang_color = {}
    repos = 0
    for n in recent_repos():
        repos += 1
        age = (now - datetime.fromisoformat(n["pushedAt"].replace("Z", "+00:00"))).days
        w = (1.0 if n["owner"]["login"] == LOGIN else 0.6) * (1.0 - 0.6 * age / WINDOW_DAYS)
        for s in signals(n):
            score[s] += w
        edges = n["languages"]["edges"]
        total = sum(e["size"] for e in edges) or 1
        for e in edges:
            name = LANG_ALIAS.get(e["node"]["name"], e["node"]["name"])
            if name in LANG_SKIP or e["size"] / total < 0.08:
                continue
            key = "lang:" + name
            score[key] += w * (0.5 + e["size"] / total)
            lang_color[key] = e["node"]["color"] or "#8b949e"

    pillars = defaultdict(list)
    for key, v in score.items():
        if key.startswith("lang:"):
            pillars["lang"].append((v, key[5:], lang_color[key]))
        else:
            name, pillar, color = T[key]
            pillars[pillar].append((v, name, color))

    render([(title, sorted(pillars[k], reverse=True)[:MAX_PER_PILLAR]) for k, title in PILLARS if pillars[k]],
           repos, now)


def render(groups, repos, now):
    W, X0, ROW = 830, 28, 44
    H = 96 + ROW * len(groups) + 34
    font = "font-family=\"'JetBrains Mono','DejaVu Sans Mono',Menlo,Consolas,monospace\""
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
           '<style>.c{opacity:0;animation:in .4s ease-out forwards}@keyframes in{to{opacity:1}}'
           '@media (prefers-reduced-motion:reduce){.c{animation:none;opacity:1}}</style>',
           f'<rect width="{W}" height="{H}" rx="10" fill="#0d1117" stroke="#30363d"/>',
           f'<circle cx="24" cy="22" r="5" fill="#ff5f56"/><circle cx="42" cy="22" r="5" fill="#ffbd2e"/>'
           f'<circle cx="60" cy="22" r="5" fill="#27c93f"/>',
           f'<text x="{X0}" y="62" fill="#39d353" font-size="14" {font}>$ <tspan fill="#c9d1d9">stack --now</tspan>'
           f'<tspan fill="#8b949e" font-size="12">   # derived from repos active in the last {WINDOW_DAYS} days</tspan></text>']
    y, i = 96, 0
    for title, items in groups:
        out.append(f'<text x="{X0}" y="{y + 18}" fill="#8b949e" font-size="12" {font}>{escape(title)}</text>')
        x = 200
        for _, name, color in items:
            w = 26 + len(name) * 7.4
            if x + w > W - X0:
                break
            d = f'style="animation-delay:{0.15 + i * 0.04:.2f}s"'
            out.append(f'<g class="c" {d}><rect x="{x}" y="{y}" width="{w:.0f}" height="26" rx="13" fill="#161b22" stroke="#30363d"/>'
                       f'<circle cx="{x + 13}" cy="{y + 13}" r="4" fill="{color}"/>'
                       f'<text x="{x + 22}" y="{y + 17.5}" fill="#c9d1d9" font-size="12" {font}>{escape(name)}</text></g>')
            x += w + 8
            i += 1
        y += ROW
    out.append(f'<text x="{W - X0}" y="{H - 16}" text-anchor="end" fill="#484f58" font-size="11" {font}>'
               f'{repos} active repos · updated {now:%Y-%m-%d}</text></svg>')
    os.makedirs("dist", exist_ok=True)
    with open("dist/stack.svg", "w") as f:
        f.write("\n".join(out))
    print(f"dist/stack.svg: {len(groups)} pilares, {repos} repos")


if __name__ == "__main__":
    main()
