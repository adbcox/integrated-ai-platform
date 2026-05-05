#!/usr/bin/env python3
"""Provision Zabbix monitoring for QNAP Syncthing."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

ROOT_DIR = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT_DIR / "config/zabbix/templates/qnap-syncthing.yaml"
ZABBIX_API_URL = os.environ.get("ZABBIX_API_URL", "http://127.0.0.1:10080/api_jsonrpc.php")
TARGET_HOST = os.environ.get("TARGET_HOST_NAME", "qnap-ts-x72")
LEGACY_ITEM_KEYS = [
    "d17119.syncthing.rest.alive",
    "d17119.syncthing.folder.state",
    "d17119.syncthing.folder.need_files",
    "d17119.syncthing.folder.need_bytes",
    "d17119.syncthing.system.uptime",
]
LEGACY_TRIGGER_DESCRIPTIONS = [
    "QNAP Syncthing REST unreachable",
    "QNAP Syncthing folder error state",
    "QNAP Syncthing sync stalled",
    "QNAP Syncthing pending bytes excessive",
    "QNAP Syncthing OOM-restart pattern",
]

SEVERITY_MAP = {
    "not_classified": 0,
    "info": 1,
    "warning": 2,
    "average": 3,
    "high": 4,
    "disaster": 5,
}

VALUE_TYPE_MAP = {
    "numeric": 3,
    "text": 4,
}


def run(cmd: list[str]) -> str:
    return subprocess.check_output(cmd, text=True).strip()


def resolve_admin_vault_token() -> str:
    cmd = [
        "bash",
        "-lc",
        f"source {ROOT_DIR}/scripts/lib/vault-admin-token.sh >/dev/null 2>&1 && resolve_admin_vault_token",
    ]
    return run(cmd)


def vault_kv_get(field: str, path: str, vault_token: str) -> str:
    cmd = [
        "docker",
        "exec",
        "-e",
        f"VAULT_TOKEN={vault_token}",
        "vault-server",
        "vault",
        "kv",
        "get",
        f"-field={field}",
        path,
    ]
    return run(cmd)


def zabbix_token(vault_token: str) -> str:
    return vault_kv_get("api_token", "secret/zabbix/exporter", vault_token)


def zbx(method: str, params: dict, token: str) -> dict:
    req = urllib.request.Request(
        ZABBIX_API_URL,
        data=json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode(),
        headers={
            "Content-Type": "application/json-rpc",
            "Authorization": f"Bearer {token}",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Zabbix API HTTP {exc.code}: {exc.read().decode()}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Zabbix API unreachable: {exc}") from exc
    if "error" in body:
        raise RuntimeError(f"Zabbix API error for {method}: {body['error']}")
    return body["result"]


def ensure_group(name: str, token: str) -> str:
    result = zbx("templategroup.get", {"output": ["groupid"], "filter": {"name": [name]}}, token)
    if result:
        return result[0]["groupid"]
    created = zbx("templategroup.create", {"name": name}, token)
    return created["groupids"][0]


def ensure_template(name: str, groupid: str, token: str) -> str:
    result = zbx("template.get", {"output": ["templateid", "host"], "filter": {"host": [name]}}, token)
    if result:
        return result[0]["templateid"]
    created = zbx(
        "template.create",
        {"host": name, "groups": [{"groupid": groupid}]},
        token,
    )
    return created["templateids"][0]


def ensure_host(name: str, token: str) -> str:
    result = zbx("host.get", {"output": ["hostid", "host", "name"], "filter": {"host": [name]}}, token)
    if result:
        return result[0]["hostid"]
    raise RuntimeError(f"Zabbix host {name!r} not found")


def ensure_macro(templateid: str, macro_spec: dict, vault_token: str, token: str) -> None:
    macro = macro_spec["macro"]
    value = macro_spec.get("value")
    vault_spec = macro_spec.get("vault")
    if vault_spec:
        value = vault_kv_get(vault_spec["field"], vault_spec["path"], vault_token)
    if value is None:
        raise RuntimeError(f"macro {macro} has no value")
    existing = zbx(
        "usermacro.get",
        {"output": ["hostmacroid"], "hostids": [templateid], "filter": {"macro": macro}},
        token,
    )
    if existing:
        zbx("usermacro.update", {"hostmacroid": existing[0]["hostmacroid"], "value": value}, token)
    else:
        zbx("usermacro.create", {"hostid": templateid, "macro": macro, "value": value}, token)


def item_payload(templateid: str, item_spec: dict) -> dict:
    payload = {
        "hostid": templateid,
        "name": item_spec["name"],
        "key_": item_spec["key"],
        "type": 2,
        "value_type": VALUE_TYPE_MAP[item_spec["value_type"]],
        "delay": "0",
        "preprocessing": [],
    }
    return payload


def ensure_item(targetid: str, item_spec: dict, token: str) -> None:
    key = item_spec["key"]
    existing = zbx(
        "item.get",
        {"output": ["itemid"], "hostids": [targetid], "filter": {"key_": key}},
        token,
    )
    payload = item_payload(targetid, item_spec)
    if existing:
        payload["itemid"] = existing[0]["itemid"]
        payload.pop("hostid", None)
        zbx("item.update", payload, token)
    else:
        zbx("item.create", payload, token)


def severity_num(name: str) -> int:
    try:
        return SEVERITY_MAP[name]
    except KeyError as exc:
        raise RuntimeError(f"unknown severity {name!r}") from exc


def ensure_trigger(targetid: str, trigger_spec: dict, token: str) -> None:
    desc = trigger_spec["name"]
    expr = trigger_spec["expression"]
    existing = zbx(
        "trigger.get",
        {"output": ["triggerid"], "hostids": [targetid], "filter": {"description": [desc]}},
        token,
    )
    payload = {
        "description": desc,
        "expression": expr,
        "priority": severity_num(trigger_spec["severity"]),
    }
    if existing:
        zbx("trigger.delete", [entry["triggerid"] for entry in existing], token)
    payload["status"] = 0
    zbx("trigger.create", payload, token)


def link_template_to_host(hostid: str, templateid: str, token: str) -> None:
    host = zbx("host.get", {"output": ["hostid"], "hostids": [hostid], "selectParentTemplates": ["templateid"]}, token)[0]
    linked = {tpl["templateid"] for tpl in host.get("parentTemplates", [])}
    if templateid in linked:
        return
    zbx("host.update", {"hostid": hostid, "templates": [{"templateid": templateid}]}, token)


def cleanup_legacy_artifacts(templateid: str, targetid: str, token: str) -> None:
    legacy_items = zbx(
        "item.get",
        {
            "output": ["itemid", "key_"],
            "hostids": [templateid],
            "filter": {"key_": LEGACY_ITEM_KEYS},
        },
        token,
    )
    if legacy_items:
        zbx("item.delete", [entry["itemid"] for entry in legacy_items], token)

    legacy_triggers = zbx(
        "trigger.get",
        {
            "output": ["triggerid"],
            "hostids": [templateid],
            "filter": {"description": LEGACY_TRIGGER_DESCRIPTIONS},
        },
        token,
    )
    if legacy_triggers:
        zbx("trigger.delete", [entry["triggerid"] for entry in legacy_triggers], token)


def ensure_collector_script() -> None:
    script = ROOT_DIR / "scripts/qnap-syncthing-zabbix-sender.sh"
    if script.exists():
        return
    raise RuntimeError(
        "collector script missing: scripts/qnap-syncthing-zabbix-sender.sh must exist before provisioning"
    )


def main() -> int:
    spec = yaml.safe_load(SPEC_PATH.read_text())
    template_spec = spec["template"]

    vault_token = resolve_admin_vault_token()
    token = zabbix_token(vault_token)

    groupid = ensure_group(template_spec["group"], token)
    templateid = ensure_template(template_spec["name"], groupid, token)

    for macro_spec in template_spec.get("macros", []):
        ensure_macro(templateid, macro_spec, vault_token, token)

    hostid = ensure_host(template_spec["host"], token)

    for item_spec in template_spec.get("items", []):
        ensure_item(hostid, item_spec, token)

    for trigger_spec in template_spec.get("triggers", []):
        ensure_trigger(hostid, trigger_spec, token)

    link_template_to_host(hostid, templateid, token)
    cleanup_legacy_artifacts(templateid, hostid, token)
    ensure_collector_script()

    print(f"[qnap-syncthing] provisioned template {template_spec['name']} on host {template_spec['host']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
