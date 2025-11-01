import pytest
from src.tractionbuild.policy.zones import Zone, mk_strategy

def test_zone_red_hashes_and_masks():
    f = mk_strategy(Zone.RED, salt="s")
    out = f("john @x.com 704-555-1234 ssn: 123-45-6789 lat: 35.23")
    assert "<email:" in out and "<phone:" in out
    assert "<id" in out and "<geo>" in out

def test_zone_green_minimal():
    g = mk_strategy(Zone.GREEN)
    out = g("call 704-555-1234 or mail john @x.com")
    assert "<phone>" in out and "<email>" in out
