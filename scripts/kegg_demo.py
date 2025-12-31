# kegg_demo.py
# Run:
#   python kegg_demo.py
# Optional:
#   python kegg_demo.py --product "beta-carotene" --outdir outputs

import argparse
import os
import re
from typing import List, Dict, Tuple

import requests
import pandas as pd

BASE = "https://rest.kegg.jp"


def kegg_get(entry: str) -> str:
    r = requests.get(f"{BASE}/get/{entry}", timeout=30)
    r.raise_for_status()
    return r.text


def kegg_find(db: str, query: str) -> str:
    r = requests.get(f"{BASE}/find/{db}/{query}", timeout=30)
    r.raise_for_status()
    return r.text


def parse_kegg_section(text: str, section: str) -> List[str]:
    """
    Extract a SECTION from KEGG flat file.
    Returns a list of stripped lines belonging to that section.
    """
    lines = text.splitlines()
    collecting = False
    out = []
    for line in lines:
        if line.startswith(section):
            collecting = True
            out.append(line[len(section):].strip())
        elif collecting:
            if line.startswith(" "):
                out.append(line.strip())
            else:
                break
    # Flatten possible empty items
    return [x for x in out if x]


def parse_find_hits(find_text: str) -> List[Tuple[str, str]]:
    """
    Parse KEGG 'find' output: <id>\t<name>
    """
    hits = []
    for line in find_text.splitlines():
        if not line.strip():
            continue
        parts = line.split("\t", 1)
        if len(parts) == 2:
            hits.append((parts[0].strip(), parts[1].strip()))
    return hits


def choose_best_compound_id(product_query: str, hits: List[Tuple[str, str]]) -> str:
    """
    Minimal heuristic:
    - Prefer exact match on name (case-insensitive) in the hit description
    - Else return the first hit
    """
    q = product_query.strip().lower()
    for cid, desc in hits:
        # desc usually starts with primary name; try exact word boundary match
        if re.search(rf"\b{re.escape(q)}\b", desc.lower()):
            return cid
    if not hits:
        raise ValueError(f"No KEGG compound hits found for query: {product_query}")
    return hits[0][0]


def ensure_outdir(path: str) -> str:
    os.makedirs(path, exist_ok=True)
    return path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--product", default="beta-carotene", help="Compound name to search in KEGG.")
    ap.add_argument("--compound", default=None, help="Optional explicit KEGG compound id, e.g., cpd:C02094")
    ap.add_argument("--pathway", default="path:map00906", help="KEGG pathway id, e.g., path:map00906")
    ap.add_argument("--outdir", default="outputs", help="Output directory")
    args = ap.parse_args()

    outdir = ensure_outdir(args.outdir)

    # 1) Resolve compound id
    if args.compound:
        compound_id = args.compound
    else:
        find_txt = kegg_find("compound", args.product)
        hits = parse_find_hits(find_txt)
        compound_id = choose_best_compound_id(args.product, hits)

    # Normalize id prefixes
    if not compound_id.startswith(("cpd:", "C")):
        # e.g., "C02094"
        compound_id = compound_id
    if compound_id.startswith("C"):
        compound_id = f"cpd:{compound_id}"

    pathway_id = args.pathway
    if pathway_id.startswith("map"):
        pathway_id = f"path:{pathway_id}"
    if pathway_id.startswith("009"):
        pathway_id = f"path:map{pathway_id}"

    # 2) Fetch entries
    compound_txt = kegg_get(compound_id)
    pathway_txt = kegg_get(pathway_id)

    # Save raw
    with open(os.path.join(outdir, "compound_raw.txt"), "w", encoding="utf-8") as f:
        f.write(compound_txt)
    with open(os.path.join(outdir, "pathway_raw.txt"), "w", encoding="utf-8") as f:
        f.write(pathway_txt)

    # 3) Parse key sections
    comp_name_lines = parse_kegg_section(compound_txt, "NAME")
    comp_names = []
    for line in comp_name_lines:
        # NAME lines may contain multiple names separated by ';'
        comp_names.extend([x.strip() for x in line.split(";") if x.strip()])

    pathway_name_lines = parse_kegg_section(pathway_txt, "NAME")
    pathway_name = pathway_name_lines[0] if pathway_name_lines else ""

    enzymes = parse_kegg_section(pathway_txt, "ENZYME")
    reactions = parse_kegg_section(pathway_txt, "REACTION")
    compounds = parse_kegg_section(pathway_txt, "COMPOUND")
    genes = parse_kegg_section(pathway_txt, "GENE")

    # 4) Build structured tables
    summary = pd.DataFrame(
        [{
            "product_query": args.product,
            "compound_id": compound_id,
            "compound_names": "; ".join(comp_names[:20]),
            "pathway_id": pathway_id,
            "pathway_name": pathway_name
        }]
    )
    summary.to_csv(os.path.join(outdir, "summary.csv"), index=False, encoding="utf-8")

    df_enz = pd.DataFrame({"enzyme": enzymes})
    df_rxn = pd.DataFrame({"reaction": reactions})
    df_cpd = pd.DataFrame({"pathway_compound": compounds})
    df_gene = pd.DataFrame({"gene_line": genes})

    df_enz.to_csv(os.path.join(outdir, "pathway_enzymes.csv"), index=False, encoding="utf-8")
    df_rxn.to_csv(os.path.join(outdir, "pathway_reactions.csv"), index=False, encoding="utf-8")
    df_cpd.to_csv(os.path.join(outdir, "pathway_compounds.csv"), index=False, encoding="utf-8")
    df_gene.to_csv(os.path.join(outdir, "pathway_genes.csv"), index=False, encoding="utf-8")

    # 5) Minimal markdown report
    report_md = os.path.join(outdir, "report.md")
    with open(report_md, "w", encoding="utf-8") as f:
        f.write(f"# KEGG Expert System Demo: {args.product}\n\n")
        f.write(f"- Compound: **{compound_id}**\n")
        if comp_names:
            f.write(f"- Names: {', '.join(comp_names[:10])}\n")
        f.write(f"- Pathway: **{pathway_id}** {pathway_name}\n\n")
        f.write("## Parsed Items\n\n")
        f.write(f"- Enzymes (n={len(enzymes)}): saved to `pathway_enzymes.csv`\n")
        f.write(f"- Reactions (n={len(reactions)}): saved to `pathway_reactions.csv`\n")
        f.write(f"- Compounds (n={len(compounds)}): saved to `pathway_compounds.csv`\n")
        f.write(f"- Genes lines (n={len(genes)}): saved to `pathway_genes.csv`\n")

    print("OK")
    print(f"Output dir: {os.path.abspath(outdir)}")
    print(f"Compound: {compound_id}")
    print(f"Pathway : {pathway_id} {pathway_name}")


if __name__ == "__main__":
    main()
