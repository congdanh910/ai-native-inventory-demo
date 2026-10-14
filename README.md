# Inventory demo

A small stock-keeping CLI (Python 3.12, standard library only). It is the second pilot project of the AI-native SDLC POC: the platform onboards it with `AGENTS.md` and `.sdlc/project.yaml` only.

```bash
python -m inventory.cli --file stock.json add bolt-1 "Hex bolt" --quantity 10
python -m inventory.cli --file stock.json adjust BOLT-1 -3
python -m inventory.cli --file stock.json list
python -m unittest discover -s tests -t .
```
