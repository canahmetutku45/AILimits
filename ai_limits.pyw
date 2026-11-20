"""AI Limits - AI plan limits on the Windows taskbar.

Shows Claude, Codex (ChatGPT) and Antigravity usage limits as a strip on the
left of the taskbar, with a detailed panel on click.

Dev:    pythonw ai_limits.pyw
Build:  build.bat  ->  dist\\AILimits.exe (installs itself on first run)
"""
import glob
import json
import os
import sys
import threading
import time
import tkinter as tk
import urllib.request
from datetime import datetime, timezone

HOME = os.path.expanduser("~")
APP_DIR = os.path.join(os.environ.get("APPDATA", HOME), "AILimits")
STATE_FILE = os.path.join(APP_DIR, "state.json")
CACHE_FILE = os.path.join(APP_DIR, "cache.json")
REFRESH_SEC = 60
HTTP_TIMEOUT = 15
APP_NAME = "AI Limits"
EXE_NAME = "AILimits.exe"
INSTALL_DIR = os.path.join(os.environ.get("LOCALAPPDATA", HOME), "Programs", "AILimits")
# v1 was installed as "AI Limitleri": cleaned up on install
OLD_INSTALL_DIR = os.path.join(os.environ.get("LOCALAPPDATA", HOME), "Programs", "AILimitleri")
FROZEN = getattr(sys, "frozen", False)
# Renew expired Claude Code / Codex sign-ins and save them back. The user
# chooses this in the installer and in Settings ("Keep sign-ins fresh").
RENEW_SIGNINS = True


class NotInstalled(Exception):
    """The service is not used on this PC: hide its section."""

BG = "#16181d"
PANEL = "#1e2128"
TRACK = "#2b2f38"
FG = "#e6e8eb"
MUTED = "#8b919c"
GREEN, AMBER, RED = "#3fb47a", "#e0a43a", "#e05252"
FONT = "Segoe UI"


# ----------------------------------------------------------------- yardimcilar
def http_json(url, headers=None, body=None, timeout=HTTP_TIMEOUT):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def to_epoch(v):
    """ISO metni, saniye ya da milisaniye -> epoch saniye."""
    if v is None or v == "":
        return None
    if isinstance(v, (int, float)):
        return v / 1000 if v > 1e11 else v
    try:
        s = str(v).replace("Z", "+00:00")
        if "." in s:  # Python 3.10 en fazla 6 haneli kesir kabul eder
            head, rest = s.split(".", 1)
            n = 0
            while n < len(rest) and rest[n].isdigit():
                n += 1
            frac, tz = rest[:n], rest[n:]
            s = f"{head}.{frac[:6]}{tz}"
        return datetime.fromisoformat(s).timestamp()
    except Exception:
        return None


def fmt_reset(ts):
    if not ts:
        return ""
    left = int(ts - time.time())
    if left <= 0:
        return "resetting"
    d, rem = divmod(left, 86400)
    h, rem = divmod(rem, 3600)
    m = rem // 60
    if d:
        return f"{d}d {h}h"
    if h:
        return f"{h}h {m}m"
    return f"{m}m"


def bar(label, used_pct, reset_ts=None, note="", group=""):
    return {"label": label, "pct": max(0.0, min(100.0, float(used_pct))),
            "reset": reset_ts, "note": note, "group": group}


# -------------------------------------------------------------------- Claude
CLAUDE_KIND_NAMES = {
    "session": "5-hour session",
    "weekly_all": "Weekly · all models",
    "weekly_opus": "Weekly · Opus",
    "weekly_sonnet": "Weekly · Sonnet",
    "weekly_fable": "Weekly · Fable",
}
CLAUDE_KEY_NAMES = {
    "five_hour": "5-hour session",
    "seven_day": "Weekly · all models",
    "seven_day_opus": "Weekly · Opus",
    "seven_day_sonnet": "Weekly · Sonnet",
    "seven_day_oauth_apps": "Weekly · connected apps",
    "seven_day_cowork": "Weekly · Cowork",
}


CLAUDE_TOKEN_URL = "https://platform.claude.com/v1/oauth/token"
CLAUDE_CLIENT_ID = "9d1c250a-e61b-44d9-88ed-5944d1962f5e"   # Claude Code OAuth client


def _write_json_atomic(path, obj):
    tmp = path + ".ailimits.tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
    os.replace(tmp, path)


def _refresh_claude(path):
    """Refresh the Claude Code sign-in exactly like Claude Code does, and write
    the new tokens back to the same file, so Claude Code keeps working with them
    (the same way several Claude Code windows share one sign-in)."""
    full = json.load(open(path, encoding="utf-8"))
    oauth = full["claudeAiOauth"]
    scopes = oauth.get("scopes") or []
    if isinstance(scopes, str):
        scopes = scopes.split()
    try:
        new = http_json(CLAUDE_TOKEN_URL, {"Content-Type": "application/json",
                                           "User-Agent": "ai-limits-widget/2.1"},
                        {"grant_type": "refresh_token", "refresh_token": oauth["refreshToken"],
                         "client_id": CLAUDE_CLIENT_ID, "scope": " ".join(scopes)})
    except Exception:
        raise RuntimeError("Claude sign-in expired — run Claude Code once to sign in")
    # re-read right before writing: another Claude Code window may have refreshed
    full = json.load(open(path, encoding="utf-8"))
    oauth = full["claudeAiOauth"]
    oauth["accessToken"] = new["access_token"]
    if new.get("refresh_token"):
        oauth["refreshToken"] = new["refresh_token"]
    oauth["expiresAt"] = int((time.time() + int(new.get("expires_in", 3600))) * 1000)
    if new.get("refresh_token_expires_in"):
        oauth["refreshTokenExpiresAt"] = int(
            (time.time() + int(new["refresh_token_expires_in"])) * 1000)
    _write_json_atomic(path, full)
    return oauth


def fetch_claude():
    path = os.path.join(HOME, ".claude", ".credentials.json")
    if not os.path.exists(path):
        raise NotInstalled()
    oauth = json.load(open(path, encoding="utf-8"))["claudeAiOauth"]
    exp = oauth.get("expiresAt")
    if exp and exp / 1000 < time.time() + 300:
        if not RENEW_SIGNINS:
            raise RuntimeError("Claude sign-in expired — open Claude Code once")
        oauth = _refresh_claude(path)       # no need to open Claude Code
    data = http_json(
        "https://api.anthropic.com/api/oauth/usage",
        {"Authorization": "Bearer " + oauth["accessToken"],
         "anthropic-beta": "oauth-2025-04-20",
         "User-Agent": "ai-limits-widget/1.0"})
    bars = []
    for lim in data.get("limits") or []:
        if lim.get("percent") is None:
            continue
        kind = lim.get("kind") or "?"
        name = CLAUDE_KIND_NAMES.get(kind) or kind.replace("_", " ").capitalize()
        if lim.get("scope"):
            name += f" · {lim['scope']}"
        bars.append(bar(name, lim["percent"], to_epoch(lim.get("resets_at"))))
    if not bars:  # eski yanit bicimi
        for key, name in CLAUDE_KEY_NAMES.items():
            w = data.get(key)
            if isinstance(w, dict) and w.get("utilization") is not None:
                bars.append(bar(name, w["utilization"], to_epoch(w.get("resets_at"))))
    ex = data.get("extra_usage") or {}
    if ex.get("is_enabled") and ex.get("utilization") is not None:
        bars.append(bar("Extra usage (monthly)", ex["utilization"]))
    plan = (oauth.get("subscriptionType") or "").capitalize()
    return {"title": "Claude", "plan": plan, "bars": bars}


# --------------------------------------------------------------------- Codex
def _codex_window_name(seconds):
    if not seconds:
        return "Limit"
    mins = seconds / 60
    if mins <= 24 * 60:
        return f"{round(mins / 60)}-hour window"
    if round(mins / 1440) == 7:
        return "Weekly"
    return f"{round(mins / 1440)}-day window"


def _codex_rl_bars(rl, prefix=""):
    out = []
    if not isinstance(rl, dict):
        return out
    for key in ("primary_window", "secondary_window"):
        w = rl.get(key)
        if isinstance(w, dict) and w.get("used_percent") is not None:
            name = _codex_window_name(w.get("limit_window_seconds"))
            out.append(bar(prefix + name, w["used_percent"], to_epoch(w.get("reset_at"))))
    return out


MAIN_CODEX_HOME = os.environ.get("CODEX_HOME") or os.path.join(HOME, ".codex")
EXTRA_CODEX_DIR = os.path.join(APP_DIR, "chatgpt")   # eklenen hesaplar: <n>/auth.json
OPENAI_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"   # Codex CLI'nin OAuth istemcisi


def codex_homes():
    """(klasor, widget'a_ait_mi) listesi: ana ~/.codex + eklenen hesaplar."""
    homes = []
    if os.path.exists(os.path.join(MAIN_CODEX_HOME, "auth.json")):
        homes.append((MAIN_CODEX_HOME, False))
    for d in sorted(glob.glob(os.path.join(EXTRA_CODEX_DIR, "*"))):
        if os.path.exists(os.path.join(d, "auth.json")):
            homes.append((d, True))
    return homes


def _jwt_claims(token):
    import base64
    try:
        p = token.split(".")[1]
        p += "=" * (-len(p) % 4)
        return json.loads(base64.urlsafe_b64decode(p))
    except Exception:
        return {}


