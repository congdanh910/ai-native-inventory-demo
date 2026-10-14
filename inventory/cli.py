"""Command line interface: parses arguments, calls the model and the store, prints results. No rules here."""

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

from inventory.items import add_item, adjust_stock, filter_by_category, remove_item, sorted_items
from inventory.store import load_items, save_items


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="inventory", description="Keep track of stock.")
    parser.add_argument("--file", type=Path, default=Path("inventory.json"))
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="add an item")
    add.add_argument("sku")
    add.add_argument("name")
    add.add_argument("--quantity", type=int, default=0)
    add.add_argument("--category")
    adjust = commands.add_parser("adjust", help="add or remove stock")
    adjust.add_argument("sku")
    adjust.add_argument("delta", type=int)
    remove = commands.add_parser("remove", help="remove an item")
    remove.add_argument("sku")
    list_command = commands.add_parser("list", help="list items by SKU")
    list_command.add_argument("--category")
    return parser


def format_table(items) -> str:
    ordered = sorted_items(items)
    name_width = max([len("NAME"), *(len(item.name) for item in ordered)])
    lines = [f"{'SKU':<20} {'QTY':>6}  {'NAME':<{name_width}}  CATEGORY"]
    lines += [
        f"{item.sku:<20} {item.quantity:>6}  {item.name:<{name_width}}  {item.category or ''}"
        for item in ordered
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None, out=sys.stdout) -> int:
    args = build_parser().parse_args(argv)
    try:
        items = load_items(args.file)
        if args.command == "add":
            items = add_item(items, args.sku, args.name, args.quantity, now(), category=args.category)
        elif args.command == "adjust":
            items = adjust_stock(items, args.sku, args.delta, now())
        elif args.command == "remove":
            items = remove_item(items, args.sku)
        else:
            print(format_table(filter_by_category(items, args.category)), file=out)
            return 0
        save_items(args.file, items)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
