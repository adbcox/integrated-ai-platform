"""Seam tests for LEDT-P6-PACKET-ROUTING-METADATA-SEAM-1."""
from __future__ import annotations
import json, sys
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))
from framework.packet_routing_metadata import PacketRoutingMetadata, PacketRoutingMetadataBuilder, ROUTING_POLICY_VERSION

def test_import_builder():
    assert callable(PacketRoutingMetadataBuilder)

def test_default_is_local_first():
    r = PacketRoutingMetadataBuilder().build("test")
    assert r.preferred_executor == "local_first"
    assert r.claude_fallback_allowed is False
    assert r.local_exec_allowed is True

def test_claude_only_sets_fallback_allowed():
    r = PacketRoutingMetadataBuilder().build("test", override_executor="claude_only")
    assert r.preferred_executor == "claude_only"
    assert r.claude_fallback_allowed is True

def test_local_first_not_fallback_allowed():
    r = PacketRoutingMetadataBuilder().build("test")
    assert r.claude_fallback_allowed is False

def test_routing_policy_version():
    r = PacketRoutingMetadataBuilder().build("test")
    assert r.routing_policy_version == ROUTING_POLICY_VERSION

def test_emit_local_first_rate(tmp_path):
    b = PacketRoutingMetadataBuilder()
    records = [b.build(f"p{i}") for i in range(4)] + [b.build("ex", override_executor="claude_only")]
    path = b.emit(records, tmp_path)
    d = json.loads(Path(path).read_text())
    assert d["local_first_rate"] >= 0.8
    assert d["claude_only_count"] <= 1
    assert all(r["routing_policy_version"] == ROUTING_POLICY_VERSION for r in d["records"])