def _refresh_codex_token(home, auth):
    """Refresh a Codex/ChatGPT sign-in and write it back to that auth.json,
    exactly like the Codex CLI does."""
    t = auth["tokens"]
    new = http_json("https://auth.openai.com/oauth/token",
                    {"Content-Type": "application/json"},
                    {"client_id": OPENAI_CLIENT_ID, "grant_type": "refresh_token",
                     "refresh_token": t["refresh_token"], "scope": "openid profile email"})
    for k in ("access_token", "refresh_token", "id_token"):
        if new.get(k):
            t[k] = new[k]
    auth["last_refresh"] = datetime.now(timezone.utc).isoformat()
    _write_json_atomic(os.path.join(home, "auth.json"), auth)


def _codex_usage(home, owned):
    path = os.path.join(home, "auth.json")
    auth = json.load(open(path, encoding="utf-8"))
    t = auth["tokens"]
    exp = _jwt_claims(t["access_token"]).get("exp", 0)
    # our own extra accounts: refresh early; the main Codex sign-in only once it
    # has expired (the Codex CLI refreshes it itself while you use it)
    if (owned and exp < time.time() + 3600) or \
            (not owned and RENEW_SIGNINS and exp < time.time() + 120):
        _refresh_codex_token(home, auth)
    return http_json(
        "https://chatgpt.com/backend-api/wham/usage",
        {"Authorization": "Bearer " + t["access_token"],
         "ChatGPT-Account-Id": t.get("account_id") or "",
         "User-Agent": "ai-limits-widget/1.0"})


def _account_name(home, data=None):
    if data and data.get("email"):
        return data["email"]
    try:
        auth = json.load(open(os.path.join(home, "auth.json"), encoding="utf-8"))
        return _jwt_claims(auth["tokens"]["id_token"]).get("email") or "account"
    except Exception:
        return os.path.basename(home)


def fetch_codex():
    homes = codex_homes()
    if not homes:
        raise NotInstalled()
    multi = len(homes) > 1
    bars, plans, seen = [], [], set()
    for home, owned in homes:
        try:
            data = _codex_usage(home, owned)
        except Exception:
            if owned:
                bars.append(bar(_account_name(home), 0, None,
                                "couldn't connect — sign in again",
                                _account_name(home)))
                continue
            try:
                local = fetch_codex_local(home)
            except Exception:
                continue
            g = _account_name(home) if multi else ""
            for b in local["bars"]:
                b["group"] = g
            bars += local["bars"]
            plans.append(local["plan"])
            continue
        acc = data.get("account_id") or data.get("email")
        if acc in seen:  # ayni hesap iki kez eklenmis
            continue
        seen.add(acc)
        plan = (data.get("plan_type") or "").capitalize()
        plans.append(plan)
        g = f"{data.get('email') or 'account'} · {plan}" if multi else ""
        acct_bars = _codex_rl_bars(data.get("rate_limit"), "Codex · ")
        acct_bars += _codex_rl_bars(data.get("code_review_rate_limit"), "Code review · ")
        for extra in data.get("additional_rate_limits") or []:
            if isinstance(extra, dict):
                name = extra.get("limit_name") or extra.get("metered_feature") or "Extra limit"
                acct_bars += _codex_rl_bars(extra.get("rate_limit") or extra, f"{name} · ")
        for model, info in (data.get("model_usage") or {}).items():
            if isinstance(info, dict) and info.get("available") is False:
                acct_bars.append(bar(model, 100, to_epoch(info.get("available_at")),
                                     "unavailable"))
        for b in acct_bars:
            b["group"] = g
        bars += acct_bars
    if not bars:
        raise RuntimeError("No ChatGPT account — right-click › Add ChatGPT account")
    plan = plans[0] if len(set(plans)) == 1 and not multi else f"{len(seen) or len(plans)} accounts"
    return {"title": "ChatGPT / Codex", "plan": plan, "bars": bars}


def fetch_codex_local(home=MAIN_CODEX_HOME):
    """Ag yoksa: Codex oturum kayitlarindaki son rate_limits olayini oku."""
    files = sorted(glob.glob(os.path.join(home, "sessions", "**", "*.jsonl"),
                             recursive=True), key=os.path.getmtime, reverse=True)[:5]
    latest = {}
    plan = ""
    for f in files:
        with open(f, encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                if '"rate_limits"' not in line:
                    continue
                try:
                    rl = json.loads(line)["payload"]["rate_limits"]
                except Exception:
                    continue
                lid = rl.get("limit_id") or "codex"
                latest[lid] = rl  # dosyada sonraki satir daha yeni
        if latest:
            break
    bars = []
    for lid, rl in latest.items():
        plan = rl.get("plan_type") or plan
        for key in ("primary", "secondary"):
            w = rl.get(key)
            if isinstance(w, dict) and w.get("used_percent") is not None:
                reset = to_epoch(w.get("resets_at"))
                pct = 0 if reset and reset < time.time() else w["used_percent"]
                name = _codex_window_name((w.get("window_minutes") or 0) * 60)
                bars.append(bar(f"{rl.get('limit_name') or lid.capitalize()} · {name}",
                                pct, reset, "local log"))
    if not bars:
        raise RuntimeError("No Codex data found")
    return {"title": "Codex / ChatGPT", "plan": plan.capitalize(), "bars": bars}


# --------------------------------------------------------------- Antigravity
def _walk(o):
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from _walk(v)
    elif isinstance(o, list):
        for v in o:
            yield from _walk(v)


def _ag_bars(data):
    bars, seen = [], set()
    for node in _walk(data):
        qi = node.get("quotaInfo") if isinstance(node.get("quotaInfo"), dict) else None
        src = qi if qi is not None else node
        if "remainingFraction" not in src and "resetTime" not in src:
            continue
        label = (node.get("label") or node.get("displayName") or node.get("modelName")
                 or node.get("name") or (node.get("modelOrAlias") or {}).get("model"))
        if not label or label in seen:
            continue
        seen.add(label)
        rem = float(src.get("remainingFraction", 0) or 0)  # alan yoksa = tukenmis
        bars.append(bar(str(label), (1 - rem) * 100, to_epoch(src.get("resetTime"))))
    return bars


AG_GROUP_NAMES = {"Gemini Models": "Gemini models",
                  "Claude and GPT models": "Claude & GPT models"}
AG_WINDOW_NAMES = {"5h": "5-hour", "weekly": "Weekly", "daily": "Daily"}


def _ag_summary_bars(summ):
    bars = []
    groups = (summ.get("response") or summ).get("groups") or []
    for g in groups:
        gname = g.get("displayName") or "Group"
        gname = AG_GROUP_NAMES.get(gname, gname)
        buckets = sorted(g.get("buckets") or [],
                         key=lambda b: 0 if b.get("window") == "5h" else 1)
        for b in buckets:
            w = b.get("window") or ""
            name = AG_WINDOW_NAMES.get(w) or b.get("displayName") or w
            rem = float(b.get("remainingFraction", 0) or 0)
            bars.append(bar(name, (1 - rem) * 100, to_epoch(b.get("resetTime")),
                            group=gname))
    return bars


def _pid_alive(pid):
    import ctypes
    if not pid:
        return False
    k32 = ctypes.windll.kernel32
    h = k32.OpenProcess(0x1000, False, int(pid))     # QUERY_LIMITED_INFORMATION
    if not h:
        return False
    code = ctypes.c_ulong(0)
    ok = k32.GetExitCodeProcess(h, ctypes.byref(code))
    k32.CloseHandle(h)
    return bool(ok) and code.value == 259            # STILL_ACTIVE


def fetch_antigravity():
    if not os.path.isdir(os.path.join(HOME, ".gemini", "antigravity")):
        raise NotInstalled()
    ddir = os.path.join(HOME, ".gemini", "antigravity", "daemon")
    hubs = sorted(glob.glob(os.path.join(ddir, "hub_*.json")),
                  key=os.path.getmtime, reverse=True)
    body = {"metadata": {"ideName": "antigravity", "extensionName": "antigravity",
                         "locale": "en"}}
    last_err = None
    for h in hubs:
        try:
            j = json.load(open(h, encoding="utf-8"))
        except Exception:
            continue
        if not _pid_alive(j.get("pid")):          # stale file from an old session
            continue
        base = f"http://127.0.0.1:{j['httpPort']}/exa.language_server_pb.LanguageServerService/"
        hdr = {"Content-Type": "application/json", "Connect-Protocol-Version": "1",
               "X-Codeium-Csrf-Token": j.get("csrfToken", "")}
        try:
            status = http_json(base + "GetUserStatus", hdr, body, timeout=4)
        except Exception as e:
            last_err = e
            continue
        us = status.get("userStatus") or {}
        plan = ((us.get("planStatus") or {}).get("planInfo") or {}).get("planName") \
            or (us.get("userTier") or {}).get("name") or ""
        # 1) quota summary: model groups share one 5-hour and one weekly limit
        try:
            summ = http_json(base + "RetrieveUserQuotaSummary", hdr, body, timeout=4)
            bars = _ag_summary_bars(summ)
            if bars:
                return {"title": "Antigravity", "plan": plan, "bars": bars}
        except Exception:
            pass
        # 2) fallback: per-model quota
        bars = _ag_bars(status)
        if bars:
            return {"title": "Antigravity", "plan": plan, "bars": bars}
    # Antigravity's own server isn't running: start it briefly in the background
    return _antigravity_background()


AG_BG_EVERY = 300          # seconds between background checks
_ag_bg = {"at": 0.0, "data": None}


def _ag_language_server():
    p = os.path.join(os.environ.get("LOCALAPPDATA", HOME), "Programs", "antigravity",
                     "resources", "bin", "language_server.exe")
    return p if os.path.exists(p) else None


def _listening_ports(pid):
    """TCP ports a process listens on (Windows TCP table, no extra tools)."""
    import ctypes
    from ctypes import wintypes as wt2

    class ROW(ctypes.Structure):
        _fields_ = [("state", wt2.DWORD), ("laddr", wt2.DWORD), ("lport", wt2.DWORD),
                    ("raddr", wt2.DWORD), ("rport", wt2.DWORD), ("pid", wt2.DWORD)]
    size = wt2.DWORD(0)
    iphlp = ctypes.windll.iphlpapi
    iphlp.GetExtendedTcpTable(None, ctypes.byref(size), False, 2, 5, 0)
    buf = ctypes.create_string_buffer(size.value)
    if iphlp.GetExtendedTcpTable(buf, ctypes.byref(size), False, 2, 5, 0) != 0:
        return []
    n = ctypes.cast(buf, ctypes.POINTER(wt2.DWORD))[0]
    rows = ctypes.cast(ctypes.addressof(buf) + 4, ctypes.POINTER(ROW * n)).contents
    out = []
    for r in rows:
        if r.pid == pid and r.state == 2:        # MIB_TCP_STATE_LISTEN
            out.append(((r.lport & 0xFF) << 8) | ((r.lport >> 8) & 0xFF))
    return out


def _ag_version():
    """Antigravity's version, from the newest server discovery file."""
    files = sorted(glob.glob(os.path.join(HOME, ".gemini", "antigravity", "daemon",
                                          "hub_*.json")), key=os.path.getmtime, reverse=True)
    for f in files:
        try:
            v = json.load(open(f, encoding="utf-8")).get("lsVersion")
            if v:
                return v
        except Exception:
            pass
    return "2.33.0"


def _antigravity_background():
    """Run Antigravity's language server headless for a few seconds with the
    sign-in Antigravity already saved, ask it for the quota, then stop it.
    Throttled to once every AG_BG_EVERY seconds."""
    import secrets
    import subprocess
    if _ag_bg["data"] and time.time() - _ag_bg["at"] < AG_BG_EVERY:
        return _ag_bg["data"]
    ls = _ag_language_server()
    if not ls:
        raise RuntimeError("Antigravity isn't running — open it to refresh")
    tok = secrets.token_hex(16)
    args = [ls, "--standalone", "--override_ide_name", "antigravity",
            "--subclient_type", "hub", "--override_ide_version", _ag_version(),
            "--override_user_agent_name", "antigravity",
            "--https_server_port", "0", "--http_server_port", "0", "--csrf_token", tok,
            "--app_data_dir", "antigravity",
            "--api_server_url", "https://generativelanguage.googleapis.com",
            "--cloud_code_endpoint", "https://daily-cloudcode-pa.googleapis.com",
            "--exit_on_stdin_close"]
    p = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, creationflags=0x08000000)
    body = {"metadata": {"ideName": "antigravity", "extensionName": "antigravity",
                         "locale": "en"}}
    hdr = {"Content-Type": "application/json", "Connect-Protocol-Version": "1",
           "X-Codeium-Csrf-Token": tok}
    try:
        t0 = time.time()
        while time.time() - t0 < 25:
            if p.poll() is not None:
                break
            for port in _listening_ports(p.pid):
                base = f"http://127.0.0.1:{port}/exa.language_server_pb.LanguageServerService/"
                try:
                    summ = http_json(base + "RetrieveUserQuotaSummary", hdr, body, timeout=6)
                except Exception:
                    continue
                bars = _ag_summary_bars(summ)
                if not bars:
                    continue
                plan = ""
                try:
                    us = http_json(base + "GetUserStatus", hdr, body, timeout=6)
                    us = us.get("userStatus") or {}
                    plan = ((us.get("planStatus") or {}).get("planInfo") or {}).get(
                        "planName") or ""
                except Exception:
                    pass
                data = {"title": "Antigravity", "plan": plan, "bars": bars}
                _ag_bg.update(at=time.time(), data=data)
                return data
            time.sleep(0.6)
    finally:
        try:
            p.stdin.close()
        except Exception:
            pass
        try:
            p.kill()
            p.wait(5)
        except Exception:
            pass
    raise RuntimeError("Antigravity sign-in needed — open Antigravity once")


