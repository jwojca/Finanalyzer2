"""
One-time script: import keywords from groups.yaml into the FinAnalazer2 database.

- Matches YAML subgroup names to existing DB categories (case-insensitive).
- If no match found, creates a new category (with main group as parent).
- Skips keywords that already exist (case-insensitive) for the same category.

Usage:
    python import_yaml_keywords.py [path/to/groups.yaml]
"""
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import yaml
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from app import database as db

YAML_PATH = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    Path(r"C:\Users\xwojci00\Documents\FinAnalazer\Groups\groups.yaml")

# Manual name mapping: YAML subgroup name → existing DB category name
# Add more here if needed.
NAME_MAP = {
    "Restaurace a Fast Food": "Restaurace a fast food",
    "Léky": "Lékárna",
    "Lékaři": "Lékař",
    "Pojišťovny": "Pojistky",
    "Provoz": "Pohonné hmoty",
    "Servis a opravy": "Auto - servis a pojistky",
    "Doplňky, vybavení": "Vybavení a opravy",
    "Video": "Streaming",
    "Audio": "Streaming",
    "Ostatní": "Internet a telefon",
    "Akce": "Kino a kultura",
    "Vybavení": "Oblečení a obuv",
}

# Categories to skip entirely
SKIP = {"Uncategorized"}


def main():
    db.init_db()

    with open(YAML_PATH, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    # Build lookup: lowercase name → category row
    all_cats = db.get_all_categories()
    cat_by_name = {c["name"].lower(): c for c in all_cats}

    added_kw = 0
    skipped_kw = 0
    created_cats = []

    for group in data["groups"]:
        main_name = group["main"]
        if main_name in SKIP:
            continue

        for subgroup in group.get("subgroups", []):
            sub_name = subgroup["name"]
            if sub_name in SKIP:
                continue

            # Resolve DB category
            resolved_name = NAME_MAP.get(sub_name, sub_name)
            cat = cat_by_name.get(resolved_name.lower())

            if cat is None:
                # Find or create parent
                parent = cat_by_name.get(main_name.lower())
                if parent is None:
                    parent_id = db.add_category(main_name, None, "#888888")
                    new_parent = db.get_category_by_id(parent_id)
                    cat_by_name[main_name.lower()] = new_parent
                    parent = new_parent
                    created_cats.append(main_name)

                new_id = db.add_category(resolved_name, parent["id"], "#5599ff")
                cat = db.get_category_by_id(new_id)
                cat_by_name[resolved_name.lower()] = cat
                created_cats.append(resolved_name)
                print(f"  [NEW CAT] {main_name} -> {resolved_name}")

            # Get existing keywords for this category (lowercase)
            existing = {
                row["keyword"].lower()
                for row in db.get_keywords()
                if row["category_id"] == cat["id"]
            }

            for kw_raw in subgroup.get("keywords", []):
                kw = kw_raw.strip().upper()
                if kw.lower() in existing:
                    skipped_kw += 1
                    continue
                db.add_keyword(kw, cat["id"], "all", 5)
                existing.add(kw.lower())
                added_kw += 1

    print(f"\nHotovo:")
    print(f"  Přidáno klíčových slov: {added_kw}")
    print(f"  Přeskočeno (duplicity): {skipped_kw}")
    if created_cats:
        print(f"  Vytvořeny nové kategorie: {', '.join(created_cats)}")


if __name__ == "__main__":
    main()
