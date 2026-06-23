from __future__ import annotations

import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _load_installer_module():
    module_path = ROOT / "scripts" / "install_codex_plugin.py"
    spec = importlib.util.spec_from_file_location("install_codex_plugin", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {module_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class InstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.installer = _load_installer_module()

    def test_load_or_create_marketplace_creates_personal_shape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "marketplace.json"
            marketplace = self.installer.load_or_create_marketplace(path, "personal")
        self.assertEqual(marketplace["name"], "personal")
        self.assertEqual(marketplace["interface"]["displayName"], "Personal")
        self.assertEqual(marketplace["plugins"], [])

    def test_upsert_marketplace_entry_adds_required_plugin_shape(self) -> None:
        marketplace = {"name": "personal", "interface": {"displayName": "Personal"}, "plugins": []}
        status = self.installer.upsert_marketplace_entry(marketplace)
        self.assertEqual(status, "created")
        self.assertEqual(
            marketplace["plugins"][0],
            {
                "name": "prompt-preflight",
                "source": {"source": "local", "path": "./plugins/prompt-preflight"},
                "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                "category": "Productivity",
            },
        )

    def test_upsert_marketplace_entry_preserves_other_plugins_and_extra_fields(self) -> None:
        marketplace = {
            "name": "team",
            "interface": {"displayName": "Team"},
            "plugins": [
                {"name": "other-plugin", "source": {"source": "local", "path": "./plugins/other"}},
                {
                    "name": "prompt-preflight",
                    "source": {"source": "local", "path": "./old/path"},
                    "policy": {"installation": "NOT_AVAILABLE", "authentication": "ON_USE"},
                    "category": "Other",
                    "notes": "keep me",
                },
            ],
        }
        status = self.installer.upsert_marketplace_entry(marketplace)
        self.assertEqual(status, "updated")
        self.assertEqual(len(marketplace["plugins"]), 2)
        self.assertEqual(marketplace["plugins"][0]["name"], "other-plugin")
        self.assertEqual(marketplace["plugins"][1]["notes"], "keep me")
        self.assertEqual(
            marketplace["plugins"][1]["source"],
            {"source": "local", "path": "./plugins/prompt-preflight"},
        )
        self.assertEqual(
            marketplace["plugins"][1]["policy"],
            {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
        )
        self.assertEqual(marketplace["plugins"][1]["category"], "Productivity")

    def test_destination_clean_requires_prompt_preflight_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "prompt-preflight"
            destination.mkdir()
            self.assertFalse(self.installer.destination_is_safe_to_clean(destination))

    def test_source_plugin_validates_current_repo(self) -> None:
        manifest = self.installer.validate_source_plugin(ROOT)
        self.assertEqual(manifest["name"], "prompt-preflight")

    def test_missing_codex_cli_is_nonfatal_status(self) -> None:
        status = self.installer.run_codex_install(
            "personal",
            codex_bin="definitely_missing_codex_binary_for_test",
            reinstall=True,
            dry_run=False,
        )
        self.assertEqual(status, "cli-unavailable")

    def test_codex_plugin_deeplink_includes_encoded_marketplace_path(self) -> None:
        marketplace_path = Path("/tmp/my marketplace/marketplace.json")
        link = self.installer.codex_plugin_deeplink(marketplace_path)
        expected_path = str(marketplace_path.resolve()).replace("/", "%2F").replace(" ", "%20")
        self.assertEqual(
            link,
            f"codex://plugins/prompt-preflight?marketplacePath={expected_path}",
        )


if __name__ == "__main__":
    unittest.main()
