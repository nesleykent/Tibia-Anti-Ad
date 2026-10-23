import SwiftUI

// The toolbar popover: every option in a grouped form, as in System Settings.
// Changes are saved immediately and visible Safari pages sync them live.
struct SettingsView: View {
    @Bindable var model: SettingsModel
    @State private var showingBlocked = false

    private func toggle(_ setting: Setting, disabled: Bool = false) -> some View {
        Toggle(isOn: Binding(get: { model.value(setting.id) }, set: { model.set(setting.id, $0) })) {
            Text(setting.title)
            Text(setting.detail)
        }
        .disabled(disabled || !model.value("enabled"))
    }

    var body: some View {
        ZStack {
            settingsForm
                .opacity(showingBlocked ? 0 : 1)
                .allowsHitTesting(!showingBlocked)
                .accessibilityHidden(showingBlocked)
            if showingBlocked {
                BlockedStreamsView(model: model, onBack: { showingBlocked = false })
            }
        }
        .frame(width: 360, height: 560)
    }

    private var settingsForm: some View {
        Form {
            Section {
                Toggle(isOn: Binding(get: { model.value("enabled") }, set: { model.set("enabled", $0) })) {
                    Text("Tibia Anti-Ad").font(.headline)
                    Text(model.value("enabled") ? "On" : "Paused. Every feature is off.")
                }
            }
            ForEach(SettingsModel.sections, id: \.title) { section in
                Section(section.title) {
                    ForEach(section.settings) { setting in
                        if setting.id == "backgroundQuality" && model.value("removeStreamAds") {
                            Toggle(isOn: .constant(true)) {
                                Text(setting.title)
                                Text("Included with Remove stream ads.")
                            }
                            .disabled(true)
                        } else {
                            toggle(setting)
                        }
                    }
                }
            }
            Section {
                toggle(SettingsModel.tibiaFilter)
                Button {
                    showingBlocked = true
                } label: {
                    HStack {
                        LabeledContent("Blocked streams", value: model.onTibiaDirectory ? "\(model.hidden.count)" : "")
                        Image(systemName: "chevron.right").foregroundStyle(.secondary)
                    }
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("open-blocked-streams")
                LabeledContent {
                    Button("Update Now") { model.requestRulesUpdate() }
                        .disabled(model.rulesRequested)
                } label: {
                    Text("Filter rules")
                    Text(rulesStatus)
                }
            } header: {
                Text("Tibia Category")
            } footer: {
                Text("Video options apply when Twitch reloads.")
            }
            Section("Fansites") {
                ForEach(SettingsModel.fansites) { site in
                    toggle(Setting(id: site.key, title: site.domain,
                                   detail: "\(site.rules) network rules, \(site.selectors) hidden elements"))
                }
            }
        }
        .formStyle(.grouped)
        .toggleStyle(.switch)
    }

    private var rulesStatus: String {
        if model.rulesRequested { return "Checking when you next open Twitch…" }
        if let error = model.rulesError { return "Update failed: \(error)" }
        if let date = model.rulesFetchedAt { return "Updated \(date.formatted(date: .abbreviated, time: .shortened)) from GitHub" }
        return "Built-in rules, checked every 6 hours"
    }
}
