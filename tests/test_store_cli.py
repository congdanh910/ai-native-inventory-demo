import io
import json
from pathlib import Path
import tempfile
import unittest

from inventory.cli import main
from inventory.items import add_item
from inventory.store import load_items, save_items

T0 = "2026-01-01T00:00:00+00:00"


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
