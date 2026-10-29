import json, os, sys, urllib.request, re

LOGIN = sys.argv[1] if len(sys.argv) > 1 else "0d1ns0n"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/stats.svg"
TOKEN = os.environ.get("STATS_TOKEN") or os.environ["GITHUB_TOKEN"]
HERE = os.path.dirname(os.path.abspath(__file__))

def req(url, accept="application/vnd.github+json", data=None):
    r = urllib.request.Request(url, data=data,
        headers={"Authorization": f"bearer {TOKEN}", "Accept": accept,
                 "Content-Type": "application/json", "User-Agent": LOGIN})
    return urllib.request.urlopen(r)

def api(path, accept="application/vnd.github+json"):
    return json.load(req("https://api.github.com/" + path, accept))

def gql(q):
    return json.load(req("https://api.github.com/graphql", data=json.dumps({"query": q}).encode()))["data"]

v = gql('{viewer{followers{totalCount} repositories(first:100,ownerAffiliations:[OWNER,COLLABORATOR,ORGANIZATION_MEMBER]){nodes{nameWithOwner isFork}}}}')["viewer"]
repo_names = [r["nameWithOwner"] for r in v["repositories"]["nodes"] if not r["isFork"]]
followers = v["followers"]["totalCount"]

def commit_count(full):
    try:
        r = req(f"https://api.github.com/repos/{full}/commits?per_page=1")
        m = re.search(r'[?&]page=(\d+)>; rel="last"', r.headers.get("Link", ""))
        return int(m.group(1)) if m else len(json.load(r))
    except Exception:
        return 0

counts = {f: commit_count(f) for f in repo_names}
commits_total = sum(counts.values())
top_project = max(counts.values()) if counts else 0
repos = len(repo_names)
prs = api(f"search/issues?q=author:{LOGIN}+type:pr&per_page=1")["total_count"]

langs = json.load(open(os.path.join(HERE, "langs.json"), encoding="utf-8"))
fluent = langs["fluent"]
weights = [96, 92, 90, 88, 72, 70, 58, 50][:len(fluent)]

stats = [
    ("COMMITS", commits_total, "across all repos"),
    ("REPOSITORIES", repos, "incl. private"),
    ("PULL REQUESTS", prs, "authored"),
    ("TOP PROJECT", top_project, "commits"),
    ("LANGUAGES", len(fluent), "fluent"),
    ("PRODUCTION", "15+", "components"),
]

W, H = 900, 340
s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
 '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#05060f"/><stop offset="1" stop-color="#0b0f1f"/></linearGradient>',
 '<pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M30 0H0V30" fill="none" stroke="#00ff9f" stroke-opacity="0.12"/></pattern>',
 '<filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
 '<linearGradient id="scan" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#00ff9f" stop-opacity="0"/><stop offset="0.5" stop-color="#00ff9f" stop-opacity="0.25"/><stop offset="1" stop-color="#00ff9f" stop-opacity="0"/></linearGradient>',
 '<style>text{font-family:"Fira Code","JetBrains Mono",Consolas,monospace}.l{font-size:11px;letter-spacing:2px;fill:#8b93b5}.n{font-size:28px;font-weight:700;fill:#eaf2ff;filter:url(#glow)}.h{font-size:13px;letter-spacing:4px;fill:#00ff9f}.p{font-size:10px;fill:#8b93b5}.ln{font-size:12px;fill:#eaf2ff}.cur{animation:blink 1s infinite steps(1)}@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}',
 ''.join(f'.f{i}{{opacity:0;animation:fi .6s ease-out {0.12*i:.2f}s forwards}}' for i in range(14)),
 '@keyframes fi{to{opacity:1}}</style></defs>',
 f'<rect width="{W}" height="{H}" fill="url(#bg)"/><rect width="{W}" height="{H}" fill="url(#grid)"/>',
 f'<rect width="{W}" height="{H}" fill="none" stroke="#00ff9f" stroke-opacity="0.5" stroke-width="2"/>',
 f'<path d="M0 0H40V4H4V40H0Z M{W} 0H{W-40}V4H{W-4}V40H{W}Z M0 {H}H40V{H-4}H4V{H-40}H0Z M{W} {H}H{W-40}V{H-4}H{W-4}V{H-40}H{W}Z" fill="#00ff9f"/>',
 '<text class="h" x="40" y="44">&gt; TELEMETRY // github.com/' + LOGIN + '<tspan class="cur">_</tspan></text>',
 f'<line x1="470" y1="70" x2="470" y2="{H-30}" stroke="#00ff9f" stroke-opacity="0.3" stroke-dasharray="4 6"/>']

for i, (lab, val, sub) in enumerate(stats):
    x = 40 + (i % 2) * 215
    y = 100 + (i // 2) * 76
    disp = f"{val:,}" if isinstance(val, int) else str(val)
    s.append(f'<g class="f{i}"><text class="l" x="{x}" y="{y}">{lab}</text>'
             f'<text class="n" x="{x}" y="{y+32}">{disp}</text>'
             f'<text class="p" x="{x}" y="{y+48}">{sub}</text></g>')

s.append('<text class="h" x="500" y="88">LANGUAGES</text>')
for i, lg in enumerate(fluent):
    pct = weights[i]
    y = 104 + i * 27
    s.append(f'<g class="f{i+6}"><text class="ln" x="500" y="{y+9}">{lg["n"]}</text>'
             f'<rect x="640" y="{y+2}" width="220" height="6" rx="3" fill="#ffffff" fill-opacity="0.06"/>'
             f'<rect x="640" y="{y+2}" width="{int(220*pct/100)}" height="6" rx="3" fill="{lg["c"]}" filter="url(#glow)">'
             f'<animate attributeName="width" from="0" to="{int(220*pct/100)}" dur="1.2s" begin="{0.3+i*0.12:.2f}s" fill="freeze"/></rect></g>')

s.append(f'<rect width="{W}" height="50" fill="url(#scan)"><animate attributeName="y" values="-50;{H}" dur="4s" repeatCount="indefinite"/></rect></svg>')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write("\n".join(s))
print(f"ok: {commits_total} commits, {repos} repos, top {top_project}, {prs} PRs")
