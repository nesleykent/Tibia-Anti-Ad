import Foundation

// Settings and Tibia filter state shared by the app, the Safari web extension
// and the toolbar extension through their App Group. The web extension keeps
// its own storage for its scripts and exchanges it here by native messaging
// (SafariWebExtensionHandler); the toolbar popover reads and edits this copy.
enum SharedStore {
    static let group = Bundle.main.object(forInfoDictionaryKey: "TibiaAppGroup") as? String ?? "group.com.nesleykent.tibiaantiad"
    static var defaults: UserDefaults { UserDefaults(suiteName: group) ?? .standard }

    enum Key {
        static let exportRequestedAt = "exportRequestedAt"
        static let exportStatus = "exportStatus"
        static let exportURL = "exportURL"
        static let webSettings = "webSettings"          // resolved settings, written by the web extension
        static let settings = "settings"                // settings edited in the popover
        static let settingsChangedAt = "settingsChangedAt"
        static let shown = "tibiaShown"                 // channel -> title shown by the viewer
        static let shownChangedAt = "tibiaShownChangedAt"
        static let hidden = "hidden"                    // streams hidden on the last Tibia directory page
        static let rules = "rules"                      // filter rules status
        static let rulesRequestedAt = "rulesRequestedAt"
    }

    // The containing app and toolbar use the same authenticated App Group.
    // A plain command-line UserDefaults suite does not address this container.
    static func requestRulesUpdate(defaults: UserDefaults = SharedStore.defaults) {
        defaults.set(Date().timeIntervalSince1970 * 1000, forKey: Key.rulesRequestedAt)
        defaults.synchronize()
    }

    static func requestDiagnostics(url: URL, defaults: UserDefaults = SharedStore.defaults) {
        guard url.scheme == "https", ["twitch.tv", "www.twitch.tv"].contains(url.host ?? ""),
              url.path.lowercased().trimmingCharacters(in: CharacterSet(charactersIn: "/")) == "directory/category/tibia" else {
            defaults.set("Open the Twitch Tibia category first.", forKey: Key.exportStatus)
            return
        }
        defaults.set(url.absoluteString, forKey: Key.exportURL)
        defaults.set("Preparing download…", forKey: Key.exportStatus)
        defaults.set(Date().timeIntervalSince1970 * 1000, forKey: Key.exportRequestedAt)
        defaults.synchronize()
    }

    // A native message from the web extension's background script.
    static func handle(_ message: [String: Any], defaults: UserDefaults = SharedStore.defaults) -> [String: Any] {
        switch message["type"] as? String {
        case "sync":
            if let settings = message["settings"] as? [String: Any] { defaults.set(settings, forKey: Key.webSettings) }
            if let shown = message["tibiaShown"] as? [String: Any], defaults.double(forKey: Key.shownChangedAt) == 0 {
                defaults.set(shown, forKey: Key.shown)
            }
            if let rules = message["rules"] as? [String: Any] {
                // JSON null bridges as NSNull, which UserDefaults cannot store.
                // Persist the known property-list fields before returning edits.
                var stored: [String: Any] = [:]
                if let fetchedAt = rules["fetchedAt"] as? NSNumber { stored["fetchedAt"] = fetchedAt }
                if let error = rules["error"] as? String { stored["error"] = error }
                defaults.set(stored, forKey: Key.rules)
            }
            return [
                "settings": defaults.dictionary(forKey: Key.settings) ?? [:],
                "settingsChangedAt": defaults.double(forKey: Key.settingsChangedAt),
                "tibiaShown": defaults.dictionary(forKey: Key.shown) ?? [:],
                "tibiaShownChangedAt": defaults.double(forKey: Key.shownChangedAt),
                "rulesRequestedAt": defaults.double(forKey: Key.rulesRequestedAt),
                "exportRequestedAt": defaults.double(forKey: Key.exportRequestedAt),
                "exportURL": defaults.string(forKey: Key.exportURL) ?? "",
            ]
        case "export-result":
            defaults.set(message["status"] as? String ?? "Export failed.", forKey: Key.exportStatus)
            return [:]
        case "hidden":
            // The native popover matches the retained directory report against
            // its active page URL. Reports from channel/other Twitch tabs must
            // not erase it just because those pages have no directory cards.
            guard message["onDirectory"] as? Bool == true else { return [:] }
            // Keep only the fields consumed by the native list. Model results
            // contain JSON nulls (for example reference.origin), which cannot
            // be persisted in UserDefaults and abort the native request.
            let cards = (message["hidden"] as? [[String: Any]] ?? []).compactMap { card -> [String: String]? in
                guard let channel = card["channel"] as? String else { return nil }
                return ["channel": channel, "title": card["title"] as? String ?? "",
                        "reason": card["reason"] as? String ?? "", "game": card["game"] as? String ?? "Other games"]
            }
            defaults.set(["url": message["url"] as? String ?? "", "hidden": cards,
                          "onDirectory": message["onDirectory"] as? Bool ?? false,
                          "mode": message["mode"] as? String ?? "hide"], forKey: Key.hidden)
            return [:]
        default:
            return [:]
        }
    }
}
