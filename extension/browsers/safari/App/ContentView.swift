import AppKit
import SafariServices
import SwiftUI

private let webExtensionIdentifier = "com.nesleykent.tibiaantiad.Extension"
private let safariIdentifier = "com.apple.Safari"
private let repositoryURL = URL(string: "https://github.com/nesleykent/Tibia-Anti-Ad")!

@main
struct TibiaAntiAdApp: App {
    var body: some Scene {
        Window("Tibia Anti-Ad", id: "main") {
            ContentView()
        }
        .windowResizability(.contentSize)
    }
}

// The app's window: whether Safari has the extension on, and a way to its settings.
struct ContentView: View {
    @State private var isEnabled: Bool?
    @State private var isUnavailable = false
    @State private var settingsError: String?

    var body: some View {
        VStack(spacing: 14) {
            Image(nsImage: NSImage(named: isEnabled == true ? "StatusActive" : "StatusInactive") ?? NSApp.applicationIconImage)
                .renderingMode(.template)
                .resizable()
                .frame(width: 72, height: 72)
                .foregroundStyle(.primary)
                .accessibilityHidden(true)
            Text("Tibia Anti-Ad")
                .font(.title2.weight(.semibold))
            Text(message)
                .foregroundStyle(.secondary)
                .multilineTextAlignment(.center)
                .fixedSize(horizontal: false, vertical: true)
            Button("Open Safari Settings…") {
                Task { await openSafariSettings() }
            }
            .keyboardShortcut(.defaultAction)
            .controlSize(.large)
            .padding(.top, 4)
            Link("Tibia Anti-Ad on GitHub", destination: repositoryURL)
                .font(.callout)
        }
        .padding(.horizontal, 36)
        .padding(.vertical, 28)
        .frame(width: 420)
        .task {
            // Recheck whenever the app comes back from Safari Settings.
            await refresh()
            for await _ in NotificationCenter.default.notifications(named: NSApplication.didBecomeActiveNotification) {
                await refresh()
            }
        }
        .alert("Couldn’t Open Safari Settings", isPresented: .constant(settingsError != nil)) {
            Button("OK", role: .cancel) { settingsError = nil }
        } message: {
            Text("Open Safari → Settings → Extensions and select Tibia Anti-Ad.\n\n\(settingsError ?? "")")
        }
    }

    private var message: String {
        if isUnavailable {
            return "Safari can’t report the extension’s status. Check Tibia Anti-Ad in Safari Settings → Extensions."
        }
        switch isEnabled {
        case true?: return "Tibia Anti-Ad is on. Its settings are in its Safari toolbar button."
        case false?: return "Tibia Anti-Ad is off. Turn it on in Safari Settings → Extensions."
        case nil: return "Checking Safari…"
        }
    }

    private func refresh() async {
        do {
            isEnabled = try await SFSafariExtensionManager.stateOfSafariExtension(withIdentifier: webExtensionIdentifier).isEnabled
            isUnavailable = false
        } catch {
            isEnabled = nil
            isUnavailable = true
        }
    }

    // Safari reports an unknown extension (SFErrorDomain 1) until it has run once
    // with a newly installed app: open Safari and ask again before giving up.
    private func openSafariSettings() async {
        do {
            try await SFSafariApplication.showPreferencesForExtension(withIdentifier: webExtensionIdentifier)
            NSApplication.shared.terminate(nil)
        } catch {
            if let safari = NSWorkspace.shared.urlForApplication(withBundleIdentifier: safariIdentifier) {
                _ = try? await NSWorkspace.shared.openApplication(at: safari, configuration: NSWorkspace.OpenConfiguration())
                try? await Task.sleep(for: .seconds(2))
            }
            do {
                try await SFSafariApplication.showPreferencesForExtension(withIdentifier: webExtensionIdentifier)
                NSApplication.shared.terminate(nil)
            } catch {
                await refresh()
                settingsError = error.localizedDescription
            }
        }
    }
}
