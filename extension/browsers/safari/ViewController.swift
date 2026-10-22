import Cocoa
import Observation
import SafariServices
import SwiftUI

private let extensionBundleIdentifier = "com.nesleykent.tibiaantiad.Extension"
private let repositoryURL = URL(string: "https://github.com/nesleykent/Tibia-Anti-Ad")!

// Whether Safari has the extension turned on; nil while unknown.
@MainActor @Observable final class ExtensionState {
    private(set) var isEnabled: Bool?
    private(set) var isUnavailable = false

    func refresh() {
        SFSafariExtensionManager.getStateOfSafariExtension(withIdentifier: extensionBundleIdentifier) { state, error in
            DispatchQueue.main.async {
                self.isEnabled = error == nil ? state?.isEnabled : nil
                self.isUnavailable = error != nil || state == nil
            }
        }
    }
}

// The app's window: native SwiftUI in place of the converter's web page.
struct ContentView: View {
    @State private var state = ExtensionState()
    @State private var settingsError: String?

    private var message: String {
        if state.isUnavailable {
            return "Safari can’t report the extension’s status. Check Tibia Anti-Ad in Safari Settings → Extensions."
        }
        switch state.isEnabled {
        case true?: return "Tibia Anti-Ad is on. Its settings are in the Safari toolbar; turn it off in Safari Settings → Extensions."
        case false?: return "Tibia Anti-Ad is off. Turn it on in Safari Settings → Extensions."
        case nil: return "Checking Safari…"
        }
    }

    var body: some View {
        VStack(spacing: 14) {
            Image(nsImage: NSImage(named: state.isEnabled == true ? "StatusActive" : "StatusInactive") ?? NSApp.applicationIconImage)
                .renderingMode(.template)
                .resizable()
                .frame(width: 72, height: 72)
                .foregroundStyle(.primary)
                .accessibilityHidden(true)
            Text("Tibia Anti-Ad")
                .font(.title2.weight(.semibold))
            Text(message)
                .font(.body)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .fixedSize(horizontal: false, vertical: true)
            Button("Open Safari Settings…", action: openSafariSettings)
                .keyboardShortcut(.defaultAction)
                .controlSize(.large)
                .padding(.top, 4)
            Link("Tibia Anti-Ad on GitHub", destination: repositoryURL)
                .font(.callout)
        }
        .padding(.horizontal, 36)
        .padding(.vertical, 28)
        .frame(width: 420)
        // Recheck whenever the app comes back from Safari Settings.
        .task {
            state.refresh()
            for await _ in NotificationCenter.default.notifications(named: NSApplication.didBecomeActiveNotification) {
                state.refresh()
            }
        }
        .alert("Couldn’t Open Safari Settings", isPresented: Binding(get: { settingsError != nil }, set: { if !$0 { settingsError = nil } })) {
            Button("OK", role: .cancel) {}
        } message: {
            Text("Open Safari → Settings → Extensions and select Tibia Anti-Ad.\n\n\(settingsError ?? "")")
        }
    }

    private func openSafariSettings() {
        SFSafariApplication.showPreferencesForExtension(withIdentifier: extensionBundleIdentifier) { error in
            DispatchQueue.main.async {
                if let error { settingsError = error.localizedDescription }
                else { NSApplication.shared.terminate(nil) }
            }
        }
    }
}

// The storyboard's view controller. Replacing loadView skips the storyboard's
// web view, so the window shows the SwiftUI view above.
final class ViewController: NSViewController {
    override func loadView() {
        view = NSHostingView(rootView: ContentView())
    }

    override func viewDidAppear() {
        super.viewDidAppear()
        view.window?.title = "Tibia Anti-Ad"
        view.window?.styleMask.remove(.resizable)
    }
}
