import csv, json, urllib.request
from datetime import datetime, timedelta

URL = "https://raw.githubusercontent.com/coinmetrics/data/master/csv/btc.csv"

print("Fetching BTC data...")
with urllib.request.urlopen(URL) as r:
    content = r.read().decode("utf-8")

lines = content.strip().split("\n")
header = lines[0].split(",")
date_idx = header.index("time")
price_idx = header.index("PriceUSD")

rows = []
for line in lines[1:]:
    cols = line.split(",")
    d = cols[date_idx]
    p = cols[price_idx].strip()
    if d >= "2011-01-01" and p:
        rows.append((d, float(p)))

price_map = {r[0]: r[1] for r in rows}
print(f"Loaded {len(rows)} daily prices from {rows[0][0]} to {rows[-1][0]}")

results = []
for date_str, buy_price in rows:
    buy_date = datetime.strptime(date_str, "%Y-%m-%d")
    sell_date = buy_date + timedelta(days=4 * 365 + 1)
    sell_price = None
    sell_date_str = None
    for offset in range(0, 5):
        candidate = (sell_date + timedelta(days=offset)).strftime("%Y-%m-%d")
        if candidate in price_map:
            sell_price = price_map[candidate]
            sell_date_str = candidate
            break
    if sell_price is None:
        continue
    annualized = (sell_price / buy_price) ** (1 / 4) - 1
    total_return = (sell_price / buy_price) - 1
    results.append({
        "b": date_str,
        "s": sell_date_str,
        "bp": round(buy_price, 2),
        "sp": round(sell_price, 2),
        "tr": round(total_return * 100, 2),
        "ar": round(annualized * 100, 2),
    })

results_sorted = sorted(results, key=lambda x: x["ar"], reverse=True)
for i, r in enumerate(results_sorted, 1):
    r["rank"] = i

ann = sorted([r["ar"] for r in results])
n = len(ann)

def pct(lst, p):
    return lst[int(len(lst) * p / 100)]

stats = {
    "n": n,
    "mean": round(sum(ann) / n, 1),
    "median": round(pct(ann, 50), 1),
    "p10": round(pct(ann, 10), 1),
    "p25": round(pct(ann, 25), 1),
    "p75": round(pct(ann, 75), 1),
    "p90": round(pct(ann, 90), 1),
    "best": round(ann[-1], 1),
    "worst": round(ann[0], 1),
    "last_updated": rows[-1][0],
    "latest_price": round(rows[-1][1], 0),
}

buckets = [0] * 7
for v in ann:
    if v < 50: buckets[0] += 1
    elif v < 100: buckets[1] += 1
    elif v < 150: buckets[2] += 1
    elif v < 200: buckets[3] += 1
    elif v < 250: buckets[4] += 1
    elif v < 300: buckets[5] += 1
    else: buckets[6] += 1

print(f"Computed {n} four-year periods. Median: {stats['median']}% Worst: {stats['worst']}%")

data_json = json.dumps(results, separators=(",", ":"))
stats_json = json.dumps(stats, separators=(",", ":"))
buckets_json = json.dumps(buckets)

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Bitcoin 4-year return explorer</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,600;1,9..144,300&display=swap" rel="stylesheet">
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#0d0f12;
  --surface:#151820;
  --surface2:#1d2230;
  --border:#2a3045;
  --text:#e8eaf0;
  --muted:#7a8099;
  --accent:#f0c040;
  --accent2:#4a9eff;
  --green:#4ade80;
  --red:#f87171;
  --mono:'DM Mono',monospace;
  --serif:'Fraunces',serif;
}}
body{{background:var(--bg);color:var(--text);font-family:var(--mono);min-height:100vh;padding:0}}
a{{color:var(--accent2);text-decoration:none}}

.page{{max-width:900px;margin:0 auto;padding:2.5rem 1.5rem 4rem}}

header{{margin-bottom:3rem;border-bottom:1px solid var(--border);padding-bottom:2rem}}
.eyebrow{{font-size:11px;letter-spacing:0.12em;color:var(--muted);text-transform:uppercase;margin-bottom:0.75rem}}
h1{{font-family:var(--serif);font-size:clamp(2rem,5vw,3.2rem);font-weight:300;line-height:1.15;color:var(--text);margin-bottom:0.75rem}}
h1 em{{font-style:italic;color:var(--accent)}}
.subtitle{{font-size:13px;color:var(--muted);line-height:1.6;max-width:560px}}
.badge{{display:inline-block;background:var(--surface2);border:1px solid var(--border);border-radius:4px;font-size:11px;padding:3px 8px;color:var(--muted);margin-top:1rem}}
.badge span{{color:var(--green)}}

