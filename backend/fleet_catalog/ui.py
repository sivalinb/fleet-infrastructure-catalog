"""Python interface for infrastructure identity, ownership, and source evidence."""

import html
import os
from pathlib import Path
from uuid import uuid4

import gradio as gr
import httpx
import plotly.graph_objects as go

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / ".runtime/exports"
SCENARIOS = [
    ("Original source snapshots", "refresh"),
    ("Conflicting service ownership", "ownership-conflict"),
    ("Stale hardware feed", "stale-source"),
    ("Degraded node", "node-degraded"),
    ("Node absent from hardware feed", "missing-node"),
]
CSS = """
.gradio-container {max-width:1440px!important;margin:auto!important}
.hero {background:#102d4a;color:white;padding:30px;border-radius:16px;margin-bottom:14px}
.hero h1 {color:white;font-size:42px;letter-spacing:-.04em;margin:8px 0}
.hero p {color:#c7deed;max-width:840px;font-size:16px;line-height:1.6}
.eyebrow {font-size:11px;letter-spacing:.15em;text-transform:uppercase;color:#81e0d9}
.stats {display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:12px 0}
.stat {padding:18px;border:1px solid #d7e3ec;border-radius:12px;background:white;color:#17354f}
.stat b {display:block;font-size:28px;color:#17354f!important}.stat small {color:#587287}
@media(max-width:700px){.stats{grid-template-columns:repeat(2,1fr)}.hero h1{font-size:30px}}
"""


def request(path, body=None, raw=False):
    token = os.getenv("CATALOG_API_TOKEN", "")
    headers = {"Authorization": "Bearer " + token} if token else {}
    address = os.getenv("CATALOG_API_URL", "http://127.0.0.1:8002").rstrip("/")
    with httpx.Client(timeout=30, headers=headers) as client:
        response = (
            client.get(address + path)
            if body is None
            else client.post(address + path, json=body)
        )
        response.raise_for_status()
        return response.text if raw else response.json()


def topology(data, selected=None):
    levels = ["cluster", "rack", "node", "service", "team"]
    colors = ["#17354f", "#577ba4", "#008b96", "#7762c9", "#b98334"]
    positions = {}
    fig = go.Figure()
    for x, kind in enumerate(levels):
        items = [e for e in data.get("entities", []) if e["kind"] == kind]
        for y, entity in enumerate(items):
            positions[entity["id"]] = (x, (y + 1) / (len(items) + 1))
    for edge in data.get("edges", []):
        if edge["source"] not in positions or edge["target"] not in positions:
            continue
        a, b = positions[edge["source"]], positions[edge["target"]]
        active = selected in {edge["source"], edge["target"]}
        fig.add_trace(
            go.Scatter(
                x=[a[0], b[0]],
                y=[a[1], b[1]],
                mode="lines",
                line={
                    "color": "#008b96" if active else "#dce5ee",
                    "width": 3 if active else 1,
                },
                hoverinfo="skip",
                showlegend=False,
            )
        )
    for kind, color in zip(levels, colors):
        items = [e for e in data.get("entities", []) if e["kind"] == kind]
        fig.add_trace(
            go.Scatter(
                x=[positions[e["id"]][0] for e in items],
                y=[positions[e["id"]][1] for e in items],
                mode="markers",
                name=kind.title(),
                customdata=[e["id"] for e in items],
                hovertemplate="%{customdata}<extra></extra>",
                marker={
                    "size": [23 if e["id"] == selected else 14 for e in items],
                    "color": [
                        "#bd5c35" if e.get("health") == "degraded" else color
                        for e in items
                    ],
                },
            )
        )
    fig.update_layout(
        height=360,
        template="plotly_white",
        margin={"l": 25, "r": 25, "t": 35, "b": 25},
        showlegend=False,
        xaxis={
            "tickvals": list(range(5)),
            "ticktext": [k.upper() for k in levels],
            "range": [-0.2, 4.2],
            "showgrid": False,
            "zeroline": False,
        },
        yaxis={"visible": False},
        font={"family": "Arial", "color": "#17354f"},
    )
    return fig


def refresh():
    try:
        data = request("/api/catalog")
        entities = data["entities"]
        values = [
            ("Entities", len(entities)),
            ("Modeled GPU slots", sum(e.get("gpus", 0) for e in entities)),
            ("Sources", len(data["sources"])),
            ("Quality findings", sum(len(e["issues"]) for e in entities)),
        ]
        summary = (
            '<div class="stats">'
            + "".join(
                f'<div class="stat"><small>{label}</small><b>{value}</b></div>'
                for label, value in values
            )
            + "</div>"
        )
        sources = [
            [
                s["name"],
                "Stale" if s["stale"] else "Current",
                s["age_seconds"],
                s["ttl_seconds"],
            ]
            for s in data["sources"]
        ]
        issues = [
            [e["id"], i["code"], i["message"]] for e in entities for i in e["issues"]
        ]
        choices = [
            (e.get("name", e["id"]) + " · " + e["kind"], e["id"]) for e in entities
        ]
        return (
            data,
            summary,
            gr.update(
                choices=choices,
                value="node:FTL-A11"
                if any(e["id"] == "node:FTL-A11" for e in entities)
                else entities[0]["id"]
                if entities
                else None,
            ),
            topology(data),
            sources,
            issues,
        )
    except (httpx.HTTPError, ValueError, KeyError) as error:
        return (
            {},
            "Catalog API unavailable: " + html.escape(str(error)),
            gr.update(choices=[], value=None),
            topology({}),
            [],
            [],
        )


