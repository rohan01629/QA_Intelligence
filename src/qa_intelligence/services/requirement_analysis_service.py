"""RequirementAnalysisService — structured QA analysis of a User Story.

Produces Feature Type, risk, rules, modules, dependencies, regression impact,
applicable/skipped categories, requirement gaps, and QA Strategy.

Does NOT generate test cases.
"""

from __future__ import annotations

import structlog

from qa_intelligence.domain.enums import GapSeverity, TestCategory
from qa_intelligence.domain.models.analysis import FeatureAnalysis, RequirementAnalysis
from qa_intelligence.domain.models.qa_strategy import CategoryExclusion, QAStrategy
from qa_intelligence.domain.models.user_story import UserStory
from qa_intelligence.domain.policies.category_policy import (
    always_categories_ordered,
    evaluate_categories,
)
from qa_intelligence.domain.policies.estimate_policy import preliminary_estimates
from qa_intelligence.domain.policies.feature_type_policy import classify_feature_type
from qa_intelligence.domain.policies.gap_policy import detect_requirement_gaps
from qa_intelligence.domain.policies.risk_policy import classify_risk
from qa_intelligence.domain.policies.signals import (
    extract_dependency_candidates,
    extract_module_candidates,
    extract_rule_like_lines,
    story_corpus,
)
from qa_intelligence.infrastructure.errors import ConfigurationError
from qa_intelligence.repositories.protocols import UserStoryRepository

logger = structlog.get_logger(__name__)


class RequirementAnalysisService:
    """Analyze a User Story into a structured RequirementAnalysis / QA Strategy."""

    def __init__(self, user_story_repository: UserStoryRepository | None = None) -> None:
        self._user_story_repository = user_story_repository

    async def analyze(
        self,
        *,
        user_story_id: int | None = None,
        user_story: UserStory | None = None,
    ) -> RequirementAnalysis:
        """Analyze by embedded story and/or fetch by ID from Azure DevOps."""
        story = await self._resolve_story(user_story_id=user_story_id, user_story=user_story)
        return self.analyze_story(story)

    def analyze_story(self, story: UserStory) -> RequirementAnalysis:
        """Pure deterministic analysis of an in-memory User Story."""
        feature_type, feature_rationale = classify_feature_type(story)
        risk = classify_risk(story, feature_type)
        applicable_optional, exclusion_reasons, category_reason = evaluate_categories(
            story,
            feature_type,
        )
        gaps = detect_requirement_gaps(story, feature_type)
        blocked = any(gap.severity == GapSeverity.BLOCKING for gap in gaps)

        business_rules = extract_rule_like_lines(story)
        validation_rules = [
            rule
            for rule in business_rules
            if any(
                token in rule.lower()
                for token in ("valid", "required", "must", "reject", "format", "schema")
            )
        ]
        modules = extract_module_candidates(story)
        dependencies = extract_dependency_candidates(story_corpus(story), story)
        regression_impact = _regression_impact(feature_type.display_name, risk.display_name, modules)
        data_flow_notes = _data_flow_notes(story, feature_type.display_name)

        feature_analysis = FeatureAnalysis(
            feature_type=feature_type,
            risk_level=risk,
            business_rules=business_rules,
            dependencies=dependencies,
            modules=modules,
            validation_rules=validation_rules,
            data_flow_notes=data_flow_notes,
            regression_impact=regression_impact,
            applicable_optional_categories=applicable_optional,
            excluded_optional_categories=list(exclusion_reasons.keys()),
            rationale=f"{feature_rationale} {category_reason}".strip(),
        )

        testing_required = _ordered_unique(
            [*always_categories_ordered(), *applicable_optional]
        )
        # When blocked, still report intended categories but estimates are zero.
        testing_not_required = [
            CategoryExclusion(category=category, reason=reason)
            for category, reason in exclusion_reasons.items()
            if category not in testing_required
        ]

        estimates = preliminary_estimates(
            story,
            testing_required,
            risk,
            blocked=blocked,
        )

        qa_strategy = QAStrategy(
            feature_type=feature_type,
            risk=risk,
            testing_required=testing_required,
            testing_not_required=testing_not_required,
            reason=category_reason,
            estimates=estimates,
            blocked=blocked,
        )

        analysis = RequirementAnalysis(
            user_story_id=story.id,
            feature_analysis=feature_analysis,
            requirement_gaps=gaps,
            qa_strategy=qa_strategy,
            blocked=blocked,
        )

        logger.info(
            "requirement.analysis_completed",
            user_story_id=story.id,
            feature_type=feature_type.value,
            risk=risk.value,
            blocked=blocked,
            required_categories=[c.value for c in testing_required],
            skipped_categories=[c.category.value for c in testing_not_required],
            gap_count=len(gaps),
        )
        return analysis

    async def _resolve_story(
        self,
        *,
        user_story_id: int | None,
        user_story: UserStory | None,
    ) -> UserStory:
        if user_story is not None:
            return user_story
        if user_story_id is None:
            raise ConfigurationError(
                "Either user_story_id or user_story must be provided",
            )
        if self._user_story_repository is None:
            raise ConfigurationError(
                "UserStoryRepository is required when analyzing by user_story_id",
                details={"user_story_id": user_story_id},
            )
        return await self._user_story_repository.get_by_id(user_story_id)


def _ordered_unique(categories: list[TestCategory]) -> list[TestCategory]:
    seen: set[TestCategory] = set()
    ordered: list[TestCategory] = []
    for category in categories:
        if category in seen:
            continue
        seen.add(category)
        ordered.append(category)
    return ordered


def _regression_impact(feature_label: str, risk_label: str, modules: list[str]) -> str:
    module_part = ", ".join(modules[:5]) if modules else "unspecified modules"
    return (
        f"{risk_label} regression risk for {feature_label} changes "
        f"affecting {module_part}."
    )


def _data_flow_notes(story: UserStory, feature_label: str) -> str:
    if story.acceptance_criteria:
        return (
            f"{feature_label} change with {len(story.acceptance_criteria)} "
            "acceptance criteria defining expected inputs/outcomes."
        )
    return f"{feature_label} change with limited documented data-flow detail."
