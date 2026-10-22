import Cocoa
import SafariServices
import WebKit

private let extensionBundleIdentifier = "com.nesleykent.tibiaantiad.Extension"

// WKUserContentController retains its handlers; avoid retaining the view controller.
private final class WeakMessageHandler: NSObject, WKScriptMessageHandler {
    weak var owner: ViewController?
    init(_ owner: ViewController) { self.owner = owner }
    func userContentController(_ controller: WKUserContentController, didReceive message: WKScriptMessage) {
        owner?.userContentController(controller, didReceive: message)
    }
}

final class ViewController: NSViewController, WKNavigationDelegate, WKScriptMessageHandler {
    @IBOutlet private var webView: WKWebView!

    override func viewDidLoad() {
        super.viewDidLoad()
        webView.navigationDelegate = self
        webView.configuration.userContentController.add(WeakMessageHandler(self), name: "controller")
        guard let resource = Bundle.main.url(forResource: "Main", withExtension: "html"),
              let directory = Bundle.main.resourceURL else { return }
        webView.loadFileURL(resource, allowingReadAccessTo: directory)
    }

    func webView(_ webView: WKWebView, didFinish navigation: WKNavigation!) {
        SFSafariExtensionManager.getStateOfSafariExtension(withIdentifier: extensionBundleIdentifier) { [weak self] state, error in
            DispatchQueue.main.async {
                guard let self else { return }
                if let state, error == nil {
                    self.webView.evaluateJavaScript("show(\(state.isEnabled), true)")
                } else {
                    self.webView.evaluateJavaScript("showStatusError()")
                }
            }
        }
    }

    func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction,
                 decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
        decisionHandler(action.request.url?.isFileURL == true ? .allow : .cancel)
    }

    func userContentController(_ controller: WKUserContentController, didReceive message: WKScriptMessage) {
        guard message.frameInfo.isMainFrame, message.name == "controller",
              message.body as? String == "open-preferences" else { return }
        SFSafariApplication.showPreferencesForExtension(withIdentifier: extensionBundleIdentifier) { [weak self] error in
            DispatchQueue.main.async {
                if let error {
                    guard self != nil else { return }
                    let alert = NSAlert()
                    alert.messageText = "Couldn’t open Safari Settings"
                    alert.informativeText = "Open Safari → Settings → Extensions and select Tibia Anti-Ad.\n\n" + error.localizedDescription
                    alert.runModal()
                } else {
                    NSApplication.shared.terminate(nil)
                }
            }
        }
    }
}
