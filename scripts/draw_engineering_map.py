# draw_engineering_map.py
# Goal: Draw engineering route map for beta-carotene production in yeast

import os
import networkx as nx
import matplotlib.pyplot as plt

OUTDIR = "outputs"

def main():
    G = nx.DiGraph()

    # ===== Nodes =====
    # Precursors
    G.add_node("Acetyl-CoA", type="precursor")

    # MVA pathway
    mva_nodes = [
        "ERG10", "ERG13", "HMG1/2",
        "ERG12", "ERG8", "ERG19",
        "IDI1", "ERG20", "BTS1"
    ]

    # Heterologous carotenoid pathway
    crt_nodes = ["crtE", "crtB", "crtI", "crtY"]

    # Product
    G.add_node("β-carotene", type="product")

    # Add nodes
    for n in mva_nodes:
        G.add_node(n, type="mva")

    for n in crt_nodes:
        G.add_node(n, type="heterologous")

    # ===== Edges =====
    # MVA flow
    G.add_edge("Acetyl-CoA", "ERG10")
    for i in range(len(mva_nodes) - 1):
        G.add_edge(mva_nodes[i], mva_nodes[i + 1])

    # Connect to heterologous pathway
    G.add_edge("BTS1", "crtE")
    for i in range(len(crt_nodes) - 1):
        G.add_edge(crt_nodes[i], crt_nodes[i + 1])

    # Final product
    G.add_edge("crtY", "β-carotene")

    # ===== Layout =====
    pos = {
        "Acetyl-CoA": (-4, 0),
        "ERG10": (-3, 0),
        "ERG13": (-2.5, 0),
        "HMG1/2": (-2, 0),
        "ERG12": (-1.5, 0),
        "ERG8": (-1, 0),
        "ERG19": (-0.5, 0),
        "IDI1": (0, 0),
        "ERG20": (0.5, 0),
        "BTS1": (1, 0),
        "crtE": (1.8, 0),
        "crtB": (2.4, 0),
        "crtI": (3.0, 0),
        "crtY": (3.6, 0),
        "β-carotene": (4.4, 0),
    }

    # ===== Draw =====
    plt.figure(figsize=(16, 4))

    node_colors = []
    for n in G.nodes():
        t = G.nodes[n]["type"]
        if t == "precursor":
            node_colors.append("#A6CEE3")
        elif t == "mva":
            node_colors.append("#B2DF8A")
        elif t == "heterologous":
            node_colors.append("#FB9A99")
        else:
            node_colors.append("#FDBF6F")

    nx.draw(
        G,
        pos,
        with_labels=True,
        node_color=node_colors,
        node_size=2500,
        font_size=9,
        arrows=True,
        arrowstyle="->",
        arrowsize=15
    )

    plt.title("Engineering Route for β-Carotene Production in Yeast", fontsize=14)
    plt.axis("off")

    os.makedirs(OUTDIR, exist_ok=True)
    outpath = os.path.join(OUTDIR, "beta_carotene_engineering_map.png")
    plt.savefig(outpath, dpi=300, bbox_inches="tight")
    plt.close()

    print(f"Engineering route map saved to {outpath}")

if __name__ == "__main__":
    main()
