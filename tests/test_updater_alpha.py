import unittest
from unittest.mock import patch, MagicMock
import json
import os
from wakfu_task_bar.updater import VERSION, version_parts, check_latest

class UpdateChannelTests(unittest.TestCase):
    def test_prerelease_order(self):
        self.assertEqual(VERSION, os.getenv("WAKFU_RELEASE_VERSION", "0.3.0-alpha").removeprefix("v"))
        self.assertLess(version_parts("v0.3.0-alpha"), version_parts("v0.3.0"))
        self.assertLess(version_parts("v0.3.0-alpha"), version_parts("v0.3.0-beta"))
        self.assertGreater(version_parts("v0.3.0-alpha"), version_parts("v0.2.2"))
        with self.assertRaises(ValueError):
            version_parts("v0.3.0-malicious")

    @patch("wakfu_task_bar.updater.platform.system",return_value="Darwin")
    @patch("wakfu_task_bar.updater.urllib.request.urlopen")
    def test_experimental_can_find_prerelease(self, urlopen, _system):
        releases = [
            {"tag_name":"v0.2.2","prerelease":False,"draft":False,"assets":[]},
            {"tag_name":"v0.3.0-alpha","prerelease":True,"draft":False,
             "assets":[{"name":"Wakfu-Task-Bar-Game-macOS-Intel.zip"}]},
            {"tag_name":"v0.4.0-alpha","prerelease":True,"draft":True,"assets":[]}
        ]
        response = MagicMock()
        response.read.return_value = json.dumps(releases).encode()
        urlopen.return_value.__enter__.return_value = response
        found = check_latest("experimental")
        self.assertEqual(found["tag"],"v0.3.0-alpha")
        self.assertEqual(found["newer"], version_parts(found["tag"]) > version_parts(VERSION))
        self.assertIsNotNone(found["asset"])

    def test_invalid_channel(self):
        with self.assertRaises(ValueError):
            check_latest("untrusted")
