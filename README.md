# NieR:Automata cheat code on keyboard and mouse

A step-by-step guide (with screenshots) for entering NieR:Automata's final cheat code on PC using a keyboard
and mouse, via a virtual Xbox controller. Open `index.html` in a browser to read it locally.

## Before you publish

1. Open `index.html` in a text editor and search for these two placeholders, then replace them:
   - `YOUR_VIDEO_ID` (appears once, in the YouTube link at the top)
   - `YOUR_NAME` (appears once, in the link text)
2. Search for `TODO (author)` and add a screenshot of your finished **Button to Axis** mapping
   (save it in `images/` and add an `<img>` tag, or copy the figure markup used elsewhere on the page).
3. Check every sentence that says what you did (Steam Input, Special K, the Custom controls swap) matches
   what you actually did.

## Host it free on GitHub Pages

1. Create a new public repository on GitHub, for example `nier-automata-cheat-keyboard`.
2. Upload everything in this folder (`index.html`, `images/`, `tools/`, `.nojekyll`, `README.md`) to the
   top level of the repository. Keep the folder structure as it is, or the images will not load.
3. In the repository, open **Settings**, then **Pages**. Under **Build and deployment**, set the source to
   **Deploy from a branch**, choose the `main` branch and the `/ (root)` folder, and click **Save**.
4. After a minute the site is live at `https://YOUR-GITHUB-USERNAME.github.io/REPOSITORY-NAME/`.
5. Put that link in your YouTube description.

## Contents

- `index.html` is the whole guide: dark theme by default, with a toggle for a light theme.
- `images/` holds the screenshots (WebP).
- `tools/` holds three read-only Python scripts used to inspect the game's cheat code.

Third-party tools (ViGEmBus, UCR, Interception) are linked to their official pages and are not included here.
