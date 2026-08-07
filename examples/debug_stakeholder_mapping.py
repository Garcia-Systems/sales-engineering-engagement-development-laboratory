"""Focused Chapter 7 debugger: compare evidence proximity, not seniority."""

from engagement_dev.scenarios import analyze_chapter_seven

analysis = analyze_chapter_seven()
hypothesis = analysis.hypothesis
validation_question = hypothesis.validation_questions[2]
stakeholder = analysis.stakeholder_map.stakeholders[0]
knowledge_domains = stakeholder.knowledge_domains
question_proximity = next(item for item in stakeholder.question_proximities if item.validation_question == validation_question)
supported_responsibilities = stakeholder.responsibilities
unknown_authority = stakeholder.purchasing_authority
contact_priority = next(item for item in analysis.priorities if item.stakeholder_id == stakeholder.contact.id)
executive = next(item for item in analysis.stakeholder_map.stakeholders if item.contact.id == "marcus")

# Break here: Maya's DIRECT operational evidence proximity outranks Marcus's senior title.
print(contact_priority.priority.value, stakeholder.contact.name, question_proximity.proximity.value)
print("Executive comparator:", executive.contact.name, executive.question_proximities[-1].proximity.value)
