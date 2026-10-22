import Foundation
import SafariServices

// Safari requires a principal class for a web extension. The extension does not
// use native messaging, so every request is completed without a reply.
final class SafariWebExtensionHandler: NSObject, NSExtensionRequestHandling {
    func beginRequest(with context: NSExtensionContext) {
        context.completeRequest(returningItems: [], completionHandler: nil)
    }
}
