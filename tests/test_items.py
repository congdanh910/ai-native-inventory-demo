import unittest

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


if __name__ == "__main__":
    unittest.main()
