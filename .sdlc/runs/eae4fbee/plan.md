# Plan v1: Categories

Add an optional category to items in three layers, keeping inventory format version 1. Older files have no category field, so they still load and the missing key is read as no category (AC-4). In inventory/items.py (rules): add a `category: str | None = None` field at the end of the frozen `Item` dataclass. Because it has a default, existing positional `Item(...)` calls keep working. Also in items.py, add `normalize_category`, which trims leading and trailing whitespace and converts to lower case, and returns None when the result is empty or missing. `add_item` gets an optional keyword `category=None` that goes through `normalize_category`. `adjust_stock` uses `dataclasses.replace`, so it already keeps the category, and `remove_item` leaves the other items untouched (AC-8). A new `filter_by_category` keeps only items whose stored category equals the normalised filter. If the filter is None, empty or only whitespace, it returns every item, which is the spec's proposed default for the open question. In inventory/store.py (persistence): `save_items` already writes `item.__dict__`, so the category is saved automatically, with no category written as JSON null. `load_items` reads `record.get("category")`, so a missing key or null both mean no category. Any value that is not a string or null raises the existing ValueError for an invalid item; nothing is silently converted. In inventory/cli.py (interface): `add` and `list` each get a `--category` option. `add` passes the value to `add_item`. `list` applies `filter_by_category` before `format_table`. `format_table` gets a CATEGORY column, left blank for items with no category. Sorting still uses `sorted_items`, the header always prints, and `list` returns 0 without saving (AC-5, AC-6, AC-7). There are no UI markup or stylesheet files, so there is no markup or styling task. Existing CLI tests that check the `list` output will need updating by the QA Engineer.

## Tasks

### T1 Add optional category to the item model with normalisation and filtering rules
- Modify: `inventory/items.py`
- Provides: `normalize_category`, `filter_by_category`
- Acceptance criteria: AC-1, AC-2, AC-6, AC-8
- Validation: unit-tests, compile

### T2 Persist and load the item category, treating missing or null as no category, at format version 1
- Depends on: T1
- Modify: `inventory/store.py`
- Acceptance criteria: AC-3, AC-4, AC-8
- Validation: unit-tests, compile

### T3 Connect --category to add and list, and show a category column in the list table
- Depends on: T1, T2
- Modify: `inventory/cli.py`
- Acceptance criteria: AC-1, AC-2, AC-5, AC-6, AC-7
- Validation: unit-tests, compile

## Test plan

