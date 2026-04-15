from collections import Counter, defaultdict
from datetime import datetime, timezone
from html import escape
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def build_statement_query(item_id: str) -> str:
    return f"""
SELECT ?property ?propertyLabel ?value ?valueLabel WHERE {{
  BIND(wd:{item_id} AS ?item)
  ?item ?p ?statement .
  ?property wikibase:claim ?p .
  ?statement ?ps ?value .
  ?property wikibase:statementProperty ?ps .

  SERVICE wikibase:label {{ bd:serviceParam wikibase:language \"[AUTO_LANGUAGE],en\". }}
}}
ORDER BY ?propertyLabel
""".strip()


def fetch_sparql_bindings(query: str, endpoint: str = "https://query.wikidata.org/sparql"):
    params = urlencode({"query": query, "format": "json"})
    request_url = f"{endpoint}?{params}"
    request = Request(
        request_url,
        headers={
            "Accept": "application/sparql-results+json",
            "User-Agent": "bimprototpye02-quarto-site/1.0 (https://www.wikidata.org/wiki/Q138547468)",
        },
    )
    with urlopen(request) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload.get("results", {}).get("bindings", [])


def properties_from_bindings(bindings):
    properties = defaultdict(list)
    for row in bindings:
        prop = row.get("propertyLabel", {}).get("value", "Unknown property")
        value_obj = row.get("value", {})
        value_type = value_obj.get("type", "literal")
        value_uri = value_obj.get("value", "")

        label = row.get("valueLabel", {}).get("value", value_uri)
        label = label if label else value_uri

        if value_type == "uri":
            properties[prop].append({"label": label, "url": value_uri, "kind": "entity"})
        else:
            properties[prop].append({"label": label, "url": "", "kind": "literal"})

    return properties


def property_frequency(properties):
    return Counter({k: len(v) for k, v in properties.items()})


def value_kind_breakdown(properties):
    counter = Counter()
    for values in properties.values():
        for v in values:
            counter[v.get("kind", "literal")] += 1
    return counter


def _bar_row(label: str, value: int, max_value: int, color: str) -> str:
    ratio = 0 if max_value == 0 else int((value / max_value) * 100)
    return (
        f'<div class="wd-bar-row">'
        f'<div class="wd-bar-label">{escape(label)}</div>'
        f'<div class="wd-bar-track"><div class="wd-bar-fill" style="width:{ratio}%;background:{color}"></div></div>'
        f'<div class="wd-bar-value">{value}</div>'
        f"</div>"
    )


def _property_chart_html(freq: Counter, top_n: int = 10) -> str:
    most_common = freq.most_common(top_n)
    if not most_common:
        return "<p>No properties found.</p>"

    max_value = max(v for _, v in most_common)
    rows = [
        _bar_row(label, value, max_value, "#1d4ed8")
        for label, value in most_common
    ]
    return "<div class=\"wd-bars\">" + "".join(rows) + "</div>"


def _kind_chart_html(kind_breakdown: Counter) -> str:
    entity_count = kind_breakdown.get("entity", 0)
    literal_count = kind_breakdown.get("literal", 0)
    total = entity_count + literal_count
    entity_pct = 0 if total == 0 else round((entity_count / total) * 100)
    literal_pct = 100 - entity_pct if total else 0

    return f"""
    <div class="wd-kind-wrap">
      <div class="wd-kind-bar">
        <div class="wd-kind-entity" style="width:{entity_pct}%"></div>
        <div class="wd-kind-literal" style="width:{literal_pct}%"></div>
      </div>
      <div class="wd-kind-legend">
        <span><strong>{entity_count}</strong> Entity values</span>
        <span><strong>{literal_count}</strong> Literal values</span>
      </div>
    </div>
    """


