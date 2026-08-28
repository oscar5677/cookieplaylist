#!/usr/bin/env python3
"""
Fetches an M3U playlist and converts it into a JSON list of channels.

Each M3U entry looks like:

#EXTINF:-1 tvg-id="461" tvg-name="Star Sports Select 2 HD" tvg-logo="..." group-title="Sports",Star Sports Select 2 HD
#KODIPROP:inputstream.adaptive.manifest_type=mpd
#KODIPROP:inputstream.adaptive.license_type=clearkey
#KODIPROP:inputstream.adaptive.license_key=https://.../license/461/
#EXTVLCOPT:http-user-agent=...
#EXTHTTP:{"cookie":"__hdnea__=..."}
https://.../index.mpd?|Cookie=...&xxx=...

Output entries look like:

{
    "name": "Star Sports Select 2 HD",
    "id": "461",
    "category": "Sports",
    "url": "https://.../index.mpd",
    "cookie": "__hdnea__=...",
    "logo": "https://..."
}
"""

import json
import re
import sys
import urllib.request

M3U_URL = "https://raw.githubusercontent.com/Sflex0719/STBPLUS/refs/heads/main/Zio.m3u"
OUTPUT_FILE = "channels.json"

TVG_ID_RE = re.compile(r'tvg-id="([^"]*)"')
TVG_NAME_RE = re.compile(r'tvg-name="([^"]*)"')
TVG_LOGO_RE = re.compile(r'tvg-logo="([^"]*)"')
GROUP_TITLE_RE = re.compile(r'group-title="([^"]*)"')
TITLE_RE = re.compile(r",([^,]*)$")


def fetch_m3u(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def parse_m3u(content: str):
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    channels = []
    current = {}

    for line in lines:
        if line.startswith("#EXTM3U"):
            continue

        if line.startswith("#EXTINF"):
            current = {}
            id_match = TVG_ID_RE.search(line)
            name_match = TVG_NAME_RE.search(line)
            logo_match = TVG_LOGO_RE.search(line)
            group_match = GROUP_TITLE_RE.search(line)
            title_match = TITLE_RE.search(line)

            current["id"] = id_match.group(1) if id_match else ""
            current["name"] = (
                name_match.group(1)
                if name_match
                else (title_match.group(1).strip() if title_match else "")
            )
            current["logo"] = logo_match.group(1) if logo_match else ""
            current["category"] = group_match.group(1) if group_match else ""
            current["cookie"] = ""
            continue

        if line.startswith("#EXTHTTP"):
            try:
                payload = json.loads(line.split(":", 1)[1])
                current["cookie"] = payload.get("cookie", "")
            except (json.JSONDecodeError, IndexError):
                pass
            continue

        if line.startswith("#"):
            # #KODIPROP, #EXTVLCOPT, etc. — ignored
            continue

        if line.startswith("http"):
            # Strip the trailing "|Cookie=...&xxx=..." part, keep the raw stream URL
            url_part = line.split("?|", 1)[0]
            channels.append(
                {
                    "name": current.get("name", ""),
                    "id": current.get("id", ""),
                    "category": current.get("category", ""),
                    "url": url_part,
                    "cookie": current.get("cookie", ""),
                    "logo": current.get("logo", ""),
                }
            )
            current = {}

    return channels


def main():
    try:
        content = fetch_m3u(M3U_URL)
    except Exception as exc:  # noqa: BLE001
        print(f"Failed to fetch M3U: {exc}", file=sys.stderr)
        sys.exit(1)

    channels = parse_m3u(content)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(channels, f, indent=2, ensure_ascii=False)

    print(f"Wrote {len(channels)} channels to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
