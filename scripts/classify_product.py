import json

def classify_product(product_name, config_path="data/product_classes.json"):
    product = product_name.lower()
    with open(config_path, "r", encoding="utf-8") as f:
        classes = json.load(f)

    for cls, info in classes.items():
        for kw in info["keywords"]:
            if kw in product:
                return cls, info
    return None, None
