from src.tractionbuild.core.budget import TokenBudget

def test_budget_hard_and_soft():
    b = TokenBudget(hard_cap=100, soft_cap=60)
    assert b.can_spend(50)
    b.in_tokens = 40; b.out_tokens = 10
    assert b.over_soft() is False
    b.out_tokens = 25
    assert b.over_soft() is True
    assert b.can_spend(40) is False  # 40+25+40 > 100