SERVICES = [("claude", fetch_claude), ("codex", fetch_codex),
            ("antigravity", fetch_antigravity)]
# how often each service is asked (seconds); usage APIs rate-limit eager callers
SERVICE_EVERY = {"claude": 180, "codex": 90, "antigravity": 60}
BACKOFF_429 = 600


# ----------------------------------------------------------------- kalicilik
def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def save_json(path, obj):
    try:
        os.makedirs(APP_DIR, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False)
    except Exception:
        pass


def autostart_enabled():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run") as k:
            winreg.QueryValueEx(k, "AILimits")
            return True
    except Exception:
        return False


def launch_command():
    if FROZEN:
        return f'"{sys.executable}"'
    pyw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    return f'"{pyw}" "{os.path.abspath(__file__)}"'


def set_autostart(on):
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                        winreg.KEY_SET_VALUE) as k:
        if on:
            winreg.SetValueEx(k, "AILimits", 0, winreg.REG_SZ, launch_command())
        else:
            try:
                winreg.DeleteValue(k, "AILimits")
            except FileNotFoundError:
                pass


# ------------------------------------------------------------ kurulum (exe)
START_MENU_LNK = os.path.join(os.environ.get("APPDATA", HOME), "Microsoft", "Windows",
                              "Start Menu", "Programs", APP_NAME + ".lnk")


def _make_shortcut(target, lnk):
    import subprocess
    ps = ("$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:AIL_LNK);"
          "$s.TargetPath=$env:AIL_TARGET;$s.WorkingDirectory=Split-Path $env:AIL_TARGET;"
          "$s.IconLocation=$env:AIL_TARGET;$s.Save()")
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                   env=dict(os.environ, AIL_LNK=lnk, AIL_TARGET=target),
                   creationflags=0x08000000, timeout=30)  # CREATE_NO_WINDOW


def _remove_old_version():
    """Close and delete v1 ("AI Limitleri") if it is installed."""
    import shutil
    import subprocess
    old_exe = os.path.join(OLD_INSTALL_DIR, "AILimitleri.exe")
    if not os.path.exists(OLD_INSTALL_DIR):
        return
    ps = ("Get-CimInstance Win32_Process | ? { $_.ExecutablePath -eq $env:AIL_TARGET } | "
          "% { Stop-Process -Id $_.ProcessId -Force }")
    subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                   env=dict(os.environ, AIL_TARGET=old_exe),
                   capture_output=True, creationflags=0x08000000, timeout=30)
    time.sleep(0.8)
    shutil.rmtree(OLD_INSTALL_DIR, ignore_errors=True)
    try:
        os.remove(os.path.join(os.path.dirname(START_MENU_LNK), "AI Limitleri.lnk"))
    except OSError:
        pass


def install_dialog(update):
    """Ask before changing anything on the PC. -> dict of choices or None."""
    import tkinter as tk
    import ctypes as _ct
    try:
        _ct.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        pass
    import render as R
    from PIL import ImageTk
    st = load_json(STATE_FILE, {})
    opts = {"autostart": autostart_enabled() if update else True, "shortcut": True,
            "renew": st.get("renew", True)}
    result = {}
    root = tk.Tk()
    root.title("AI Limits setup")
    root.resizable(False, False)
    try:
        root.iconbitmap(default=sys.executable)
    except Exception:
        pass
    k = root.winfo_fpixels("1i") / 96.0
    W, H = 420, 468
    t = R.theme("modern", "dark")
    cv = tk.Canvas(root, width=int(W * k), height=int(H * k), highlightthickness=0,
                   bg=t["bg"])
    cv.pack()
    item = cv.create_image(0, 0, anchor="nw")
    hits = []

    def draw():
        nonlocal hits
        img, hits = R.installer(W, H, k, t, opts, update)
        root._img = ImageTk.PhotoImage(img)
        cv.itemconfig(item, image=root._img)

    def hit(e):
        lx, ly = e.x / k, e.y / k
        for (x1, y1, x2, y2), act in hits:
            if x1 <= lx <= x2 and y1 <= ly <= y2:
                return act
        return None

    def click(e):
        act = hit(e)
        if not act:
            return
        if act.startswith("opt:"):
            key = act[4:]
            opts[key] = not opts[key]
            draw()
        elif act == "install":
            result.update(opts)
            root.destroy()
        elif act == "cancel":
            root.destroy()

    cv.bind("<Button-1>", click)
    cv.bind("<Motion>", lambda e: cv.config(cursor="hand2" if hit(e) else ""))
    root.bind("<Return>", lambda e: (result.update(opts), root.destroy()))
    root.bind("<Escape>", lambda e: root.destroy())
    draw()
    root.update_idletasks()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"+{(sw - int(W * k)) // 2}+{(sh - int(H * k)) // 2}")
    root.lift()
    root.attributes("-topmost", True)
    root.after(300, lambda: root.attributes("-topmost", False))
    root.mainloop()
    return result or None


