#!/usr/bin/env python3
"""Compare compiled SDK interfaces with artifacts from the contracts source."""
import argparse
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def parameter_type(parameter):
    ty = parameter["type"]
    if ty.startswith("tuple"):
        return "(" + ",".join(parameter_type(component) for component in parameter["components"]) + ")" + ty[5:]
    return ty


def normalize(abi):
    entries = []
    for item in abi:
        kind = item["type"]
        if kind == "constructor":
            continue
        entry = {"type": kind, "name": item.get("name", ""), "inputs": [parameter_type(p) for p in item.get("inputs", [])]}
        if kind in ("function", "fallback", "receive"):
            entry["stateMutability"] = item["stateMutability"]
            entry["outputs"] = [parameter_type(p) for p in item.get("outputs", [])]
        if kind == "event":
            entry["anonymous"] = item.get("anonymous", False)
            entry["indexed"] = [p.get("indexed", False) for p in item["inputs"]]
        entries.append(json.dumps(entry, sort_keys=True))
    return sorted(entries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=ROOT / "out", help="Foundry compiled artifacts")
    contracts = Path(os.environ.get("DIESIS_CONTRACTS_DIR", ROOT / "../../diesis-core/diesis/contracts")).resolve()
    parser.add_argument("--artifacts", type=Path, default=contracts / "out", help="compiled artifacts from the contracts source checkout")
    args = parser.parse_args()
    config = json.loads((ROOT / "generation.json").read_text())
    problems = []
    count = 0
    for name in config["contracts"]:
        interface = name if name.startswith("I") and name[1].isupper() else "I" + name
        matches = sorted(args.artifacts.rglob(f"{name}.json"))
        if len(matches) != 1:
            problems.append(f"expected one source artifact for {name}; found {len(matches)}")
            continue
        source = json.loads(matches[0].read_text())["abi"]
        path = args.out / f"{interface}.sol/{interface}.json"
        if not path.exists():
            problems.append(f"missing compiled interface: {path}")
            continue
        compiled = json.loads(path.read_text())["abi"]
        expected, actual = normalize(source), normalize(compiled)
        if expected != actual:
            problems.append(f"ABI mismatch: {name}\nmissing: {sorted(set(expected) - set(actual))}\nextra: {sorted(set(actual) - set(expected))}")
        count += len(expected)
    if problems:
        parser.exit(1, "\n".join(problems) + "\n")
    print(f"ABI parity: {len(config['contracts'])} interfaces, {count} entries")


if __name__ == "__main__":
    main()
