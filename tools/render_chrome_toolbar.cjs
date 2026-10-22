// Optional artwork regeneration: Node.js with sharp available on NODE_PATH.
// The checked-in PNGs keep normal builds dependency-free.
const sharp = require('sharp');
const path = require('node:path');
const fs = require('node:fs/promises');
const root = path.join(__dirname, '..', 'extension/browsers/chrome');
(async () => {
    await fs.mkdir(path.join(root, 'icons/chrome-toolbar'), { recursive: true });
    for (const [state, name] of [['inactive', 'infinity-circle'], ['active', 'infinity-circle-fill']]) {
        for (const size of [16, 32, 48, 128]) {
            await sharp(path.join(root, 'artwork', `${name}.svg`), { density: 384 })
                .resize(size, size).png()
                .toFile(path.join(root, 'icons/chrome-toolbar', `${state}-${size}.png`));
        }
    }
    // Extension/popup branding uses the project's own artwork on both browsers.
    for (const size of [16, 32, 48, 64, 96, 128, 256, 512]) {
        await sharp(path.join(root, 'artwork/infinity-circle-fill.svg'), { density: 1536 })
            .resize(size, size).png()
            .toFile(path.join(__dirname, '..', `extension/src/icons/icon-${size}.png`));
    }
})().catch(error => { console.error(error); process.exitCode = 1; });
