# Privacy policy

AI Limits does not collect, store or send any information about you to its author or to
any third party. There is no analytics, telemetry, crash reporting or advertising.

This program will not transfer any information to other networked systems unless
specifically requested by the user or the person installing or operating it. The only
network requests it makes are to the services you already use, to read your own usage:

| Service | Contacted | What is sent | Why |
|---|---|---|---|
| Claude | `api.anthropic.com`, `platform.claude.com` | Your Claude Code sign-in token | Read your usage limits; renew an expired sign-in (only if "Keep sign-ins fresh" is on) |
| ChatGPT / Codex | `chatgpt.com`, `auth.openai.com` | Your Codex sign-in token | Read your Codex limits; renew an expired sign-in |
| Antigravity | Antigravity's own server on your PC (`127.0.0.1`), which talks to Google as it normally does | Antigravity's saved sign-in, used by Antigravity's server itself | Read your quota |

Each of these services handles the request under its own privacy policy
([Anthropic](https://www.anthropic.com/legal/privacy),
[OpenAI](https://openai.com/policies/privacy-policy),
[Google](https://policies.google.com/privacy)).

## What AI Limits reads and writes on your PC

- **Reads** the sign-ins those apps already saved: `%USERPROFILE%\.claude\.credentials.json`,
  `%USERPROFILE%\.codex\auth.json` and Antigravity's entry in Windows Credential Manager.
- **Writes** renewed sign-ins back to the Claude Code and Codex files, only when
  "Keep sign-ins fresh" is on (you choose this during install and in Settings).
- **Stores** its own settings and the last fetched numbers in `%APPDATA%\AILimits`, and extra
  ChatGPT accounts you add in `%APPDATA%\AILimits\chatgpt`.

## Changes to your system

All of these are shown and can be turned off in the installer:

- Installs to `%LOCALAPPDATA%\Programs\AILimits` (no admin rights).
- Optional: a Start menu shortcut.
- Optional: a "start with Windows" entry (`HKCU\Software\Microsoft\Windows\CurrentVersion\Run`).

**Uninstall:** right-click the strip, choose **Uninstall AI Limits…**. This removes the
program, the shortcut, the startup entry and `%APPDATA%\AILimits`.
