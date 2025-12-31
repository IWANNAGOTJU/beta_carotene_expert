# 🧬 Beta-Carotene Expert System (Demo)

A lightweight expert-system-style pipeline for **β-carotene biosynthesis pathway analysis and engineering guidance**, designed as a **bioinformatics & synthetic biology demo project**.

---

## 📌 Project Overview

β-Carotene is an important carotenoid widely used in food, nutrition, and biotechnology.  
This project implements a **rule-based expert system** combined with **pathway mapping** to:

- Identify biosynthetic pathways related to β-carotene
- Map enzymes, genes, and reactions involved
- Generate structured outputs to guide metabolic engineering design

The goal is **not high-throughput prediction**, but a **clear, interpretable, and extendable framework** that demonstrates how computational analysis can guide wet-lab design.

---

## 🧠 System Design

The project follows an **expert-system-inspired architecture**:

1. **Product classification**
   - Classify target compounds (e.g. β-carotene) using keyword rules
2. **Pathway mapping**
   - Identify related metabolic pathways
3. **Gene / enzyme extraction**
   - Extract enzymes, reactions, and genes involved
4. **Engineering recommendations**
   - Provide structured outputs for downstream design decisions

All logic is transparent and easy to extend to other products.

---

## 📁 Project Structure

beta_carotene_expert/
├── data/ # Product classes and configuration files
├── scripts/ # Core analysis scripts
│ ├── classify_product.py
│ ├── kegg_demo.py
│ ├── yeast_mapping.py
│ └── run_expert_system.py
├── outputs/ # Generated analysis results (CSV / TXT / MD)
└── README.md
