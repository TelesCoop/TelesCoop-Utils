#!/usr/bin/env python3
"""
Update SSH keys for a user across multiple VPS servers.

Reads employee info from employees.yaml, fetches the public key from GitHub,
and reads the hosts inventory from TelesCoop/ansible-ssh-config to get VPS list.

Usage:
    python update_ssh_keys.py <username>
    python update_ssh_keys.py <username> --vps vps00 vps01
    python update_ssh_keys.py <username> --dry-run
"""

import argparse
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

import yaml

EMPLOYEES_FILE = Path(__file__).parent.parent / "employees.yaml"
HOSTS_URL = "https://raw.githubusercontent.com/TelesCoop/ansible-ssh-config/main/hosts"
DEFAULT_SSH_PORT = 22


def load_employees():
    with open(EMPLOYEES_FILE) as f:
        data = yaml.safe_load(f)
    return data["employees"]


def fetch_hosts():
    """Fetch and parse Ansible inventory from GitHub.

    Returns a list of dicts: [{"name": "vps00", "host": "vps00.tlscp.fr", "port": 42722, "user": "ubuntu"}, ...]
    """
    try:
        with urllib.request.urlopen(HOSTS_URL) as response:
            content = response.read().decode("utf-8")
    except Exception as e:
        print(f"Error fetching hosts file: {e}")
        sys.exit(1)

    servers = []
    current_group = None

    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue

        group_match = re.match(r"^\[(.+)]$", line)
        if group_match:
            current_group = group_match.group(1)
            continue

        if current_group:
            parts = line.split()
            host_part = parts[0]

            # Parse host:port
            if ":" in host_part:
                host, port = host_part.rsplit(":", 1)
                port = int(port)
            else:
                host = host_part
                port = DEFAULT_SSH_PORT

            # Parse ansible_user
            user = "ubuntu"
            for part in parts[1:]:
                if part.startswith("ansible_user="):
                    user = part.split("=", 1)[1]

            servers.append({
                "name": current_group,
                "host": host,
                "port": port,
                "user": user,
            })

    return servers


def find_employee(employees, username):
    for emp in employees:
        if emp["name"] == username:
            return emp
    return None


def fetch_ssh_key(url):
    """Fetch SSH public key from a URL (e.g. GitHub)."""
    try:
        with urllib.request.urlopen(url) as response:
            keys = response.read().decode("utf-8").strip()
            if not keys:
                print(f"  Error: no keys found at {url}")
                return None
            return keys
    except Exception as e:
        print(f"  Error fetching key from {url}: {e}")
        return None


def run_ssh_command(server, command, dry_run=False):
    """Run a command on a VPS via SSH."""
    ssh_cmd = [
        "ssh",
        f"{server['user']}@{server['host']}",
        "-p", str(server["port"]),
        "-o", "ConnectTimeout=10",
        "-o", "StrictHostKeyChecking=accept-new",
        command,
    ]
    if dry_run:
        print(f"  [DRY RUN] ssh {server['user']}@{server['host']} -p {server['port']}")
        return True

    result = subprocess.run(ssh_cmd, capture_output=True, text=True, timeout=30)
    if result.returncode != 0:
        print(f"  Error: {result.stderr.strip()}")
        return False
    return True


def update_user_key(server, username, new_key, dry_run=False):
    """Update SSH key in user's own authorized_keys."""
    user_auth_keys = f"/home/{username}/.ssh/authorized_keys"

    command = (
        f"sudo mkdir -p /home/{username}/.ssh && "
        f"echo '{new_key}' | sudo tee {user_auth_keys} > /dev/null && "
        f"sudo chmod 700 /home/{username}/.ssh && "
        f"sudo chmod 600 {user_auth_keys} && "
        f"sudo chown -R {username}: /home/{username}/.ssh"
    )

    return run_ssh_command(server, command, dry_run)


def update_admin_key(server, username, new_key, dry_run=False):
    """Replace user's key in the admin user's authorized_keys."""
    admin_auth_keys = f"/home/{server['user']}/.ssh/authorized_keys"

    # Remove old key(s) for this user and add the new one
    command = (
        f"sudo sed -i '/ {username}$/d' {admin_auth_keys} && "
        f"echo '{new_key}' | sudo tee -a {admin_auth_keys} > /dev/null"
    )

    return run_ssh_command(server, command, dry_run)


def main():
    parser = argparse.ArgumentParser(description="Update SSH keys for a user on multiple VPS servers.")
    parser.add_argument("username", help="Employee username (e.g. antoine.bernier)")
    parser.add_argument(
        "--vps",
        nargs="+",
        help="VPS names to update (default: all from hosts file)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show commands without executing")
    parser.add_argument(
        "--key-url",
        help="Override SSH key URL (default: from employees.yaml)",
    )
    args = parser.parse_args()

    employees = load_employees()
    employee = find_employee(employees, args.username)

    if not employee:
        print(f"Error: user '{args.username}' not found in employees.yaml")
        print(f"Available users: {', '.join(e['name'] for e in employees)}")
        sys.exit(1)

    if employee.get("has_ssh_access") is False:
        print(f"Error: user '{args.username}' does not have SSH access (has_ssh_access: false)")
        sys.exit(1)

    key_url = args.key_url or employee.get("ssh_key")
    if not key_url:
        print(f"Error: no ssh_key URL configured for '{args.username}'")
        sys.exit(1)

    print(f"Fetching hosts from {HOSTS_URL}")
    all_servers = fetch_hosts()

    if args.vps:
        servers = [s for s in all_servers if s["name"] in args.vps]
        missing = set(args.vps) - {s["name"] for s in servers}
        if missing:
            print(f"Warning: VPS not found in hosts file: {', '.join(missing)}")
    else:
        servers = all_servers

    print(f"Target servers: {', '.join(s['name'] for s in servers)}")
    print()

    print(f"Fetching SSH keys from {key_url}")
    raw_keys = fetch_ssh_key(key_url)
    if not raw_keys:
        sys.exit(1)

    # Process all keys: append username as comment if not already present
    keys = []
    for key in raw_keys.strip().splitlines():
        key = key.strip()
        if not key:
            continue
        if not key.endswith(args.username):
            key = f"{key} {args.username}"
        keys.append(key)

    print(f"{len(keys)} key(s) found:")
    for key in keys:
        print(f"  {key[:60]}...{key[-20:]}")
    print()

    keys_content = "\n".join(keys)

    success_count = 0
    fail_count = 0

    for server in servers:
        print(f"[{server['name']}] {server['user']}@{server['host']}:{server['port']}")

        print(f"  Updating {args.username}'s authorized_keys...")
        if update_user_key(server, args.username, keys_content, args.dry_run):
            print(f"  OK - user key updated")
        else:
            print(f"  FAILED - user key")
            fail_count += 1
            continue

        print(f"  Updating {server['user']}'s authorized_keys...")
        if update_admin_key(server, args.username, keys_content, args.dry_run):
            print(f"  OK - admin key updated")
        else:
            print(f"  FAILED - admin key")
            fail_count += 1
            continue

        success_count += 1
        print()

    print(f"Done: {success_count} VPS updated, {fail_count} failures")
    if fail_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
