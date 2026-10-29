import json, os, sys, urllib.request

LOGIN = sys.argv[1] if len(sys.argv) > 1 else "0d1ns0n"
OUT = sys.argv[2] if len(sys.argv) > 2 else "assets/stats.svg"
TOKEN = os.environ.get("STATS_TOKEN") or os.environ["GITHUB_TOKEN"]
HERE = os.path.dirname(os.path.abspath(__file__))

QUERY = """
query($login:String!){ user(login:$login){
  followers{totalCount}
  repositories(ownerAffiliations:OWNER){ totalCount }
  contributionsCollection{ totalCommitContributions restrictedContributionsCount
    totalPullRequestContributions totalRepositoryContributions
    contributionCalendar{ totalContributions } }
}}"""

def gql(q, v):
    req = urllib.request.Request("https://api.github.com/graphql",
        data=json.dumps({"query": q, "variables": v}).encode(),
        headers={"Authorization": f"bearer {TOKEN}", "Content-Type": "application/json", "User-Agent": LOGIN})
    with urllib.request.urlopen(req) as r:
        d = json.load(r)
    if "errors" in d:
        raise SystemExit(d["errors"])
    return d["data"]["user"]

u = gql(QUERY, {"login": LOGIN})
cc = u["contributionsCollection"]
commits = cc["totalCommitContributions"] + cc["restrictedContributionsCount"]
total = cc["contributionCalendar"]["totalContributions"]

langs = json.load(open(os.path.join(HERE, "langs.json"), encoding="utf-8"))
fluent = langs["fluent"]
weights = [96, 92, 90, 88, 72, 70, 58, 50][:len(fluent)]

stats = [
    ("CONTRIBUTIONS", total, "last 365 days"),
    ("COMMITS", commits, "incl. private"),
    ("PULL REQUESTS", cc["totalPullRequestContributions"], ""),
    ("REPOSITORIES", u["repositories"]["totalCount"], "owned"),
    ("PROJECTS", u["repositories"]["totalCount"] + cc["totalRepositoryContributions"], "touched"),
    ("FOLLOWERS", u["followers"]["totalCount"], ""),
]

W, H = 900, 340
s = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">',
 '<defs><linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#05060f"/><stop offset="1" stop-color="#0b0f1f"/></linearGradient>',
 '<pattern id="grid" width="30" height="30" patternUnits="userSpaceOnUse"><path d="M30 0H0V30" fill="none" stroke="#00ff9f" stroke-opacity="0.12"/></pattern>',
 '<filter id="glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="3" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter>',
 '<linearGradient id="scan" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#00ff9f" stop-opacity="0"/><stop offset="0.5" stop-color="#00ff9f" stop-opacity="0.25"/><stop offset="1" stop-color="#00ff9f" stop-opacity="0"/></linearGradient>',
 '<style>text{font-family:"Fira Code","JetBrains Mono",Consolas,monospace}.l{font-size:11px;letter-spacing:3px;fill:#8b93b5}.n{font-size:28px;font-weight:700;fill:#eaf2ff;filter:url(#glow)}.h{font-size:13px;letter-spacing:4px;fill:#00ff9f}.p{font-size:10px;fill:#8b93b5}.ln{font-size:12px;fill:#eaf2ff}.cur{animation:blink 1s infinite steps(1)}@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}',
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
    s.append(f'<g class="f{i}"><text class="l" x="{x}" y="{y}">{lab}</text>'
             f'<text class="n" x="{x}" y="{y+32}">{val:,}</text>'
             f'<text class="p" x="{x}" y="{y+48}">{sub}</text></g>')

s.append('<text class="h" x="500" y="88">LANGUAGES</text>')
for i, lg in enumerate(fluent):
    pct = weights[i]
    y = 104 + i * 27
    w = int(330 * pct / 100)
    s.append(f'<g class="f{i+6}"><text class="ln" x="500" y="{y+9}">{lg["n"]}</text>'
             f'<rect x="640" y="{y+2}" width="220" height="6" rx="3" fill="#ffffff" fill-opacity="0.06"/>'
             f'<rect x="640" y="{y+2}" width="{int(220*pct/100)}" height="6" rx="3" fill="{lg["c"]}" filter="url(#glow)">'
             f'<animate attributeName="width" from="0" to="{int(220*pct/100)}" dur="1.2s" begin="{0.3+i*0.12:.2f}s" fill="freeze"/></rect></g>')

s.append(f'<rect width="{W}" height="50" fill="url(#scan)"><animate attributeName="y" values="-50;{H}" dur="4s" repeatCount="indefinite"/></rect></svg>')
os.makedirs(os.path.dirname(OUT), exist_ok=True)
open(OUT, "w", encoding="utf-8").write("\n".join(s))
print(f"ok: {total} contrib, {commits} commits, {len(fluent)} langs")
