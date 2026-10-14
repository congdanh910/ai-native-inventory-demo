"""Pure item model: every rule about items lives here (no files, no printing)."""

from dataclasses import dataclass, replace
import re

SKU = re.compile(r"[A-Z0-9][A-Z0-9-]{1,19}")


@dataclass(frozen=True)
class Item:
    sku: str
    name: str
    quantity: int
    created_at: str  # ISO 8601, set by the caller so tests stay deterministic
    updated_at: str
    category: str | None = None


def normalize_sku(sku: str) -> str:
    value = (sku or "").strip().upper()
    if not SKU.fullmatch(value):
        raise ValueError(f"Invalid SKU: {sku!r}")
    return value


def normalize_category(category: str | None) -> str | None:
    if category is None:
        return None
    if not isinstance(category, str):
        raise ValueError("Category must be a string")
    return category.strip().lower() or None


def add_item(
    items: list[Item], sku: str, name: str, quantity: int, now: str,
    category: str | None = None,
) -> list[Item]:
    sku = normalize_sku(sku)
    name = (name or "").strip()
    if not name:
        raise ValueError("Name is required")
    if not isinstance(quantity, int) or quantity < 0:
        raise ValueError("Quantity must be a whole number of at least 0")
    if any(item.sku == sku for item in items):
        raise ValueError(f"SKU already exists: {sku}")
    return [*items, Item(sku, name, quantity, now, now, normalize_category(category))]


def adjust_stock(items: list[Item], sku: str, delta: int, now: str) -> list[Item]:
    sku = normalize_sku(sku)
    if not isinstance(delta, int) or delta == 0:
        raise ValueError("Adjustment must be a non-zero whole number")
    found = False
    result = []
    for item in items:
        if item.sku == sku:
            found = True
            if item.quantity + delta < 0:
                raise ValueError(f"Not enough stock for {sku}: have {item.quantity}, need {-delta}")
            item = replace(item, quantity=item.quantity + delta, updated_at=now)
        result.append(item)
    if not found:
        raise ValueError(f"Unknown SKU: {sku}")
    return result


def remove_item(items: list[Item], sku: str) -> list[Item]:
    sku = normalize_sku(sku)
    if not any(item.sku == sku for item in items):
        raise ValueError(f"Unknown SKU: {sku}")
    return [item for item in items if item.sku != sku]


def sorted_items(items: list[Item]) -> list[Item]:
    return sorted(items, key=lambda item: item.sku)


def filter_by_category(items: list[Item], category: str | None) -> list[Item]:
    category = normalize_category(category)
    if category is None:
        return list(items)
    return [item for item in items if item.category == category]
