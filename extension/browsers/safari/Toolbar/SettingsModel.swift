import Foundation
import Observation

struct Setting: Identifiable {
    let id: String
    let title: String
    let detail: String
}

struct Fansite: Identifiable, Decodable {
    let domain: String
    let key: String
    let rules: Int
    let selectors: Int
    var id: String { key }
}

struct BlockedStream: Identifiable, Hashable {
    let channel: String
    let title: String
    let reason: String
    let game: String
    var id: String { channel }
}

// The popover's view of the shared settings. Defaults match extension/src/settings.js.
@MainActor @Observable final class SettingsModel {
    static let sections: [(title: String, settings: [Setting])] = [
        ("Ads and Tracking", [
            Setting(id: "blockAds", title: "Block ad servers", detail: "Twitch, Amazon and Google ad networks."),
            Setting(id: "blockTracking", title: "Block tracking", detail: "Telemetry, analytics and ID-sync servers."),
            Setting(id: "hideDisplayAds", title: "Hide display ads", detail: "Banners, sponsored tiles, player ad frames, ad-block warnings."),
        ]),
        ("Video Player", [
            Setting(id: "removeStreamAds", title: "Remove stream ads", detail: "Swaps ad breaks for an ad-free stream; may drop to 360p or pause."),
            Setting(id: "sourceQuality", title: "Source quality", detail: "Starts every stream at the highest quality."),
            Setting(id: "backgroundQuality", title: "Keep quality in background", detail: "Stops Twitch lowering the quality in hidden tabs."),
            Setting(id: "hideAdBreakBanner", title: "Hide ad-break banner", detail: "Hides the countdown shown while an ad plays."),
        ]),
        ("Page Clutter", [
            Setting(id: "hideUpsells", title: "Hide upsells", detail: "Turbo, Prime Gaming, Luna and Subtember."),
            Setting(id: "hidePrompts", title: "Hide prompts", detail: "Apple TV offer, emotes tip and Prime Benefits."),
            Setting(id: "hideSignupPrompts", title: "Hide sign-up prompts", detail: "Sign-up bar, chat sign-up gate and follow pop-up."),
            Setting(id: "hideCookieBanner", title: "Hide cookie banner", detail: "Hides the banner without accepting anything."),
        ]),
    ]
    static let tibiaFilter = Setting(id: "tibiaFilter", title: "Hide other games",
                                     detail: "OTServers, Pokémon servers and idle games. Undecided streams stay visible.")
    nonisolated static let defaultsOff: Set<String> = ["hideAdBreakBanner"]
    static let fansites: [Fansite] = {
        guard let url = Bundle.main.url(forResource: "Sites", withExtension: "json"),
              let data = try? Data(contentsOf: url) else { return [] }
        return (try? JSONDecoder().decode([Fansite].self, from: data)) ?? []
    }()

    private(set) var mode = "hide"
    private(set) var threshold = 0.01
    private(set) var exportStatus = "Full titles, tags and model evidence from this page."
    private(set) var values: [String: Bool] = [:]
    private(set) var shown: [String: String] = [:]
    private(set) var hidden: [BlockedStream] = []
    private(set) var onTibiaDirectory = false
    private(set) var rulesFetchedAt: Date?
    private(set) var rulesError: String?
    private(set) var rulesRequested = false
    private let defaults: UserDefaults
    private var pageURL: URL?

    init(defaults: UserDefaults = SharedStore.defaults) {
        self.defaults = defaults
    }

    nonisolated static func storedValue(_ key: String, defaults: UserDefaults = SharedStore.defaults) -> Bool {
        let edited = defaults.dictionary(forKey: SharedStore.Key.settings)?[key] as? Bool
        let web = defaults.dictionary(forKey: SharedStore.Key.webSettings)?[key] as? Bool
        return edited ?? web ?? !defaultsOff.contains(key)
    }

    func value(_ key: String) -> Bool { values[key] ?? Self.storedValue(key, defaults: defaults) }

