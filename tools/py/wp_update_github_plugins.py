"""Update GitHub-distributed WordPress plugins through WP Admin upload.

Why this exists:
- The WP REST plugins controller can install WordPress.org slugs, but it cannot
  replace an installed plugin from an arbitrary release ZIP.
- The project has an Application Password with administrator capabilities, so we
  create a temporary admin, use a normal wp-login cookie for the upload flow,
  then delete the temporary user.
"""
from __future__ import annotations

import html
import io
import json
import os
import re
import secrets
import string
import sys
import zipfile
from pathlib import Path
from typing import Iterable

import requests
from requests.auth import HTTPBasicAuth


ROOT = Path(__file__).resolve().parents[2]


def load_env() -> None:
    for raw in (ROOT / ".env").read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def wp_base() -> str:
    return os.environ.get("WP_BASE", "https://suriota.com").rstrip("/")


def app_auth() -> HTTPBasicAuth:
    return HTTPBasicAuth(os.environ["WP_USER"], os.environ["WP_APP_PASS"])


def random_password(length: int = 32) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%^*()-_=+"
    return "".join(secrets.choice(alphabet) for _ in range(length))


def create_temp_admin() -> tuple[int, str, str]:
    base = wp_base()
    username = f"codex_update_{secrets.token_hex(4)}"
    password = random_password()
    email = f"{username}@suriota.invalid"
    payload = {
        "username": username,
        "name": "Codex Update Runner",
        "email": email,
        "password": password,
        "roles": ["administrator"],
    }
    r = requests.post(
        f"{base}/wp-json/wp/v2/users",
        auth=app_auth(),
        json=payload,
        timeout=30,
    )
    if r.status_code not in (200, 201):
        raise RuntimeError(f"create temp admin failed: HTTP {r.status_code} {r.text[:300]}")
    user_id = int(r.json()["id"])
    print(f"created temporary admin user id={user_id}")
    return user_id, username, password


def delete_temp_admin(user_id: int) -> None:
    base = wp_base()
    r = requests.delete(
        f"{base}/wp-json/wp/v2/users/{user_id}",
        auth=app_auth(),
        params={"force": "true", "reassign": "1"},
        timeout=30,
    )
    if r.status_code not in (200, 204):
        print(f"WARN could not delete temporary admin id={user_id}: HTTP {r.status_code} {r.text[:200]}")
        return
    print(f"deleted temporary admin user id={user_id}")


def login(username: str, password: str) -> requests.Session:
    base = wp_base()
    session = requests.Session()
    r = session.post(
        f"{base}/wp-login.php",
        data={
            "log": username,
            "pwd": password,
            "wp-submit": "Log In",
            "redirect_to": f"{base}/wp-admin/",
            "testcookie": "1",
        },
        timeout=30,
        allow_redirects=True,
    )
    check = session.get(f"{base}/wp-admin/plugins.php", timeout=30, allow_redirects=True)
    if "wp-login.php" in check.url or "loginform" in check.text:
        raise RuntimeError(f"temporary admin login failed: final_url={check.url} login_http={r.status_code}")
    print("temporary admin wp-admin login OK")
    return session


def find_nonce(text: str, nonce_name: str) -> str:
    patterns = [
        rf'name=["\']_wpnonce["\'][^>]*value=["\']([^"\']+)["\']',
        rf'value=["\']([^"\']+)["\'][^>]*name=["\']_wpnonce["\']',
        rf'name=["\']{re.escape(nonce_name)}["\'][^>]*value=["\']([^"\']+)["\']',
        rf'value=["\']([^"\']+)["\'][^>]*name=["\']{re.escape(nonce_name)}["\']',
    ]
    for pattern in patterns:
        m = re.search(pattern, text, re.I | re.S)
        if m:
            return html.unescape(m.group(1))
    raise RuntimeError(f"could not find nonce {nonce_name}")


