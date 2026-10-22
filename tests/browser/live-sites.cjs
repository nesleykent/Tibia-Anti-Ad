// Opt-in live verification. Uses a disposable Chrome profile and the real
// unpacked extension; no request interception or injected cosmetic filters.
// Evidence stays in ignored local/, with network URLs reduced to hostnames.
const { chromium } = require('playwright');
const fs = require('node:fs/promises');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
const deep = process.argv.includes('--deep');
const deepPages = {
  'guildstats.eu': '/guild/United', 'hakaimarket.com': '/monsters/dragon',
  'hunt-analyser.com': '/creature_analysis', 'intibia.com': '/bestiary-tracker',
  'tibialife.com.br': '/orcsoberfest-14/', 'tibiamonk.com': '/en/calculators/experience',
  'tibiapal.com': '/hunting', 'tibiavip.app': '/worlds', 'tibiopedia.pl': '/monsters/Cockroach',
};
const requestedPath = process.env.TIBIA_SITE_PATH || '/';
if (!requestedPath.startsWith('/') || requestedPath.startsWith('//') || /[?#]/.test(requestedPath)) {
  throw new Error('Use a public path on the selected site, without query strings');
}
const suffix = deep ? '-deep' : requestedPath === '/' ? '' : '-configured-content-' + requestedPath.replace(/[^a-z0-9]+/gi, '-');
const attempt = (process.env.TIBIA_AUDIT_RUN || '').replace(/[^a-z0-9-]/gi, '-');
const output = path.join(root, 'local/verification/live-sites' + suffix + (attempt ? '-' + attempt : ''));
const sites = [
  'tibiawiki.com.br', 'tibiopedia.pl', 'exevopan.com', 'forum.portaltibia.com.br',
  'guildstats.eu', 'hakaimarket.com', 'hunt-analyser.com', 'intibia.com',
  'portaltibia.com.br', 'tibia.fandom.com', 'tibialife.com.br', 'tibiamonk.com',
  'tibiapal.com', 'tibiaring.com', 'tibiavip.app',
];
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
  await fs.mkdir(output, { recursive: true });
  const profile = await fs.mkdtemp(path.join(output, 'profile-'));
  let context;
  try {
    context = await chromium.launchPersistentContext(profile, {
      executablePath: process.env.CHROME_BETA_BINARY || '/Applications/Google Chrome Beta.app/Contents/MacOS/Google Chrome Beta',
      headless: true, ignoreDefaultArgs: ['--disable-extensions'],
      args: ['--enable-unsafe-extension-debugging'],
    });
    const browserSession = await context.browser().newBrowserCDPSession();
    const browser = await browserSession.send('Browser.getVersion');
    const { id } = await browserSession.send('Extensions.loadUnpacked', {
      path: path.join(root, 'dist/tibia-anti-ad-chrome'),
    });
    const worker = context.serviceWorkers().find(w => w.url().includes(id)) || await context.waitForEvent('serviceworker');
    let results = { date: new Date().toISOString(), browser: browser.product,
      platform: process.platform, extension: id, implementation: 'real extension; no routing or CSS simulation', runs: [] };
    try { results = JSON.parse(await fs.readFile(path.join(output, 'results.json'), 'utf8')); } catch (error) {
      if (error.code !== 'ENOENT') throw error;
    }
    const selected = process.argv.slice(2).filter(arg => arg !== '--deep');
    siteLoop: for (const site of selected.length ? selected : sites) {
      if (!sites.includes(site)) throw new Error('Site outside inventory');
      if (deep && !deepPages[site]) continue;
      const pagePath = deep ? deepPages[site] : requestedPath;
      const previous = results.runs.filter(run => run.site === site);
      if (previous.some(run => run.status >= 400 || run.page?.challenge)
          || previous.some(run => run.width === 390 && run.enabled && !run.error)) continue;
      const pairs = !deep && ['tibiawiki.com.br', 'tibiopedia.pl'].includes(site) ? 5 : 1;
      for (const width of [1440, 390]) {
        // Five cold-cache pairs at desktop; one responsive pair at mobile width.
        for (let pair = 0; pair < (width === 1440 ? pairs : 1); pair++) {
          for (const enabled of pair % 2 ? [true, false] : [false, true]) {
            await worker.evaluate(async enabled => {
              await chrome.storage.local.set({ enabled });
            }, enabled);
            // Wait for the actual service worker to apply the settings to DNR.
            const rulesets = await worker.evaluate(async enabled => {
              for (let i = 0; i < 100; i++) {
                const sets = await chrome.declarativeNetRequest.getEnabledRulesets();
                if (Boolean(sets.length) === enabled) return sets;
                await new Promise(resolve => setTimeout(resolve, 20));
              }
              throw new Error('Extension settings did not reach DNR');
            }, enabled);
            await context.clearCookies();
            const page = await context.newPage();
            await page.setViewportSize({ width, height: 900 });
            const session = await context.newCDPSession(page);
            await session.send('Network.enable');
            await session.send('Network.setCacheDisabled', { cacheDisabled: true });
            await session.send('Performance.enable');
            const hosts = {}, blocked = {};
            let bytes = 0;
            page.on('request', req => {
              try { const host = new URL(req.url()).hostname; hosts[host] = (hosts[host] || 0) + 1; } catch {}
            });
            page.on('requestfailed', req => {
              if (req.failure()?.errorText.includes('BLOCKED_BY_CLIENT')) {
                const host = new URL(req.url()).hostname;
                blocked[host] = (blocked[host] || 0) + 1;
              }
            });
            session.on('Network.loadingFinished', event => { bytes += event.encodedDataLength; });
            await page.addInitScript(() => {
              window.__verificationLongTasks = [];
              new PerformanceObserver(list => {
                for (const entry of list.getEntries()) window.__verificationLongTasks.push(Math.max(0, entry.duration - 50));
              }).observe({ type: 'longtask', buffered: true });
            });
            const run = { site, path: pagePath, width, pair, enabled, rulesets, started: new Date().toISOString() };
            run.scriptErrors = [];
            page.on('pageerror', error => run.scriptErrors.push(error.message.slice(0, 500)));
            let started = Date.now();
            try {
              let response = await page.goto(`https://${site}${pagePath}`, { waitUntil: 'domcontentloaded', timeout: 25000 });
              if (site === 'tibiopedia.pl' && new URL(page.url()).pathname === '/setup') {
                // The site's book artwork owns the selection handlers.
                await page.locator('#flagEn').click();
                await page.locator('#writtingLibrary').click();
                await Promise.all([
                  page.waitForURL(url => url.pathname !== '/setup', { waitUntil: 'domcontentloaded' }),
                  page.locator('#enter_button').click(),
                ]);
              }
              if (response?.status() < 400) {
                // The page-world settings mirror is asynchronous on a fresh
                // origin. Warm it first, then measure a cold HTTP-cache reload.
                await page.waitForFunction(enabled => {
                  try { return JSON.parse(localStorage.getItem('tibia-anti-ad:settings'))?.enabled === enabled; }
                  catch { return false; }
                }, enabled, { timeout: 5000 });
                await session.send('Network.clearBrowserCache');
                for (const host of Object.keys(hosts)) delete hosts[host];
                for (const host of Object.keys(blocked)) delete blocked[host];
                bytes = 0;
                started = Date.now();
                response = await page.goto(`https://${site}${pagePath}`, { waitUntil: 'domcontentloaded', timeout: 25000 });
              }
              run.status = response?.status();
              await sleep(5000);
              await page.mouse.wheel(0, 600);
              await sleep(3000);
              run.page = await page.evaluate(() => ({
                title: document.title, bodyCharacters: document.body?.innerText.length || 0,
                rootChildren: document.querySelector('#root')?.childElementCount,
                rootDisplay: document.querySelector('#root') ? getComputedStyle(document.querySelector('#root')).display : null,
                headings: [...document.querySelectorAll('h1,h2')].map(e => e.innerText).slice(0, 8),
                links: document.querySelectorAll('a[href]').length,
                inputs: document.querySelectorAll('input,select,textarea').length,
                adIntentRoots: [...document.querySelectorAll('[id^="google-anno"]')].map(e => ({
                  id: e.id, parent: e.parentElement?.tagName, display: getComputedStyle(e).display,
                })),
                totalBlockingTime: (window.__verificationLongTasks || []).reduce((a, b) => a + b, 0),
                challenge: /just a moment|verify you are human|access denied|checking your browser|performing security verification/i.test(document.title + ' ' + document.body?.innerText.slice(0, 600)),
              }));
              if (pair === 0) {
                await page.screenshot({ path: path.join(output, `${site}-${width}-${enabled ? 'filtered' : 'baseline'}.png`) });
              }
            } catch (error) {
              run.error = error.message.split('\n')[0];
              run.finalPath = new URL(page.url()).pathname;
              run.failureTitle = await page.title();
              await page.screenshot({ path: path.join(output, `${site}-${width}-error.png`) }).catch(() => {});
            }
            run.elapsedMs = Date.now() - started;
            run.transferredBytes = bytes;
            run.requests = Object.values(hosts).reduce((a, b) => a + b, 0);
            run.hosts = hosts;
            run.blockedByClient = blocked;
            results.runs.push(run);
            await fs.writeFile(path.join(output, 'results.json'), JSON.stringify(results, null, 2) + '\n');
            console.log(JSON.stringify({ site, width, pair, enabled, status: run.status, characters: run.page?.bodyCharacters,
              blocked: Object.values(blocked).reduce((a, b) => a + b, 0), error: run.error }));
            await page.close();
            // A challenge is not a measured site: do not repeat it or score it.
            if (run.status >= 400 || run.error || run.page?.challenge) continue siteLoop;
          }
        }
      }
    }
    if (results.runs.some(run => run.error || run.status >= 400 || run.page?.challenge || run.page?.bodyCharacters === 0)) process.exitCode = 2;
  } finally {
    await context?.close();
    await fs.rm(profile, { recursive: true, force: true });
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
