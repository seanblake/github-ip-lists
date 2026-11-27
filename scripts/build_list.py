"""Build a plain-text list of GitHub's git IPv4 ranges for a UniFi network list.

Reads https://api.github.com/meta and writes one CIDR per line, plus a
status.json carrying the generation time so a consumer can tell a fresh
list from a stale one.

The list decides where a firewall lets SSH go, so a bad input must fail the
run rather than publish: an empty or shrunken list would break git, and a
very wide range would open SSH to far more than GitHub.
"""

from __future__ import annotations

import ipaddress
import json
import sys
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

META_URL = "https://api.github.com/meta"
MIN_ENTRIES = 20
# GitHub's widest git range today is a /20. Anything wider than /16 is not a
# plausible GitHub allocation and is refused rather than published.
MAX_PREFIX_WIDTH = 16
# Refuse a drop of more than half the previous count in one run; a real
# renumbering is gradual, a truncated response is not.
MAX_SHRINK_RATIO = 0.5


def fetch_git_v4() -> list[ipaddress.IPv4Network]:
    req = urllib.request.Request(
        META_URL, headers={"Accept": "application/vnd.github+json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        meta = json.load(resp)
    nets = []
    for entry in meta["git"]:
        net = ipaddress.ip_network(entry, strict=True)
        if net.version == 4:
            nets.append(net)
    return sorted(set(nets))


def validate(nets: list[ipaddress.IPv4Network], previous: int | None) -> None:
    if len(nets) < MIN_ENTRIES:
        sys.exit(f"refusing: only {len(nets)} ranges (minimum {MIN_ENTRIES})")
    for net in nets:
        if not net.is_global:
            sys.exit(f"refusing: {net} is not a public range")
        if net.prefixlen < MAX_PREFIX_WIDTH:
            sys.exit(f"refusing: {net} is wider than /{MAX_PREFIX_WIDTH}")
    if previous and len(nets) < previous * MAX_SHRINK_RATIO:
        sys.exit(f"refusing: count fell from {previous} to {len(nets)}")


def main() -> None:
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)
    list_path = out / "github-git-v4.txt"
    previous = None
    if list_path.exists():
        previous = len(list_path.read_text().split())

    nets = fetch_git_v4()
    validate(nets, previous)

    list_path.write_text("".join(f"{n}\n" for n in nets))
    status = {
        "generated_at": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": META_URL,
        "count": len(nets),
    }
    (out / "status.json").write_text(json.dumps(status, indent=2) + "\n")
    print(f"wrote {len(nets)} ranges (previous: {previous})")


if __name__ == "__main__":
    main()
