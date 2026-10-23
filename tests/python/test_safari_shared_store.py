"""Run the real native report persistence boundary when Swift is available."""
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


@unittest.skipUnless(shutil.which('swiftc'), 'Swift compiler unavailable')
class SharedStoreTests(unittest.TestCase):
    def test_hidden_report_accepts_model_json_nulls(self):
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            main = folder / 'main.swift'
            main.write_text('''import Foundation
let suite = "tibia-tests-" + UUID().uuidString
let defaults = UserDefaults(suiteName: suite)!
defer { defaults.removePersistentDomain(forName: suite) }
let stream: [String: Any] = ["channel": "fixture", "title": "Full title", "reason": "99% private server", "game": "Private servers",
    "references": [["origin": NSNull()]], "raw_logit": NSNull()]
_ = SharedStore.handle(["type": "hidden", "url": "https://www.twitch.tv/directory/category/tibia", "onDirectory": true,
    "mode": "bottom", "hidden": [stream]], defaults: defaults)
let report = defaults.dictionary(forKey: SharedStore.Key.hidden)!
let rows = report["hidden"] as! [[String: String]]
precondition(rows.count == 1 && rows[0]["channel"] == "fixture")
precondition(rows[0]["title"] == "Full title" && rows[0].count == 4)
precondition(report["mode"] as? String == "bottom")
MainActor.assumeIsolated {
    defaults.set(["tibiaMode": "bottom", "tibiaThreshold": 0.5], forKey: SharedStore.Key.settings)
    let model = SettingsModel(defaults: defaults)
    let url = URL(string: "https://www.twitch.tv/directory/category/tibia")!
    model.reload(pageURL: url)
    model.requestExport()
    precondition(defaults.string(forKey: SharedStore.Key.exportURL) == url.absoluteString)
    precondition(model.mode == "bottom" && model.threshold == 0.5 && model.hidden.count == 1)
    model.setMode("show")
    model.reload(pageURL: url)
    precondition(model.hidden.isEmpty)
    model.setMode("bottom")
    model.setShown("fixture", title: "An earlier title")
    model.reload(pageURL: url)
    precondition(model.hidden.count == 1, "Old broadcast overrides must not hide the current affected stream from the list")
    model.setShown("fixture", title: "Full title")
    model.reload(pageURL: url)
    precondition(model.hidden.isEmpty)
}
print("PASS native moved-stream report persists despite JSON nulls")
''')
            executable = folder / 'check'
            result = subprocess.run(['swiftc', '-module-cache-path', str(folder / 'cache'),
                str(ROOT / 'extension/browsers/safari/Shared/SharedStore.swift'),
                str(ROOT / 'extension/browsers/safari/Toolbar/SettingsModel.swift'), str(main), '-o', str(executable)],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            result = subprocess.run([str(executable)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr[-1500:])