def render_profile_html(item_id: str, properties) -> str:
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    statement_count = sum(len(v) for v in properties.values())

    freq = property_frequency(properties)
    kind_breakdown = value_kind_breakdown(properties)

    cards = []
    for prop_name in sorted(properties.keys()):
        values_html = []
        for entry in properties[prop_name]:
            label = escape(entry["label"])
            if entry["url"]:
                url = escape(entry["url"])
                values_html.append(
                    f'<li><a href="{url}" target="_blank" rel="noopener">{label}</a></li>'
                )
            else:
                values_html.append(f"<li>{label}</li>")

        cards.append(
            f"""
            <section class=\"wd-card\">
              <h3>{escape(prop_name)}</h3>
              <ul>{''.join(values_html)}</ul>
            </section>
            """
        )

    return f"""
<style>
:root {{
  --bg: #f4f7fb;
  --ink: #0f172a;
  --card: #ffffff;
  --accent: #005f73;
  --border: #dbe4ee;
}}
body {{
  background: radial-gradient(circle at 20% 10%, #e2efff 0%, var(--bg) 45%);
}}
.wd-shell {{
  padding: 1rem 0 2rem;
}}
.wd-hero {{
  background: linear-gradient(135deg, #0a9396, #005f73);
  color: white;
  border-radius: 16px;
  padding: 1.25rem 1.5rem;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.14);
  margin-bottom: 1rem;
}}
.wd-hero h2 {{
  margin: 0;
  font-size: 1.5rem;
}}
.wd-meta {{
  margin-top: 0.4rem;
  color: #d8f3f4;
}}
.wd-insights {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: 0.85rem;
  margin-bottom: 1rem;
}}
.wd-panel {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 0.9rem 1rem;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
}}
.wd-panel h3 {{
  margin: 0 0 0.6rem;
  color: var(--accent);
}}
.wd-bars {{
  display: grid;
  gap: 0.4rem;
}}
.wd-bar-row {{
  display: grid;
  grid-template-columns: minmax(120px, 1fr) 2fr 40px;
  gap: 0.5rem;
  align-items: center;
  font-size: 0.9rem;
}}
.wd-bar-track {{
  height: 10px;
  background: #e5e7eb;
  border-radius: 999px;
  overflow: hidden;
}}
.wd-bar-fill {{
  height: 10px;
}}
.wd-kind-bar {{
  display: flex;
  width: 100%;
  height: 16px;
  background: #e5e7eb;
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 0.5rem;
}}
.wd-kind-entity {{
  background: #0f766e;
}}
.wd-kind-literal {{
  background: #f59e0b;
}}
.wd-kind-legend {{
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  font-size: 0.9rem;
}}
.wd-grid {{
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 0.85rem;
}}
.wd-card {{
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 0.9rem 1rem;
  box-shadow: 0 4px 14px rgba(15, 23, 42, 0.06);
}}
.wd-card h3 {{
  margin-top: 0;
  margin-bottom: 0.45rem;
  font-size: 1rem;
  color: var(--accent);
}}
.wd-card ul {{
  margin: 0;
  padding-left: 1.1rem;
  color: var(--ink);
}}
.wd-card li {{
  margin: 0.25rem 0;
  line-height: 1.35;
}}
.wd-card a {{
  color: #0a58ca;
  text-decoration: none;
}}
.wd-card a:hover {{
  text-decoration: underline;
}}
</style>

<div class="wd-shell">
  <section class="wd-hero">
    <h2>Wikidata Statement Profile</h2>
    <div class="wd-meta">Item: <strong>{escape(item_id)}</strong> · Statements: <strong>{statement_count}</strong> · Generated: {generated_at}</div>
    <div class="wd-meta"><a href="https://www.wikidata.org/wiki/{escape(item_id)}" style="color:white;text-decoration:underline" target="_blank" rel="noopener">Open item on Wikidata</a></div>
  </section>

  <section class="wd-insights">
    <div class="wd-panel">
      <h3>Top Properties by Statement Count</h3>
      {_property_chart_html(freq, top_n=10)}
    </div>
    <div class="wd-panel">
      <h3>Value Type Breakdown</h3>
      {_kind_chart_html(kind_breakdown)}
    </div>
  </section>

  <section class="wd-grid">
    {''.join(cards)}
  </section>
</div>
"""
