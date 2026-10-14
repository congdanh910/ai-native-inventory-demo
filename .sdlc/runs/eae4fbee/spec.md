# Spec: Categories

## Goal

Let a store keeper give each item an optional category, see it in the item list, and list only the items in one category. Inventory files saved before this feature must keep loading.

## User stories

- As a store keeper, I want to give an item a category when I add it so that my stock is grouped.
- As a store keeper, I want to list only the items in one category, without caring about upper or lower case, so that I can review one group at a time.
- As a store keeper, I want the item list to show each item's category so that I can see how my stock is grouped.
- As a store keeper, I want my existing inventory file to keep working after this change so that I do not lose or have to re-enter my data.

## Acceptance criteria

- AC-1: `add SKU NAME --category VALUE` saves the item with VALUE trimmed of leading and trailing whitespace and converted to lower case. For example, `--category '  Tools '` is stored as `tools`.
- AC-2: An item added without `--category`, or with a category that is empty or only whitespace (for example `--category ''` or `--category '   '`), is saved with no category. This is not an error.
- AC-3: The item's category is written to the inventory file and is the same after the file is loaded again. An item with no category still has no category after a save and reload.
- AC-4: An inventory file saved before this feature, whose items have no category field and which has the existing format version, loads without error. Every item has no category, and all other fields (SKU, name, quantity, created_at, updated_at) are unchanged.
- AC-5: `list` shows a category column for every item, next to the existing SKU, QTY and NAME columns. Items keep the existing sort order by SKU. The column is blank for items with no category.
- AC-6: `list --category NAME` shows only items whose category matches NAME, ignoring case and leading or trailing whitespace. For example, `--category TOOLS` and `--category ' tools '` both show items stored as `tools`. Items in other categories and items with no category are not shown. Items keep the sort order by SKU, and the header is still printed.
- AC-7: `list --category NAME` for a category that no item has prints only the table header. It exits with status 0 and does not change the inventory file.
- AC-8: Other commands (`adjust`, `remove`) keep an item's category unchanged, including when the item has no category.

## Assumptions

- The Product Owner gave no answers. All the decisions below are the analyst's assumptions.
- Items with no category show a blank cell in the category column, not a placeholder such as '-' or 'none'.
- When `list --category` finds no matching items, it prints only the header and exits successfully (status 0). It does not report an error.
- Only leading and trailing whitespace is removed from a category. Whitespace inside it is kept, and the intent sets no other character or length rules.
- A category can only be set when an item is added. The intent does not ask for a way to change or clear the category of an existing item.
- The intent does not say what `list --category ''` (empty or whitespace only) should do. The proposed default is to treat it like `list` with no filter and show all items; this is confirmed or overridden through the non-blocking question.

## Concerns

- `store.load_items` rejects any file whose `version` is not `FORMAT_VERSION` (currently 1). If the Tech Lead raises the format version for the new field, files saved before this feature (version 1) must still load (AGENTS.md and AC-4). Otherwise, keep version 1 and treat a missing category as no category.
- Per AGENTS.md, the category rules (trimming, lower case, empty means none, case-insensitive matching) belong in `inventory/items.py` as pure functions. `cli.py` should only wire `--category` to them. `add_item` will need a new optional parameter; existing callers and tests must keep working.
- `store.save_items` writes `item.__dict__`, so a new `Item` field will be saved automatically. When loading, the Tech Lead should decide how no category is stored (missing key, null or empty string) and how a category of the wrong type (for example a number) is rejected with a `ValueError`, following the 'never silently convert' convention.
- Adding a category column changes the `list` output that existing CLI tests may check. Those tests will need updating.
- AGENTS.md requires `ValueError` for invalid input, but the intent sets no rules that would make a category invalid. No validation error is specified beyond the normalisation in AC-1 and AC-2.

## Open questions

- What should `list --category ''` (empty or only whitespace) show: all items (proposed default), only items with no category, or an error?
- Should store keepers be able to set, change or clear the category of an existing item, or is setting it at `add` enough for this feature?
