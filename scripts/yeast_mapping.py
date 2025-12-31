# yeast_mapping.py
# Goal: Map carotenoid pathway genes to S. cerevisiae (sce) and mark missing steps.
# Run:
#   python scripts/yeast_mapping.py

import os
import re
import requests
import pandas as pd

BASE = "https://rest.kegg.jp"
OUTDIR = "outputs"
PATHWAY = "path:map00906"   # Carotenoid biosynthesis
ORG = "sce"                 # Saccharomyces cerevisiae


def kegg_get(entry: str) -> str:
    r = requests.get(f"{BASE}/get/{entry}", timeout=30)
    r.raise_for_status()
    return r.text


def kegg_link(target_db: str, source: str) -> str:
    """
    KEGG link API:
      /link/<target_db>/<source>
    Example:
      /link/sce/path:map00906  -> list of sce genes linked to that pathway (if any)
      /link/enzyme/path:map00906 -> EC numbers in pathway
      /link/reaction/path:map00906 -> reactions in pathway
    """
    r = requests.get(f"{BASE}/link/{target_db}/{source}", timeout=30)
    r.raise_for_status()
    return r.text


def parse_section(text: str, section: str):
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
    return [x for x in out if x]


def parse_kegg_link_pairs(text: str):
    """
    Parse KEGG /link output lines: <source>\t<target>
    """
    pairs = []
    for line in text.splitlines():
        if not line.strip():
            continue
        a, b = line.split("\t")
        pairs.append((a.strip(), b.strip()))
    return pairs


def ensure_outdir():
    os.makedirs(OUTDIR, exist_ok=True)


