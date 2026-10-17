"""Packaged object inventories and cabin scene configuration."""
import gzip
import hashlib
import json
from importlib.resources import files


def object_inventory(object_set="core20"):
    data = files("astrobench").joinpath("data")
    registry = json.loads(data.joinpath("object_sets.json").read_text(encoding="utf-8"))
    if object_set not in registry["sets"]:
        raise ValueError("Unknown object set: " + object_set)
    spec = registry["sets"][object_set]
    raw = data.joinpath(spec["manifest"]).read_bytes()
    if spec["format"] == "jsonl.gz":
        raw = gzip.decompress(raw)
    if hashlib.sha256(raw).hexdigest() != spec["sha256"]:
        raise ValueError("Object inventory hash mismatch")
    rows = ([json.loads(line) for line in raw.decode("utf-8").splitlines() if line.strip()]
            if spec["format"].startswith("jsonl") else json.loads(raw))
    if len(rows) != spec["object_count"] or len({r["object_id"] for r in rows}) != len(rows):
        raise ValueError("Object inventory count/identity mismatch")
    return {"schema": "astrobench.object_selection/v1", "object_set": object_set,
            "object_count": len(rows), "inventory_sha256": spec["sha256"],
            "status": spec["status"], "objects": rows}


def scene_catalog():
    return json.loads(files("astrobench").joinpath("data/scenes.json").read_text(encoding="utf-8"))


def select_catalog(catalog, object_set="core20"):
    if object_set == "custom":
        return catalog
    required = [row["object_id"] for row in object_inventory(object_set)["objects"]]
    by_id = {row["object_id"]: row for row in catalog}
    if len(by_id) != len(catalog):
        raise ValueError("Duplicate object_id in catalog")
    missing = set(required) - set(by_id)
    if missing:
        raise ValueError(f"Missing {len(missing)} catalog entries; first: {sorted(missing)[0]}")
    return [by_id[key] for key in required]
