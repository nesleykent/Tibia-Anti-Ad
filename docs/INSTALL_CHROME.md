# Install Tibia Anti-Ad in Chrome

This guide is for Chrome on a Windows, Mac or Linux computer. **The main method uses buttons and folders — no terminal or programming is needed.** Chrome on a phone or tablet cannot follow this installation method.

Tibia Anti-Ad is currently an experimental extension installed from a downloaded folder. It does not update automatically.

## 1. Download

**[Download Tibia Anti-Ad for Chrome (.zip)](https://github.com/nesleykent/Tibia-Anti-Ad/releases/download/v1.0.0-alpha.2/tibia-anti-ad-chrome.zip)**

Click the link above and save **`tibia-anti-ad-chrome.zip`**. No GitHub account or terminal is needed. This is the prepared Chrome package, ready to extract and load.

[Release details and checksum](https://github.com/nesleykent/Tibia-Anti-Ad/releases/tag/v1.0.0-alpha.2).

## 2. Extract the ZIP and keep the folder

A ZIP file is a compressed folder. Chrome needs its extracted contents.

- **Windows:** right-click the ZIP, choose **Extract All…**, then **Extract**.
- **Mac:** double-click the ZIP. Finder creates an extracted folder.
- **Linux:** open the ZIP with your archive manager and choose **Extract**.

The ZIP contains a folder named **`tibia-anti-ad-chrome`**. Move that folder somewhere permanent, such as **Documents**. Do this **before** loading it in Chrome.

Open the folder. You should see a file named **`manifest.json`** alongside files such as **`background.js`** and **`popup.html`**:

```text
Documents/
└── tibia-anti-ad-chrome/       ← Select this folder in the next step
    ├── manifest.json
    ├── background.js
    ├── popup.html
    ├── icons/
    └── …other extension files
```

If you see another folder instead, open it until you reach `manifest.json`. You do not need to open or edit that file. Keep all the other files together with it.

## 3. Load the folder in Chrome

1. Open Chrome.
2. Type **`chrome://extensions`** in the address bar and press **Enter**. Copy or type this address; ordinary web pages cannot open it as a clickable link.
3. Turn on **Developer mode**, near the top of the page.
4. Click **Load unpacked**.
5. Select the **folder that contains `manifest.json`** from step 2, then confirm your selection. Choose the folder, not the ZIP or the file itself.
6. Find the **Tibia Anti-Ad** card on the Extensions page. Its switch should be on.

Button names may be translated if your Chrome uses another language. A computer managed by an employer or school may not allow Developer mode.

Chrome continues reading the extension from this folder. **Keep it in the same place after installation.** You can delete the downloaded ZIP once extraction is complete, but keep the extracted folder.

## 4. Open its controls

1. Click Chrome's **Extensions** button, usually shown as a puzzle piece next to the address bar.
2. Find **Tibia Anti-Ad** and click its **Pin** button to keep the icon visible.
3. Click the Tibia Anti-Ad icon to open its settings.
4. Use the top **Tibia Anti-Ad** switch to pause or resume the extension. Individual switches let you choose Twitch features and fansites.
5. Reload any Twitch or supported fansite tabs that were already open before installation.

Review the site's access controls under **Details** on the extension's Chrome card if Chrome asks about access. The extension needs access to Twitch and the supported fansites to filter their pages.

To try stream filtering, open the [Tibia category on Twitch](https://www.twitch.tv/directory/category/tibia). If a stream is hidden, the extension's **Hidden on this page** section explains the decision; **Show** restores it. Uncertain streams stay visible.

The enabled Chrome card and a working settings panel confirm installation. They do not guarantee that every ad will be removed: live Twitch video-ad replacement is experimental and can affect playback during an ad break.

## Update later

1. Download and extract a newer Chrome package by following steps 1–2.
2. Replace the **contents** of your existing **`tibia-anti-ad-chrome`** folder with the new package's contents. Keep the installed folder's name and location, and make sure `manifest.json` is directly inside it. Remove old package files first so obsolete files are not left behind.
3. Open **`chrome://extensions`** and click the **Reload** button on the Tibia Anti-Ad card. It is usually shown as a circular arrow.
4. Reload Twitch and fansite tabs.

Reloading the existing installation keeps its stored settings. Removing the extension and installing it again can reset them.

## Pause or remove it

- **Pause everything:** switch Tibia Anti-Ad off in its settings or on its Chrome card, then reload affected pages.
- **Fix a problem on one fansite:** switch that site off in the extension's settings, then reload the page.
- **Uninstall:** open **`chrome://extensions`**, click **Remove** on Tibia Anti-Ad, confirm, and reload affected pages. You can then delete its extracted folder.

If Source quality was enabled on Twitch, select your preferred video quality in the Twitch player afterward.

## If something goes wrong

| What you see | What to do |
| --- | --- |
| “Manifest file is missing or unreadable” | Extract the ZIP first. Choose the folder directly containing `manifest.json`, not its parent folder. |
| An error mentions Safari settings or `background.scripts` | You selected the shared source folder instead of the prepared Chrome package. Use the direct Chrome ZIP download at the top of this page. |
| No Developer mode or Load unpacked button | Check that you are using desktop Chrome. A managed computer may restrict extension installation; contact its administrator. |
| The extension cannot find its files after a restart | Its installed folder may have been moved or deleted. Restore the folder to its original location, or load the extracted package again. |
| The settings open but a page is unchanged | Reload the page, check that the relevant feature/site switch is on, and review the extension's site access under Details. |
| A legitimate Tibia stream disappears | Use **Show** under **Hidden on this page**, or turn off **Hide other games**. |
| Video playback or a fansite breaks | Pause the affected feature and reload. Report the page, browser version and steps through [GitHub issues](https://github.com/nesleykent/Tibia-Anti-Ad/issues). |

## Optional: prepare the Chrome folder yourself

Use this route only if you prefer building from source. It requires **Python 3.11 or newer**; Node.js is not needed just to build this package.

1. On the [repository page](https://github.com/nesleykent/Tibia-Anti-Ad), choose **Code → Download ZIP**, then extract it. You can also use an existing clone.
2. Open a terminal in the extracted project folder — the folder containing `README.md`, `tools` and `extension`.
3. Run the command for your computer:

   **Mac / Linux**

   ```sh
   python3 tools/build_chrome_extension.py
   ```

   **Windows**

   ```powershell
   py -3 tools/build_chrome_extension.py
   ```

   If Windows uses `python` instead of the `py` launcher, run `python tools/build_chrome_extension.py` with Python 3.11 or newer.

4. The command creates **`dist/tibia-anti-ad-chrome`** inside the project folder.
5. Continue at **step 3** above and select that generated folder. Keep the project folder in place while the extension is installed.

The shared **`extension/src`** folder is not the prepared Chrome package. After source updates, run the build command again, reload the extension in Chrome, then reload affected pages.

## References

- [Chrome's official instructions for loading a local extension](https://developer.chrome.com/docs/extensions/get-started/tutorial/hello-world#load-unpacked).
- [Download and release details](https://github.com/nesleykent/Tibia-Anti-Ad/releases/tag/v1.0.0-alpha.2).
- [Feature details and known limitations](../extension/README.md).
