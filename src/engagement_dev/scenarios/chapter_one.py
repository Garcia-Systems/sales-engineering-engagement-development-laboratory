"""Chapter 1's fixed provider, offer candidates, and readable report."""

from dataclasses import dataclass

from engagement_dev.domain import (
    Capability,
    CapabilityProfile,
    OfferBoundary,
    ProblemClass,
    ProofArtifact,
    ServiceOffer,
)
from engagement_dev.services import OfferEvaluation, OfferEvaluator


CAPABILITIES = (
    Capability("python", "Python application development", "Build maintainable Python applications."),
    Capability("web", "Web application development", "Build focused browser-based tools."),
    Capability("api", "REST API integration", "Connect documented HTTP APIs and handle failures."),
    Capability("data", "Relational data modeling", "Model transactional relational data."),
    Capability("automation", "Workflow automation", "Prototype repeatable operational workflows."),
    Capability("testing", "Automated testing", "Create deterministic automated verification."),
    Capability("prototype", "Technical prototyping", "Test technical feasibility before implementation."),
)

PROBLEM_CLASSES = {
    "SYSTEM_INTEGRATION": ProblemClass(
        "SYSTEM_INTEGRATION", "System integration", "Disconnected software and manual handoffs.", ("api", "data", "prototype")
    ),
    "MANUAL_WORKFLOW": ProblemClass(
        "MANUAL_WORKFLOW", "Manual workflow", "Repeated information processing or data transfer.", ("automation", "web", "prototype")
    ),
    "DATA_SYNCHRONIZATION": ProblemClass(
        "DATA_SYNCHRONIZATION", "Data synchronization", "Systems whose data must remain consistent.", ("api", "data", "testing")
    ),
    "INTERNAL_TOOLING": ProblemClass(
        "INTERNAL_TOOLING", "Internal tooling", "Focused tools supporting internal work.", ("python", "web", "data")
    ),
    "TECHNICAL_EVALUATION": ProblemClass(
        "TECHNICAL_EVALUATION", "Technical evaluation", "Uncertainty requiring a bounded prototype.", ("prototype", "testing")
    ),
    "PROCESS_VISIBILITY": ProblemClass(
        "PROCESS_VISIBILITY", "Process visibility", "Limited visibility across an operational process.", ("web", "data", "api")
    ),
}

PROOF = (
    ProofArtifact(
        "inventory-lab", "Inventory Synchronization Laboratory",
        "Fictional educational artifact demonstrating event processing, failure handling, and tests.",
        ("python", "api", "data", "testing"),
    ),
    ProofArtifact(
        "banking-lab", "Digital Banking Systems Laboratory",
        "Fictional educational artifact demonstrating domain modeling and deterministic transaction simulations.",
        ("python", "data", "testing"),
    ),
    ProofArtifact(
        "workflow-prototype", "Workflow Prototype",
        "Fictional demonstration of API integration and an internal web workflow.",
        ("web", "api", "automation", "prototype"),
    ),
)

BOUNDARIES = (
    OfferBoundary("no-guaranteed-roi", "No guaranteed ROI or business outcome."),
    OfferBoundary("investigate-first", "No assumption that automation or custom software is appropriate."),
    OfferBoundary("no-regulatory-claim", "No legal compliance or regulatory certification claim."),
    OfferBoundary("no-security-audit", "No specialized cybersecurity audit or industrial control engineering."),
    OfferBoundary("discovery-before-build", "No commitment to implementation before discovery."),
)


@dataclass(frozen=True)
class ChapterOneData:
    profile: CapabilityProfile
    offers: tuple[ServiceOffer, ...]


def load_chapter_one() -> ChapterOneData:
    profile = CapabilityProfile("Northstar Systems Studio", CAPABILITIES, PROOF, BOUNDARIES)
    offers = (
        ServiceOffer(
            "A",
            "We investigate operational workflows involving disconnected software systems and repeated manual data transfer to determine whether integration or automation could improve the workflow.",
            ("api", "automation"),
            (PROBLEM_CLASSES["SYSTEM_INTEGRATION"], PROBLEM_CLASSES["MANUAL_WORKFLOW"]),
            ("inventory-lab", "workflow-prototype"),
            (BOUNDARIES[0], BOUNDARIES[1], BOUNDARIES[4]),
        ),
        ServiceOffer(
            "B", "We use AI to revolutionize any business.", (), (), (),
            (BOUNDARIES[1], BOUNDARIES[4]),
        ),
        ServiceOffer(
            "C", "We guarantee a 40% reduction in operating costs through automation.",
            ("automation",), (PROBLEM_CLASSES["MANUAL_WORKFLOW"],),
            ("workflow-prototype",), (BOUNDARIES[0],),
        ),
        ServiceOffer(
            "D",
            "We investigate synchronization problems between business systems and prototype integration approaches when the evidence supports doing so.",
            ("api", "data", "prototype"), (PROBLEM_CLASSES["DATA_SYNCHRONIZATION"],),
            ("inventory-lab", "workflow-prototype"), (BOUNDARIES[1], BOUNDARIES[4]),
        ),
    )
    return ChapterOneData(profile, offers)


def evaluate_chapter_one() -> tuple[tuple[ServiceOffer, OfferEvaluation], ...]:
    data = load_chapter_one()
    evaluator = OfferEvaluator()
    return tuple((offer, evaluator.evaluate(offer, data.profile)) for offer in data.offers)


def chapter_one_report() -> str:
    data = load_chapter_one()
    capability_by_id = {item.identifier: item for item in data.profile.capabilities}
    proof_by_id = {item.identifier: item for item in data.profile.proof_artifacts}
    lines = ["CHAPTER 1 — DEFINE THE OFFER", "", "PROVIDER", data.profile.provider_name, "", "CAPABILITIES"]
    lines.extend(f"* {item.name}" for item in data.profile.capabilities)
    lines.extend(("", "PROOF"))
    lines.extend(f"* {item.name}" for item in data.profile.proof_artifacts)
    lines.extend(("", "BOUNDARIES"))
    lines.extend(f"* {item.statement}" for item in data.profile.boundaries)
    evaluator = OfferEvaluator()
    for offer in data.offers:
        result = evaluator.evaluate(offer, data.profile)
        lines.extend(("", f"OFFER CANDIDATE {offer.identifier}", f'“{offer.statement}”', "", "EVALUATION", result.status, "", "WHY"))
        lines.extend(f"* {finding}" for finding in result.findings)
        if result.relevant_capability_ids:
            lines.append("Relevant capabilities:")
            lines.extend(f"* {capability_by_id[item].name}" for item in result.relevant_capability_ids if item in capability_by_id)
        if result.supporting_proof_ids:
            lines.append("Supporting proof:")
            lines.extend(f"* {proof_by_id[item].name}" for item in result.supporting_proof_ids)
        if offer.boundaries:
            lines.append(f"Boundary: {offer.boundaries[0].statement}")
    lines.extend((
        "", "LIFECYCLE", "Provider Capability → Supported Offer → Relevant Problem Classes → Market Selection → Account Investigation",
        "", "QUESTION", "Does this company show evidence of a problem class that falls within the capabilities we can credibly investigate?",
    ))
    return "\n".join(lines) + "\n"
