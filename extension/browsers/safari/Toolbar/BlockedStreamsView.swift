import SwiftUI

// Streams the Tibia filter hides on the current Twitch page, grouped by game,
// with search, a category filter and Show; Shown by You undoes a correction.
struct BlockedStreamsView: View {
    @Bindable var model: SettingsModel
    @State private var search = ""
    @State private var category = ""

    private var categories: [String] { Array(Set(model.hidden.map(\.game))).sorted() }

    private var groups: [(game: String, streams: [BlockedStream])] {
        let words = search.lowercased().split(separator: " ")
        let matching = model.hidden.filter { stream in
            (category.isEmpty || stream.game == category) && words.allSatisfy {
                "\(stream.channel) \(stream.title) \(stream.reason) \(stream.game)".lowercased().contains($0)
            }
        }
        return Dictionary(grouping: matching, by: \.game).map { ($0.key, $0.value) }
            .sorted { $0.streams.count > $1.streams.count }
    }

    var body: some View {
        List {
            if !model.onTibiaDirectory {
                Text("Open the Tibia category on Twitch to see the streams hidden there.")
                    .foregroundStyle(.secondary)
            } else if groups.isEmpty {
                Text(model.hidden.isEmpty ? "No streams are hidden on this page." : "No blocked streams match.")
                    .foregroundStyle(.secondary)
            }
            ForEach(groups, id: \.game) { group in
                Section("\(group.game) (\(group.streams.count))") {
                    ForEach(group.streams) { stream in
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(stream.channel)
                                Text(stream.title).font(.caption).foregroundStyle(.secondary).lineLimit(1)
                                Text(stream.reason).font(.caption).foregroundStyle(.secondary)
                            }
                            Spacer()
                            Button("Show") { model.setShown(stream.channel, title: stream.title) }
                                .accessibilityLabel("Show \(stream.channel)")
                        }
                    }
                }
            }
            if !model.shown.isEmpty {
                Section {
                    ForEach(model.shown.sorted(by: { $0.key < $1.key }), id: \.key) { channel, title in
                        HStack {
                            VStack(alignment: .leading, spacing: 2) {
                                Text(channel)
                                Text(title).font(.caption).foregroundStyle(.secondary).lineLimit(1)
                            }
                            Spacer()
                            Button("Hide") { model.setShown(channel, title: nil) }
                                .accessibilityLabel("Hide \(channel) again")
                        }
                    }
                } header: {
                    Text("Shown by You")
                } footer: {
                    Text("Each stays visible until its title changes.")
                }
            }
        }
        .searchable(text: $search, prompt: "Search channels, titles and reasons")
        .toolbar {
            Picker("Category", selection: $category) {
                Text("All Categories").tag("")
                ForEach(categories, id: \.self) { Text($0).tag($0) }
            }
        }
        .navigationTitle("Blocked Streams")
    }
}
