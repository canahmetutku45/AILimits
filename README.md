# AI Limits

Your AI plan limits, live on the Windows taskbar.

AI Limits adds a small strip to the left of your taskbar that shows how much of each
AI subscription you've used. Click it to open a panel with every limit, its reset
time and your plan.

## Download

**[⬇ Download AILimits.exe](../../releases/latest/download/AILimits.exe)** (Windows 10/11,
no admin rights needed), or see all versions on the [Releases page](../../releases).

## Before you install (known limitations in this version)

- **Your taskbar must be at the bottom of the screen.** If it's on the left, right or top,
  the strip and the panel end up in the wrong place. This will be fixed in a later version.
- **Turn off Windows Widgets (the weather on the taskbar).** AI Limits sits on the left of
  the taskbar, exactly where the weather/Widgets button is, so the two overlap.
  Go to **Settings → Personalization → Taskbar → Taskbar items** and switch **Widgets** off.
- Works best with taskbar icons **centered** (the Windows 11 default), which leaves the left
  side free for the strip.

| Service | What you see | What it needs (once) |
|---|---|---|
| Claude | 5-hour session and weekly limits (Opus/Sonnet separately when they apply) | Signed in to Claude Code |
| ChatGPT / Codex | 5-hour and weekly Codex limits, for several accounts | Signed in with the Codex CLI |
| Antigravity | Separate quotas for Gemini models, Claude & GPT models and Gemini Argon | Signed in to Antigravity |

**None of the apps need to be open.** AI Limits refreshes everything in the background
using the sign-ins already on your PC:

- **Claude:** reads the usage API with Claude Code's sign-in. When that sign-in expires,
  AI Limits renews it the same way Claude Code does and saves it back, so Claude Code keeps
  working with it too.
- **ChatGPT:** same for the Codex sign-in. Extra accounts you add are kept in AI Limits'
  own folder.
- **Antigravity:** if Antigravity is open, AI Limits asks its running server. If not, it
  starts Antigravity's own server invisibly for about 2 seconds every 5 minutes, using your
  saved sign-in, reads the quota and stops it again.

Claude is checked every 3 minutes, ChatGPT every 90 seconds and Antigravity every minute
(every 5 minutes when Antigravity is closed). If a service says "too many requests",
AI Limits keeps the last numbers and waits 10 minutes before asking again.

Services you don't use are simply hidden.

## Install

1. Double-click `AILimits.exe`.
2. If Windows shows "Windows protected your PC", click **More info → Run anyway**.
   The app isn't code-signed yet (see [Code signing policy](#code-signing-policy)).
3. The installer shows what it will change and lets you turn each item off:
   **Start with Windows**, **Start menu shortcut** and **Keep sign-ins fresh** (renew
   expired Claude Code / Codex sign-ins). It installs to `%LOCALAPPDATA%\Programs\AILimits`
   and doesn't need admin rights.
4. A short tour opens on first run. You can replay it any time with right-click → **Show tour**.

To update, double-click the new `AILimits.exe`. It closes the old version and replaces it.

## Using it

- **Click the strip** to open or close the panel. Click outside it or press Esc to close.
- **Hover** over the strip to pause it. **Scroll the mouse wheel** over it to flip through limits.
- **Panel controls:**
  - **Theme**: dark or light panel.
  - **Motion**: turns on the spring-in panel, counting numbers, sliding strip and liquid gauges.
  - **Taskbar**: pick the strip style.
    - *Cycle*: one limit at a time, switching every 10 seconds.
    - *Rings*: one ring per service with its logo inside. Each ring shows whichever
      limit will run out first.
- **Click a gauge** at the top of the panel to jump to that service. **Click a card title**
  to collapse it.
- **Settings (gear icon):**
  - **Style preset:** *Minimal* (monochrome, Geist Mono), *Modern* (dark dashboard, Geist),
    *Kawaii* (pink and pastel, Fredoka, a chibi mascot who blinks and gets flustered when a
    limit runs high), *Goofy* (loud cartoon colors, Chewy, a googly-eyed blob whose eyes follow
    your mouse). Click the mascot to poke it.
  - **Appearance:** dark or light.
  - **Font:** Geist, Geist Mono, Fredoka, Chewy or Segoe UI, mixed with any preset.
  - **Motion:** Off, Calm, Lively or Wild. Controls the panel's spring, the title animation,
    the liquid waves and how far the cards bounce.
  - **Liquid gauges**, **Mascot**, **Taskbar strip** style and **Switch every** 5/10/20/30 s.
  - **Start with Windows** and **Keep sign-ins fresh**.
  - **Reset to preset defaults.**
- **Right-click** for refresh, ChatGPT accounts, start with Windows, the tour, quit and uninstall.
- **Adding a second ChatGPT account:** right-click → *Add ChatGPT account…* → sign in with
  that account in the browser. If the browser is already signed in to another account, use a
  private window.

## Uninstall

Right-click the strip and choose **Uninstall AI Limits…**. This removes the program, the
Start menu shortcut, the startup entry and its settings folder.

## Privacy

This program will not transfer any information to other networked systems unless
specifically requested by the user or the person installing or operating it. Your sign-in
tokens are read only on your own PC and are sent only to the service they belong to:
Anthropic, OpenAI, or the Antigravity app running locally. There is no analytics or
telemetry. Details: [Privacy policy](PRIVACY.md).

## Code signing policy

Free code signing provided by [SignPath.io](https://signpath.io), certificate by
[SignPath Foundation](https://signpath.org).
*(Application pending. Until it's approved, releases are unsigned.)*

- Every `AILimits.exe` on the Releases page is built by
  [GitHub Actions](../../actions/workflows/build.yml) from the tagged source in this repository.
- Committers and reviewers: [canahmetutku45](https://github.com/canahmetutku45)
- Approvers: [canahmetutku45](https://github.com/canahmetutku45)
- Privacy policy: [PRIVACY.md](PRIVACY.md)

## For developers

- Source: `ai_limits.pyw` (data, windows), `render.py` (all drawing, with Pillow) and
  `mascots.py` (the preset mascots, original artwork drawn from shapes).
- Build with `build.bat`. The output is `dist\AILimits.exe`.
- Fonts in `assets/`: Geist and Geist Mono (SIL OFL), Fredoka (SIL OFL), Chewy (Apache 2.0).
  Their license files are next to them.
- The Claude and OpenAI logos come from Simple Icons. The Antigravity logo comes from the
  Antigravity app. All of them are trademarks of their owners and are used only to label
  each service.
