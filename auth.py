"""One-time auth helper for trypeggy/instagram_dm_mcp.

Trypeggy's server calls `client.login(username, password)` unconditionally on
startup with no 2FA handling. If the account has 2FA enabled, that call raises
TwoFactorRequired and the server exits before MCP transport opens.

This script runs the login flow OUTSIDE the server and writes the session file
that trypeggy loads on startup. Two modes:

  Interactive (terminal):
    python auth.py [--username U] [--password P]
    Prompts for 2FA code on stdin if Instagram challenges.

  From-browser (driven by OpenSwarm Electron):
    python auth.py --from-browser
    Reads {"sessionid": "...", "ds_user_id": "...", "cookies": {...}} on stdin,
    builds an instagrapi session from those cookies, validates via
    account_info(), saves session, prints JSON result on stdout.

After a successful run, the MCP server can boot via:
    python src/mcp_server.py
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import sys
from pathlib import Path
from urllib.parse import unquote

from dotenv import load_dotenv
from instagrapi import Client
from instagrapi.exceptions import (
    BadPassword,
    ChallengeRequired,
    TwoFactorRequired,
)


def _from_browser(session_dir: Path) -> int:
    """Build session from browser cookies. Reads JSON on stdin, writes JSON on stdout."""
    def _dbg(msg: str) -> None:
        print(f"[auth-from-browser] {msg}", file=sys.stderr, flush=True)

    _dbg("entry")
    try:
        payload = json.loads(sys.stdin.read())
    except json.JSONDecodeError as e:
        print(json.dumps({"ok": False, "error": f"invalid JSON on stdin: {e}"}))
        return 1

    sid = unquote(payload.get("sessionid", ""))
    ds_user_id = payload.get("ds_user_id", "")
    all_cookies: dict = payload.get("cookies", {})
    _dbg(f"sid_len={len(sid)} ds_user_id={ds_user_id!r} cookies={list(all_cookies.keys())}")

    if not sid:
        print(json.dumps({"ok": False, "error": "sessionid missing from payload"}))
        return 1

    cl = Client()
    cl.delay_range = [1, 3]
    for name, value in all_cookies.items():
        cl.private.cookies.set(name, unquote(str(value)), domain=".instagram.com")
    _dbg(f"cookies set on client: {list(cl.private.cookies.get_dict().keys())}")

    try:
        cl.login_by_sessionid(sid)
        _dbg(f"login_by_sessionid OK, user_id={cl.user_id!r}")
    except Exception as e:  # noqa: BLE001
        _dbg(f"login_by_sessionid raised: {type(e).__name__}: {e}")

    # Try multiple resolution strategies in order; first one to give us a
    # username wins.
    username: str | None = None
    last_err: str | None = None

    # Strategy 1: account_info() (private mobile API current-user endpoint)
    try:
        info = cl.account_info()
        username = info.username
        _dbg(f"account_info OK, username={username!r}")
    except Exception as e:  # noqa: BLE001
        last_err = f"account_info: {type(e).__name__}: {e}"
        _dbg(last_err)

    # Strategy 2: user_info_by_id with the ds_user_id from cookies
    if not username and ds_user_id:
        try:
            info = cl.user_info_v1(int(ds_user_id))
            username = info.username
            _dbg(f"user_info_v1 OK, username={username!r}")
        except Exception as e:  # noqa: BLE001
            last_err = f"user_info_v1: {type(e).__name__}: {e}"
            _dbg(last_err)

    # Strategy 3: hit the mobile API user info endpoint directly with the
    # browser cookies. Same endpoint as Strategy 2 but bypasses instagrapi's
    # response parser, which sometimes breaks on schema drift.
    if not username and ds_user_id:
        try:
            import requests
            r = requests.get(
                f"https://i.instagram.com/api/v1/users/{ds_user_id}/info/",
                headers={
                    "User-Agent": cl.user_agent,
                    "X-IG-App-ID": "936619743392459",
                },
                cookies={
                    name: unquote(str(value)) for name, value in all_cookies.items()
                },
                timeout=10,
            )
            _dbg(f"strategy 3 (raw mobile API) HTTP {r.status_code} body_first_120={r.text[:120]!r}")
            if r.status_code == 200:
                data = r.json()
                username = data.get("user", {}).get("username")
                if username:
                    _dbg(f"strategy 3 OK, username={username!r}")
            else:
                last_err = f"raw mobile API: HTTP {r.status_code}"
        except Exception as e:  # noqa: BLE001
            last_err = f"raw mobile API: {type(e).__name__}: {e}"
            _dbg(last_err)

    # Strategy 4: web HTML endpoint with a desktop Chrome user-agent. Different
    # anti-abuse weighting than the mobile API; sometimes works when 467s the
    # private endpoints.
    if not username:
        try:
            import re
            import requests
            r = requests.get(
                "https://www.instagram.com/",
                headers={
                    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                },
                cookies={
                    name: unquote(str(value)) for name, value in all_cookies.items()
                },
                timeout=15,
            )
            _dbg(f"strategy 4 (web HTML) HTTP {r.status_code} body_len={len(r.text)}")
            if r.status_code == 200:
                # Several patterns IG embeds the viewer's username in
                for pattern in [
                    r'"viewer":\{[^}]*?"username":"([^"]+)"',
                    r'"username":"([^"]+)","is_verified":(?:true|false),"profile_pic_url"',
                    r'<meta property="og:url" content="https://www\.instagram\.com/([^/"]+)/?"',
                ]:
                    m = re.search(pattern, r.text)
                    if m:
                        username = m.group(1)
                        _dbg(f"strategy 4 matched pattern, username={username!r}")
                        break
                if not username:
                    last_err = "web HTML: page loaded but no username pattern matched"
                    _dbg(last_err)
            else:
                last_err = f"web HTML: HTTP {r.status_code}"
        except Exception as e:  # noqa: BLE001
            last_err = f"web HTML: {type(e).__name__}: {e}"
            _dbg(last_err)

    if not username:
        print(json.dumps({
            "ok": False,
            "error": (
                f"could not resolve account ({last_err or 'unknown'}). "
                "Instagram is likely anti-abuse-blocking this account or IP "
                "(HTTP 467 = Feedback Required). Typical fix: wait 4-24 hours, "
                "use a different network, or sign in with a different account."
            ),
        }))
        return 1

    session_file = session_dir / f"{username}_session.json"
    try:
        cl.dump_settings(session_file)
    except Exception as e:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": f"failed to save session: {e}"}))
        return 1

    try:
        (session_dir / "current_user.txt").write_text(username)
    except Exception:  # noqa: BLE001
        pass

    _dbg(f"success, saved {session_file}")
    print(json.dumps({
        "ok": True,
        "username": username,
        "user_id": str(cl.user_id) if cl.user_id else ds_user_id,
        "session_file": str(session_file),
    }))
    return 0


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description="One-time IG auth for trypeggy MCP")
    parser.add_argument("--username", default=os.getenv("INSTAGRAM_USERNAME"))
    parser.add_argument("--password", default=os.getenv("INSTAGRAM_PASSWORD"))
    parser.add_argument(
        "--session-dir",
        default=str(Path.home() / ".instagram_dm_mcp" / "sessions"),
        help="Where to write {username}_session.json (default: ~/.instagram_dm_mcp/sessions/)",
    )
    parser.add_argument(
        "--from-browser",
        action="store_true",
        help="Read browser cookies JSON on stdin, save session, exit",
    )
    args = parser.parse_args()

    session_dir = Path(args.session_dir)
    session_dir.mkdir(parents=True, exist_ok=True)

    if args.from_browser:
        return _from_browser(session_dir)

    username = args.username or input("Instagram username: ").strip()
    password = args.password or getpass.getpass("Instagram password: ")

    if not username or not password:
        print("ERROR: username and password are required", file=sys.stderr)
        return 1

    session_file = session_dir / f"{username}_session.json"

    cl = Client()
    cl.delay_range = [1, 3]

    # If a session already exists and still works, we are done.
    if session_file.exists():
        try:
            cl.load_settings(session_file)
            cl.get_timeline_feed()
            print(f"Existing session at {session_file} is valid. Nothing to do.")
            return 0
        except Exception as e:  # noqa: BLE001
            print(f"Existing session invalid ({type(e).__name__}: {e}); re-authenticating.")
            cl = Client()
            cl.delay_range = [1, 3]

    print(f"Logging in as @{username}...")
    try:
        cl.login(username, password)
    except TwoFactorRequired:
        print("Two-factor required.")
        last = getattr(cl, "last_json", {}) or {}
        tfi = last.get("two_factor_info", {}) or {}
        if tfi.get("sms_two_factor_on"):
            phone = tfi.get("obfuscated_phone_number") or "your phone"
            print(f"An SMS code should have been sent to {phone}.")
        elif tfi.get("totp_two_factor_on"):
            print("Use the 6-digit code from your authenticator app.")
        else:
            print("Use the code from whichever 2FA method is enabled on your account.")
        code = input("2FA code: ").strip()
        if not code:
            print("ERROR: no code provided", file=sys.stderr)
            return 1
        try:
            cl.login(username, password, verification_code=code)
        except Exception as e:  # noqa: BLE001
            print(f"ERROR: 2FA login failed: {type(e).__name__}: {e}", file=sys.stderr)
            return 1
    except BadPassword:
        print("ERROR: wrong password", file=sys.stderr)
        return 1
    except ChallengeRequired as e:
        print(
            "ERROR: Instagram is asking for an extra verification step we can't handle "
            "here. Open instagram.com in a browser, sign in, complete any prompts "
            "(check the email-or-app challenge), then rerun this script.\n"
            f"Details: {e}",
            file=sys.stderr,
        )
        return 1
    except Exception as e:  # noqa: BLE001
        print(f"ERROR: {type(e).__name__}: {e}", file=sys.stderr)
        return 1

    cl.dump_settings(session_file)
    try:
        (Path(args.session_dir) / "current_user.txt").write_text(username)
    except Exception:  # noqa: BLE001
        pass
    print(f"Session saved to {session_file}")
    print("Done. The MCP server can now boot without prompting for 2FA again.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
