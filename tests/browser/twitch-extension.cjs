// Real unpacked Chrome extension: content-world download and popup controls.
const {chromium} = require('playwright');
const fs = require('node:fs/promises');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../..');
const output = path.join(root, 'local/verification');
(async () => {
    await fs.mkdir(output, {recursive:true});
    const profile = await fs.mkdtemp(path.join(output, 'diagnostics-profile-'));
    let context;
    try {
        context = await chromium.launchPersistentContext(profile, {
            executablePath: process.env.CHROME_BETA_BINARY || '/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta',
            headless:true, ignoreDefaultArgs:['--disable-extensions'], args:['--enable-unsafe-extension-debugging'],
            acceptDownloads:true, viewport:{width:1280,height:800},
        });
        const cdp = await context.browser().newBrowserCDPSession();
        const {id} = await cdp.send('Extensions.loadUnpacked', {path:path.join(root,'dist/tibia-anti-ad-chrome')});
        const worker = context.serviceWorkers().find(w => w.url().includes(id)) || await context.waitForEvent('serviceworker');
        const page = await context.newPage();
        await page.route('https://www.twitch.tv/**', route => route.fulfill({contentType:'text/html',body:'<body><div style="display:flex" id="grid"></div></body>'}));
        await page.goto('https://www.twitch.tv/directory/category/tibia');
        await page.evaluate(() => {
            for (let i = 0; i < 6; i++) {
                const cell = document.createElement('section');
                const article = document.createElement('article');
                article.innerHTML = `<a data-a-target="preview-card-channel-link" href="/fixture${i}"><h4>truncated</h4></a>`;
                article.__reactFiberFixture = {memoizedProps:{channelLogin:`fixture${i}`, title:(i % 2 ? 'Hunt bosses ' : 'RubinOT ')+'Full title '.repeat(35)+'END', currentViewerCount:3747,
                    tagListProps:{freeformTags:[{name:'Português'},{name:'Exact tag'}]}}};
                cell.append(article); document.querySelector('#grid').append(cell);
            }
        });
        await page.waitForFunction(() => document.querySelectorAll('article[data-tibia-private-result]').length === 6);
        const tabId = await worker.evaluate(async () => (await chrome.tabs.query({url:'https://www.twitch.tv/directory/category/tibia'}))[0].id);
        const data = await worker.evaluate(tab => chrome.tabs.sendMessage(tab,{type:'tibia-anti-ad:tibia-diagnostics'}),tabId);
        assert.equal(data.streams.length,6);
        assert.ok(data.streams.every(r => r.title.endsWith('END') && r.viewers === 3747));
        await page.evaluate(() => {
            const article = document.querySelector('article');
            article.__reactFiberFixture.memoizedProps.currentViewerCount = 4501;
            article.querySelector('h4').textContent = 'viewer count updated';
        });
        await page.waitForFunction(() => JSON.parse(document.querySelector('article').getAttribute('data-twitch-clean-meta')).viewers === 4501);
        const updated = await worker.evaluate(tab => chrome.tabs.sendMessage(tab,{type:'tibia-anti-ad:tibia-diagnostics'}),tabId);
        assert.equal(updated.streams[0].viewers,4501);
        await worker.evaluate(() => chrome.storage.local.set({tibiaMode:'bottom',tibiaThreshold:0.5}));
        await page.waitForFunction(() => document.querySelector('section').style.order === '3');
        const downloaded = page.waitForEvent('download');
        assert.equal((await worker.evaluate(tab => chrome.tabs.sendMessage(tab,{type:'tibia-anti-ad:export-diagnostics'}),tabId)).ok,true);
        await (await downloaded).saveAs(path.join(output,'chrome-extension-diagnostics.json'));
        assert.equal(JSON.parse(await fs.readFile(path.join(output,'chrome-extension-diagnostics.json'),'utf8')).streams.length,6);
        // Open the real action popup, so active-tab discovery and UI event wiring
        // use Chrome APIs rather than a mocked popup environment.
        await worker.evaluate(() => chrome.action.openPopup());
        const targets = (await cdp.send('Target.getTargets')).targetInfos;
        const popupTarget = targets.find(t => t.url === `chrome-extension://${id}/popup.html`);
        assert.ok(popupTarget, 'real action popup must open');
        const {sessionId} = await cdp.send('Target.attachToTarget', {targetId:popupTarget.targetId, flatten:false});
        let sequence = 0;
        const pending = new Map();
        cdp.on('Target.receivedMessageFromTarget', event => {
            if (event.sessionId !== sessionId) return;
            const reply = JSON.parse(event.message);
            if (reply.id && pending.has(reply.id)) { pending.get(reply.id)(reply); pending.delete(reply.id); }
        });
        const send = async (method, params = {}) => {
            const callId = ++sequence;
            const response = new Promise(resolve => pending.set(callId, resolve));
            await cdp.send('Target.sendMessageToTarget', {sessionId, message:JSON.stringify({id:callId, method, params})});
            const reply = await response;
            assert.ok(!reply.error, JSON.stringify(reply.error));
            return reply.result;
        };
        const evaluate = async expression => {
            const result = await send('Runtime.evaluate', {expression, returnByValue:true, awaitPromise:true, userGesture:true});
            assert.ok(!result.exceptionDetails, JSON.stringify(result.exceptionDetails));
            return result.result.value;
        };
        await evaluate(`new Promise(resolve => { const poll = () => document.body.classList.contains('loading') ? setTimeout(poll, 20) : resolve(); poll(); })`);
        assert.equal(await evaluate(`document.querySelector('#tibiaMode').value`),'bottom');
        await evaluate(`const input = document.querySelector('#tibiaThreshold'); input.value = '60'; input.dispatchEvent(new Event('change', {bubbles:true}));`);
        assert.equal(await worker.evaluate(async () => (await chrome.storage.local.get('tibiaThreshold')).tibiaThreshold),0.6);
        await evaluate(`const mode = document.querySelector('#tibiaMode'); mode.value='show'; mode.dispatchEvent(new Event('change', {bubbles:true}));`);
        await page.waitForFunction(() => !document.querySelector('[data-twitch-clean-hidden]') && !document.querySelector('section[style*="order"]'));
        const screenshot = async (anchor, filename) => {
            await evaluate(`document.querySelector('${anchor}').scrollIntoView()`);
            const {data} = await send('Page.captureScreenshot');
            await fs.writeFile(path.join(output,filename),Buffer.from(data,'base64'));
        };
        await screenshot('#h-tibia','diagnostics-popup-controls.png');
        await screenshot('#h-diagnostics','diagnostics-popup-export.png');
        const popupDownload = page.waitForEvent('download');
        await evaluate(`document.querySelector('#export-button').click()`);
        await (await popupDownload).saveAs(path.join(output,'chrome-popup-diagnostics.json'));
        assert.equal(JSON.parse(await fs.readFile(path.join(output,'chrome-popup-diagnostics.json'),'utf8')).mode,'show');
        console.log('PASS real Chrome extension: full React metadata, isolated content download, real popup modes, threshold persistence and popup export');
    } finally {
        try { await context?.close(); }
        finally { await fs.rm(profile, {recursive:true, force:true}); }
    }
})().catch(error => {console.error(error);process.exit(1)});
