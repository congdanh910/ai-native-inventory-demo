import unittest

from inventory import items as item_rules
from inventory.items import Item, add_item, adjust_stock, normalize_sku, remove_item, sorted_items

T0 = "2026-01-01T00:00:00+00:00"
T1 = "2026-01-02T00:00:00+00:00"


def one_item():
    return add_item([], " ab-1 ", " Bolt ", 5, T0)


class ItemTests(unittest.TestCase):
    def test_add_normalizes_and_stamps(self):
        self.assertEqual(one_item(), [Item("AB-1", "Bolt", 5, T0, T0)])

    def test_add_rejects_bad_input(self):
        with self.assertRaisesRegex(ValueError, "Invalid SKU"):
            add_item([], "a b", "Bolt", 1, T0)
        with self.assertRaisesRegex(ValueError, "Name is required"):
            add_item([], "AB-1", "  ", 1, T0)
        with self.assertRaisesRegex(ValueError, "at least 0"):
            add_item([], "AB-1", "Bolt", -1, T0)
        with self.assertRaisesRegex(ValueError, "already exists"):
            add_item(one_item(), "ab-1", "Nut", 1, T0)

    def test_adjust_stock(self):
        items = adjust_stock(one_item(), "AB-1", -2, T1)
        self.assertEqual((items[0].quantity, items[0].updated_at), (3, T1))
        with self.assertRaisesRegex(ValueError, "Not enough stock"):
            adjust_stock(items, "AB-1", -4, T1)
        with self.assertRaisesRegex(ValueError, "Unknown SKU"):
            adjust_stock(items, "ZZ-9", 1, T1)
        with self.assertRaisesRegex(ValueError, "non-zero"):
            adjust_stock(items, "AB-1", 0, T1)

    def test_remove_and_sort(self):
        items = add_item(one_item(), "AA-2", "Nut", 1, T0)
        self.assertEqual([i.sku for i in sorted_items(items)], ["AA-2", "AB-1"])
        self.assertEqual([i.sku for i in remove_item(items, "ab-1")], ["AA-2"])

    def test_normalize_sku(self):
        self.assertEqual(normalize_sku("x9-y"), "X9-Y")

    def test_tc_1_add_normalizes_category(self):
        result = add_item([], "AB-1", "Bolt", 5, T0, category="  Tools ")
        self.assertEqual(result, [Item("AB-1", "Bolt", 5, T0, T0, category="tools")])

    def test_tc_2_normalize_category_preserves_inner_whitespace(self):
        for value, expected in (
            ("  Tools ", "tools"),
            ("TOOLS", "tools"),
            ("Hand Tools", "hand tools"),
        ):
            with self.subTest(value=value):
                self.assertEqual(item_rules.normalize_category(value), expected)

    def test_tc_4_missing_or_blank_category_is_none(self):
        for value in (None, "", "   "):
            with self.subTest(category=value):
                if value is None:
                    result = add_item([], "AB-1", "Bolt", 5, T0)
                else:
                    result = add_item([], "AB-1", "Bolt", 5, T0, category=value)
                self.assertIsNone(result[0].category)
                self.assertIsNone(item_rules.normalize_category(value))

    def test_tc_13_filter_category_ignores_case_and_outer_whitespace(self):
        records = [
            Item("AB-1", "Bolt", 5, T0, T0, category="tools"),
            Item("AA-3", "Awl", 2, T0, T0, category="tools"),
            Item("CC-1", "Brush", 1, T0, T0, category="paint"),
            Item("DD-1", "Unsorted", 1, T0, T0),
        ]
        for category in ("TOOLS", " tools "):
            with self.subTest(category=category):
                self.assertCountEqual(
                    item_rules.filter_by_category(records, category), records[:2]
                )

    def test_tc_14_blank_category_filter_keeps_all_items(self):
        records = [
            Item("AB-1", "Bolt", 5, T0, T0, category="tools"),
            Item("AA-3", "Awl", 2, T0, T0, category="tools"),
            Item("CC-1", "Brush", 1, T0, T0, category="paint"),
            Item("DD-1", "Unsorted", 1, T0, T0),
        ]
        for category in (None, "", "   "):
            with self.subTest(category=category):
                self.assertEqual(item_rules.filter_by_category(records, category), records)

    def test_tc_17_adjust_stock_preserves_categories(self):
        records = add_item([], "AB-1", "Bolt", 5, T0, category="tools")
        records = add_item(records, "AA-2", "Nut", 1, T0)

        records = adjust_stock(records, "AB-1", -2, T1)
        records = adjust_stock(records, "AA-2", 3, T1)

        by_sku = {item.sku: item for item in records}
        self.assertEqual((by_sku["AB-1"].quantity, by_sku["AB-1"].category), (3, "tools"))
        self.assertEqual((by_sku["AA-2"].quantity, by_sku["AA-2"].category), (4, None))

    def test_tc_18_remove_preserves_remaining_categories(self):
        records = add_item([], "AB-1", "Bolt", 5, T0, category="tools")
        records = add_item(records, "AA-2", "Nut", 1, T0)
        records = add_item(records, "CC-1", "Brush", 1, T0, category="paint")

        remaining = remove_item(records, "CC-1")

        self.assertEqual(
            [(item.sku, item.category) for item in remaining],
            [("AB-1", "tools"), ("AA-2", None)],
        )


if __name__ == "__main__":
    unittest.main()
