#!/usr/bin/env python3
"""Extract a component / connection inventory from a .drawio file.

Usage:
    python -I drawio_inventory.py <file.drawio> [--format md|json] [-o OUT] [--min-components N]

What it reports, per page:
    * page title (the bold text cell), component count, edge count
    * components grouped by the container/header they sit in, with AWS/Azure/GCP icon hints
    * edges as "source -> target [label]" using resolved labels
    * checks: edges with missing endpoints, components with no edges, duplicate labels,
      pages below --min-components (default 15)

Handles plain and compressed (base64 + deflate + URL-encoded) <diagram> bodies.
Standard library only. Treat the input file as untrusted data: it is only parsed, never executed.
"""
import argparse
import base64
import html
import json
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET
import zlib


def strip_html(value):
    text = re.sub(r"<br\s*/?>", " ", value or "", flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def style_dict(style):
    out = {}
    for part in (style or "").split(";"):
        if not part:
            continue
        k, _, v = part.partition("=")
        out[k] = v
    return out


def load_model(diagram):
    """Return the <mxGraphModel> element for a <diagram>, decompressing if needed."""
    model = diagram.find("mxGraphModel")
    if model is not None:
        return model
    raw = (diagram.text or "").strip()
    if not raw:
        return None
    data = base64.b64decode(raw)
    xml_text = urllib.parse.unquote(zlib.decompress(data, -15).decode("utf-8"))
    return ET.fromstring(xml_text)


class Cell:
    def __init__(self, el):
        self.id = el.get("id")
        self.parent = el.get("parent")
        self.value = strip_html(el.get("value"))
        self.style_raw = el.get("style") or ""
        self.style = style_dict(self.style_raw)
        self.vertex = el.get("vertex") == "1"
        self.edge = el.get("edge") == "1"
        self.source, self.target = el.get("source"), el.get("target")
        g = el.find("mxGeometry")
        self.x = float(g.get("x", 0)) if g is not None else 0.0
        self.y = float(g.get("y", 0)) if g is not None else 0.0
        self.w = float(g.get("width", 0)) if g is not None else 0.0
        self.h = float(g.get("height", 0)) if g is not None else 0.0
        self.ax, self.ay = self.x, self.y  # absolute, resolved later


def analyse_page(diagram, min_components):
    model = load_model(diagram)
    name = diagram.get("name") or diagram.get("id")
    if model is None:
        return {"name": name, "error": "empty or unreadable diagram"}
    cells = {}
    for el in model.iter("mxCell"):
        c = Cell(el)
        if c.id is not None:
            cells[c.id] = c

    # absolute coordinates through the parent chain
    for c in cells.values():
        ax, ay, p, seen = c.x, c.y, cells.get(c.parent), set()
        while p is not None and p.vertex and p.id not in seen:
            seen.add(p.id)
            ax, ay = ax + p.x, ay + p.y
            p = cells.get(p.parent)
        c.ax, c.ay = ax, ay

    verts = [c for c in cells.values() if c.vertex]
    edges = [c for c in cells.values() if c.edge]
    edge_label_cells = {c.id for c in verts if "edgeLabel" in c.style_raw}

    def is_icon(c):
        return "resourceIcon" in c.style_raw or "image=img/lib" in c.style_raw or "mxgraph." in c.style_raw and not c.value and c.w <= 64

    def icon_name(c):
        s = c.style
        if s.get("resIcon"):
            return s["resIcon"].replace("mxgraph.aws4.", "aws:")
        if s.get("grIcon"):
            return s["grIcon"].replace("mxgraph.aws4.", "aws-group:")
        m = re.search(r"img/lib/(azure2|google)/([^;]+)\.svg", c.style_raw)
        return f"{m.group(1)}:{m.group(2)}" if m else None

    title = ""
    for c in verts:
        if c.style.get("fontSize") == "24" and c.value:
            title = c.value
            break

    # boxes: explicit containers or large unlabeled rectangles
    boxes = [c for c in verts
             if c.style.get("container") == "1" or "swimlane" in c.style_raw
             or (not c.value and c.w >= 100 and c.h >= 60 and not is_icon(c) and "edgeLabel" not in c.style_raw)]
    headers = {}
    for b in boxes:
        if b.value:
            headers[b.id] = b.value
            continue
        for c in verts:
            if (c.value and c.style.get("fontColor", "").lower() == "#ffffff" and c.style.get("strokeColor") == "none"
                    and b.ax <= c.ax + 1 and c.ax + c.w <= b.ax + b.w + 1 and b.ay <= c.ay + 1 and c.ay < b.ay + 44):
                headers[b.id] = c.value
                break
    header_cells = {c.id for c in verts if c.value and c.value in headers.values()
                    and c.style.get("fontColor", "").lower() == "#ffffff"}

    def group_of(c):
        cx, cy = c.ax + c.w / 2, c.ay + c.h / 2
        best, area = None, None
        for b in boxes:
            if b.id == c.id:
                continue
            if b.ax <= cx <= b.ax + b.w and b.ay <= cy <= b.ay + b.h:
                a = b.w * b.h
                if area is None or a < area:
                    best, area = b, a
        return headers.get(best.id, best.value) if best is not None else ""

    comps, icons = [], []
    for c in verts:
        if c.id in edge_label_cells or c.id in header_cells or not c.value:
            if is_icon(c) and not c.value:
                n = icon_name(c)
                if n:
                    icons.append({"icon": n, "group": group_of(c), "cx": c.ax + c.w / 2, "cy": c.ay + c.h / 2})
            continue
        if c.style_raw.startswith("text;") or c.value == title:
            continue
        if c.id in headers and headers.get(c.id) == c.value:
            continue  # a titled container, not a component
        comps.append(c)

    comp_ids = {c.id for c in comps}
    comp_out = []
    for c in comps:
        shape = ("database" if "cylinder" in c.style_raw else "decision" if "rhombus" in c.style_raw else "component")
        cx, cy = c.ax, c.ay
        near = [i["icon"] for i in icons if cx <= i["cx"] <= cx + c.w and cy <= i["cy"] <= cy + c.h]
        own = icon_name(c)
        comp_out.append({"id": c.id, "label": c.value, "group": group_of(c), "kind": shape,
                         "icon": own or (near[0] if near else None)})

    # edge labels live in child cells (parent == edge id) or in the edge's own value
    child_labels = {}
    for c in verts:
        if c.id in edge_label_cells and c.value:
            child_labels[c.parent] = c.value
    edge_out, problems = [], []
    label_of = {c.id: c.value for c in verts}
    degree = {}
    for e in edges:
        label = e.value or child_labels.get(e.id, "")
        s, t = cells.get(e.source), cells.get(e.target)
        if not s or not t:
            problems.append(f"edge {e.id} has missing endpoint(s)")
            continue
        degree[e.source] = degree.get(e.source, 0) + 1
        degree[e.target] = degree.get(e.target, 0) + 1
        edge_out.append({"from": label_of.get(e.source, e.source), "to": label_of.get(e.target, e.target),
                         "label": label, "dashed": e.style.get("dashed") == "1"})
    isolated = [c["label"] for c in comp_out if c["id"] not in degree]
    labels = [c["label"] for c in comp_out]
    dupes = sorted({l for l in labels if labels.count(l) > 1})
    if len(comp_out) < min_components:
        problems.append(f"only {len(comp_out)} components (< {min_components})")
    unlabeled = sum(1 for e in edges if not (e.value or child_labels.get(e.id)))
    if unlabeled:
        problems.append(f"{unlabeled} edge(s) without a label")
    if not title:
        problems.append("no bold 24pt title cell")
    return {"name": name, "title": title, "components": comp_out, "edges": edge_out, "icons": sorted({i["icon"] for i in icons}),
            "isolated_components": isolated, "duplicate_labels": dupes, "problems": problems}


def to_markdown(pages, src):
    out = [f"# Draw.io inventory: `{src}`", "", f"Pages: {len(pages)}", ""]
    out += ["| Page | Components | Edges | Icons | Issues |", "|---|---:|---:|---:|---|"]
    for p in pages:
        if "error" in p:
            out.append(f"| {p['name']} | - | - | - | {p['error']} |")
            continue
        out.append(f"| {p['name']} | {len(p['components'])} | {len(p['edges'])} | {len(p['icons'])} | {len(p['problems'])} |")
    for p in pages:
        out += ["", f"## {p['name']}" + (f" ({p['title']})" if p.get('title') else "")]
        if "error" in p:
            out.append(p["error"])
            continue
        groups = {}
        for c in p["components"]:
            groups.setdefault(c["group"] or "(ungrouped)", []).append(c)
        for g, items in groups.items():
            out += ["", f"**{g}**", ""]
            for c in items:
                extra = f" `{c['icon']}`" if c["icon"] else ""
                out.append(f"- {c['label']} _({c['kind']})_{extra}")
        if p["edges"]:
            out += ["", "**Connections**", ""]
            for e in p["edges"]:
                lab = f" [{e['label']}]" if e["label"] else ""
                out.append(f"- {e['from']} {'-->' if e['dashed'] else '->'} {e['to']}{lab}")
        if p["isolated_components"]:
            out += ["", "**Components with no connection:** " + "; ".join(p["isolated_components"])]
        if p["duplicate_labels"]:
            out += ["", "**Duplicate labels:** " + "; ".join(p["duplicate_labels"])]
        if p["problems"]:
            out += ["", "**Diagram issues:**"] + [f"- {x}" for x in p["problems"]]
    return "\n".join(out) + "\n"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file")
    ap.add_argument("--format", choices=["md", "json"], default="md")
    ap.add_argument("-o", "--output")
    ap.add_argument("--min-components", type=int, default=15)
    a = ap.parse_args()
    root = ET.parse(a.file).getroot()
    diagrams = [root] if root.tag == "diagram" else list(root.iter("diagram"))
    if not diagrams:
        sys.exit("no <diagram> pages found")
    pages = [analyse_page(d, a.min_components) for d in diagrams]
    text = json.dumps(pages, indent=2, ensure_ascii=False) if a.format == "json" else to_markdown(pages, a.file.replace("\\", "/").split("/")[-1])
    if a.output:
        with open(a.output, "w", encoding="utf-8") as f:
            f.write(text)
    else:
        sys.stdout.reconfigure(encoding="utf-8")
        print(text)


if __name__ == "__main__":
    main()