    func reload(pageURL: URL?) {
        if let pageURL { self.pageURL = pageURL }
        let pageURL = self.pageURL
        let keys = ["enabled", Self.tibiaFilter.id] + Self.sections.flatMap { $0.settings.map(\.id) } + Self.fansites.map(\.key)
        // Edits newer than the web extension's last report win.
        let edited = defaults.dictionary(forKey: SharedStore.Key.settings) ?? [:]
        let web = defaults.dictionary(forKey: SharedStore.Key.webSettings) ?? [:]
        values = Dictionary(uniqueKeysWithValues: keys.map { key in
            (key, (edited[key] as? Bool) ?? (web[key] as? Bool) ?? !Self.defaultsOff.contains(key))
        })
        let storedMode = (edited["tibiaMode"] ?? web["tibiaMode"]) as? String
        mode = ["show", "bottom", "hide"].contains(storedMode ?? "") ? storedMode! : value("tibiaFilter") ? "hide" : "show"
        let storedThreshold = (edited["tibiaThreshold"] ?? web["tibiaThreshold"]) as? Double ?? 0.01
        threshold = storedThreshold.isFinite && (0...1).contains(storedThreshold) ? storedThreshold : 0.01
        exportStatus = defaults.string(forKey: SharedStore.Key.exportStatus) ?? "Full titles, tags and model evidence from this page."
        shown = defaults.dictionary(forKey: SharedStore.Key.shown) as? [String: String] ?? [:]
        let report = defaults.dictionary(forKey: SharedStore.Key.hidden) ?? [:]
        let reportURL = (report["url"] as? String).flatMap(URL.init(string:))
        let samePage = pageURL == nil || reportURL.map { $0.host == pageURL?.host && $0.path == pageURL?.path } == true
        if pageURL != nil || hidden.isEmpty {
            onTibiaDirectory = samePage && report["onDirectory"] as? Bool == true
            hidden = !onTibiaDirectory || !value("enabled") || mode == "show" ? [] : (report["hidden"] as? [[String: Any]] ?? []).compactMap { card in
                guard let channel = card["channel"] as? String, shown[channel] != card["title"] as? String else { return nil }
                return BlockedStream(channel: channel, title: card["title"] as? String ?? "",
                                     reason: card["reason"] as? String ?? "", game: card["game"] as? String ?? "Other games")
            }
        }
        let rules = defaults.dictionary(forKey: SharedStore.Key.rules) ?? [:]
        let fetched = rules["fetchedAt"] as? Double ?? 0
        rulesFetchedAt = fetched > 0 ? Date(timeIntervalSince1970: fetched / 1000) : nil
        rulesError = rules["error"] as? String
    }

    func set(_ key: String, _ on: Bool) {
        values[key] = on
        if !value("enabled") || !value("tibiaFilter") { hidden = [] }
        var edited = defaults.dictionary(forKey: SharedStore.Key.settings) ?? [:]
        for (k, v) in values { edited[k] = v }
        defaults.set(edited, forKey: SharedStore.Key.settings)
        defaults.set(Date().timeIntervalSince1970 * 1000, forKey: SharedStore.Key.settingsChangedAt)
    }

    func setMode(_ mode: String) {
        guard ["show", "bottom", "hide"].contains(mode) else { return }
        self.mode = mode
        set("tibiaFilter", mode != "show")
        editPreference("tibiaMode", mode)
    }

    func setThreshold(_ threshold: Double) {
        guard threshold.isFinite && (0...1).contains(threshold) else { return }
        self.threshold = threshold
        editPreference("tibiaThreshold", threshold)
    }

    private func editPreference(_ key: String, _ value: Any) {
        var edited = defaults.dictionary(forKey: SharedStore.Key.settings) ?? [:]
        edited[key] = value
        defaults.set(edited, forKey: SharedStore.Key.settings)
        defaults.set(Date().timeIntervalSince1970 * 1000, forKey: SharedStore.Key.settingsChangedAt)
    }

    func requestExport() {
        guard let pageURL else { return }
        defaults.set(pageURL.absoluteString, forKey: SharedStore.Key.exportURL)
        exportStatus = "Preparing download…"
        defaults.set(exportStatus, forKey: SharedStore.Key.exportStatus)
        defaults.set(Date().timeIntervalSince1970 * 1000, forKey: SharedStore.Key.exportRequestedAt)
    }

    // channel -> title keeps that broadcast visible until its title changes; nil undoes it.
    func setShown(_ channel: String, title: String?) {
        shown[channel] = title
        if title != nil { hidden.removeAll { $0.channel == channel } }
        defaults.set(shown, forKey: SharedStore.Key.shown)
        defaults.set(Date().timeIntervalSince1970 * 1000, forKey: SharedStore.Key.shownChangedAt)
    }

    func requestRulesUpdate() {
        SharedStore.requestRulesUpdate(defaults: defaults)
        rulesRequested = true
    }
}
