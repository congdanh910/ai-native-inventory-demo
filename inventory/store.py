"""JSON persistence. Loading validates every record; invalid files are reported, never silently changed."""

import json
from pathlib import Path

from inventory.items import Item, normalize_category

FORMAT_VERSION = 1


def load_items(path: Path) -> list[Item]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("version") != FORMAT_VERSION or not isinstance(data.get("items"), list):
        raise ValueError(f"{path} is not an inventory file of version {FORMAT_VERSION}")
    items = []
    for record in data["items"]:
        try:
            category = record.get("category")
            normalize_category(category)
            items.append(Item(sku=record["sku"], name=record["name"], quantity=int(record["quantity"]),
                              created_at=record["created_at"], updated_at=record["updated_at"],
                              category=category))
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{path} contains an invalid item: {record!r}") from exc
    return items


def save_items(path: Path, items: list[Item]) -> None:
    records = [item.__dict__ for item in items]
    path.write_text(json.dumps({"version": FORMAT_VERSION, "items": records}, indent=2) + "\n", encoding="utf-8")
