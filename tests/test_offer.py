from dataclasses import FrozenInstanceError

import pytest

from engagement_dev.domain import Capability, ServiceOffer
from engagement_dev.scenarios import chapter_one_report, load_chapter_one
from engagement_dev.scenarios.chapter_one import PROBLEM_CLASSES
from engagement_dev.services import OfferEvaluationStatus, OfferEvaluator


def test_capabilities_and_boundaries_are_immutable_and_deterministic():
    first = load_chapter_one().profile
    second = load_chapter_one().profile
    assert first.capabilities == second.capabilities
    assert first.boundaries == second.boundaries
    with pytest.raises(FrozenInstanceError):
        first.capabilities[0].name = "Changed"  # type: ignore[misc]


def test_proof_references_only_profile_capabilities():
    profile = load_chapter_one().profile
    known = {capability.identifier for capability in profile.capabilities}
    assert all(set(proof.capability_ids) <= known for proof in profile.proof_artifacts)


def test_unknown_capability_cannot_silently_become_supported():
    data = load_chapter_one()
    offer = ServiceOffer(
        "unknown", "We investigate a bounded security question.", ("security-audit",),
        (PROBLEM_CLASSES["TECHNICAL_EVALUATION"],), ("workflow-prototype",), data.profile.boundaries,
    )
    result = OfferEvaluator().evaluate(offer, data.profile)
    assert result.status is OfferEvaluationStatus.OUTSIDE_CAPABILITY
    assert result.findings == ("Capability 'security-audit' is not in the provider profile.",)


def test_problem_classes_require_a_relevant_selected_capability():
    data = load_chapter_one()
    offer = ServiceOffer(
        "mismatch", "We investigate a synchronization question.", ("web",),
        (PROBLEM_CLASSES["DATA_SYNCHRONIZATION"],), ("workflow-prototype",), data.profile.boundaries,
    )
    assert OfferEvaluator().evaluate(offer, data.profile).status is OfferEvaluationStatus.OUTSIDE_CAPABILITY


def test_selected_capability_requires_selected_proof():
    data = load_chapter_one()
    unproved = Capability("new-skill", "New skill", "Not demonstrated")
    profile = type(data.profile)(
        data.profile.provider_name, data.profile.capabilities + (unproved,), data.profile.proof_artifacts, data.profile.boundaries
    )
    offer = ServiceOffer(
        "unproved", "We investigate a bounded technical question.", ("new-skill",),
        (type(PROBLEM_CLASSES["TECHNICAL_EVALUATION"])("NEW", "New", "New problem", ("new-skill",)),),
        (), data.profile.boundaries,
    )
    assert OfferEvaluator().evaluate(offer, profile).status is OfferEvaluationStatus.INSUFFICIENT_PROOF


def test_scenario_supported_vague_and_overclaimed_results_are_explicit():
    data = load_chapter_one()
    results = {offer.identifier: OfferEvaluator().evaluate(offer, data.profile) for offer in data.offers}
    assert results["A"].status is OfferEvaluationStatus.SUPPORTED
    assert results["B"].status is OfferEvaluationStatus.OVERCLAIMED
    assert results["C"].status is OfferEvaluationStatus.OVERCLAIMED
    assert results["D"].status is OfferEvaluationStatus.SUPPORTED
    vague = ServiceOffer("vague", "We build software.", (), (), (), data.profile.boundaries)
    assert OfferEvaluator().evaluate(vague, data.profile).status is OfferEvaluationStatus.NO_PROBLEM_CLASS


def test_evaluation_explanations_and_cli_output_are_deterministic():
    data = load_chapter_one()
    evaluator = OfferEvaluator()
    assert evaluator.evaluate(data.offers[0], data.profile) == evaluator.evaluate(data.offers[0], data.profile)
    assert chapter_one_report() == chapter_one_report()
    assert "Northstar Systems Studio" in chapter_one_report()
    assert chapter_one_report().count("SUPPORTED\n") == 2
    assert "OVERCLAIMED" in chapter_one_report()
