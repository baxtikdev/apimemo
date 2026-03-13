from __future__ import annotations

from apimemo.pricing import calculate_cost


class TestCalculateCost:
    def test_exact_match(self) -> None:
        cost = calculate_cost("gpt-4o", 1_000_000, 0)
        assert cost == 2.50

    def test_output_cost(self) -> None:
        cost = calculate_cost("gpt-4o", 0, 1_000_000)
        assert cost == 10.00

    def test_mixed(self) -> None:
        cost = calculate_cost("gpt-4o", 500_000, 500_000)
        assert cost == (500_000 * 2.50 + 500_000 * 10.00) / 1_000_000

    def test_small_tokens(self) -> None:
        cost = calculate_cost("gpt-4o", 100, 50)
        expected = (100 * 2.50 + 50 * 10.00) / 1_000_000
        assert abs(cost - expected) < 1e-10

    def test_unknown_model(self) -> None:
        cost = calculate_cost("unknown-model-xyz", 100, 100)
        assert cost is None

    def test_fuzzy_match_substring(self) -> None:
        cost = calculate_cost("gpt-4o-2024-11-20", 1_000_000, 0)
        assert cost == 2.50

    def test_anthropic_pricing(self) -> None:
        cost = calculate_cost("claude-3-5-sonnet-20241022", 1_000_000, 1_000_000)
        assert cost == 3.00 + 15.00

    def test_google_pricing(self) -> None:
        cost = calculate_cost("gemini-2.0-flash", 1_000_000, 1_000_000)
        assert cost == 0.10 + 0.40

    def test_zero_tokens(self) -> None:
        cost = calculate_cost("gpt-4o", 0, 0)
        assert cost == 0.0

    def test_groq_pricing(self) -> None:
        cost = calculate_cost("llama-3.1-70b-versatile", 1_000_000, 1_000_000)
        assert cost == 0.59 + 0.79
