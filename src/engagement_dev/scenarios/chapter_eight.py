"""Chapter 8: design and evaluate outreach without communicating externally."""

from dataclasses import dataclass, replace

from engagement_dev.domain import OutreachChannel, OutreachEvidence, OutreachMessage, OutreachObjective
from engagement_dev.scenarios.chapter_one import load_chapter_one
from engagement_dev.scenarios.chapter_seven import analyze_chapter_seven
from engagement_dev.services import OutreachChannelAdapter, OutreachEvaluation, OutreachEvaluator


@dataclass(frozen=True)
class EvaluatedOutreach:
    label: str
    message: OutreachMessage
    evaluation: OutreachEvaluation


@dataclass(frozen=True)
class ChapterEightAnalysis:
    candidates: tuple[EvaluatedOutreach, ...]
    selected: object
    professional_network_message: str
    external_communication_performed: bool = False
    hypothesis_validated: bool = False
    qualified_engagement_created: bool = False


def analyze_chapter_eight() -> ChapterEightAnalysis:
    previous = analyze_chapter_seven()
    stakeholder = previous.stakeholder_map.stakeholders[0]
    hypothesis = previous.hypothesis
    proof_ids = tuple(item.identifier for item in load_chapter_one().profile.proof_artifacts)
    evidence_ids = tuple(hypothesis.evidence_ids)
    claims = (
        OutreachEvidence("Blue Heron Resort announced a fourth property.", ("r5",)),
        OutreachEvidence("Blue Heron Resort posted an Operations Systems Coordinator role.", ("r4",)),
        OutreachEvidence("Maya's publicly described role focuses on operational systems coordination across properties.", ("se-maya-resp",)),
    )
    observation = "I saw that Blue Heron Resort announced a fourth property and posted an Operations Systems Coordinator role."
    relevance = "Your publicly described role focuses on operational systems coordination across properties."
    credibility = "At Northstar Systems Studio, we investigate workflow and systems-integration problems in multi-system operations."
    question = "I was curious how you are approaching coordination across reservations, events, and property operations as the organization grows?"
    cta = "If that is something you are working through, I would be interested in comparing notes for 20 minutes."
    adapter = OutreachChannelAdapter()
    base = OutreachMessage("outreach-a", "blue-resort", "maya", hypothesis.id, OutreachObjective.VALIDATE_HYPOTHESIS,
        OutreachChannel.EMAIL, observation, relevance, credibility, question, cta, claims,
        ("workflow-prototype",), "")
    supported = replace(base, body=adapter.render(base, OutreachChannel.EMAIL))
    candidates = (
        supported,
        replace(base, id="outreach-b", observation="Your expansion must be causing serious integration problems.", relevance="", validation_question="Your systems are broken.", call_to_action="We can fix your systems and save you money.", body="Your expansion must be causing serious integration problems. We can fix your systems and save you money."),
        replace(base, id="outreach-c", observation="", relevance="", credibility="", validation_question="Would you like to hear about our services?", factual_claims=(), credibility_proof_ids=(), body="Hi Maya, I would love to connect and tell you about our software development services."),
        replace(base, id="outreach-d", body=" ".join([supported.body] * 5)),
        replace(base, id="outreach-e", validation_question="Would an API solve this?", body="We can build an API that integrates your reservation and event systems."),
    )
    evaluator = OutreachEvaluator()
    evaluated = tuple(EvaluatedOutreach(chr(65 + index), item, evaluator.evaluate(item, account_evidence_ids=evidence_ids, stakeholder=stakeholder, proof_artifact_ids=proof_ids)) for index, item in enumerate(candidates))
    selected_message = evaluated[0]
    attempt = evaluator.ready_attempt(selected_message.message, selected_message.evaluation)
    network = adapter.render(replace(supported, channel=OutreachChannel.PROFESSIONAL_NETWORK), OutreachChannel.PROFESSIONAL_NETWORK)
    return ChapterEightAnalysis(evaluated, attempt, network)


def chapter_eight_report() -> str:
    analysis = analyze_chapter_eight()
    hypothesis = analyze_chapter_seven().hypothesis
    lines = ["CHAPTER 8 — DESIGNING EVIDENCE-BASED OUTREACH", "", "ACCOUNT", "Blue Heron Resort", "", "STAKEHOLDER", "Maya Chen", "Operations Systems Coordinator", "", "OUTREACH OBJECTIVE", "VALIDATE_HYPOTHESIS", "", "PUBLIC EVIDENCE USED", "- Fourth property announced", "- Operations Systems Coordinator role posted", "", "INTERNAL HYPOTHESIS", hypothesis.cautious_statement, "", "IMPORTANT", "The hypothesis will be expressed as a question, not as a fact."]
    for item in analysis.candidates:
        lines += ["", "---", "", f"CANDIDATE {item.label}", item.message.body, "", "EVALUATION", item.evaluation.outcome.value, "", "WHY", *[f"- {finding}" for finding in item.evaluation.findings]]
    message = analysis.selected.message
    lines += ["", "---", "", "SELECTED OUTREACH", message.body, "", "STATUS", analysis.selected.status.value, "", "ACTUAL MESSAGE SENT", "No.", "", "MESSAGE DECOMPOSITION", "", "OBSERVATION", message.observation, "", "RELEVANCE", message.relevance, "", "CREDIBILITY", message.credibility, "", "QUESTION", message.validation_question, "", "CALL TO ACTION", message.call_to_action, "", "PROFESSIONAL NETWORK VERSION", analysis.professional_network_message, "", "BOUNDARY", "Outreach tests the hypothesis; it does not validate it or create a qualified engagement."]
    return "\n".join(lines) + "\n"
