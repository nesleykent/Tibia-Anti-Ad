import Foundation

// Settings and Tibia filter state shared by the app, the Safari web extension
// and the toolbar extension through their App Group. The web extension keeps
// its own storage for its scripts and exchanges it here by native messaging
// (SafariWebExtensionHandler); the toolbar popover reads and edits this copy.
enum SharedStore {
    static let group = Bundle.main.object(forInfoDictionaryKey: "TibiaAppGroup") as? String ?? "group.com.nesleykent.tibiaantiad"
    static var defaults: UserDefaults { UserDefaults(suiteName: group) ?? .standard }

    enum Key {
        static let webSettings = "webSettings"          // resolved settings, written by the web extension
        static let settings = "settings"                // settings edited in the popover
        static let settingsChangedAt = "settingsChangedAt"
        static let shown = "tibiaShown"                 // channel -> title shown by the viewer
        static let shownChangedAt = "tibiaShownChangedAt"
        static let hidden = "hidden"                    // streams hidden on the last Tibia directory page
        static let rules = "rules"                      // filter rules status
        static let rulesRequestedAt = "rulesRequestedAt"
    }

    // A native message from the web extension's background script.
    static func handle(_ message: [String: Any]) -> [String: Any] {
        let defaults = defaults
        switch message["type"] as? String {
        case "sync":
            if let settings = message["settings"] as? [String: Any] { defaults.set(settings, forKey: Key.webSettings) }
            if let shown = message["tibiaShown"] as? [String: Any], defaults.double(forKey: Key.shownChangedAt) == 0 {
                defaults.set(shown, forKey: Key.shown)
            }
            if let rules = message["rules"] as? [String: Any] { defaults.set(rules, forKey: Key.rules) }
            return [
                "settings": defaults.dictionary(forKey: Key.settings) ?? [:],
                "settingsChangedAt": defaults.double(forKey: Key.settingsChangedAt),
                "tibiaShown": defaults.dictionary(forKey: Key.shown) ?? [:],
                "tibiaShownChangedAt": defaults.double(forKey: Key.shownChangedAt),
                "rulesRequestedAt": defaults.double(forKey: Key.rulesRequestedAt),
            ]
        case "hidden":
            defaults.set(["url": message["url"] as? String ?? "", "hidden": message["hidden"] as? [Any] ?? [],
                          "onDirectory": message["onDirectory"] as? Bool ?? false], forKey: Key.hidden)
            return [:]
        default:
            return [:]
        }
    }
}