def self_install():
    """When run from wherever it was downloaded: ask the user (install_dialog),
    then copy itself to the user's programs folder, add the chosen shortcut and
    startup entry and launch the installed copy. No admin rights needed.
    True = this copy should exit."""
    if not FROZEN:
        return False
    here = os.path.normcase(os.path.abspath(sys.executable))
    target = os.path.join(INSTALL_DIR, EXE_NAME)
    if here == os.path.normcase(os.path.abspath(target)):
        return False
    import shutil
    import subprocess
    choices = install_dialog(update=os.path.exists(target))
    if choices is None:                 # cancelled: change nothing
        return True
    st = load_json(STATE_FILE, {})
    st["renew"] = bool(choices.get("renew"))
    save_json(STATE_FILE, st)
    # close an installed older version so its file isn't locked (only the exe in
    # the install folder, never this downloaded copy)
    if os.path.exists(target):
        ps = ("Get-CimInstance Win32_Process | ? { $_.ExecutablePath -eq $env:AIL_TARGET } | "
              "% { Stop-Process -Id $_.ProcessId -Force }")
        subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps],
                       env=dict(os.environ, AIL_TARGET=target),
                       capture_output=True, creationflags=0x08000000, timeout=30)
        time.sleep(0.8)
    _remove_old_version()
    os.makedirs(INSTALL_DIR, exist_ok=True)
    shutil.copy2(sys.executable, target)
    if choices.get("shortcut"):
        try:
            _make_shortcut(target, START_MENU_LNK)
        except Exception:
            pass
    else:
        try:
            os.remove(START_MENU_LNK)
        except OSError:
            pass
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Run", 0,
                        winreg.KEY_SET_VALUE) as k:
        if choices.get("autostart"):
            winreg.SetValueEx(k, "AILimits", 0, winreg.REG_SZ, f'"{target}"')
        else:
            try:
                winreg.DeleteValue(k, "AILimits")
            except FileNotFoundError:
                pass
    subprocess.Popen([target], close_fds=True)
    return True


def uninstall():
    """Remove the startup entry, shortcut and settings; delete the exe on exit."""
    import shutil
    import subprocess
    set_autostart(False)
    for p in (START_MENU_LNK,):
        try:
            os.remove(p)
        except OSError:
            pass
    shutil.rmtree(APP_DIR, ignore_errors=True)
    if FROZEN and os.path.normcase(os.path.dirname(sys.executable)) == \
            os.path.normcase(INSTALL_DIR):
        subprocess.Popen(f'cmd /c timeout /t 2 /nobreak >nul & rmdir /s /q "{INSTALL_DIR}"',
                         creationflags=0x08000000)


# ------------------------------------------------------------------------ UI
import ctypes
import ctypes.wintypes as wt

import render as R

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
# HWND is pointer-sized on 64-bit; without argtypes -1 (TOPMOST) gets mangled.
user32.SetWindowPos.argtypes = [wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int,
                                ctypes.c_int, ctypes.c_int, ctypes.c_uint]
user32.GetParent.argtypes = [wt.HWND]
user32.GetParent.restype = wt.HWND
user32.GetForegroundWindow.restype = wt.HWND
user32.FindWindowW.restype = wt.HWND
user32.GetWindowRect.argtypes = [wt.HWND, ctypes.POINTER(wt.RECT)]
user32.SetForegroundWindow.argtypes = [wt.HWND]
user32.GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, ctypes.c_int]
user32.GetDC.restype = wt.HDC
user32.ReleaseDC.argtypes = [wt.HWND, wt.HDC]
gdi32.GetPixel.argtypes = [wt.HDC, ctypes.c_int, ctypes.c_int]
gdi32.GetPixel.restype = wt.DWORD
HWND_TOPMOST = wt.HWND(-1)
SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE, SWP_SHOWWINDOW = 0x1, 0x2, 0x10, 0x40
ROTATE_MS = 10_000


def light_theme():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize") as k:
            return winreg.QueryValueEx(k, "SystemUsesLightTheme")[0] == 1
    except Exception:
        return False


def taskbar_rect():
    h = user32.FindWindowW("Shell_TrayWnd", None)
    r = wt.RECT()
    user32.GetWindowRect(h, ctypes.byref(r))
    return r.left, r.top, r.right, r.bottom


def screen_pixel(x, y):
    dc = user32.GetDC(0)
    c = gdi32.GetPixel(dc, x, y)
    user32.ReleaseDC(0, dc)
    if c < 0 or c == 0xFFFFFFFF:
        return None
    return f"#{c & 0xFF:02x}{(c >> 8) & 0xFF:02x}{(c >> 16) & 0xFF:02x}"


def top_hwnd(widget):
    return user32.GetParent(widget.winfo_id()) or widget.winfo_id()


def round_corners(widget):
    """Windows 11 rounded corners (DWM)."""
    try:
        hwnd = top_hwnd(widget)
        pref = ctypes.c_int(2)  # DWMWCP_ROUND
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 33, ctypes.byref(pref), 4)
    except Exception:
        pass


def foreground_is_fullscreen():
    fg = user32.GetForegroundWindow()
    if not fg:
        return False
    cls = ctypes.create_unicode_buffer(64)
    user32.GetClassNameW(fg, cls, 64)
    if cls.value in ("Progman", "WorkerW", "Shell_TrayWnd"):
        return False
    r = wt.RECT()
    user32.GetWindowRect(fg, ctypes.byref(r))
    return (r.left <= 0 and r.top <= 0 and r.right >= user32.GetSystemMetrics(0)
            and r.bottom >= user32.GetSystemMetrics(1))


def set_border_color(widget, hexcol):
    """Windows 11 window border color (DWMWA_BORDER_COLOR)."""
    try:
        h = hexcol.lstrip("#")
        colorref = ctypes.c_uint(int(h[4:6] + h[2:4] + h[0:2], 16))
        ctypes.windll.dwmapi.DwmSetWindowAttribute(top_hwnd(widget), 34,
                                                   ctypes.byref(colorref), 4)
    except Exception:
        pass


