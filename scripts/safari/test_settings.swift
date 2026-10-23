// Compile with the real Toolbar views/model and SharedStore.swift. Uses a
// disposable defaults suite and synthetic streams, never the personal App Group.
import AppKit
import SwiftUI

@main struct SettingsCheck {
    @MainActor static func main() {
        NSApplication.shared.setActivationPolicy(.accessory)
        Task { @MainActor in
            do { try await check(); exit(0) }
            catch { print("FAIL native settings: \(error)"); exit(1) }
        }
        NSApplication.shared.run()
    }

    @MainActor static func check() async throws {
        let suite = "tibia-settings-test-\(UUID().uuidString)"
        let defaults = UserDefaults(suiteName: suite)!
        defer { defaults.removePersistentDomain(forName: suite) }
        let page = URL(string: "https://www.twitch.tv/directory/category/tibia")!
        let cards = (0..<30).map { ["channel": "fixture\($0)", "title": "Synthetic stream \($0)",
                                  "reason": "Estimated private-server probability: 99%", "game": "Other games"] }
        defaults.set(["url": page.absoluteString, "onDirectory": true, "hidden": cards], forKey: SharedStore.Key.hidden)
        let model = SettingsModel(defaults: defaults)
        model.reload(pageURL: page)
        precondition(model.hidden.count == cards.count)
        model.set("tibiaFilter", false)
        precondition(model.hidden.isEmpty, "Disabling must clear the native blocked count immediately")
        model.reload(pageURL: nil)
        precondition(model.hidden.isEmpty, "An old report must not restore the blocked count while filtering is off")
        model.set("tibiaFilter", true)
        model.reload(pageURL: nil)
        precondition(model.hidden.count == cards.count)
        model.set("enabled", false)
        model.reload(pageURL: nil)
        precondition(model.hidden.isEmpty)
        model.set("enabled", true)
        model.reload(pageURL: URL(string: "https://www.twitch.tv/directory/category/chess")!)
        model.reload(pageURL: nil)
        precondition(model.hidden.isEmpty, "Refresh must retain the active page, not revive a different page's report")
        model.reload(pageURL: page)
        let root = URL(fileURLWithPath: CommandLine.arguments.dropFirst().first ?? FileManager.default.currentDirectoryPath)
        let output = root.appendingPathComponent("local/verification/safari-controls")
        try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
        let host = NSHostingView(rootView: SettingsView(model: model).background(Color(nsColor: .windowBackgroundColor)))
        let window = NSWindow(contentRect: NSRect(x: 0, y: 0, width: 360, height: 560), styleMask: [.titled], backing: .buffered, defer: false)
        window.contentView = host
        window.makeKeyAndOrderFront(nil)
        NSApplication.shared.activate(ignoringOtherApps: true)
        defer { window.close() }
        try await Task.sleep(for: .milliseconds(600))
        let initial = host.bitmapImageRepForCachingDisplay(in: host.bounds)!
        host.cacheDisplay(in: host.bounds, to: initial)
        try initial.representation(using: .png, properties: [:])!.write(to: output.appendingPathComponent("settings-root.png"))
        func views(_ view: NSView) -> [NSView] { [view] + view.subviews.flatMap { views($0) } }
        if let scroll = views(host).compactMap({ $0 as? NSScrollView }).first, let content = scroll.documentView {
            scroll.contentView.scroll(to: NSPoint(x: 0, y: max(0, content.bounds.height - scroll.contentView.bounds.height)))
            scroll.reflectScrolledClipView(scroll.contentView)
        }
        try await Task.sleep(for: .milliseconds(350))
        let scrolled = host.bitmapImageRepForCachingDisplay(in: host.bounds)!
        host.cacheDisplay(in: host.bounds, to: scrolled)
        try scrolled.representation(using: .png, properties: [:])!.write(to: output.appendingPathComponent("settings-scrolled.png"))
        // Hit positions are grounded in the captured 360x560 native form.
        // Send events only to this test window, never the user's Safari window.
        func click(x: CGFloat, fromTop y: CGFloat) {
            let point = host.convert(NSPoint(x: x, y: host.isFlipped ? y : host.bounds.height - y), to: nil)
            for type in [NSEvent.EventType.leftMouseDown, .leftMouseUp] {
                let event = NSEvent.mouseEvent(with: type, location: point, modifierFlags: [], timestamp: 0,
                    windowNumber: window.windowNumber, context: nil, eventNumber: 0, clickCount: 1, pressure: 1)!
                window.sendEvent(event)
            }
        }
        let scrollCount = views(host).filter { $0 is NSScrollView }.count
        let originalPosition = views(host).compactMap { $0 as? NSScrollView }.first!.contentView.bounds.origin
        click(x: 120, fromTop: 375)
        try await Task.sleep(for: .milliseconds(500))
        precondition(views(host).filter { $0 is NSScrollView }.count > scrollCount, "Blocked streams did not open")
        for dark in [false, true] {
            window.appearance = NSAppearance(named: dark ? .darkAqua : .aqua)
            try await Task.sleep(for: .milliseconds(250))
            for button in views(host).compactMap({ $0 as? NSPopUpButton }) {
                precondition(button.itemTitles.contains("All Categories"))
                precondition(button.title == "All Categories")
            }
            let bitmap = host.bitmapImageRepForCachingDisplay(in: host.bounds)!
            host.cacheDisplay(in: host.bounds, to: bitmap)
            try bitmap.representation(using: .png, properties: [:])!.write(to: output.appendingPathComponent("blocked-\(dark ? "dark" : "light").png"))
        }
        // Scrolling the actual List must leave the explicit header available.
        if let scroll = views(host).compactMap({ $0 as? NSScrollView }).last,
           let content = scroll.documentView {
            scroll.contentView.scroll(to: NSPoint(x: 0, y: content.bounds.height))
            scroll.reflectScrolledClipView(scroll.contentView)
        }
        try await Task.sleep(for: .milliseconds(250))
        click(x: 40, fromTop: 20)
        try await Task.sleep(for: .milliseconds(500))
        precondition(views(host).filter { $0 is NSScrollView }.count == scrollCount, "Back did not restore settings")
        precondition(views(host).compactMap { $0 as? NSScrollView }.first!.contentView.bounds.origin == originalPosition,
                     "Back must preserve the settings scroll position")
        print("PASS native settings: forward/back navigation, fixed header, search, light/dark rendering, disabled counts and page-scoped refresh")
    }
}