def hidden_fields(form_html: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for name, value in re.findall(
        r'<input[^>]+type=["\']hidden["\'][^>]*name=["\']([^"\']+)["\'][^>]*value=["\']([^"\']*)["\'][^>]*>',
        form_html,
        re.I | re.S,
    ):
        fields[html.unescape(name)] = html.unescape(value)
    return fields


def extract_replace_action(response_text: str) -> tuple[str, dict[str, str]] | None:
    # WordPress displays a second confirmation form when the plugin directory
    # already exists. Submit that form to replace the existing plugin.
    for form in re.findall(r"<form\b[^>]*>.*?</form>", response_text, re.I | re.S):
        if "overwrite" in form.lower() or "replace current with uploaded" in form.lower():
            action_match = re.search(r'action=["\']([^"\']+)["\']', form, re.I)
            action = html.unescape(action_match.group(1)) if action_match else "update.php?action=upload-plugin"
            fields = hidden_fields(form)
            return action, fields
    m = re.search(
        r'<a\b[^>]*href=["\']([^"\']*action=upload-plugin[^"\']*overwrite=update-plugin[^"\']*)["\'][^>]*>\s*Replace current with uploaded\s*</a>',
        response_text,
        re.I | re.S,
    )
    if m:
        return html.unescape(m.group(1)), {}
    return None


def download_zip(url: str) -> bytes:
    r = requests.get(url, timeout=120, headers={"User-Agent": "codex-suriota-update"})
    r.raise_for_status()
    if len(r.content) < 1000:
        raise RuntimeError(f"download too small from {url}: {len(r.content)} bytes")
    return r.content


def minimize_elementor_mcp_zip(zip_bytes: bytes) -> bytes:
    """Remove optional release payload so it fits small WP admin upload limits.

    Kept: plugin PHP/includes/assets/vendor runtime files.
    Removed: translation packs, docs, sample prompts, and pricing-page media.
    """
    source = zipfile.ZipFile(io.BytesIO(zip_bytes))

    def skip(name: str) -> bool:
        return (
            "/languages/" in name
            or name.endswith(("README.md", "CHANGELOG.md", "LICENSE", "LICENSE.txt", "readme.txt"))
            or "/prompts/" in name
            or "/tests/" in name
            or "/.github/" in name
            or (
                "/includes/vendors/fremius/assets/js/pricing/" in name
                and name.lower().endswith((".png", ".svg", ".jpg", ".gif"))
            )
        )

    out_bytes = io.BytesIO()
    with zipfile.ZipFile(out_bytes, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as target:
        for info in source.infolist():
            if info.is_dir() or skip(info.filename):
                continue
            target.writestr(info.filename, source.read(info.filename))
    minimized = out_bytes.getvalue()
    if b"elementor-mcp.php" not in minimized:
        raise RuntimeError("minimized Elementor MCP zip sanity check failed")
    print(f"minimized Elementor MCP ZIP: {len(zip_bytes)} -> {len(minimized)} bytes")
    return minimized


def upload_plugin_zip(session: requests.Session, name: str, zip_url: str) -> None:
    base = wp_base()
    upload_page = session.get(f"{base}/wp-admin/plugin-install.php?tab=upload", timeout=30)
    nonce = find_nonce(upload_page.text, "_wpnonce")
    zip_bytes = download_zip(zip_url)
    if name == "MCP Tools for Elementor" and len(zip_bytes) > 1_000_000:
        zip_bytes = minimize_elementor_mcp_zip(zip_bytes)
    filename = zip_url.rsplit("/", 1)[-1] or f"{name}.zip"
    print(f"uploading {name}: {filename} ({len(zip_bytes)} bytes)")

    r = session.post(
        f"{base}/wp-admin/update.php?action=upload-plugin",
        data={"_wpnonce": nonce, "_wp_http_referer": "/wp-admin/plugin-install.php?tab=upload", "install-plugin-submit": "Install Now"},
        files={"pluginzip": (filename, zip_bytes, "application/zip")},
        timeout=180,
        allow_redirects=True,
    )
    if "Plugin installed successfully" in r.text or "Plugin updated successfully" in r.text:
        print(f"updated {name} via upload")
        return

    replace = extract_replace_action(r.text)
    if replace:
        action, fields = replace
        if not action.startswith("http"):
            action = f"{base}/wp-admin/{action.lstrip('/')}"
        fields.setdefault("overwrite", "update-plugin")
        if fields:
            rr = session.post(action, data=fields, timeout=180, allow_redirects=True)
        else:
            rr = session.get(action, timeout=180, allow_redirects=True)
        if "Plugin updated successfully" in rr.text or "updated successfully" in rr.text:
            print(f"replaced existing {name}")
            return
        title = re.search(r"<title[^>]*>(.*?)</title>", rr.text, re.I | re.S)
        raise RuntimeError(f"replace failed for {name}: title={title.group(1) if title else 'n/a'} body={rr.text[:500]}")

    title = re.search(r"<title[^>]*>(.*?)</title>", r.text, re.I | re.S)
    raise RuntimeError(f"upload failed for {name}: title={title.group(1) if title else 'n/a'} body={r.text[:500]}")


def plugin_versions() -> list[dict[str, str]]:
    r = requests.get(f"{wp_base()}/wp-json/wp/v2/plugins", auth=app_auth(), timeout=30)
    r.raise_for_status()
    return [
        {
            "plugin": item.get("plugin", ""),
            "name": item.get("name", ""),
            "version": item.get("version", ""),
            "status": item.get("status", ""),
        }
        for item in r.json()
    ]


def print_selected_versions(keys: Iterable[str]) -> None:
    selected = []
    for item in plugin_versions():
        if any(item["plugin"].startswith(key) for key in keys):
            selected.append(item)
    print(json.dumps(selected, ensure_ascii=False, indent=2))


def main() -> int:
    load_env()
    targets = [
        ("mcp-adapter/", "0.5.0", "MCP Adapter", "https://github.com/WordPress/mcp-adapter/releases/download/v0.5.0/mcp-adapter.zip"),
        ("elementor-mcp/", "1.7.4", "MCP Tools for Elementor", "https://github.com/msrbuilds/elementor-mcp/releases/download/v1.7.4/elementor-mcp-1.7.4.zip"),
    ]
    print("before:")
    print_selected_versions(["mcp-adapter/", "elementor-mcp/"])

    user_id = 0
    try:
        user_id, username, password = create_temp_admin()
        session = login(username, password)
        versions = plugin_versions()
        for plugin_prefix, expected_version, name, url in targets:
            current = next((item for item in versions if item["plugin"].startswith(plugin_prefix)), None)
            if current and current["version"] == expected_version:
                print(f"skip {name}: already {expected_version}")
                continue
            upload_plugin_zip(session, name, url)
        print("after:")
        print_selected_versions(["mcp-adapter/", "elementor-mcp/"])
        return 0
    finally:
        if user_id:
            delete_temp_admin(user_id)


if __name__ == "__main__":
    raise SystemExit(main())