def ease_out(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def spring(t, dist, damp=7.5, freq=12.5):
    """Damped spring offset: starts at dist, overshoots, settles at 0."""
    import math
    return dist * math.exp(-damp * t) * math.cos(freq * t)


PANEL_W = 360          # logical px
TOUR_W, TOUR_H = 340, 440
FRAME_MS = 16
LIQUID_MS = 66         # ~15 fps idle wave on the taskbar
HEADER_MS = 33         # ~30 fps living header while the panel is open
INTRO_SEC = 1.25
MOTION_LEVELS = ("off", "calm", "lively", "wild")

TOUR_STEPS = [
    dict(art="welcome", title="Welcome to AI Limits",
         body=["Your Claude, ChatGPT and Antigravity limits, live on the taskbar.",
               "Here's a 30-second tour."]),
    dict(art="strip", title="Meet the strip",
         body=["It sits at the left of your taskbar and shows one limit at a time, "
               "switching every 10 seconds.",
               "Hover to pause it. Scroll the mouse wheel over it to flip through limits."]),
    dict(art="panel", title="Click for the full picture",
         body=["Click the strip to open the panel: every limit, when it resets and "
               "which plan you're on.",
               "Click a service to collapse it. Click anywhere outside to close."]),
    dict(art="controls", title="Make it yours",
         body=["Theme switches between dark and light. Motion turns animations on or off.",
               "The gear opens Settings: style presets (Minimal, Modern, Kawaii, Goofy), "
               "fonts, motion level, liquid gauges and the mascot."]),
    dict(art="accounts", title="No apps need to be open",
         body=["AI Limits refreshes everything in the background using the sign-ins "
               "already on this PC.",
               "Claude — signed in to Claude Code once. ChatGPT — signed in with the Codex "
               "CLI (add more via right-click). Antigravity — signed in once."]),
    dict(art="done", title="You're all set",
         body=["AI Limits starts with Windows, so it's always there.",
               "Right-click the strip any time to refresh, manage accounts, replay this "
               "tour or uninstall."]),
]


class App:
    def __init__(self):
        from PIL import ImageTk  # noqa: F401
        self.state = load_json(STATE_FILE, {})
        self.cache = load_json(CACHE_FILE, {})   # service -> {data, at}
        self.errors = {}
        self.backoff = {}
        self.collapsed = set(self.state.get("collapsed", []))
        self.busy = False
        self.loaded = False
        self.idx = 0
        self.items = []
        self.rings = []
        self.ring_disp = {}
        self.hover = False
        self.anim_job = None
        self.fly_job = None
        self.view_job = None
        self.scroll = 0
        self.knob_anim = {}
        self.phase = 0.0
        self.t0 = time.perf_counter()
        self.poke_at = None
        self.fly_open = False
        self.tour_open = False
        self.tour_step = 0
        self.view = "main"

        self.sys_light = light_theme()
        st = self.state
        st.setdefault("preset", "modern")
        st.setdefault("theme", "light" if self.sys_light else "dark")
        if "motion" not in st:                      # v2 had a plain on/off switch
            st["motion"] = "lively" if st.get("anim", True) else "off"
        st.setdefault("motion_last", st["motion"] if st["motion"] != "off" else "lively")
        st.setdefault("font", R.PRESETS[st["preset"]]["font"])
        st.setdefault("liquid", True)
        st.setdefault("mascot", True)
        st.setdefault("mode", "cycle")
        st.setdefault("interval", 10)
        st.setdefault("renew", True)
        global RENEW_SIGNINS
        RENEW_SIGNINS = bool(st["renew"])
        R.set_family(st["font"])
        self.hover_bg = "#ffffff" if self.sys_light else "#2e2e2e"

        self.root = tk.Tk()
        self.root.withdraw()
        self.S = self.root.winfo_fpixels("1i") / 96.0   # DPI scale

        tl, tt, tr, tb = taskbar_rect()
        self.key = screen_pixel(tl + 3, tb - 3) or ("#f3f3f3" if self.sys_light else "#1c1c1c")

        self._build_pill()
        self._build_flyout()
        self._build_tour()
        self._build_menu()

        self.place_pill()
        self.root.deiconify()
        self.fly_had_focus = False
        self._was_down = False
        self.root.after(50, self._keep_on_top)
        self.root.after(50, self._outside_click)
        self.rebuild_items()
        self.draw_pill()
        self.refresh(force=True)
        self._rotate_job = self.root.after(self.interval_ms, self._rotate)
        self.root.after(20_000, self._tick)
        self.root.after(LIQUID_MS, self._liquid_tick)
        self.root.after(HEADER_MS, self._header_tick)
        if not st.get("onboarded"):
            self.root.after(1500, self.show_tour)

    # ----------------------------------------------------------------- props
    @property
    def t(self):
        return R.theme(self.state["preset"], self.state["theme"])

    @property
    def tb_t(self):
        return R.strip_theme(self.state["preset"], self.sys_light)

    @property
    def mo(self):
        return R.MOTION.get(self.state["motion"])

    @property
    def anim(self):
        return self.state["motion"] != "off"

    @property
    def interval_ms(self):
        return int(self.state.get("interval", 10)) * 1000

    @property
    def clock(self):
        return time.perf_counter() - self.t0

    def px(self, v):
        return int(round(v * self.S))

    def _mood(self):
        worst = 0
        for key, _ in SERVICES:
            e = self.cache.get(key)
            if e:
                for b in e["data"]["bars"]:
                    # Argon-style always-full side pools shouldn't make her sad
                    if b.get("group") and "Argon" in b["group"]:
                        continue
                    worst = max(worst, b["pct"])
        return "bad" if worst >= 85 else "warn" if worst >= 60 else "ok"

    # ------------------------------------------------------------------ strip
    def _build_pill(self):
        r = self.root
        r.title(APP_NAME)
        r.overrideredirect(True)
        r.attributes("-topmost", True)
        r.configure(bg=self.key)
        self.cv = tk.Canvas(r, bg=self.key, highlightthickness=0, cursor="hand2")
        self.cv.pack()
        self.pill_item = self.cv.create_image(0, 0, anchor="nw")
        self.cv.bind("<Button-1>", lambda e: self.toggle_flyout())
        self.cv.bind("<Button-3>", self._popup)
        self.cv.bind("<Enter>", lambda e: self._set_hover(True))
        self.cv.bind("<Leave>", lambda e: self._set_hover(False))
        self.cv.bind("<MouseWheel>", lambda e: self._step(-1 if e.delta > 0 else 1))

    def pill_size(self):
        tl, tt, tr, tb = taskbar_rect()
        th = (tb - tt) / self.S
        h = max(32, min(th - 8, 44))
        if self.state["mode"] == "rings" and self.rings:
            w = R.rings_width(len(self.rings), h)
        else:
            w = 232
        return w, h

    def place_pill(self):
        tl, tt, tr, tb = taskbar_rect()
        self.tb = (tl, tt, tr, tb)
        self.pw_l, self.ph_l = self.pill_size()
        w, h = self.px(self.pw_l), self.px(self.ph_l)
        self.cv.config(width=w, height=h)
        x = tl + self.px(8)
        y = tt + ((tb - tt) - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _set_hover(self, v):
        self.hover = v
        self.draw_pill()

    def rebuild_items(self):
        items, rings = [], []
        for key, _ in SERVICES:
            entry = self.cache.get(key)
            if not entry:
                continue
            data = entry["data"]
            svc = data["title"].split(" /")[0]
            for b in data["bars"]:
                who = b.get("group", "").split("@")[0] if b.get("group") else ""
                items.append((svc + (f" · {who}" if who else ""), b))
            if data["bars"]:
                rings.append((key, self._ring_value(key, data["bars"])))
        self.items = items
        if self.idx >= len(items):
            self.idx = 0
        old_n = len(self.rings)
        self.rings = rings
        if len(rings) != old_n:
            self.place_pill()
        if self.state["mode"] == "rings":
            self._animate_rings()

    @staticmethod
    def _ring_value(key, bars):
        """One ring per service: the limit that bites first. With several
        ChatGPT accounts, the freest account; Antigravity, its first group."""
        groups = {}
        for b in bars:
            groups.setdefault(b.get("group", ""), []).append(b["pct"])
        per_group = [max(v) for v in groups.values()]
        if key == "codex":
            return min(per_group)
        return per_group[0]

    def _item_view(self, it):
        if not it:
            return None
        title, b = it
        return title, dict(b, reset_txt=fmt_reset(b.get("reset")))

    def _liquid(self, amp=None):
        mo = self.mo
        if not (mo and self.state["liquid"]):
            return None
        return (self.phase, amp if amp is not None else mo["amp"] * 0.85)

    def draw_pill(self, offset=1.0, prev=None):
        from PIL import ImageTk
        hover = self.hover or self.flyout_open()
        lq = self._liquid()
        tb_t = self.tb_t
        if self.state["mode"] == "rings" and self.rings:
            rings = [(k, self.ring_disp.get(k, v)) for k, v in self.rings]
            im = R.pill_rings(self.pw_l, self.ph_l, self.S, self.key, tb_t, rings,
                              hover, self.hover_bg, lq)
        elif self.items:
            im = R.pill_cycle(self.pw_l, self.ph_l, self.S, self.key, tb_t,
                              self._item_view(self.items[self.idx]), hover, self.hover_bg,
                              offset, self._item_view(prev) if prev else None, lq)
        else:
            c = R.Canvas2x(self.pw_l, self.ph_l, self.S, self.key)
            if hover:
                c.rrect(1, 1, self.pw_l - 1, self.ph_l - 1, 6, fill=self.hover_bg)
            msg = "No AI account found · right-click" if self.loaded else "Loading AI limits…"
            c.text(12, self.ph_l / 2, msg, 11, tb_t["muted"], anchor="lm")
            im = c.image()
        self.pill_img = ImageTk.PhotoImage(im)
        self.cv.itemconfig(self.pill_item, image=self.pill_img)

    def _liquid_tick(self):
        """Keeps the taskbar liquid moving while Motion and liquid are on."""
        try:
            mo = self.mo
            if mo and self.root.state() != "withdrawn":
                self.phase += mo["speed"]
                if self.state["liquid"] and not self.anim_job:
                    self.draw_pill()
                if self.tour_open and not self.tour_job:
                    self._render_tour()
        except Exception:
            pass
        self.root.after(LIQUID_MS, self._liquid_tick)

    def _header_tick(self):
        """Living header (title shimmer, pulse, mascot, liquid) at ~30 fps."""
        try:
            if (self.fly_open and self.anim and not self.fly_job and not self.view_job
                    and self.view == "main"):
                self._render_header()
        except Exception:
            pass
        self.root.after(HEADER_MS, self._header_tick)

    def _rotate(self):
        if self.state["mode"] == "cycle" and not self.flyout_open() and not self.hover:
            self._step(1)
        self._rotate_job = self.root.after(self.interval_ms, self._rotate)

    def _restart_rotation(self):
        try:
            self.root.after_cancel(self._rotate_job)
        except Exception:
            pass
        self._rotate_job = self.root.after(self.interval_ms, self._rotate)

    def _step(self, d):
        if self.state["mode"] != "cycle" or len(self.items) < 2:
            return
        prev = self.items[self.idx]
        self.idx = (self.idx + d) % len(self.items)
        if not self.anim:
            self.draw_pill()
            return
        if self.anim_job:
            self.root.after_cancel(self.anim_job)
        start = time.perf_counter()
        dur = {"calm": 0.6, "lively": 0.45, "wild": 0.38}[self.state["motion"]]

        def frame():
            p = min(1.0, (time.perf_counter() - start) / dur)
            self.phase += 0.05
            self.draw_pill(p, prev if p < 1 else None)
            self.anim_job = self.root.after(FRAME_MS, frame) if p < 1 else None
        frame()

    def _animate_rings(self, from_zero=False):
        targets = dict(self.rings)
        if not self.anim:
            self.ring_disp = dict(targets)
            self.draw_pill()
            return
        start_vals = {k: (0 if from_zero else self.ring_disp.get(k, 0)) for k in targets}
        if all(abs(start_vals[k] - targets[k]) < .5 for k in targets) and not from_zero:
            self.ring_disp = dict(targets)
            self.draw_pill()
            return
        if self.anim_job:
            self.root.after_cancel(self.anim_job)
        start = time.perf_counter()
        dur = 0.9

        def frame():
            p = ease_out(min(1.0, (time.perf_counter() - start) / dur))
            self.ring_disp = {k: start_vals[k] + (targets[k] - start_vals[k]) * p
                              for k in targets}
            self.phase += 0.08
            self.draw_pill()
            self.anim_job = self.root.after(FRAME_MS, frame) if p < 1 else None
        frame()

    def _keep_on_top(self):
        """The taskbar jumps above us when clicked; put us back on top."""
        try:
            if foreground_is_fullscreen():
                if self.root.state() != "withdrawn":
                    self.root.withdraw()
            else:
                if self.root.state() == "withdrawn":
                    self.root.deiconify()
                if taskbar_rect() != self.tb:
                    self.place_pill()
                user32.SetWindowPos(top_hwnd(self.root), HWND_TOPMOST, 0, 0, 0, 0,
                                    SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
            if self.flyout_open() and not self.menu_open and not self.fly_job:
                ours = (top_hwnd(self.fly), top_hwnd(self.root), top_hwnd(self.tour))
                fg = user32.GetForegroundWindow()
                if fg in ours:
                    self.fly_had_focus = True
                elif self.fly_had_focus:
                    self.hide_flyout()      # user switched to another window
        except Exception:
            pass
        self.root.after(150, self._keep_on_top)

    def _outside_click(self):
        """Close the panel on a click outside it (even without focus)."""
        if self.flyout_open() and not self.menu_open:
            down = any(user32.GetAsyncKeyState(k) & 0x8000 for k in (0x01, 0x02))
            if down and not self._was_down:
                pt = wt.POINT()
                user32.GetCursorPos(ctypes.byref(pt))
                inside = False
                for wdg in (self.fly, self.root, self.tour):
                    r = wt.RECT()
                    user32.GetWindowRect(top_hwnd(wdg), ctypes.byref(r))
                    if r.left <= pt.x < r.right and r.top <= pt.y < r.bottom:
                        inside = True
                if not inside:
                    self.hide_flyout()
            self._was_down = down
        else:
            self._was_down = False
        self.root.after(30, self._outside_click)

    # ------------------------------------------------------------------ panel
    def _build_flyout(self):
        f = tk.Toplevel(self.root)
        f.withdraw()
        f.overrideredirect(True)
        f.attributes("-topmost", True)
        f.title(APP_NAME + " panel")
        f.bind("<Escape>", lambda e: self._escape())
        self.fly = f
        self.fcv = tk.Canvas(f, highlightthickness=0, bd=0)
        self.fcv.pack(fill="both", expand=True)
        self.body_item = self.fcv.create_image(0, 0, anchor="nw")
        self.head_item = self.fcv.create_image(0, 0, anchor="nw")
        self.fcv.bind("<Button-1>", self._panel_click)
        self.fcv.bind("<Button-3>", self._popup)
        self.fcv.bind("<MouseWheel>", self._panel_wheel)
        self.fcv.bind("<Motion>", self._panel_motion)
        self.menu_open = False
        self.head_hits, self.body_hits = [], []
        self.head_h = self.body_h = self.view_h = 0
        self.intro_start = None

    def _escape(self):
        if self.view == "settings":
            self.switch_view("main")
        else:
            self.hide_flyout()

    def flyout_open(self):
        return self.fly_open

    def toggle_flyout(self):
        if self.flyout_open():
            self.hide_flyout()
        else:
            self.show_flyout()

    def _sections(self):
        out = []
        for key, _ in SERVICES:
            entry = self.cache.get(key)
            err = self.errors.get(key)
            if not entry and not err:
                continue
            data = (entry or {}).get("data") or {"title": key.capitalize(), "bars": []}
            data = dict(data, bars=[dict(b, reset_txt=fmt_reset(b.get("reset")))
                                    for b in data["bars"]])
            stale = datetime.fromtimestamp(entry["at"]).strftime("%H:%M") \
                if (err and entry) else None
            out.append((key, data, err, stale))
        return out

    def _intro_t(self):
        if self.intro_start is None:
            return None
        t = time.perf_counter() - self.intro_start
        return None if t >= INTRO_SEC else t

    def _look(self):
        """Direction from the mascot to the mouse, for the googly eyes."""
        try:
            pt = wt.POINT()
            user32.GetCursorPos(ctypes.byref(pt))
            mx = self.fly.winfo_rootx() + self.px(PANEL_W - 128)
            my = self.fly.winfo_rooty() + self.px(32)
            dx, dy = pt.x - mx, pt.y - my
            import math
            n = math.hypot(dx, dy) or 1
            f = min(1.0, n / self.px(80))
            return (dx / n * f, dy / n * f)
        except Exception:
            return (0.0, 0.0)

    def _subtitle(self):
        n = len([1 for k, _ in SERVICES if self.cache.get(k)])
        last = self.state.get("last_refresh")
        if self.busy and not last:
            return "Refreshing…"
        if not last:
            return "No data yet"
        hhmm = datetime.fromtimestamp(last).strftime("%H:%M")
        word = {"goofy": "Last poked", "kawaii": "Checked"}.get(self.state["preset"], "Updated")
        return f"{word} {hhmm} · {n} service{'s' if n != 1 else ''}" + (
            " · refreshing…" if self.busy else "")

    def _render_header(self, ss=2):
        from PIL import ImageTk
        t = self.t
        if self.view == "settings":
            himg, self.head_hits, self.head_h = R.settings_header(PANEL_W, self.S, t, ss)
        else:
            it = self._intro_t() if self.anim else None
            mo = self.mo or {}
            amp = mo.get("amp", 0)
            hero_p = 9.0
            if it is not None:
                hero_p = it / 0.9
                amp = amp + mo.get("slosh", 0) * max(0.0, 1 - it / INTRO_SEC) ** 2
            mascot = R.PRESETS[self.state["preset"]]["mascot"] if self.state["mascot"] else None
            poke = (time.perf_counter() - self.poke_at) if self.poke_at else None
            st = dict(subtitle=self._subtitle(), busy=self.busy, mode=self.state["mode"],
                      theme=self.state["theme"], anim=self.anim, knob_anim=self.knob_anim,
                      rings=self.rings, hero_p=hero_p, phase=self.phase, amp=amp,
                      liquid=self.anim and self.state["liquid"], motion=self.mo,
                      title_t=it, clock=self.clock, mascot=mascot, mood=self._mood(),
                      look=self._look() if mascot == "googly" else (0, 0), poke=poke)
            himg, self.head_hits, self.head_h = R.panel_header(PANEL_W, self.S, t, st, ss)
        self.head_photo = ImageTk.PhotoImage(himg)
        self.fcv.itemconfig(self.head_item, image=self.head_photo)

    def _settings_state(self):
        st = self.state
        return dict(preset=st["preset"], theme=st["theme"], font=st["font"],
                    motion=st["motion"], liquid=st["liquid"], mascot=st["mascot"],
                    mode=st["mode"], interval=int(st["interval"]), knob_anim=self.knob_anim,
                    autostart=autostart_enabled(), renew=st["renew"])

    def _render_body(self, ss=3):
        from PIL import ImageTk
        if self.view == "settings":
            bimg, self.body_hits, self.body_h = R.settings_body(
                PANEL_W, self.S, self.t, self._settings_state(), ss)
        else:
            bimg, self.body_hits, self.body_h = R.panel_body(
                PANEL_W, self.S, self.t, self._sections(), self.collapsed,
                intro=self._intro_t() if self.anim else None, ss=ss, motion=self.mo)
        self.body_photo = ImageTk.PhotoImage(bimg)
        self.fcv.itemconfig(self.body_item, image=self.body_photo)

    def render_panel(self, keep_scroll=True, ss=3):
        t = self.t
        self._render_header(2)
        self._render_body(ss)
        self.fcv.config(bg=t["bg"])
        self.fly.configure(bg=t["bg"])
        tl, tt, tr, tb = taskbar_rect()
        max_view = tt / self.S * 0.85 - self.head_h
        self.view_h = min(self.body_h, max_view)
        if not keep_scroll:
            self.scroll = 0
        self.scroll = max(0, min(self.scroll, self.body_h - self.view_h))
        self.fcv.coords(self.body_item, 0, self.px(self.head_h - self.scroll))
        self.fcv.config(width=self.px(PANEL_W), height=self.px(self.head_h + self.view_h))
        set_border_color(self.fly, t["border"])

    def _panel_geometry(self, dy=0, w=PANEL_W, h_l=None):
        tl, tt, tr, tb = taskbar_rect()
        h = self.px(h_l if h_l is not None else self.head_h + self.view_h)
        x = tl + self.px(8)
        y = tt - h - self.px(10) + int(dy)
        return f"{self.px(w)}x{h}+{x}+{y}"

    def _spring_px(self, t):
        mo = self.mo
        if not mo:
            return 0
        return self.px(spring(t, mo["spring"], mo["damp"], mo["freq"]))

    def show_flyout(self):
        if self.tour_open:
            self.hide_tour(finish=False)
        self.fly_open = True
        self.view = "main"
        f = self.fly
        if self.fly_job:
            self.root.after_cancel(self.fly_job)
            self.fly_job = None
        self.intro_start = time.perf_counter() if self.anim else None
        self.render_panel(keep_scroll=False, ss=2 if self.anim else 3)
        self.fcv.coords(self.head_item, 0, 0)
        if self.anim:
            f.attributes("-alpha", 0.0)
        f.geometry(self._panel_geometry(self._spring_px(0)))
        f.deiconify()
        round_corners(f)
        f.lift()
        f.focus_force()
        user32.SetForegroundWindow(top_hwnd(f))
        self.draw_pill()
        if not self.anim:
            f.attributes("-alpha", 1.0)
            return

        def frame():
            if not self.fly_open:
                return
            it = time.perf_counter() - self.intro_start
            f.attributes("-alpha", min(1.0, it / 0.16))
            f.geometry(self._panel_geometry(self._spring_px(it)))
            if it < INTRO_SEC:
                self._render_header(2)
                self._render_body(2)
                self.fly_job = self.root.after(FRAME_MS, frame)
            else:
                self.fly_job = None
                self.intro_start = None
                f.geometry(self._panel_geometry())
                self.render_panel()          # final, full quality
        frame()

    def hide_flyout(self):
        if not self.fly_open:
            return
        self.fly_open = False
        self.fly_had_focus = False
        self.intro_start = None
        self._save_state()
        self.draw_pill()
        if self.fly_job:
            self.root.after_cancel(self.fly_job)
            self.fly_job = None
        f = self.fly
        if not self.anim:
            f.withdraw()
            return
        start = time.perf_counter()
        dur = 0.16

        def frame():
            p = min(1.0, (time.perf_counter() - start) / dur)
            e = p * p
            f.attributes("-alpha", 1 - e)
            f.geometry(self._panel_geometry(self.px(16) * e))
            if p < 1:
                self.fly_job = self.root.after(FRAME_MS, frame)
            else:
                self.fly_job = None
                f.withdraw()
        frame()

    def switch_view(self, view):
        """Slide between the main panel and Settings."""
        if view == self.view:
            return
        direction = 1 if view == "settings" else -1
        self.view = view
        self.scroll = 0
        self.render_panel(keep_scroll=False)
        self.fly.geometry(self._panel_geometry())
        if not self.anim:
            self.fcv.coords(self.head_item, 0, 0)
            return
        W = self.px(PANEL_W)
        start = time.perf_counter()

        def frame():
            p = ease_out((time.perf_counter() - start) / 0.28)
            x = int(direction * W * 0.35 * (1 - p))
            self.fcv.coords(self.head_item, x, 0)
            self.fcv.coords(self.body_item, x, self.px(self.head_h - self.scroll))
            if p < 1:
                self.view_job = self.root.after(FRAME_MS, frame)
            else:
                self.view_job = None
        frame()

    def _hit(self, x, y):
        lx, ly = x / self.S, y / self.S
        if ly < self.head_h:
            for (x1, y1, x2, y2), act in self.head_hits:
                if x1 <= lx <= x2 and y1 <= ly <= y2:
                    return act
            return None
        by = ly - self.head_h + self.scroll
        for (x1, y1, x2, y2), act in self.body_hits:
            if x1 <= lx <= x2 and y1 <= by <= y2:
                return act
        return None

    def _panel_motion(self, e):
        self.fcv.config(cursor="hand2" if self._hit(e.x, e.y) else "")

    def _set_scroll(self, v):
        self.scroll = max(0, min(v, self.body_h - self.view_h))
        self.fcv.coords(self.body_item, 0, self.px(self.head_h - self.scroll))

    def _panel_wheel(self, e):
        if self.body_h > self.view_h:
            self._set_scroll(self.scroll - e.delta / 120 * 48)

    def _apply_look(self, rerender=True):
        """After a style change: fonts, strip, panel, border."""
        R.set_family(self.state["font"])
        self.place_pill()
        self.draw_pill()
        if rerender:
            self.render_panel()
            self.fly.geometry(self._panel_geometry())

    def _panel_click(self, e):
        act = self._hit(e.x, e.y)
        if not act or self.fly_job:
            return
        st = self.state
        if act == "refresh":
            self.refresh(force=True)
        elif act == "settings":
            self.switch_view("settings")
        elif act == "back":
            self.switch_view("main")
        elif act == "mascot":
            self.poke_at = time.perf_counter()
        elif act == "theme" or act.startswith("theme:"):
            new = act.split(":", 1)[1] if ":" in act else (
                "light" if st["theme"] == "dark" else "dark")
            if new != st["theme"]:
                st["theme"] = new
                self._knob("theme", new == "dark") if act == "theme" else self._apply_look()
        elif act == "anim":
            if st["motion"] == "off":
                st["motion"] = st.get("motion_last", "lively")
            else:
                st["motion_last"] = st["motion"]
                st["motion"] = "off"
            self._knob("anim", self.anim, force=True)
            self.draw_pill()
        elif act.startswith("motion:"):
            st["motion"] = act.split(":", 1)[1]
            if st["motion"] != "off":
                st["motion_last"] = st["motion"]
            self._apply_look()
        elif act.startswith("preset:"):
            name = act.split(":", 1)[1]
            p = R.PRESETS[name]
            st.update(preset=name, font=p["font"], motion=p["motion"],
                      motion_last=p["motion"])
            self._apply_look()
        elif act.startswith("font:"):
            st["font"] = act.split(":", 1)[1]
            self._apply_look()
        elif act in ("liquid", "mascot"):
            st[act] = not st[act]
            self._knob(act, st[act])
            self.draw_pill()
        elif act == "renew":
            global RENEW_SIGNINS
            st["renew"] = RENEW_SIGNINS = not st["renew"]
            self._knob(act, st["renew"])
        elif act == "autostart":
            on = not autostart_enabled()
            set_autostart(on)
            self.auto_var.set(on)
            self._knob(act, on)
        elif act.startswith("mode:"):
            mode = act.split(":", 1)[1]
            if mode != st["mode"]:
                st["mode"] = mode
                self.place_pill()
                if mode == "rings":
                    self._animate_rings(from_zero=True)
                else:
                    self.draw_pill()
                self.render_panel()
        elif act.startswith("interval:"):
            st["interval"] = int(act.split(":", 1)[1])
            self._restart_rotation()
            self.render_panel()
        elif act == "reset":
            p = R.PRESETS[st["preset"]]
            st.update(font=p["font"], motion=p["motion"], motion_last=p["motion"],
                      liquid=True, mascot=True, interval=10)
            self._restart_rotation()
            self._apply_look()
        elif act.startswith("toggle:"):
            key = act.split(":", 1)[1]
            self.collapsed.symmetric_difference_update({key})
            self.render_panel()
            self.fly.geometry(self._panel_geometry())
        elif act.startswith("jump:"):
            key = act.split(":", 1)[1]
            self.collapsed.discard(key)
            self.render_panel()
            self.fly.geometry(self._panel_geometry())
            for (x1, y1, x2, y2), a in self.body_hits:
                if a == "toggle:" + key:
                    self._scroll_to(y1 - 6)
        self._save_state()

    def _scroll_to(self, target):
        target = max(0, min(target, self.body_h - self.view_h))
        if not self.anim:
            self._set_scroll(target)
            return
        start, s0 = time.perf_counter(), self.scroll

        def frame():
            p = ease_out((time.perf_counter() - start) / 0.35)
            self._set_scroll(s0 + (target - s0) * p)
            if p < 1:
                self.root.after(FRAME_MS, frame)
        frame()

    def _knob(self, kind, on, force=False):
        """Slide a switch knob to its new side."""
        travel = 14
        if not (self.anim or force):
            self.knob_anim.pop(kind, None)
            self._apply_look()
            return
        if kind == "theme":                 # recolor everything right away
            self.knob_anim[kind] = -travel if on else travel
            self._apply_look()
        start = time.perf_counter()
        dur = 0.18

        def frame():
            p = ease_out((time.perf_counter() - start) / dur)
            self.knob_anim[kind] = (-travel if on else travel) * (1 - p)
            if self.view == "settings":
                self._render_body(2)
            else:
                self._render_header(2)
            if p < 1:
                self.root.after(FRAME_MS, frame)
            else:
                self.knob_anim.pop(kind, None)
                self._apply_look()
        frame()

    # ------------------------------------------------------------------- tour
    def _build_tour(self):
        w = tk.Toplevel(self.root)
        w.withdraw()
        w.overrideredirect(True)
        w.attributes("-topmost", True)
        self.tour = w
        self.tcv = tk.Canvas(w, highlightthickness=0, bd=0, width=self.px(TOUR_W),
                             height=self.px(TOUR_H))
        self.tcv.pack()
        self.tour_item = self.tcv.create_image(0, 0, anchor="nw")
        self.tcv.bind("<Button-1>", self._tour_click)
        self.tcv.bind("<Motion>", lambda e: self.tcv.config(
            cursor="hand2" if self._tour_hit(e.x, e.y) else ""))
        w.bind("<Escape>", lambda e: self.hide_tour())
        w.bind("<Right>", lambda e: self._tour_go(self.tour_step + 1))
        w.bind("<Left>", lambda e: self._tour_go(self.tour_step - 1))
        self.tour_hits = []
        self.tour_job = None
        self.tour_slide = 1.0
        self.tour_dir = 1

    def _render_tour(self):
        from PIL import ImageTk
        st = dict(phase=self.phase, amp=(self.mo or {}).get("amp", 1.8),
                  anim=self.anim and self.state["liquid"], slide=self.tour_slide,
                  dir=self.tour_dir)
        img, self.tour_hits = R.tutorial(TOUR_W, TOUR_H, self.S, self.t, self.tour_step,
                                         TOUR_STEPS, st, ss=2)
        self.tour_photo = ImageTk.PhotoImage(img)
        self.tcv.itemconfig(self.tour_item, image=self.tour_photo)

    def show_tour(self):
        if self.flyout_open():
            self.hide_flyout()
        self.tour_open = True
        self.tour_step = 0
        self.tour_slide = 1.0
        w = self.tour
        w.configure(bg=self.t["bg"])
        self.tcv.config(bg=self.t["bg"])
        self._render_tour()
        geo = lambda dy=0: self._panel_geometry(dy, TOUR_W, TOUR_H)  # noqa: E731
        if self.anim:
            w.attributes("-alpha", 0.0)
        w.geometry(geo(self._spring_px(0)))
        w.deiconify()
        round_corners(w)
        set_border_color(w, self.t["border"])
        w.lift()
        w.focus_force()
        if not self.anim:
            w.attributes("-alpha", 1.0)
            return
        start = time.perf_counter()

        def frame():
            it = time.perf_counter() - start
            w.attributes("-alpha", min(1.0, it / 0.16))
            w.geometry(geo(self._spring_px(it)))
            if it < 0.9:
                self.tour_job = self.root.after(FRAME_MS, frame)
            else:
                self.tour_job = None
                w.geometry(geo())
        self.tour_job = self.root.after(0, frame)

    def hide_tour(self, finish=True):
        if not self.tour_open:
            return
        self.tour_open = False
        if finish:
            self.state["onboarded"] = True
            self._save_state()
        if self.tour_job:
            self.root.after_cancel(self.tour_job)
            self.tour_job = None
        w = self.tour
        if not self.anim:
            w.withdraw()
            return
        start = time.perf_counter()
        geo = lambda dy=0: self._panel_geometry(dy, TOUR_W, TOUR_H)  # noqa: E731

        def frame():
            p = min(1.0, (time.perf_counter() - start) / 0.18)
            w.attributes("-alpha", 1 - p * p)
            w.geometry(geo(self.px(16) * p * p))
            if p < 1:
                self.root.after(FRAME_MS, frame)
            else:
                w.withdraw()
        frame()

    def _tour_hit(self, x, y):
        lx, ly = x / self.S, y / self.S
        for (x1, y1, x2, y2), act in self.tour_hits:
            if x1 <= lx <= x2 and y1 <= ly <= y2:
                return act
        return None

    def _tour_click(self, e):
        act = self._tour_hit(e.x, e.y)
        if act == "next":
            self._tour_go(self.tour_step + 1)
        elif act == "back":
            self._tour_go(self.tour_step - 1)
        elif act and act.startswith("dot:"):
            self._tour_go(int(act[4:]))
        elif act in ("skip", "finish"):
            self.hide_tour()

    def _tour_go(self, step):
        if not (0 <= step < len(TOUR_STEPS)) or step == self.tour_step:
            return
        self.tour_dir = 1 if step > self.tour_step else -1
        self.tour_step = step
        if not self.anim:
            self.tour_slide = 1.0
            self._render_tour()
            return
        start = time.perf_counter()

        def frame():
            self.tour_slide = min(1.0, (time.perf_counter() - start) / 0.35)
            self._render_tour()
            if self.tour_slide < 1:
                self.root.after(FRAME_MS, frame)
        frame()

    # ------------------------------------------------------------------- menu
    def _build_menu(self):
        self.auto_var = tk.BooleanVar(value=autostart_enabled())
        m = tk.Menu(self.root, tearoff=0)
        m.add_command(label="Refresh now", command=lambda: self.refresh(force=True))
        m.add_command(label="Settings…", command=self._open_settings)
        m.add_separator()
        m.add_command(label="Add ChatGPT account…", command=self._add_chatgpt)
        self.remove_menu = tk.Menu(m, tearoff=0)
        m.add_cascade(label="Remove ChatGPT account", menu=self.remove_menu)
        m.add_separator()
        m.add_checkbutton(label="Start with Windows", variable=self.auto_var,
                          command=lambda: set_autostart(self.auto_var.get()))
        m.add_command(label="Show tour", command=self.show_tour)
        m.add_separator()
        m.add_command(label="Quit", command=self.quit)
        if FROZEN:
            m.add_command(label="Uninstall AI Limits…", command=self._uninstall)
        self.menu = m

    def _open_settings(self):
        if not self.fly_open:
            self.show_flyout()
            self.root.after(int(INTRO_SEC * 1000) + 50 if self.anim else 50,
                            lambda: self.switch_view("settings"))
        else:
            self.switch_view("settings")

    def _uninstall(self):
        from tkinter import messagebox
        if messagebox.askyesno(APP_NAME, "Remove AI Limits from this PC?\n"
                               "The startup entry, shortcut and settings will be deleted."):
            uninstall()
            self.root.destroy()

    def _popup(self, e):
        self.remove_menu.delete(0, "end")
        extras = [h for h, owned in codex_homes() if owned]
        for h in extras:
            self.remove_menu.add_command(label=_account_name(h),
                                         command=lambda h=h: self._remove_chatgpt(h))
        if not extras:
            self.remove_menu.add_command(label="(no added accounts)", state="disabled")
        self.menu_open = True
        try:
            self.menu.tk_popup(e.x_root, e.y_root)
        finally:
            self.menu.grab_release()
            self.menu_open = False

    def _add_chatgpt(self):
        """Run `codex login` in a fresh CODEX_HOME folder for an extra account."""
        import shutil
        import subprocess
        if not shutil.which("codex"):
            from tkinter import messagebox
            messagebox.showinfo(APP_NAME, "Adding a ChatGPT account needs the Codex CLI.\n\n"
                                "To install it (with Node.js), run in a terminal:\n"
                                "npm install -g @openai/codex")
            return
        os.makedirs(EXTRA_CODEX_DIR, exist_ok=True)
        n = 1
        while True:
            d = os.path.join(EXTRA_CODEX_DIR, str(n))
            if not os.path.exists(os.path.join(d, "auth.json")):
                break
            n += 1
        os.makedirs(d, exist_ok=True)
        msg = ("echo Sign in with the ChatGPT account you want to ADD. & "
               "echo (If the browser opens another account, sign out first or use a private window.) & "
               "echo. & codex login -c cli_auth_credentials_store=\"file\" & echo. & "
               "echo Done. You can close this window. & pause")
        subprocess.Popen(["cmd", "/c", msg], env=dict(os.environ, CODEX_HOME=d),
                         creationflags=subprocess.CREATE_NEW_CONSOLE)
        self._watch_login(d, 0)

    def _watch_login(self, d, tries):
        if os.path.exists(os.path.join(d, "auth.json")):
            self.refresh(force=True)
        elif tries < 100:  # wait ~5 minutes
            self.root.after(3000, lambda: self._watch_login(d, tries + 1))

    def _remove_chatgpt(self, home):
        import shutil
        shutil.rmtree(home, ignore_errors=True)
        self.refresh(force=True)

    def _save_state(self):
        self.state.update(collapsed=sorted(self.collapsed))
        save_json(STATE_FILE, self.state)

    def quit(self):
        self._save_state()
        self.root.destroy()

    # ------------------------------------------------------------------- data
    def _tick(self):
        self.draw_pill()  # refresh countdowns
        if self.flyout_open() and not self.fly_job and not self.anim:
            self.render_panel()
        self.refresh()
        self.root.after(20_000, self._tick)

    def _due(self, key, force):
        now = time.time()
        if now < self.backoff.get(key, 0):
            return False
        if force:
            return True
        e = self.cache.get(key)
        return not e or now - e.get("at", 0) >= SERVICE_EVERY.get(key, 60) - 1

    def refresh(self, force=False):
        if self.busy:
            return
        due = [k for k, _ in SERVICES if self._due(k, force)]
        if not due and self.loaded:
            return
        self.busy = True
        threading.Thread(target=self._fetch_all, args=(due,), daemon=True).start()

    def _fetch_all(self, due):
        import urllib.error
        for key, fn in SERVICES:
            if key not in due:
                continue
            try:
                data = fn()
                self.cache[key] = {"data": data, "at": time.time()}
                self.errors.pop(key, None)
            except NotInstalled:            # not on this PC: don't show it
                self.cache.pop(key, None)
                self.errors.pop(key, None)
            except urllib.error.HTTPError as e:
                if e.code == 429:           # rate-limited: keep last data, back off
                    self.backoff[key] = time.time() + BACKOFF_429
                    if key not in self.cache:
                        self.errors[key] = "Busy right now — retrying in a few minutes"
                else:
                    self.errors[key] = f"Couldn't connect (HTTP {e.code})"
            except Exception as e:
                self.errors[key] = str(e) if isinstance(e, RuntimeError) else \
                    f"Couldn't connect ({type(e).__name__})"
        save_json(CACHE_FILE, self.cache)
        self.state["last_refresh"] = time.time()
        self.root.after(0, self._done)

    def _done(self):
        self.busy = False
        self.loaded = True
        self.rebuild_items()
        self.draw_pill()
        if self.flyout_open() and not self.fly_job and self.view == "main":
            self.render_panel()
            self.fly.geometry(self._panel_geometry())

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    if "--dump" in sys.argv:  # test: print to console
        for k, fn in SERVICES:
            try:
                print(k, json.dumps(fn(), ensure_ascii=False, indent=1))
            except Exception as e:
                print(k, "ERROR:", e)
    else:
        # downloaded exe opened for the first time: install, launch, exit
        if self_install():
            sys.exit(0)
        # single instance
        _mutex = ctypes.windll.kernel32.CreateMutexW(None, False, "AILimitsTaskbarWidget")
        if ctypes.windll.kernel32.GetLastError() == 183:
            sys.exit(0)
        App().run()
