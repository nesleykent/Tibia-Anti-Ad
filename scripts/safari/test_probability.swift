// Render the actual shared filter and Safari-only view in a disposable WebKit page.
// No Safari preferences, personal profile, signing credentials or live accounts are used.
import AppKit
import WebKit

private final class Fixture: NSObject, WKURLSchemeHandler {
    let html: Data
    init(_ html: Data) { self.html = html }
    func webView(_ webView: WKWebView, start task: any WKURLSchemeTask) {
        task.didReceive(URLResponse(url: task.request.url!, mimeType: "text/html", expectedContentLength: html.count, textEncodingName: "utf-8"))
        task.didReceive(html)
        task.didFinish()
    }
    func webView(_ webView: WKWebView, stop task: any WKURLSchemeTask) {}
}

@main struct ProbabilityCheck {
    @MainActor static func main() {
        let app = NSApplication.shared
        app.setActivationPolicy(.accessory)
        Task { @MainActor in
            do { try await check(); exit(0) }
            catch { print("FAIL WebKit probability check: \(error)"); exit(1) }
        }
        app.run()
    }

    @MainActor static func wait(_ view: WKWebView, _ condition: String) async throws {
        for _ in 0..<100 {
            if (try? await view.evaluateJavaScript(condition)) as? Bool == true { return }
            try await Task.sleep(for: .milliseconds(100))
        }
        throw NSError(domain: "ProbabilityCheck", code: 1, userInfo: [NSLocalizedDescriptionKey: "Timed out: \(condition)"])
    }

