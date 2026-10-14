# Intent: Categories

## Problem

As a store keeper, I want to group items by category so that I can list one group at a time.

## Desired outcome

- An item may have a category; categories are trimmed and stored in lower case, and an empty category means none.
- `add` accepts `--category`, and `list --category NAME` shows only that category (case-insensitive).
- `list` shows a category column.
- Inventory files saved before this feature load with no category.

## Affected users and systems

_None._

## Constraints

_None._

## Open questions

_None._
