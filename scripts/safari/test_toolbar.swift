// Optional native integration check. Requires macOS 15.4+ / the WebKit SDK.
// swiftc -parse-as-library scripts/safari/test_toolbar.swift -o /tmp/tibia-toolbar-test
// /tmp/tibia-toolbar-test
import AppKit
import WebKit

private final class TestBrowser: NSObject, WKWebExtensionControllerDelegate {
    func webExtensionController(_ controller: WKWebExtensionController,
                                openWindowsFor context: WKWebExtensionContext) -> [any WKWebExtensionWindow] { [] }
}

@main struct ToolbarCheck {
    @MainActor static func main() {
        let app = NSApplication.shared
        Task { @MainActor in
            do { try await check(); exit(0) }
            catch { print("FAIL native toolbar check: \(error)"); exit(1) }
        }
        app.run()
    }

    @MainActor static func check() async throws {
        let root = URL(fileURLWithPath: CommandLine.arguments.dropFirst().first ?? FileManager.default.currentDirectoryPath)
        let directory = root.appendingPathComponent("local/verification/toolbar")
        try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
        let ext = try await WKWebExtension(resourceBaseURL: root.appendingPathComponent("extension/src"))
        precondition(ext.errors.isEmpty, "WebKit manifest errors: \(ext.errors)")
        let controller = WKWebExtensionController(configuration: .nonPersistent())
        let testBrowser = TestBrowser()
        controller.delegate = testBrowser
        WKWebExtension.MatchPattern.registerCustomURLScheme("safari-web-extension")
        let context = WKWebExtensionContext(for: ext)
        context.baseURL = URL(string: "safari-web-extension://toolbar-test/")!
        for permission in ext.requestedPermissions {
            context.setPermissionStatus(.grantedExplicitly, for: permission)
        }
        try controller.load(context)
        defer { try? controller.unload(context) }
        let view = WKWebView(frame: CGRect(x: 0, y: 0, width: 400, height: 700),
                             configuration: context.webViewConfiguration!)
        let window = NSWindow(contentRect: view.bounds, styleMask: [.titled], backing: .buffered, defer: false)
        window.title = "Tibia Anti-Ad — UI verification"
        window.contentView = view
        window.orderFrontRegardless()
        defer { window.close() }
        view.load(URLRequest(url: context.baseURL.appendingPathComponent("popup.html")))
        for _ in 0..<100 {
            if view.url != nil && !view.isLoading { break }
            try await Task.sleep(for: .milliseconds(100))
        }
        var images = [Bool: Data]()
        for enabled in [false, true, false, true] {
            _ = try await view.callAsyncJavaScript(
                "await browser.storage.local.set({enabled: enabled}); return true",
                arguments: ["enabled": enabled], in: nil, contentWorld: .page)
            let title = "Tibia Anti-Ad — Blocking \(enabled ? "enabled" : "disabled")"
            for _ in 0..<100 {
                if context.action(for: nil)?.label == title { break }
                try await Task.sleep(for: .milliseconds(50))
            }
            // Image decoding is asynchronous after the title update.
            try await Task.sleep(for: .milliseconds(300))
            let action = context.action(for: nil)!
            precondition(action.label == title, "Action title did not update")
            let source = try await view.evaluateJavaScript("document.getElementById('blocking-status-icon').getAttribute('src')") as! String
            precondition(source == "icons/safari-toolbar/\(enabled ? "active" : "inactive")-64.png")
            let image = action.icon(for: CGSize(width: 19, height: 19))!
            let png = NSBitmapImageRep(data: image.tiffRepresentation!)!
                .representation(using: .png, properties: [:])!
            if let previous = images[enabled] {
                precondition(previous == png, "Restored state has a different image")
            }
            images[enabled] = png
            try png.write(to: directory.appendingPathComponent("safari-\(enabled ? "active" : "inactive").png"))
            print("PASS native WebKit action: \(title)")
        }
        precondition(images[true] != images[false], "Both states returned the same image")
        precondition(context.errors.isEmpty, "WebKit runtime errors: \(context.errors)")
        view.appearance = NSAppearance(named: .darkAqua)
        let snapshot = try await view.takeSnapshot(configuration: nil)
        try NSBitmapImageRep(data: snapshot.tiffRepresentation!)!
            .representation(using: .png, properties: [:])!
            .write(to: directory.appendingPathComponent("safari-popup-active.png"))
        print("PASS WebKit manifest, real storage events, action titles, images and repeated toggles")
    }
}