    @MainActor static func check() async throws {
        let root = URL(fileURLWithPath: CommandLine.arguments.dropFirst().first ?? FileManager.default.currentDirectoryPath)
        let output = root.appendingPathComponent("local/verification/safari-probability")
        try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
        let fixture = Fixture(try Data(contentsOf: root.appendingPathComponent("tests/browser/fixtures/twitch-probability.html")))
        let configuration = WKWebViewConfiguration()
        configuration.websiteDataStore = .nonPersistent()
        configuration.setURLSchemeHandler(fixture, forURLScheme: "tibia-fixture")
        let scripts = configuration.userContentController
        let setup = """
        window.testErrors=[]; window.addEventListener('error',event=>testErrors.push(event.message));
        window.testStored={tibiaFilter:false}; const listeners=[];
        window.setTestSettings=async values=>{
          Object.assign(testStored,values); const changes=Object.fromEntries(Object.entries(values).map(([key,newValue])=>[key,{newValue}]));
          listeners.forEach(listener=>listener(changes,'local')); await Promise.resolve();
        };
        window.browser={storage:{local:{get:async defaults=>({...defaults,...testStored})},onChanged:{addListener:f=>listeners.push(f)}},
          runtime:{onMessage:{addListener(){}},sendMessage:async()=>true}};
        """
        scripts.addUserScript(WKUserScript(source: setup, injectionTime: .atDocumentEnd, forMainFrameOnly: true))
        for name in ["settings.js", "settings-bridge.js", "tibia-evidence.js", "tibia-classify.js", "tibia-rules.js"] {
            scripts.addUserScript(WKUserScript(source: try String(contentsOf: root.appendingPathComponent("extension/src/\(name)"), encoding: .utf8), injectionTime: .atDocumentEnd, forMainFrameOnly: true))
        }
        let css = try String(contentsOf: root.appendingPathComponent("extension/src/hide.css"), encoding: .utf8)
            + "\n" + String(contentsOf: root.appendingPathComponent("extension/browsers/safari/web/tibia-probability.css"), encoding: .utf8)
        let encodedCSS = String(data: try JSONSerialization.data(withJSONObject: [css]), encoding: .utf8)!
        scripts.addUserScript(WKUserScript(source: "const style=document.createElement('style'); style.textContent=\(encodedCSS)[0]; document.head.append(style);", injectionTime: .atDocumentEnd, forMainFrameOnly: true))
        for relative in ["extension/src/tibia-props.js", "extension/browsers/safari/web/tibia-probability.js", "extension/src/tibia-filter.js"] {
            scripts.addUserScript(WKUserScript(source: try String(contentsOf: root.appendingPathComponent(relative), encoding: .utf8), injectionTime: .atDocumentEnd, forMainFrameOnly: true))
        }
        let view = WKWebView(frame: CGRect(x: 0, y: 0, width: 1440, height: 900), configuration: configuration)
        let window = NSWindow(contentRect: view.bounds, styleMask: [.titled], backing: .buffered, defer: false)
        window.title = "Tibia probability verification"
        window.contentView = view
        window.orderFrontRegardless()
        defer { window.close() }
        view.load(URLRequest(url: URL(string: "tibia-fixture://test/directory/category/tibia")!))
        let all = "document.querySelectorAll('[data-tibia-official-probability]').length===3"
        try await wait(view, all)
        let valuesMatch = """
        [...document.querySelectorAll('article')].every(article=>{
          const result=TwitchCleanTibiaClassify.create(TWITCH_CLEAN_TIBIA_EVIDENCE)(article.querySelector('h4').title,[...article.querySelectorAll('.tw-tag')].map(t=>t.textContent));
          return Number(article.querySelector('[data-tibia-official-probability]').getAttribute('data-tibia-official-probability'))===result.score.tibia;
        })
        """
        try await wait(view, valuesMatch)
        let visibilityMatches = """
        [...document.querySelectorAll('article')].every(article=>{
          const result=TwitchCleanTibiaClassify.create(TWITCH_CLEAN_TIBIA_EVIDENCE)(article.querySelector('h4').title,[...article.querySelectorAll('.tw-tag')].map(t=>t.textContent));
          const hidden=article.getClientRects().length===0;
          return hidden===(testStored.tibiaFilter && testStored.enabled!==false && result.verdict==='other');
        })
        """
        _ = try await view.evaluateJavaScript("setTestSettings({tibiaFilter:true});true")
        try await wait(view, "\(all) && document.querySelectorAll('[data-twitch-clean-hidden]').length>0")
        try await wait(view, visibilityMatches)
        _ = try await view.evaluateJavaScript("setTestSettings({tibiaFilter:false});true")
        try await wait(view, "\(all) && document.querySelectorAll('[data-twitch-clean-hidden]').length===0")
        try await wait(view, visibilityMatches)
        for width in [1440, 375] {
            window.setContentSize(NSSize(width: width, height: width == 375 ? 1100 : 900))
            for dark in [true, false] {
                view.appearance = NSAppearance(named: dark ? .darkAqua : .aqua)
                try await Task.sleep(for: .milliseconds(250))
                let layout = """
                [...document.querySelectorAll('[data-tibia-probability-row]')].every(row=>{
                  const badge=row.querySelector('[data-tibia-official-probability]').getBoundingClientRect(), name=row.querySelector('p').getBoundingClientRect(), bounds=row.getBoundingClientRect();
                  return badge.right<=bounds.right+1 && badge.left>=name.right-1 && badge.width>0 && badge.height>0;
                }) && document.documentElement.scrollWidth<=window.innerWidth+1
                """
                try await wait(view, layout)
                let snapshot = try await view.takeSnapshot(configuration: nil)
                try NSBitmapImageRep(data: snapshot.tiffRepresentation!)!.representation(using: .png, properties: [:])!
                    .write(to: output.appendingPathComponent("\(width)-\(dark ? "dark" : "light").png"))
            }
        }
        _ = try await view.evaluateJavaScript("setTestSettings({enabled:false});true")
        try await wait(view, "document.querySelectorAll('[data-tibia-official-probability]').length===0")
        _ = try await view.evaluateJavaScript("setTestSettings({enabled:true});true")
        try await wait(view, all)
        // A downloaded model updates estimates even with Hide other games off.
        _ = try await view.evaluateJavaScript("""
        const flipped=structuredClone(TWITCH_CLEAN_TIBIA_EVIDENCE); flipped.revision++;
        for(const value of Object.values(flipped.model.weights)) value[0]*=-1;
        window.originalEstimate=Number(document.querySelector('[data-tibia-official-probability]').getAttribute('data-tibia-official-probability'));
        setTestSettings({tibiaEvidence:{data:flipped,fetchedAt:Date.now()}});true
        """)
        try await wait(view, "Math.abs(Number(document.querySelector('[data-tibia-official-probability]').getAttribute('data-tibia-official-probability'))-(1-originalEstimate))<0.00001")
        _ = try await view.evaluateJavaScript("setTestSettings({tibiaEvidence:null}); const heading=document.querySelector('h4'); heading.title='bom dia galera'; heading.textContent=heading.title;true")
        try await wait(view, valuesMatch)
        try await wait(view, all)
        _ = try await view.evaluateJavaScript("history.pushState({},'', '/directory/category/chess');true")
        try await wait(view, "document.querySelectorAll('[data-tibia-official-probability]').length===0")
        _ = try await view.evaluateJavaScript("history.pushState({},'', '/directory/category/tibia');true")
        try await wait(view, all)
        let errors = try await view.evaluateJavaScript("testErrors") as! [String]
        precondition(errors.isEmpty, "WebKit runtime errors: \(errors)")
        print("PASS WebKit: all estimates match the classifier with hiding on/off; responsive light/dark layouts, master pause, model/title updates and navigation")
        if CommandLine.arguments.contains("--live") {
            window.setContentSize(NSSize(width: 1440, height: 1000))
            view.appearance = NSAppearance(named: .darkAqua)
            view.load(URLRequest(url: URL(string: "https://www.twitch.tv/directory/category/tibia")!))
            try await wait(view, "location.hostname==='www.twitch.tv' && document.readyState!=='loading'")
            try await wait(view, "document.querySelectorAll('[data-tibia-official-probability]').length>0")
            try await wait(view, "[...document.querySelectorAll('article a[data-a-target=\"preview-card-channel-link\"]')].every(link=>link.querySelector('[data-tibia-official-probability]'))")
            _ = try await view.evaluateJavaScript("setTestSettings({tibiaFilter:true});true")
            let liveVisibility = """
            [...document.querySelectorAll('article')].filter(article=>article.querySelector('[data-tibia-official-probability]')).every(article=>{
              const badge=article.querySelector('[data-tibia-official-probability]');
              const probability=Number(badge.getAttribute('data-tibia-official-probability'));
              const cutoff=1/(1+Math.exp(TWITCH_CLEAN_TIBIA_EVIDENCE.model.threshold));
              const hidden=article.getClientRects().length===0;
              const cell=article.closest('[data-twitch-clean-tibia]');
              return cell && hidden===cell.getAttribute('data-twitch-clean-tibia').startsWith('other:') && (probability>cutoff+0.000001 || hidden);
            }) && document.querySelectorAll('[data-twitch-clean-hidden]').length>0
            """
            try await wait(view, liveVisibility)
            let visibility = try await view.evaluateJavaScript("""
            JSON.stringify({total:document.querySelectorAll('[data-tibia-official-probability]').length,
              hidden:document.querySelectorAll('[data-twitch-clean-hidden]').length,
              lowestVisible:Math.min(...[...document.querySelectorAll('[data-tibia-official-probability]')].filter(badge=>badge.getClientRects().length).map(badge=>Number(badge.getAttribute('data-tibia-official-probability'))))})
            """) as? String ?? "{}"
            print("PASS live WebKit computed visibility: \(visibility)")
            let filteredSnapshot = try await view.takeSnapshot(configuration: nil)
            try NSBitmapImageRep(data: filteredSnapshot.tiffRepresentation!)!.representation(using: .png, properties: [:])!
                .write(to: output.appendingPathComponent("live-filtered.png"))
            _ = try await view.evaluateJavaScript("setTestSettings({tibiaFilter:false});true")
            try await wait(view, "document.querySelectorAll('[data-twitch-clean-hidden]').length===0")
            let snapshot = try await view.takeSnapshot(configuration: nil)
            try NSBitmapImageRep(data: snapshot.tiffRepresentation!)!.representation(using: .png, properties: [:])!
                .write(to: output.appendingPathComponent("live-dark.png"))
            let count = try await view.evaluateJavaScript("document.querySelectorAll('[data-tibia-official-probability]').length") as? Int ?? 0
            print("PASS live WebKit Twitch presentation: \(count) probability labels")
        }
    }
}
