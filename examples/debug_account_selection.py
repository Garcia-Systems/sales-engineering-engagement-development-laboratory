"""Compare a selected and deferred account inside AccountListBuilder.build."""

from engagement_dev.scenarios import load_chapter_three
from engagement_dev.services import AccountListBuilder


if __name__ == "__main__":
    data = load_chapter_three()
    research_capacity = data.research_capacity
    queue = AccountListBuilder().build(
        selected_market=data.selected_market,
        supported_offer=data.supported_offer,
        market_characteristics=data.market_characteristics,
        accounts=data.accounts,
        evidence=data.evidence,
        interpretations=data.interpretations,
        research_capacity=research_capacity,
    )
    selected = next(item for item in queue.evaluations if item.account_id == "blue-resort")
    deferred = next(item for item in queue.evaluations if item.account_id == "tidewater-inn")
    print(f"{selected.account_id}: {selected.status}")
    print(f"{deferred.account_id}: {deferred.status}")
