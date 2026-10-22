// Twitch Clean (Chrome): Chrome's MV3 background is a service worker, which
// cannot run the Tesseract web worker. OCR therefore runs in an offscreen
// document (offscreen.html, which loads the shared ocr-background.js); this
// worker only creates that document and forwards the content script's request.
const OFFSCREEN = 'offscreen.html';
let creating = null;

const ensureOffscreen = async () => {
    if (await chrome.offscreen.hasDocument()) { return; }
    creating = creating || chrome.offscreen.createDocument({
        url: OFFSCREEN,
        reasons: [chrome.offscreen.Reason.WORKERS],
        justification: 'Run OCR on Twitch stream thumbnails for the Tibia filter.',
    }).finally(() => { creating = null; });
    await creating;
};

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message?.type !== 'tibia-ocr' || !sender.tab) { return false; }
    ensureOffscreen()
        .then(() => chrome.runtime.sendMessage({ ...message, type: 'tibia-ocr-forwarded' }))
        .then(sendResponse, () => sendResponse({ text: null }));
    return true;
});
