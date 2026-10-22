// Twitch Clean: reads the game client from stream thumbnails for the Tibia filter.
//
// The content script sends {type: 'tibia-ocr', channel}; this page fetches the
// channel's 1920x1080 preview, keeps the right third (where the client's
// minimap, Store and Battle Pass panels sit), doubles it so small UI text is
// legible, and runs bundled Tesseract (no network beyond the thumbnail). Text is
// cached per channel for CACHE_MS so revisits are instant and a channel that
// switches games is re-read.
(() => {
    'use strict';

    const api = globalThis.browser || globalThis.chrome;
    const THUMBNAIL = channel => `https://static-cdn.jtvnw.net/previews-ttv/live_user_${encodeURIComponent(channel)}-1920x1080.jpg?t=${Math.floor(Date.now() / CACHE_MS)}`;
    const CACHE_MS = 30 * 60 * 1000;
    const WORKERS = 2;
    const cache = new Map(); // channel -> {at, text}
    const inflight = new Map(); // channel -> Promise<text|null>
    const queue = [];
    let idle = [];
    let pool = null;

    const startPool = async () => {
        const base = api.runtime.getURL('vendor/tesseract/');
        const workers = await Promise.all(Array.from({ length: WORKERS }, async () => {
            const worker = await Tesseract.createWorker('eng', 1, {
                workerPath: `${base}worker.min.js`,
                corePath: base,
                langPath: base,
                workerBlobURL: false,
                cacheMethod: 'none',
            });
            await worker.setParameters({ tessedit_pageseg_mode: Tesseract.PSM.SPARSE_TEXT });
            return worker;
        }));
        idle = workers;
    };

    const crop = async blob => {
        const bitmap = await createImageBitmap(blob);
        const sx = Math.floor(bitmap.width * 2 / 3);
        const width = bitmap.width - sx;
        const canvas = new OffscreenCanvas(width * 2, bitmap.height * 2);
        const ctx = canvas.getContext('2d');
        ctx.imageSmoothingQuality = 'high';
        ctx.drawImage(bitmap, sx, 0, width, bitmap.height, 0, 0, canvas.width, canvas.height);
        bitmap.close();
        return canvas.convertToBlob({ type: 'image/png' });
    };

    const pump = () => {
        while (idle.length && queue.length) {
            const worker = idle.pop();
            const { channel, resolve } = queue.shift();
            read(worker, channel).then(resolve).finally(() => { idle.push(worker); pump(); });
        }
    };

    const read = async (worker, channel) => {
        try {
            const response = await fetch(THUMBNAIL(channel), { credentials: 'omit' });
            // Offline channels redirect to a placeholder; treat that as unreadable.
            if (!response.ok || /404_preview/.test(response.url)) { return null; }
            const { data } = await worker.recognize(await crop(await response.blob()));
            return data.text;
        } catch (error) {
            console.debug('[Twitch Clean] OCR failed', channel, error);
            return null;
        }
    };

    const ocr = channel => {
        const hit = cache.get(channel);
        if (hit && Date.now() - hit.at < CACHE_MS) { return Promise.resolve(hit.text); }
        if (inflight.has(channel)) { return inflight.get(channel); }
        pool = pool || startPool();
        const promise = pool
            .then(() => new Promise(resolve => { queue.push({ channel, resolve }); pump(); }))
            .then(text => {
                cache.set(channel, { at: Date.now(), text });
                return text;
            })
            .finally(() => inflight.delete(channel));
        inflight.set(channel, promise);
        return promise;
    };

    api.runtime.onMessage.addListener((message, _sender, sendResponse) => {
        // 'tibia-ocr-forwarded' comes from the Chrome service worker (chrome/background.js).
        // In Chrome only the forwarded copy is handled here, so each request is read once.
        const expected = location.pathname.endsWith('/offscreen.html') ? 'tibia-ocr-forwarded' : 'tibia-ocr';
        if (message?.type !== expected || typeof message.channel !== 'string' || !/^[a-z0-9_]{1,25}$/i.test(message.channel)) {
            return false;
        }
        ocr(message.channel.toLowerCase()).then(text => sendResponse({ text }));
        return true;
    });
})();