.stat-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--border);border:1px solid var(--border);border-radius:10px;overflow:hidden;margin-bottom:2.5rem}}
.stat-cell{{background:var(--surface);padding:1.25rem 1rem;}}
.stat-cell .lbl{{font-size:10px;letter-spacing:0.1em;text-transform:uppercase;color:var(--muted);margin-bottom:0.5rem}}
.stat-cell .val{{font-family:var(--serif);font-size:1.9rem;font-weight:300;line-height:1}}
.stat-cell .sub{{font-size:10px;color:var(--muted);margin-top:0.35rem}}
.val-accent{{color:var(--accent)}}
.val-green{{color:var(--green)}}
.val-red{{color:var(--red)}}

.section-label{{font-size:10px;letter-spacing:0.12em;text-transform:uppercase;color:var(--muted);margin-bottom:1rem}}

.two-col{{display:grid;grid-template-columns:1fr 300px;gap:2rem;margin-bottom:2.5rem;align-items:start}}

.hist-wrap{{position:relative;height:200px}}
canvas{{display:block}}

.pct-table{{}}
.pct-row{{display:flex;align-items:center;gap:10px;padding:5px 0;border-bottom:1px solid var(--border)}}
.pct-row:last-child{{border-bottom:none}}
.pct-name{{font-size:11px;color:var(--muted);width:68px;flex-shrink:0}}
.pct-bar-bg{{flex:1;height:4px;background:var(--surface2);border-radius:2px;overflow:hidden}}
.pct-bar-fill{{height:100%;border-radius:2px;background:var(--accent2)}}
.pct-val{{font-size:12px;font-weight:500;width:52px;text-align:right;color:var(--text)}}
.pct-row.highlight .pct-name{{color:var(--accent);font-weight:500}}
.pct-row.highlight .pct-bar-fill{{background:var(--accent)}}
.pct-row.highlight .pct-val{{color:var(--accent)}}

.lookup-box{{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:1.5rem;margin-bottom:2.5rem}}
.lookup-box h2{{font-family:var(--serif);font-size:1.2rem;font-weight:300;margin-bottom:1rem;color:var(--text)}}
.lookup-controls{{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin-bottom:0.75rem}}
.lookup-controls input[type=date]{{background:var(--surface2);border:1px solid var(--border);border-radius:6px;color:var(--text);font-family:var(--mono);font-size:13px;padding:8px 12px;outline:none;cursor:pointer;colorscheme:dark}}
.lookup-controls input[type=date]:focus{{border-color:var(--accent)}}
.lookup-controls button{{background:var(--accent);border:none;border-radius:6px;color:#0d0f12;font-family:var(--mono);font-size:13px;font-weight:500;padding:8px 20px;cursor:pointer;transition:opacity 0.15s}}
.lookup-controls button:hover{{opacity:0.85}}
.hint{{font-size:11px;color:var(--muted)}}
#noResult{{display:none;font-size:13px;color:var(--muted);padding:0.5rem 0}}
#lookupResult{{display:none;margin-top:1.25rem}}
.result-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--border);border:1px solid var(--border);border-radius:8px;overflow:hidden;margin-bottom:0.75rem}}
.result-cell{{background:var(--surface2);padding:0.75rem 1rem}}
.result-cell .lbl{{font-size:10px;letter-spacing:0.08em;text-transform:uppercase;color:var(--muted);margin-bottom:0.3rem}}
.result-cell .val{{font-size:14px;font-weight:500;color:var(--text)}}
.val-big{{font-family:var(--serif);font-size:1.4rem!important;font-weight:300!important}}
#r-context{{font-size:12px;color:var(--muted);line-height:1.6;padding:0.5rem 0}}

footer{{font-size:11px;color:var(--muted);border-top:1px solid var(--border);padding-top:1.5rem;line-height:1.8}}

@media(max-width:640px){{
  .stat-grid{{grid-template-columns:1fr 1fr}}
  .two-col{{grid-template-columns:1fr}}
  .result-grid{{grid-template-columns:1fr 1fr}}
}}
</style>
</head>
<body>
<div class="page">