def main():
    ensure_outdir()

    # 1) Fetch pathway flat file for reference + save
    pathway_txt = kegg_get(PATHWAY)
    with open(os.path.join(OUTDIR, "pathway_raw.txt"), "w", encoding="utf-8") as f:
        f.write(pathway_txt)

    pathway_name = (parse_section(pathway_txt, "NAME") or [""])[0]

    # 2) Get EC list from flat file (already parsed by your previous script, but we recompute)
    enzyme_lines = parse_section(pathway_txt, "ENZYME")
    ec_list = []
    for line in enzyme_lines:
        # could be like "1.3.99.31 1.3.99.32"
        for token in re.split(r"\s+", line.strip()):
            token = token.replace("EC:", "").strip()
            if re.match(r"^\d+\.\d+\.\d+\.\d+$", token):
                ec_list.append(token)
    ec_list = sorted(set(ec_list))

    # 3) Link: pathway -> (sce genes)
    # If pathway truly has no native sce genes, this may be empty (which is itself informative).
    sce_link_txt = kegg_link(ORG, PATHWAY)
    sce_pairs = parse_kegg_link_pairs(sce_link_txt)
    sce_genes = sorted({t for _, t in sce_pairs})  # like "sce:YJL167W"
    df_sce = pd.DataFrame({"sce_gene": sce_genes})
    df_sce.to_csv(os.path.join(OUTDIR, "sce_genes_in_pathway.csv"), index=False, encoding="utf-8")

    # 4) For each EC in pathway, check whether sce has any gene annotated to that EC
    # via: link/<org>/ec:<EC>
    rows = []
    for ec in ec_list:
        txt = kegg_link(ORG, f"ec:{ec}")
        pairs = parse_kegg_link_pairs(txt)
        genes = sorted({t for _, t in pairs})  # sce:xxxx
        rows.append({
            "ec": ec,
            "sce_gene_count": len(genes),
            "sce_genes": ";".join(genes[:50])  # cap
        })

    df_ec = pd.DataFrame(rows)

    if df_ec.empty:
        print("WARNING: No ECs mapped. This pathway is likely fully heterologous in yeast.")
        df_ec = pd.DataFrame(columns=["ec", "sce_gene_count", "sce_genes"])
    else:
        df_ec = df_ec.sort_values(["sce_gene_count", "ec"], ascending=[True, True])

    


    # 6) Engineering recommendations (expert rules)
    # Rule: If no native ECs mapped -> fully heterologous pathway
    fully_heterologous = df_ec.empty or (df_ec["sce_gene_count"].sum() == 0)

    rows_rec = []

    if fully_heterologous:
        # Heterologous carotenoid module
        for g in ["crtE", "crtB", "crtI", "crtY"]:
            rows_rec.append({
                "module_type": "heterologous",
                "gene": g,
                "role": "carotenoid biosynthesis core step",
                "confidence": "high"
            })

    # Native precursor (MVA) enhancement suggestions
    for g in ["ERG10", "ERG13", "HMG1", "HMG2", "ERG12", "ERG8", "ERG19", "IDI1", "ERG20", "BTS1"]:
        rows_rec.append({
            "module_type": "native_enhancement",
            "gene": g,
            "role": "IPP/DMAPP/FPP/GGPP precursor supply (MVA pathway)",
            "confidence": "medium"
        })

    df_rec = pd.DataFrame(rows_rec)
    df_rec.to_csv(os.path.join(OUTDIR, "engineering_recommendations.csv"),
                index=False, encoding="utf-8")

    # Append to report
    with open(os.path.join(OUTDIR, "yeast_mapping_report.md"), "a", encoding="utf-8") as f:
        f.write("\n## Engineering Recommendations\n\n")
        if fully_heterologous:
            f.write("- **Pathway feasibility**: Fully heterologous in *S. cerevisiae*\n")
            f.write("- **Required heterologous module**: crtE / crtB / crtI / crtY\n")
        else:
            f.write("- **Pathway feasibility**: Partially native\n")

        f.write("- **Native precursor enhancement (MVA pathway)**:\n")
        f.write("  ERG10, ERG13, HMG1/2, ERG12, ERG8, ERG19, IDI1, ERG20, BTS1\n")
        f.write("- **Risk notes**: NADPH demand, membrane burden, sterol competition\n")

    print("Engineering recommendations written to outputs/engineering_recommendations.csv")

    

    # === MVA pathway expert annotation ===

    mva_genes = [
        ("ERG10", "Acetyl-CoA acetyltransferase", "non-essential"),
        ("ERG13", "HMG-CoA synthase", "non-essential"),
        ("HMG1", "HMG-CoA reductase", "rate-limiting"),
        ("HMG2", "HMG-CoA reductase isozyme", "rate-limiting"),
        ("ERG12", "Mevalonate kinase", "essential"),
        ("ERG8",  "Phosphomevalonate kinase", "essential"),
        ("ERG19", "Mevalonate diphosphate decarboxylase", "essential"),
        ("IDI1",  "IPP isomerase", "important"),
        ("ERG20", "FPP synthase", "branch-point"),
        ("BTS1",  "GGPP synthase", "target-directing"),
    ]

    rows_mva = []
    for g, role, tag in mva_genes:
        rows_mva.append({
            "gene": g,
            "role": role,
            "engineering_tag": tag,
            "recommended_action": (
                "overexpression" if tag in ["rate-limiting", "target-directing"]
                else "fine-tuning"
            )
        })

    df_mva = pd.DataFrame(rows_mva)
    df_mva.to_csv(os.path.join(OUTDIR, "mva_engineering_priorities.csv"),
                index=False, encoding="utf-8")




    df_ec.to_csv(os.path.join(OUTDIR, "ec_to_sce_genes.csv"), index=False, encoding="utf-8")

    # 5) Minimal report
    md_path = os.path.join(OUTDIR, "yeast_mapping_report.md")
    if "sce_gene_count" in df_ec.columns and not df_ec.empty:
        missing = df_ec[df_ec["sce_gene_count"] == 0]
        present = df_ec[df_ec["sce_gene_count"] > 0]
    else:
        missing = pd.DataFrame()
        present = pd.DataFrame()


    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# Yeast mapping for {PATHWAY} {pathway_name}\n\n")
        f.write(f"- ECs in pathway: {len(df_ec)}\n")
        f.write(f"- ECs with >=1 *{ORG}* gene: {len(present)}\n")
        f.write(f"- ECs with 0 *{ORG}* gene (likely heterologous needed): {len(missing)}\n\n")

        f.write("## Likely heterologous-needed ECs (sce_gene_count = 0)\n\n")
        if len(missing) == 0:
            f.write("None.\n")
        else:
            for _, r in missing.iterrows():
                f.write(f"- EC:{r['ec']}\n")

        f.write("\n## Files generated\n\n")
        f.write("- `sce_genes_in_pathway.csv`\n")
        f.write("- `ec_to_sce_genes.csv`\n")
        f.write("- `yeast_mapping_report.md`\n")

    print("OK")
    print(f"Pathway: {PATHWAY} {pathway_name}")
    print(f"Outputs: {os.path.abspath(OUTDIR)}")
    print(f"EC total={len(df_ec)}, present_in_sce={len(present)}, missing_in_sce={len(missing)}")



if __name__ == "__main__":
    main()

