import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from inventory.cli import format_table, main
from inventory.items import add_item
from inventory.store import load_items, save_items

T0 = "2026-01-01T00:00:00+00:00"
T1 = "2026-01-02T00:00:00+00:00"


class StoreTests(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = Path(self.dir.name) / "inventory.json"

    def tearDown(self):
        self.dir.cleanup()

    def test_missing_file_is_empty(self):
        self.assertEqual(load_items(self.path), [])

    def test_round_trip(self):
        items = add_item([], "AB-1", "Bolt", 5, T0)
        save_items(self.path, items)
        self.assertEqual(load_items(self.path), items)

    def test_category_round_trip(self):  # TC-6
        items = add_item([], "AB-1", "Bolt", 5, T0, category="tools")
        items = add_item(items, "AB-2", "Nut", 1, T0)

        save_items(self.path, items)

        loaded = load_items(self.path)
        self.assertEqual(loaded, items)
        self.assertEqual([item.category for item in loaded], ["tools", None])

    def test_save_writes_category_to_json(self):  # TC-7
        items = add_item([], "AB-1", "Bolt", 5, T0, category="tools")

        save_items(self.path, items)

        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(data["items"][0]["category"], "tools")

    def test_load_version_one_item_without_category(self):  # TC-8
        self.path.write_text(json.dumps({"version": 1, "items": [{
            "sku": "AB-1", "name": "Bolt", "quantity": 5,
            "created_at": T0, "updated_at": T1,
        }]}), encoding="utf-8")

        loaded = load_items(self.path)

        self.assertEqual(len(loaded), 1)
        item = loaded[0]
        self.assertEqual(item.sku, "AB-1")
        self.assertEqual(item.name, "Bolt")
        self.assertEqual(item.quantity, 5)
        self.assertEqual(item.created_at, T0)
        self.assertEqual(item.updated_at, T1)
        self.assertIsNone(item.category)

    def test_load_version_one_preserves_existing_fields(self):  # TC-9
        self.path.write_text(json.dumps({"version": 1, "items": [{
            "sku": "AB-1", "name": "Bolt", "quantity": 5,
            "created_at": T0, "updated_at": T1,
        }]}), encoding="utf-8")

        item, = load_items(self.path)

        self.assertEqual(
            (item.sku, item.name, item.quantity, item.created_at, item.updated_at),
            ("AB-1", "Bolt", 5, T0, T1),
        )

    def test_load_rejects_invalid_category_type(self):  # TC-10
        self.path.write_text(json.dumps({"version": 1, "items": [{
            "sku": "AB-1", "name": "Bolt", "quantity": 5,
            "created_at": T0, "updated_at": T1, "category": 7,
        }]}), encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "invalid item"):
            load_items(self.path)

    def test_adjust_and_remove_preserve_categories(self):  # TC-19
        self.path.write_text(json.dumps({"version": 1, "items": [
            {"sku": "AB-1", "name": "Bolt", "quantity": 5,
             "created_at": T0, "updated_at": T0, "category": "tools"},
            {"sku": "AA-2", "name": "Nut", "quantity": 1,
             "created_at": T0, "updated_at": T0, "category": None},
            {"sku": "CC-1", "name": "Washer", "quantity": 4,
             "created_at": T0, "updated_at": T0, "category": "parts"},
        ]}), encoding="utf-8")
        file = ["--file", str(self.path)]

        self.assertEqual(main([*file, "adjust", "AB-1", "-2"], out=io.StringIO()), 0)
        self.assertEqual(main([*file, "adjust", "AA-2", "1"], out=io.StringIO()), 0)
        self.assertEqual(main([*file, "remove", "CC-1"], out=io.StringIO()), 0)

        loaded = {item.sku: item for item in load_items(self.path)}
        self.assertEqual(set(loaded), {"AB-1", "AA-2"})
        self.assertEqual((loaded["AB-1"].quantity, loaded["AB-1"].category), (3, "tools"))
        self.assertEqual((loaded["AA-2"].quantity, loaded["AA-2"].category), (2, None))

    def test_invalid_file_is_reported(self):
        self.path.write_text(json.dumps({"version": 1, "items": [{"sku": "AB-1"}]}))
        with self.assertRaisesRegex(ValueError, "invalid item"):
            load_items(self.path)
        self.path.write_text(json.dumps({"version": 9, "items": []}))
        with self.assertRaisesRegex(ValueError, "version 1"):
            load_items(self.path)

    def test_cli_add_adjust_list(self):
        file = ["--file", str(self.path)]
        self.assertEqual(main([*file, "add", "ab-1", "Bolt", "--quantity", "5"]), 0)
        self.assertEqual(main([*file, "adjust", "AB-1", "-2"]), 0)
        out = io.StringIO()
        self.assertEqual(main([*file, "list"], out=out), 0)
        self.assertIn("AB-1", out.getvalue())
        self.assertIn("     3  Bolt", out.getvalue())
        self.assertEqual(main([*file, "adjust", "AB-1", "-9"]), 1)

    def test_cli_add_normalizes_category(self):  # TC-3
        save_items(self.path, [])

        with patch("inventory.cli.now", return_value=T0):
            result = main(
                ["--file", str(self.path), "add", "AB-1", "Bolt", "--category", "  Tools "],
                out=io.StringIO(),
            )

        self.assertEqual(result, 0)
        self.assertEqual(load_items(self.path)[0].category, "tools")

    def test_cli_add_empty_categories_are_none(self):  # TC-5
        save_items(self.path, [])
        file = ["--file", str(self.path)]

        with patch("inventory.cli.now", return_value=T0):
            results = [
                main([*file, "add", "AB-1", "Bolt"], out=io.StringIO()),
                main([*file, "add", "AB-2", "Nut", "--category", ""], out=io.StringIO()),
                main([*file, "add", "AB-3", "Screw", "--category", "   "], out=io.StringIO()),
            ]

        self.assertEqual(results, [0, 0, 0])
        loaded = load_items(self.path)
        self.assertEqual(len(loaded), 3)
        self.assertTrue(all(item.category is None for item in loaded))

    def test_cli_list_shows_category_column(self):  # TC-11
        items = add_item([], "AB-1", "Bolt", 5, T0, category="tools")
        items = add_item(items, "AA-2", "Nut", 1, T0)
        save_items(self.path, items)
        out = io.StringIO()

        result = main(["--file", str(self.path), "list"], out=out)

        self.assertEqual(result, 0)
        header, first_row, second_row = out.getvalue().splitlines()
        self.assertTrue({"SKU", "QTY", "NAME", "CATEGORY"} <= set(header.split()))
        self.assertEqual(first_row.split(), ["AA-2", "1", "Nut"])
        self.assertEqual(second_row.split()[0], "AB-1")
        self.assertIn("tools", second_row.split())

    def test_format_table_shows_categories_in_sku_order(self):  # TC-12
        items = add_item([], "AB-1", "Bolt", 5, T0, category="tools")
        items = add_item(items, "AA-2", "Nut", 1, T0)

        lines = format_table(items).splitlines()

        self.assertEqual(len(lines), 3)
        self.assertIn("CATEGORY", lines[0].split())
        self.assertEqual(lines[1].split(), ["AA-2", "1", "Nut"])
        self.assertEqual(lines[2].split()[0], "AB-1")
        self.assertIn("tools", lines[2].split())

    def test_cli_list_filters_normalized_category(self):  # TC-15
        items = add_item([], "AB-1", "Bolt", 5, T0, category="tools")
        items = add_item(items, "AA-3", "Saw", 1, T0, category="tools")
        items = add_item(items, "CC-1", "Red", 2, T0, category="paint")
        items = add_item(items, "DD-1", "Tape", 3, T0)
        save_items(self.path, items)
        out = io.StringIO()

        result = main(["--file", str(self.path), "list", "--category", " TOOLS "], out=out)

        self.assertEqual(result, 0)
        lines = out.getvalue().splitlines()
        self.assertEqual(len(lines), 3)
        self.assertIn("CATEGORY", lines[0].split())
        self.assertEqual([line.split()[0] for line in lines[1:]], ["AA-3", "AB-1"])
        self.assertTrue(all("tools" in line.split() for line in lines[1:]))
        self.assertNotIn("CC-1", out.getvalue())
        self.assertNotIn("DD-1", out.getvalue())

    def test_cli_list_unmatched_category_is_header_only_and_read_only(self):  # TC-16
        save_items(self.path, add_item([], "AB-1", "Bolt", 5, T0, category="tools"))
        original_bytes = self.path.read_bytes()
        out = io.StringIO()

        result = main(["--file", str(self.path), "list", "--category", "garden"], out=out)

        self.assertEqual(result, 0)
        lines = out.getvalue().splitlines()
        self.assertEqual(len(lines), 1)
        self.assertIn("CATEGORY", lines[0].split())
        self.assertEqual(self.path.read_bytes(), original_bytes)


if __name__ == "__main__":
    unittest.main()