<header>
  <div class="eyebrow">Historical analysis · 2011 – present</div>
  <h1>Bitcoin <em>4-year</em><br>return explorer</h1>
  <p class="subtitle">Every 4-year holding period since 2011, annualised and ranked. Based on {n:,} complete holding periods.</p>
  <div class="badge">Last updated: <span id="lastUpdated">—</span> &nbsp;·&nbsp; Latest BTC price: <span id="latestPrice">—</span></div>
</header>

<div class="stat-grid">
  <div class="stat-cell">
    <div class="lbl">Median return</div>
    <div class="val val-accent" id="sc-median">—</div>
    <div class="sub">50th percentile · annualised</div>
  </div>
  <div class="stat-cell">
    <div class="lbl">Mean return</div>
    <div class="val" id="sc-mean">—</div>
    <div class="sub">average across all periods</div>
  </div>
  <div class="stat-cell">
    <div class="lbl">Worst period ever</div>
    <div class="val val-red" id="sc-worst">—</div>
    <div class="sub">lowest annualised return</div>
  </div>
  <div class="stat-cell">
    <div class="lbl">Positive periods</div>
    <div class="val val-green">100%</div>
    <div class="sub">every single holding period</div>
  </div>
</div>

<div class="two-col">
  <div>
    <div class="section-label">Distribution of annualised returns</div>
    <div class="hist-wrap">
      <canvas id="histChart" role="img" aria-label="Histogram showing distribution of Bitcoin 4-year annualised returns"></canvas>
    </div>
  </div>
  <div>
    <div class="section-label">Percentile breakdown</div>
    <div class="pct-table" id="pctTable"></div>
  </div>
</div>

<div class="lookup-box">
  <h2>Look up any buy date</h2>
  <div class="lookup-controls">
    <input type="date" id="dateInput" min="2011-01-01" max="2022-12-31" />
    <button onclick="doLookup()">Calculate →</button>
  </div>
  <div class="hint">Enter any date between 2011–2022 to see what that 4-year holding period returned</div>
  <div id="noResult"></div>
  <div id="lookupResult">
    <div class="result-grid">
      <div class="result-cell"><div class="lbl">Buy date</div><div class="val" id="r-buy">—</div></div>
      <div class="result-cell"><div class="lbl">Sell date</div><div class="val" id="r-sell">—</div></div>
      <div class="result-cell"><div class="lbl">Buy price</div><div class="val" id="r-bp">—</div></div>
      <div class="result-cell"><div class="lbl">Sell price</div><div class="val" id="r-sp">—</div></div>
      <div class="result-cell"><div class="lbl">Total return</div><div class="val val-big" id="r-tr">—</div></div>
      <div class="result-cell"><div class="lbl">Annualised return</div><div class="val val-big val-accent" id="r-ar">—</div></div>
      <div class="result-cell"><div class="lbl">Rank</div><div class="val" id="r-rank">—</div></div>
      <div class="result-cell"><div class="lbl">Percentile</div><div class="val" id="r-pct">—</div></div>
    </div>
    <div id="r-context"></div>
  </div>
</div>

<footer>
  Data source: <a href="https://github.com/coinmetrics/data" target="_blank">CoinMetrics open data</a> via GitHub &nbsp;·&nbsp;
  Returns are annualised using (sell/buy)^(1/4) − 1 &nbsp;·&nbsp;
  Past performance does not guarantee future results &nbsp;·&nbsp;
  Updated automatically each month
</footer>

</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.js"></script>
<script>
const STATS = {stats_json};
const BUCKETS = {buckets_json};
const ALL_DATA = {data_json};

const dataByDate = {{}};
ALL_DATA.forEach(r => {{ dataByDate[r.b] = r; }});

document.getElementById('sc-median').textContent = STATS.median.toFixed(1) + '%';
document.getElementById('sc-mean').textContent = STATS.mean.toFixed(1) + '%';
document.getElementById('sc-worst').textContent = STATS.worst.toFixed(1) + '%';
document.getElementById('lastUpdated').textContent = STATS.last_updated;
document.getElementById('latestPrice').textContent = '$' + STATS.latest_price.toLocaleString();

const pctiles = [
  {{label:'10th pct', val:STATS.p10, highlight:false}},
  {{label:'25th pct', val:STATS.p25, highlight:false}},
  {{label:'Median',   val:STATS.median, highlight:true}},
  {{label:'Mean',     val:STATS.mean, highlight:true}},
  {{label:'75th pct', val:STATS.p75, highlight:false}},
  {{label:'90th pct', val:STATS.p90, highlight:false}},
];
const pctTable = document.getElementById('pctTable');
pctiles.forEach(p => {{
  const w = Math.min(100, (p.val / STATS.best) * 100);
  const row = document.createElement('div');
  row.className = 'pct-row' + (p.highlight ? ' highlight' : '');
  row.innerHTML = `<span class="pct-name">${{p.label}}</span>
    <div class="pct-bar-bg"><div class="pct-bar-fill" style="width:${{w}}%"></div></div>
    <span class="pct-val">${{p.val.toFixed(1)}}%</span>`;
  pctTable.appendChild(row);
}});