def inspect(entity_id, data):
    if not entity_id or not data:
        return {}, [], {}, topology(data or {})
    entity = next(e for e in data["entities"] if e["id"] == entity_id)
    provenance = [
        [field, p.get("source"), p.get("observed_at")]
        for field, p in entity["provenance"].items()
    ]
    return (
        entity,
        provenance,
        request("/api/impact/" + entity_id),
        topology(data, entity_id),
    )


def apply_fixture(name):
    request("/api/catalog/scenarios/" + name, {})
    return refresh()


def export_catalog():
    REPORTS.mkdir(parents=True, exist_ok=True)
    path = REPORTS / ("catalog-" + uuid4().hex + ".yaml")
    path.write_text(request("/api/catalog/export/backstage", raw=True))
    return str(path)


def build_app():
    with gr.Blocks(
        title="Fleet Infrastructure Catalog",
        analytics_enabled=False,
        delete_cache=(3600, 3600),
    ) as app:
        gr.HTML(
            '<div class="hero"><div class="eyebrow">Infrastructure catalog / 01</div><h1>Know what you operate.</h1><p>Connect hardware, services, and owners. Resolve conflicting observations without losing their source evidence.</p></div>'
        )
        summary = gr.HTML()
        data = gr.State({})
        with gr.Row():
            refresh_button = gr.Button("Refresh inventory", variant="primary")
            entity = gr.Dropdown(label="Infrastructure entity", choices=[], scale=3)
        graph = gr.Plot(topology({}), show_label=False)
        with gr.Tabs():
            with gr.Tab("Ownership & dependencies"):
                with gr.Row():
                    details = gr.JSON(label="Resolved entity")
                    exposure = gr.JSON(label="Dependency exposure")
                provenance = gr.Dataframe(
                    headers=["Field", "Source", "Observed at"],
                    interactive=False,
                    label="Field provenance",
                )
            with gr.Tab("Source quality"):
                sources = gr.Dataframe(
                    headers=["Source", "State", "Age (seconds)", "TTL (seconds)"],
                    interactive=False,
                )
                issues = gr.Dataframe(
                    headers=["Entity", "Finding", "Explanation"],
                    interactive=False,
                    wrap=True,
                )
                gr.Markdown(
                    "Fictional source fixtures model missing records, stale observations, and conflicting owners. Applying a fixture replaces the affected fixture source snapshot."
                )
                fixture = gr.Dropdown(
                    choices=SCENARIOS,
                    value="ownership-conflict",
                    label="Source fixture",
                )
                apply = gr.Button("Apply fixture")
            with gr.Tab("Audit & export"):
                audit_button = gr.Button("Refresh audit records")
                audit = gr.JSON(label="Lifecycle changes")
                export = gr.Button("Export Backstage catalog")
                file = gr.File(label="Catalog YAML", interactive=False)
            with gr.Tab("Architecture"):
                gr.HTML((ROOT / "docs/assets/reconciliation.svg").read_text())
                gr.Markdown(
                    "Source observations are retained separately from the resolved projection. Authority is chosen per field; source freshness, conflicting evidence, missing owners, and dangling dependencies remain visible. Dependency exposure describes a relationship graph, not a predicted outage."
                )
        outputs = [data, summary, entity, graph, sources, issues]
        app.load(refresh, outputs=outputs, api_name="catalog")
        refresh_button.click(refresh, outputs=outputs, api_name="refresh_catalog")
        entity.change(
            inspect,
            [entity, data],
            [details, provenance, exposure, graph],
            api_name="inspect_entity",
        )
        apply.click(apply_fixture, fixture, outputs, api_name="apply_fixture")
        audit_button.click(
            lambda: request("/api/audit"), outputs=audit, api_name="audit"
        )
        export.click(export_catalog, outputs=file, api_name="export_catalog")
    return app


def main():
    REPORTS.mkdir(parents=True, exist_ok=True)
    theme = gr.themes.Soft(primary_hue="teal", font=["Arial", "sans-serif"])
    values = theme.to_dict()["theme"]
    theme.set(
        **{
            key: values[key.removesuffix("_dark")]
            for key in values
            if key.endswith("_dark") and key.removesuffix("_dark") in values
        }
    )
    build_app().queue().launch(
        server_name=os.getenv("GRADIO_SERVER_NAME", "127.0.0.1"),
        server_port=int(os.getenv("GRADIO_SERVER_PORT", "7861")),
        share=False,
        ssr_mode=False,
        footer_links=[],
        allowed_paths=[str(REPORTS)],
        theme=theme,
        css=CSS,
    )


if __name__ == "__main__":
    main()
