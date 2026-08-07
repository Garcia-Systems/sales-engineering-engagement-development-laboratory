"""Focused debugger exercise: step into MarketEvaluator.evaluate and inspect one market."""

from engagement_dev.scenarios import load_chapter_two
from engagement_dev.services import MarketEvaluator


if __name__ == "__main__":
    data = load_chapter_two()
    candidate = data.candidates[0]
    result = MarketEvaluator().evaluate(
        supported_offer=data.supported_offer,
        profile=data.profile,
        market=candidate.market,
        characteristics=candidate.characteristics,
        evidence=candidate.evidence,
        excluded_boundary_ids=candidate.excluded_boundary_ids,
    )
    print(f"{candidate.market.name}: {result.priority}")