new Chart(document.getElementById('histChart'), {{
  type: 'bar',
  data: {{
    labels: ['0–50%','50–100%','100–150%','150–200%','200–250%','250–300%','300%+'],
    datasets: [{{
      data: BUCKETS,
      backgroundColor: BUCKETS.map((_,i) => i===1||i===2 ? '#f0c040' : '#2a3a5a'),
      borderWidth: 0,
      borderRadius: 3,
    }}]
  }},
  options: {{
    responsive: true, maintainAspectRatio: false,
    plugins: {{
      legend: {{display:false}},
      tooltip: {{
        backgroundColor:'#1d2230',
        titleColor:'#7a8099',
        bodyColor:'#e8eaf0',
        borderColor:'#2a3045',
        borderWidth:1,
        callbacks: {{label: ctx => ` ${{ctx.parsed.y.toLocaleString()}} periods`}}
      }}
    }},
    scales: {{
      x: {{ticks:{{font:{{size:11,family:"'DM Mono',monospace"}},color:'#7a8099'}},grid:{{display:false}},border:{{color:'#2a3045'}}}},
      y: {{ticks:{{font:{{size:11,family:"'DM Mono',monospace"}},color:'#7a8099',callback:v=>v.toLocaleString()}},grid:{{color:'#1d2230'}},border:{{color:'#2a3045'}}}}
    }}
  }}
}});

function addDays(s, n) {{
  const d = new Date(s); d.setDate(d.getDate()+n); return d.toISOString().split('T')[0];
}}
function fmtP(p) {{
  if(p < 1) return '$' + p.toFixed(4);
  if(p < 1000) return '$' + p.toFixed(2);
  return '$' + p.toLocaleString('en-US', {{maximumFractionDigits:0}});
}}

function doLookup() {{
  const val = document.getElementById('dateInput').value;
  if(!val) return;
  document.getElementById('lookupResult').style.display = 'none';
  document.getElementById('noResult').style.display = 'none';

  let found = null;
  for(let off=0; off<5; off++) {{
    const c = addDays(val, off);
    if(dataByDate[c]) {{ found = dataByDate[c]; break; }}
  }}

  if(!found) {{
    const no = document.getElementById('noResult');
    no.style.display = 'block';
    no.textContent = 'No data for that date — the 4-year exit may not yet exist. Try a date before 2023.';
    return;
  }}

  const allAr = ALL_DATA.map(r=>r.ar).sort((a,b)=>a-b);
  const below = allAr.filter(v=>v<=found.ar).length;
  const pctile = Math.round(below/allAr.length*100);

  document.getElementById('r-buy').textContent = found.b;
  document.getElementById('r-sell').textContent = found.s;
  document.getElementById('r-bp').textContent = fmtP(found.bp);
  document.getElementById('r-sp').textContent = fmtP(found.sp);
  document.getElementById('r-tr').textContent = found.tr.toFixed(1) + '%';
  document.getElementById('r-ar').textContent = found.ar.toFixed(1) + '%/yr';
  document.getElementById('r-rank').textContent = '#' + found.rank.toLocaleString() + ' of ' + ALL_DATA.length.toLocaleString();
  document.getElementById('r-pct').textContent = pctile + 'th percentile';

  const diff = found.ar - STATS.median;
  document.getElementById('r-context').textContent = diff >= 0
    ? `This period beat the median by ${{diff.toFixed(1)}}pp (${{found.ar.toFixed(1)}}% vs ${{STATS.median}}% median).`
    : `This period was ${{Math.abs(diff).toFixed(1)}}pp below the median (${{found.ar.toFixed(1)}}% vs ${{STATS.median}}% median) — still a strong positive return.`;

  document.getElementById('lookupResult').style.display = 'block';
}}

document.getElementById('dateInput').addEventListener('keydown', e => {{ if(e.key==='Enter') doLookup(); }});
</script>
</body>
</html>"""

with open("index.html", "w") as f:
    f.write(html)

print(f"index.html written ({len(html):,} bytes)")
