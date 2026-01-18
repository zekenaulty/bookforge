from bookforge.prompt.budgeter import estimate_tokens, evaluate_budget


def test_estimate_tokens():
    assert estimate_tokens("") == 0
    assert estimate_tokens("abcd") == 1
    assert estimate_tokens("abcde") == 2


def test_evaluate_budget_reports_overages():
    budgets = {"write": {"dynamic_payload": 1, "total": 1}}
    segments = {"dynamic_payload": "abcd"}
    report = evaluate_budget("write", segments, budgets)
    assert report.sections[0].over_budget is False
    assert report.total_budget == 1
    assert report.over_budget is False

    segments = {"dynamic_payload": "abcdef"}
    report = evaluate_budget("write", segments, budgets)
    assert report.sections[0].over_budget is True
    assert report.over_budget is True
