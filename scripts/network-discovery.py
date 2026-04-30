#!/usr/bin/env python3
"""
Scan 192.168.10.0/24, resolve hostnames, compare against NetBox.
For each discovered host not in NetBox: create an IP address record.

Writes are gated on first-batch-verify (ADR-A-011/A-015).
Run with --dry-run to preview changes; run without for writes.
"""
import argparse
import os
import subprocess
import sys
import time

import requests

NETWORK = "192.168.10.0/24"
NETBOX_URL = os.environ.get("NETBOX_URL", "http://netbox.internal")


def get_token():
    try:
        return subprocess.check_output(
            ["vault", "kv", "get", "-field=token", "secret/netbox/api"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
    except Exception:
        return os.environ.get("NETBOX_TOKEN", "")


def nmap_scan(network: str) -> list[dict]:
    """Run nmap -sn (ping scan) and parse output."""
    result = subprocess.run(
        ["nmap", "-sn", "--open", "-oG", "-", network],
        capture_output=True, text=True, timeout=120
    )
    hosts = []
    for line in result.stdout.splitlines():
        if line.startswith("Host:"):
            parts = line.split()
            ip = parts[1]
            hostname = parts[2].strip("()") if len(parts) > 2 else ""
            hosts.append({"ip": ip, "hostname": hostname})
    return hosts


def arp_scan() -> list[dict]:
    """Read macOS ARP table for passive discovery."""
    result = subprocess.run(["arp", "-a"], capture_output=True, text=True)
    hosts = []
    for line in result.stdout.splitlines():
        # Format: hostname (ip) at mac [ether] on interface
        parts = line.split()
        if len(parts) >= 2 and "(" in parts[1]:
            ip = parts[1].strip("()")
            hostname = parts[0] if parts[0] != "?" else ""
            mac = parts[3] if len(parts) > 3 and ":" in parts[3] else ""
            hosts.append({"ip": ip, "hostname": hostname, "mac": mac})
    return hosts


def get_netbox_ips(token: str) -> set[str]:
    headers = {"Authorization": f"Token {token}"}
    r = requests.get(f"{NETBOX_URL}/api/ipam/ip-addresses/?limit=1000", headers=headers)
    return {addr["address"].split("/")[0] for addr in r.json().get("results", [])}


def create_ip(token: str, ip: str, hostname: str, dry_run: bool) -> dict | None:
    if dry_run:
        print(f"  DRY-RUN: would create IP {ip} ({hostname})")
        return None
    headers = {"Authorization": f"Token {token}", "Content-Type": "application/json"}
    payload = {
        "address": f"{ip}/24",
        "status": "active",
        "dns_name": hostname or "",
        "description": "Auto-discovered by network-discovery.py",
    }
    r = requests.post(f"{NETBOX_URL}/api/ipam/ip-addresses/", headers=headers, json=payload)
    if r.status_code == 201:
        return r.json()
    print(f"  ERROR: {r.status_code} — {r.text[:200]}", file=sys.stderr)
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Preview only; no writes")
    parser.add_argument("--arp-only", action="store_true", help="Passive ARP only; no nmap")
    args = parser.parse_args()

    token = get_token()
    if not token:
        print("ERROR: cannot get NetBox token from Vault", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning {NETWORK} ...")
    if args.arp_only:
        discovered = arp_scan()
    else:
        discovered = nmap_scan(NETWORK) + arp_scan()

    # Deduplicate by IP
    seen: dict[str, dict] = {}
    for h in discovered:
        if h["ip"] not in seen:
            seen[h["ip"]] = h
    hosts = list(seen.values())
    print(f"Discovered {len(hosts)} hosts")

    existing_ips = get_netbox_ips(token)
    new_hosts = [h for h in hosts if h["ip"] not in existing_ips]
    print(f"Not in NetBox: {len(new_hosts)} hosts")

    if not new_hosts:
        print("Nothing to add.")
        return

    # First-batch-verify (ADR-A-011)
    first = new_hosts[0]
    print(f"First-batch-verify: creating {first['ip']} ({first['hostname']})")
    result = create_ip(token, first["ip"], first["hostname"], args.dry_run)
    if not args.dry_run:
        if result is None:
            print("ABORT: first-batch-verify failed — check NetBox API")
            sys.exit(1)
        time.sleep(2)
        check = get_netbox_ips(token)
        if first["ip"] not in check:
            print("ABORT: first-batch-verify failed — IP not found in NetBox after creation")
            sys.exit(1)
        print("  First-batch-verify PASSED")

    for host in new_hosts[1:]:
        create_ip(token, host["ip"], host["hostname"], args.dry_run)
        time.sleep(0.5)   # avoid rate-limit on NetBox API

    print(f"Done. Created {len(new_hosts)} IP records in NetBox.")


if __name__ == "__main__":
    main()
