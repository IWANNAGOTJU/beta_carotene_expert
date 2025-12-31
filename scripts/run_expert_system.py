# run_expert_system.py
# Unified entry point for the metabolic expert system

import argparse
import subprocess
import sys
from classify_product import classify_product

def run(cmd):
    print(f"\n[RUN] {' '.join(cmd)}")
    ret = subprocess.run(cmd)
    if ret.returncode != 0:
        print("ERROR: command failed")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(
        description="Metabolic Engineering Expert System"
    )
    parser.add_argument(
        "--product", required=True, help="Target product name (e.g. beta-carotene)"
    )
    args = parser.parse_args()

    product = args.product
    print(f"\n=== Expert system started for product: {product} ===")

    # 1) Classify product
    cls, info = classify_product(product)
    if cls is None:
        print("ERROR: Product class not recognized.")
        print("Please extend product_classes.json")
        sys.exit(1)

    print(f"Product classified as: {cls}")
    print(f"Notes: {info.get('notes', 'N/A')}")

    # 2) Run KEGG analysis (data layer)
    run([sys.executable, "scripts/kegg_demo.py"])

    # 3) Run host feasibility & engineering logic
    run([sys.executable, "scripts/yeast_mapping.py"])

    # 4) Draw engineering map
    run([sys.executable, "scripts/draw_engineering_map.py"])

    print("\n=== Expert system finished successfully ===")
    print("Check outputs/ for reports, CSVs and engineering map.")

if __name__ == "__main__":
    main()
