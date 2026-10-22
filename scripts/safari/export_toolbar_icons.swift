// Render Apple's infinity symbols for Safari controls, never app icons/logos: a plain
// infinity when blocking is on (a line glyph like the other toolbar icons, which
// Safari tints), an infinity in a circle outline when it is paused.
import AppKit

let output = URL(fileURLWithPath: CommandLine.arguments.dropFirst().first ?? "extension/src/icons/safari-toolbar")
try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
for size in [16, 19, 32, 38, 64, 128, 256] {
    for active in [false, true] {
        let symbolName = active ? "infinity" : "infinity.circle"
        guard let symbol = NSImage(systemSymbolName: symbolName, accessibilityDescription: nil)?
            .withSymbolConfiguration(.init(pointSize: 16, weight: .regular)) else {
            fatalError("\(symbolName) requires macOS 11 or later.")
        }
        let pixels = CGFloat(size)
        let scale = pixels / 16
        let bitmap = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: size, pixelsHigh: size,
            bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true, isPlanar: false,
            colorSpaceName: .deviceRGB, bytesPerRow: 0, bitsPerPixel: 0)!
        let context = NSGraphicsContext(bitmapImageRep: bitmap)!
        NSGraphicsContext.saveGraphicsState()
        NSGraphicsContext.current = context
        let bounds = CGRect(x: 0, y: 0, width: pixels, height: pixels)
        context.cgContext.clear(bounds)
        let width = 14 * scale
        let height = width * symbol.size.height / symbol.size.width
        symbol.draw(in: CGRect(x: (pixels - width) / 2, y: (pixels - height) / 2,
                               width: width, height: height))
        // Normalize the system-rendered symbol to a monochrome alpha template.
        context.cgContext.setBlendMode(.sourceIn)
        context.cgContext.setFillColor(NSColor.black.cgColor)
        context.cgContext.fill(bounds)
        context.cgContext.setBlendMode(.normal)
        NSGraphicsContext.restoreGraphicsState()
        let name = "\(active ? "active" : "inactive")-\(size).png"
        try bitmap.representation(using: .png, properties: [:])!.write(to: output.appendingPathComponent(name))
        print(name)
    }
}
