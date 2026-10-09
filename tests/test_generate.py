import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("generate", ROOT / "scripts/generate.py")
generate = None
if (ROOT / "scripts/generate.py").exists():
    generate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(generate)


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(generate, "standalone SDK generator is missing")

    def test_constants_preserve_all_canonical_addresses_and_chains(self):
        canonical = json.loads((ROOT / "canonical.json").read_text())
        files = generate.render_constants(canonical)
        for name, address in canonical["addresses"].items():
            self.assertIn(f"address internal constant {name} = address(bytes20(hex\"{address[2:]}\"));", files["src/DiesisAddresses.sol"])
        for name, chain in canonical["chains"].items():
            self.assertIn(f"uint256 internal constant {name.upper()} = {chain['id']};", files["src/DiesisChains.sol"])

    def test_malformed_addresses_are_rejected(self):
        canonical = json.loads((ROOT / "canonical.json").read_text())
        canonical["addresses"]["WRAPPED_DS"] = "0x1234"
        with self.assertRaisesRegex(ValueError, "WRAPPED_DS"):
            generate.render_constants(canonical)

    def test_check_reports_missing_changed_and_stale_files_without_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "src/interfaces").mkdir(parents=True)
            (root / "src/interfaces/Old.sol").write_text("old")
            (root / "src/DiesisChains.sol").write_text("changed")
            expected = {"src/interfaces/IExample.sol": "new", "src/DiesisChains.sol": "chains"}
            before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
            problems = generate.sync_files(root, expected, check=True)
            self.assertIn("missing: src/interfaces/IExample.sol", problems)
            self.assertIn("out of date: src/DiesisChains.sol", problems)
            self.assertIn("stale: src/interfaces/Old.sol", problems)
            self.assertEqual(before, {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()})
            generate.sync_files(root, expected, check=False)
            self.assertEqual([], generate.sync_files(root, expected, check=True))
            self.assertFalse((root / "src/interfaces/Old.sol").exists())

    def test_interface_names_do_not_double_prefix(self):
        self.assertEqual("IDiesisStaking", generate.interface_name("DiesisStaking"))
        self.assertEqual("IWrappedDS", generate.interface_name("IWrappedDS"))

    def test_wrong_generator_version_is_rejected_before_reading_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "typegen"
            binary.write_text("#!/usr/bin/env python3\nprint('abi-typegen 0.7.0')\n")
            binary.chmod(0o755)
            with self.assertRaisesRegex(ValueError, "0.8.0 is required"):
                generate.expected_files(Path(directory), ROOT / "canonical.json", str(binary))

    def test_missing_source_artifacts_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            binary = Path(directory) / "typegen"
            binary.write_text("#!/usr/bin/env python3\nprint('abi-typegen 0.8.0')\n")
            binary.chmod(0o755)
            with self.assertRaisesRegex(ValueError, "expected one artifact for IDiesisMarkets.*found 0"):
                generate.expected_files(Path(directory), ROOT / "canonical.json", str(binary))


if __name__ == "__main__":
    unittest.main()
