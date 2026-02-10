from bookforge.runner import _heuristic_invariant_issues


def test_invariant_contradiction_detected() -> None:
    invariants = ["Shard is present and physical."]
    summary_update = {"key_events": ["The shard dissolved into him."]}
    prose = "Kaelen staggered as the shard dissolved into his chest."
    issues = _heuristic_invariant_issues(prose, summary_update, invariants, invariants)
    assert issues

