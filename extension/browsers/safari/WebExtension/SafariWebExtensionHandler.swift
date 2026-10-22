import Foundation
import SafariServices

// Answers browser.runtime.sendNativeMessage from the web extension's background script.
final class SafariWebExtensionHandler: NSObject, NSExtensionRequestHandling {
    func beginRequest(with context: NSExtensionContext) {
        let item = context.inputItems.first as? NSExtensionItem
        let message = item?.userInfo?[SFExtensionMessageKey] as? [String: Any] ?? [:]
        let response = NSExtensionItem()
        response.userInfo = [SFExtensionMessageKey: SharedStore.handle(message)]
        context.completeRequest(returningItems: [response], completionHandler: nil)
    }
}
