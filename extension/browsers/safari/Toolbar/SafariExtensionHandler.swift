import SafariServices
import SwiftUI

// The Safari toolbar button and its native popover. Safari calls the handler
// off the main thread; the popover and its model live on the main actor.
final class SafariExtensionHandler: SFSafariExtensionHandler {
    override func validateToolbarItem(in window: SFSafariWindow, validationHandler: @escaping (Bool, String) -> Void) {
        let image = SettingsModel.storedValue("enabled") ? "ToolbarActive" : "ToolbarInactive"
        window.getToolbarItem { item in
            item?.setImage(NSImage(named: image))
            item?.setLabel("Tibia Anti-Ad")
        }
        validationHandler(true, "")
    }

    override func popoverViewController() -> SFSafariExtensionViewController {
        MainActor.assumeIsolated { PopoverViewController.shared }
    }

    override func popoverWillShow(in window: SFSafariWindow) {
        Task { @MainActor in
            PopoverViewController.shared.model.reload(pageURL: nil)
            PopoverViewController.shared.beginUpdates()
        }
        window.getActiveTab { tab in
            tab?.getActivePage { page in
                page?.getPropertiesWithCompletionHandler { properties in
                    let url = properties?.url
                    Task { @MainActor in PopoverViewController.shared.model.reload(pageURL: url) }
                }
            }
        }
    }

    override func popoverDidClose(in window: SFSafariWindow) {
        Task { @MainActor in PopoverViewController.shared.endUpdates() }
        // The master switch changes the button's image.
        SFSafariApplication.setToolbarItemsNeedUpdate()
    }
}

@MainActor
final class PopoverViewController: SFSafariExtensionViewController {
    static let shared = PopoverViewController()
    let model = SettingsModel()
    private var refreshTimer: Timer?

    func beginUpdates() {
        endUpdates()
        refreshTimer = Timer.scheduledTimer(withTimeInterval: 1, repeats: true) { [weak self] _ in
            Task { @MainActor in self?.model.reload(pageURL: nil) }
        }
    }

    func endUpdates() {
        refreshTimer?.invalidate()
        refreshTimer = nil
    }

    override func loadView() {
        view = NSHostingView(rootView: SettingsView(model: model))
        preferredContentSize = NSSize(width: 360, height: 560)
    }
}
