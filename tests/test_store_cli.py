import io
import json
from pathlib import Path
import tempfile
import unittest

from inventory.cli import main
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


if __name__ == "__main__":
    unittest.main()
