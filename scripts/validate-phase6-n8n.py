#!/usr/bin/env python3
"""Validate Phase 6 n8n workflow artifacts without external services."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ROUTER_PATH = ROOT / "telegram-n8n" / "workflows" / "06-router.json"
CRON_PATH = ROOT / "telegram-n8n" / "workflows" / "06-cron-resumo-diario.json"
SETUP_PATH = ROOT / "telegram-n8n" / "SETUP.md"
BACKLOG_SQL_PATH = ROOT / "mysql" / "manual-workflow" / "approve-backlog.sql"


class ValidationError(AssertionError):
    pass


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"{path.relative_to(ROOT)} is not valid JSON: {exc}") from exc


def nodes_by_name(workflow: dict) -> dict[str, dict]:
    nodes = workflow.get("nodes")
    if not isinstance(nodes, list):
        raise ValidationError("workflow.nodes must be a list")
    result = {}
    for node in nodes:
        name = node.get("name")
        if not name:
            raise ValidationError("node without name")
        if name in result:
            raise ValidationError(f"duplicate node name: {name}")
        result[name] = node
    return result


def assert_has_node(nodes: dict[str, dict], name: str, node_type: str | None = None) -> dict:
    node = nodes.get(name)
    if not node:
        raise ValidationError(f"missing node: {name}")
    if node_type and node.get("type") != node_type:
        raise ValidationError(f"{name} type is {node.get('type')!r}, expected {node_type!r}")
    return node


def assert_contains(value: str, needle: str, label: str) -> None:
    if needle not in value:
        raise ValidationError(f"{label} missing {needle!r}")


def validate_router() -> list[str]:
    router = load_json(ROUTER_PATH)
    nodes = nodes_by_name(router)
    checks: list[str] = []

    expected_types = {
        "n8n-nodes-base.telegramTrigger",
        "n8n-nodes-base.switch",
        "n8n-nodes-base.executeCommand",
        "n8n-nodes-base.mySql",
        "n8n-nodes-base.webhook",
        "n8n-nodes-base.telegram",
        "n8n-nodes-base.code",
        "n8n-nodes-base.if",
    }
    actual_types = {node.get("type") for node in router["nodes"]}
    missing_types = expected_types - actual_types
    if missing_types:
        raise ValidationError(f"router missing node types: {sorted(missing_types)}")
    checks.append("router has required n8n node types")

    settings = router.get("settings", {})
    if settings.get("timezone") != "America/Sao_Paulo":
        raise ValidationError("router timezone must be America/Sao_Paulo")
    checks.append("router timezone is America/Sao_Paulo")

    trigger = assert_has_node(nodes, "Telegram Trigger", "n8n-nodes-base.telegramTrigger")
    restrict = trigger.get("parameters", {}).get("additionalFields", {}).get("restrictToChatIds")
    if restrict != "={{ $env.TELEGRAM_CHAT_ID_ALLOWED }}":
        raise ValidationError("Telegram Trigger must restrict to TELEGRAM_CHAT_ID_ALLOWED")
    checks.append("telegram trigger restricts to TELEGRAM_CHAT_ID_ALLOWED")

    switch = assert_has_node(nodes, "Switch Comando", "n8n-nodes-base.switch")
    rules = switch.get("parameters", {}).get("rules", {}).get("values", [])
    output_keys = {rule.get("outputKey") for rule in rules}
    required_outputs = {"status", "clipes", "aprovar", "rejeitar", "processar", "ajuda"}
    if not required_outputs <= output_keys:
        raise ValidationError(f"Switch Comando missing outputs: {sorted(required_outputs - output_keys)}")
    checks.append("switch routes all six Telegram commands")

    status_query = assert_has_node(nodes, "Status: Query Stats", "n8n-nodes-base.mySql")
    assert_contains(status_query["parameters"].get("query", ""), "status='pending'", "status query")
    assert_contains(status_query["parameters"].get("query", ""), "status='approved'", "status query")
    assert_contains(status_query["parameters"].get("query", ""), "published_today", "status query")
    checks.append("/status query covers pending, approved, published_today")

    clipes_query = assert_has_node(nodes, "Clipes: Query Pending", "n8n-nodes-base.mySql")
    assert_contains(clipes_query["parameters"].get("query", ""), "WHERE status='pending'", "/clipes query")
    assert_contains(clipes_query["parameters"].get("query", ""), "LIMIT 10", "/clipes query")
    checks.append("/clipes query lists up to 10 pending clips")

    aprovar = assert_has_node(nodes, "Aprovar: UPDATE", "n8n-nodes-base.mySql")
    aprovar_query = aprovar["parameters"].get("query", "")
    assert_contains(aprovar_query, "SET status='approved'", "/aprovar query")
    assert_contains(aprovar_query, "WHERE id=", "/aprovar query")
    assert_contains(aprovar_query, "AND status='pending'", "/aprovar query")
    assert_contains(aprovar_query, "ROW_COUNT()", "/aprovar query")
    assert_has_node(nodes, "Aprovar: Arg é inteiro?", "n8n-nodes-base.if")
    checks.append("/aprovar validates integer input and guards pending status")

    rejeitar = assert_has_node(nodes, "Rejeitar: ExecuteCommand", "n8n-nodes-base.executeCommand")
    assert_contains(
        rejeitar["parameters"].get("command", ""),
        "docker exec clip-processor python -m src.rejeitar",
        "/rejeitar command",
    )
    assert_has_node(nodes, "Rejeitar: Arg é inteiro?", "n8n-nodes-base.if")
    checks.append("/rejeitar validates integer input and calls src.rejeitar")

    processar = assert_has_node(nodes, "Processar: ExecuteCommand", "n8n-nodes-base.executeCommand")
    assert_contains(
        processar["parameters"].get("command", ""),
        "docker exec clip-processor python -m src.processar",
        "/processar command",
    )
    assert_has_node(nodes, "Processar: Arg tem URL?", "n8n-nodes-base.if")
    checks.append("/processar validates URL-like input and calls src.processar")

    notify = assert_has_node(nodes, "Notify Webhook", "n8n-nodes-base.webhook")
    if notify.get("parameters", {}).get("path") != "notify":
        raise ValidationError("Notify Webhook path must be notify")
    notify_switch = assert_has_node(nodes, "Notify: Event Type", "n8n-nodes-base.switch")
    notify_rules = notify_switch.get("parameters", {}).get("rules", {}).get("values", [])
    notify_outputs = {rule.get("outputKey") for rule in notify_rules}
    required_notify = {"upload_published", "pipeline_failure", "clip_ttl_warning"}
    if not required_notify <= notify_outputs:
        raise ValidationError(f"Notify switch missing outputs: {sorted(required_notify - notify_outputs)}")
    checks.append("notify webhook routes upload, failure, and TTL warning events")

    connections = router.get("connections", {})
    for source in [
        "Telegram Trigger",
        "Parse Comando",
        "Switch Comando",
        "Notify Webhook",
        "Notify: Event Type",
    ]:
        if source not in connections:
            raise ValidationError(f"missing router connection source: {source}")
    checks.append("router has critical connection graph entries")

    return checks


def validate_cron() -> list[str]:
    cron = load_json(CRON_PATH)
    nodes = nodes_by_name(cron)
    checks: list[str] = []

    settings = cron.get("settings", {})
    if settings.get("timezone") != "America/Sao_Paulo":
        raise ValidationError("cron timezone must be America/Sao_Paulo")

    schedule = assert_has_node(nodes, "Schedule Trigger 18h BRT", "n8n-nodes-base.scheduleTrigger")
    interval = schedule.get("parameters", {}).get("rule", {}).get("interval", [])
    expression = interval[0].get("expression") if interval else None
    if expression != "0 18 * * *":
        raise ValidationError(f"cron expression is {expression!r}, expected '0 18 * * *'")
    checks.append("daily summary runs at 18h BRT")

    count = assert_has_node(nodes, "Count Pending", "n8n-nodes-base.mySql")
    assert_contains(count["parameters"].get("query", ""), "COUNT(*) AS pending", "cron count query")
    assert_contains(count["parameters"].get("query", ""), "status='pending'", "cron count query")
    checks.append("daily summary counts pending clips")

    assert_has_node(nodes, "Tem Pending?", "n8n-nodes-base.if")
    send = assert_has_node(nodes, "Enviar Resumo", "n8n-nodes-base.telegram")
    if send.get("parameters", {}).get("chatId") != "={{ $env.TELEGRAM_CHAT_ID_ALLOWED }}":
        raise ValidationError("daily summary must send to TELEGRAM_CHAT_ID_ALLOWED")
    checks.append("daily summary sends only to allowed chat")

    connections = cron.get("connections", {})
    for source in ["Schedule Trigger 18h BRT", "Count Pending", "Tem Pending?"]:
        if source not in connections:
            raise ValidationError(f"missing cron connection source: {source}")
    checks.append("daily summary has critical connection graph entries")

    return checks


def validate_docs() -> list[str]:
    checks: list[str] = []
    if not BACKLOG_SQL_PATH.exists():
        raise ValidationError("approve-backlog.sql is missing")
    sql = BACKLOG_SQL_PATH.read_text(encoding="utf-8")
    assert_contains(sql, "UPDATE generated_clips", "approve-backlog.sql")
    assert_contains(sql, "SET status = 'approved'", "approve-backlog.sql")
    assert_contains(sql, "WHERE status = 'pending'", "approve-backlog.sql")
    checks.append("approve-backlog.sql is present and guarded to pending clips")

    setup = SETUP_PATH.read_text(encoding="utf-8")
    for term in [
        "Cloudflare Tunnel",
        "CLOUDFLARE_TUNNEL_TOKEN",
        "TELEGRAM_WEBHOOK_SECRET",
        "setWebhook",
        "06-router.json",
        "06-cron-resumo-diario.json",
    ]:
        assert_contains(setup, term, "SETUP.md")
    checks.append("SETUP.md documents Cloudflare, Telegram webhook, and workflow import")

    return checks


def main() -> int:
    validators = [
        ("router", validate_router),
        ("cron", validate_cron),
        ("docs", validate_docs),
    ]

    print("=== Phase 6 n8n artifact validation ===")
    try:
        for label, validator in validators:
            for check in validator():
                print(f"PASS [{label}] {check}")
    except ValidationError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1

    print("OK: Phase 6 n8n artifacts are structurally valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