| Case | Task | Criterion | Test | Expected | File |
|---|---|---|---|---|---|
| TC-1 | T1 | AC-1 | Given an empty list, when add_item([], "AB-1", "Bolt", 5, "2026-01-01T00:00:00+00:00", category="  Tools ") is called, then the new item's category is normalised. | The returned list is [Item("AB-1", "Bolt", 5, T0, T0, category="tools")], so the stored category is "tools". | `tests/test_items.py` |
| TC-2 | T1 | AC-1 | Given the inputs "  Tools ", "TOOLS" and "Hand Tools", when normalize_category is called on each, then each is trimmed and lower-cased and inner whitespace is kept. | normalize_category returns "tools", "tools" and "hand tools" for the three inputs. | `tests/test_items.py` |
| TC-3 | T3 | AC-1 | Given an empty inventory file in a temporary directory, when main(["--file", path, "add", "AB-1", "Bolt", "--category", "  Tools "]) runs and the file is loaded with load_items, then the item has the normalised category. | main returns 0 and load_items(path)[0].category == "tools". | `tests/test_store_cli.py` |
| TC-4 | T1 | AC-2 | Given an empty list and T0 = "2026-01-01T00:00:00+00:00", when add_item is called for "AB-1" "Bolt" 5 with no category, with category="", and with category="   ", then none of the calls raises an error. | The item from each call has category None, and normalize_category(""), normalize_category("   ") and normalize_category(None) all return None. | `tests/test_items.py` |
| TC-5 | T3 | AC-2 | Given an empty inventory file, when main adds "AB-1" with no --category, "AB-2" with --category "" and "AB-3" with --category "   ", and the file is loaded, then no item has a category. | All three main calls return 0 and every loaded item has category None. | `tests/test_store_cli.py` |
| TC-6 | T2 | AC-3 | Given items built with add_item, AB-1 "Bolt" with category "tools" and AB-2 "Nut" with no category, both at T0 = "2026-01-01T00:00:00+00:00", when save_items(path, items) is followed by load_items(path), then the categories survive the round trip. | load_items returns a list equal to the saved items, with AB-1 category "tools" and AB-2 category None. | `tests/test_store_cli.py` |
| TC-7 | T2 | AC-3 | Given an item AB-1 with category "tools" saved with save_items, when the raw JSON file is read, then the category is written to the file. | The JSON record for AB-1 has "category": "tools". | `tests/test_store_cli.py` |
| TC-8 | T2 | AC-4 | Given a file written as {"version": 1, "items": [{"sku": "AB-1", "name": "Bolt", "quantity": 5, "created_at": "2026-01-01T00:00:00+00:00", "updated_at": "2026-01-02T00:00:00+00:00"}]} with no category key, when load_items(path) is called, then it loads without error. | load_items returns one item with sku "AB-1", name "Bolt", quantity 5, created_at T0, updated_at "2026-01-02T00:00:00+00:00", and category None. | `tests/test_store_cli.py` |
| TC-9 | T2 | AC-4 | Regression guard: given the same version 1 file with no category key, when load_items(path) is called, then the existing fields are read unchanged. (expected pass) | load_items does not raise, and (sku, name, quantity, created_at, updated_at) of the loaded item equal ("AB-1", "Bolt", 5, "2026-01-01T00:00:00+00:00", "2026-01-02T00:00:00+00:00"). | `tests/test_store_cli.py` |
| TC-10 | T2 | AC-4 | Given a version 1 file whose single AB-1 record has "category": 7, when load_items(path) is called, then the wrong type is rejected and not converted. | load_items raises ValueError with a message matching "invalid item". | `tests/test_store_cli.py` |
| TC-11 | T3 | AC-5 | Given an inventory file holding AB-1 "Bolt" qty 5 category "tools" and AA-2 "Nut" qty 1 with no category, when main(["--file", path, "list"], out=io.StringIO()) runs, then the table has a category column. | main returns 0, the header line contains SKU, QTY, NAME and CATEGORY, the AA-2 row comes before the AB-1 row, the AB-1 row contains "tools", and the AA-2 row's split() is exactly ["AA-2", "1", "Nut"]. | `tests/test_store_cli.py` |
| TC-12 | T3 | AC-5 | Given items AB-1 with category "tools" and AA-2 with no category, when format_table(items) is called, then each item has a row in SKU order with the category shown or left blank. | format_table returns 3 lines: a header containing "CATEGORY", then the AA-2 row with no category text, then the AB-1 row containing "tools". | `tests/test_store_cli.py` |
| TC-13 | T1 | AC-6 | Given items AB-1 with category "tools", AA-3 with category "tools", CC-1 with category "paint" and DD-1 with no category, when filter_by_category(items, "TOOLS") and filter_by_category(items, " tools ") are called, then only the tools items are kept. | Both calls return only the items with SKUs AB-1 and AA-3. | `tests/test_items.py` |
| TC-14 | T1 | AC-6 | Given the same four items, when filter_by_category(items, None), filter_by_category(items, "") and filter_by_category(items, "   ") are called, then no filter is applied (the spec's proposed default). | Each call returns all four items. | `tests/test_items.py` |
| TC-15 | T3 | AC-6 | Given an inventory file holding AB-1 "Bolt" (tools), AA-3 "Saw" (tools), CC-1 "Red" (paint) and DD-1 "Tape" (no category), when main(["--file", path, "list", "--category", " TOOLS "], out=buf) runs, then only the tools items are listed under the header. | main returns 0, the output is the header line followed by the AA-3 row and then the AB-1 row, and CC-1 and DD-1 do not appear. | `tests/test_store_cli.py` |
| TC-16 | T3 | AC-7 | Given an inventory file holding AB-1 with category "tools", when the file bytes are recorded and main(["--file", path, "list", "--category", "garden"], out=buf) runs, then only the header is printed and the file is not touched. | main returns 0, the output has exactly one non-empty line, the header containing "CATEGORY", and the file bytes are unchanged. | `tests/test_store_cli.py` |
| TC-17 | T1 | AC-8 | Given items AB-1 with category "tools" and AA-2 with no category, added at T0 = "2026-01-01T00:00:00+00:00", when adjust_stock(items, "AB-1", -2, T1) and adjust_stock(items, "AA-2", 3, T1) are called with T1 = "2026-01-02T00:00:00+00:00", then each item's category stays the same. | After adjusting, AB-1 has category "tools" and quantity 3, and AA-2 has category None and quantity 4. | `tests/test_items.py` |
| TC-18 | T1 | AC-8 | Given items AB-1 with category "tools", AA-2 with no category and CC-1 with category "paint", when remove_item(items, "CC-1") is called, then the remaining items keep their categories. | The result has AB-1 with category "tools" and AA-2 with category None. | `tests/test_items.py` |
| TC-19 | T2 | AC-8 | Given a version 1 file written directly as JSON with AB-1 (quantity 5, "category": "tools") and AA-2 (quantity 1, "category": null), when main runs adjust AB-1 -2, then adjust AA-2 1, then remove a third item CC-1, and the file is loaded, then the categories persist. | Every main call returns 0, and load_items gives AB-1 quantity 3 with category "tools" and AA-2 quantity 2 with category None. | `tests/test_store_cli.py` |

## Grounding check: pass
