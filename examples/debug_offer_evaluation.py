"""Focused debugger exercise: step into OfferEvaluator.evaluate and inspect its inputs."""

from engagement_dev.scenarios import load_chapter_one
from engagement_dev.services import OfferEvaluator


if __name__ == "__main__":
    data = load_chapter_one()
    offer = data.offers[0]
    result = OfferEvaluator().evaluate(offer, data.profile)
    print(f"{offer.identifier}: {result.status}")
