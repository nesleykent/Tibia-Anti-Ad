(async () => {
  const CONFIG = {
    delay: 1100,
    maxScrolls: 1000,
    idleLimit: 20,
    filename: (() => {
      const now = new Date();
      const pad = (n) => String(n).padStart(2, "0");

      const timestamp =
        [now.getFullYear(), pad(now.getMonth() + 1), pad(now.getDate())].join(
          "-",
        ) +
        "-" +
        [
          pad(now.getHours()),
          pad(now.getMinutes()),
          pad(now.getSeconds()),
        ].join("-");

      return `twitch-tibia-streams-${timestamp}.json`;
    })(),
  };

  const streams = new Map();
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

  const languages = {
    português: "Português",
    portugues: "Português",
    english: "English",
    inglês: "English",
    español: "Español",
    spanish: "Español",
    polski: "Polski",
    deutsch: "Deutsch",
    français: "Français",
    italiano: "Italiano",
    türkçe: "Türkçe",
    русский: "Русский",
    日本語: "日本語",
    한국어: "한국어",
    中文: "中文",
  };

  function getScroller() {
    const candidates = [
      document.scrollingElement,
      ...document.querySelectorAll(
        "main, [class*='scroll'], [class*='Scroll']",
      ),
    ].filter(Boolean);

    const scrollable = candidates.filter((el) => {
      const style = getComputedStyle(el);

      return (
        el.scrollHeight > el.clientHeight + 100 &&
        (el === document.scrollingElement ||
          /auto|scroll/.test(style.overflowY))
      );
    });

    return (
      scrollable.sort(
        (a, b) =>
          b.scrollHeight - b.clientHeight - (a.scrollHeight - a.clientHeight),
      )[0] || document.scrollingElement
    );
  }

  function parseViewers(text) {
    const match = text.match(
      /([\d.,]+)\s*([kKmM]?)\s*(?:viewers|espectadores)/i,
    );

    if (!match) return null;

    const value = Number(match[1].replace(",", "."));
    const multiplier =
      {
        k: 1000,
        m: 1000000,
      }[match[2].toLowerCase()] || 1;

    return Math.round(value * multiplier);
  }

  function collect() {
    const before = streams.size;

    const links = document.querySelectorAll(
      'a[data-a-target="preview-card-image-link"], a[href^="/"]',
    );

    links.forEach((link) => {
      const href = link.getAttribute("href");
      const match = href?.match(/^\/([a-zA-Z0-9_]+)\/?$/);

      if (!match) return;

      const channel = match[1].toLowerCase();

      const excluded = new Set([
        "directory",
        "settings",
        "downloads",
        "subscriptions",
        "inventory",
        "wallet",
        "search",
        "friends",
        "login",
        "signup",
        "videos",
        "drops",
        "p",
      ]);

      if (excluded.has(channel)) return;

      const card =
        link.closest("article") ||
        link.closest('[data-a-target*="preview-card"]') ||
        link.parentElement?.parentElement?.parentElement;

      if (!card) return;

      const details = card.innerText?.trim() || "";

      if (!details || details.length < 15) return;

      const lines = details
        .split("\n")
        .map((x) => x.trim())
        .filter(Boolean);

      const language =
        lines.map((x) => languages[x.toLowerCase()]).find(Boolean) || null;

      const title =
        card
          .querySelector('[data-a-target="preview-card-title-link"]')
          ?.textContent?.trim() ||
        lines[0] ||
        null;

      const tags = [...card.querySelectorAll('[data-a-target="tw-tag"]')].map(
        (x) => x.textContent.trim(),
      );

      const item = {
        channel,
        url: `https://www.twitch.tv/${channel}`,
        title,
        language,
        viewers: parseViewers(details),
        tags,
        details,
      };

      const previous = streams.get(channel);

      if (!previous || details.length > previous.details.length) {
        streams.set(channel, item);
      }
    });

    return streams.size - before;
  }

  function download() {
    const data = [...streams.values()];

    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });

    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");

    a.href = url;
    a.download = CONFIG.filename;

    document.body.appendChild(a);
    a.click();
    a.remove();

    setTimeout(() => URL.revokeObjectURL(url), 10000);

    console.log(`✅ ${data.length} channels exported.`);
  }

  console.log("🚀 Starting collection...");

  let idle = 0;
  let previousPosition = -1;

  collect();

  for (let i = 0; i < CONFIG.maxScrolls; i++) {
    const scroller = getScroller();
    const before = streams.size;

    const step = Math.max(
      window.innerHeight * 0.85,
      scroller.clientHeight * 0.85,
    );

    scroller.scrollTop += step;

    await sleep(CONFIG.delay);

    const added = collect();
    const position = scroller.scrollTop;

    if (added === 0 && Math.abs(position - previousPosition) < 5) {
      idle++;
    } else {
      idle = 0;
    }

    previousPosition = position;

    console.log(
      `[${i + 1}] ${streams.size} channels | ` +
        `+${added} new | ` +
        `scroll=${Math.round(position)}`,
    );

    if (idle >= CONFIG.idleLimit) {
      console.log("🏁 End of list detected.");
      break;
    }
  }

  download();

  console.log("✅ Collection complete.");
})();
