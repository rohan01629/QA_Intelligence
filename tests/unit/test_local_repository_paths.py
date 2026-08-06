"""Unit tests for local repository path selection."""

from __future__ import annotations

from qa_intelligence.domain.models.user_story import AcceptanceCriteria, UserStory
from qa_intelligence.domain.policies.local_repository_paths import (
    derive_live_plus_qa_path,
    parse_local_repository_paths,
    select_local_repository_path,
)


LIVE = r"D:\Live_Plus_UAT"
LIVE_LEAF = r"D:\Live_Plus_UAT\fracpro-agile"
LIVE_QA = r"D:\Live_Plus_QA\fracpro-agile"
MINIFRAC = r"C:\Repos\Minifrac\fracpro-agile"
PATHS = [LIVE, MINIFRAC]
PATHS_WITH_QA = [LIVE, LIVE_QA, MINIFRAC]


def test_parse_paths_comma_and_newline() -> None:
    assert parse_local_repository_paths(f"{LIVE},{MINIFRAC}") == PATHS
    assert parse_local_repository_paths(f"{LIVE}\n{MINIFRAC}") == PATHS


def test_minifrac_story_selects_minifrac_tree() -> None:
    story = UserStory(
        id=116566,
        title="FracPro Live+- Minifrac- Display and Update Magenta Circle on LogLog Plot",
        acceptance_criteria=[
            AcceptanceCriteria(order=1, text="Show magenta circle on LogLog plot", id="AC-1")
        ],
    )
    chosen = select_local_repository_path(
        PATHS,
        user_story=story,
        require_existing=False,
    )
    assert chosen == MINIFRAC


def test_reports_story_prefers_live_plus() -> None:
    story = UserStory(
        id=116559,
        title="FracPro Live+ - Reports- Rename Download ASCII Report button",
        acceptance_criteria=[
            AcceptanceCriteria(order=1, text="Rename Download ASCII Report", id="AC-1")
        ],
    )
    chosen = select_local_repository_path(
        PATHS,
        user_story=story,
        require_existing=False,
    )
    assert chosen == LIVE_LEAF


def test_explicit_empty_list_returns_none() -> None:
    assert select_local_repository_path([], require_existing=False) is None


def test_qa_state_prefers_live_plus_qa_path() -> None:
    story = UserStory(
        id=120001,
        title="FracPro Live+ - Reports - verify behavior in QA",
        state="QA",
        acceptance_criteria=[
            AcceptanceCriteria(order=1, text="Validate reports workflow in QA", id="AC-1")
        ],
    )
    chosen = select_local_repository_path(
        PATHS_WITH_QA,
        user_story=story,
        require_existing=False,
    )
    assert chosen == LIVE_QA


def test_qa_minifrac_story_still_selects_minifrac_tree() -> None:
    story = UserStory(
        id=120003,
        title="FracPro Live+- Minifrac- Display and Update Magenta Circle on LogLog Plot",
        state="QA",
        acceptance_criteria=[
            AcceptanceCriteria(order=1, text="Show magenta circle on LogLog plot", id="AC-1")
        ],
    )
    chosen = select_local_repository_path(
        PATHS_WITH_QA,
        user_story=story,
        require_existing=False,
    )
    assert chosen == MINIFRAC


def test_non_qa_state_keeps_existing_selection_logic() -> None:
    story = UserStory(
        id=120002,
        title="FracPro Live+ - Reports- Rename Download ASCII Report button",
        state="UAT",
        acceptance_criteria=[
            AcceptanceCriteria(order=1, text="Rename Download ASCII Report", id="AC-1")
        ],
    )
    chosen = select_local_repository_path(
        PATHS_WITH_QA,
        user_story=story,
        require_existing=False,
    )
    assert chosen == LIVE_LEAF


def test_qa_state_derives_qa_path_from_uat_only_config() -> None:
    story = UserStory(
        id=120004,
        title="FracPro Live+ - Reports - verify behavior in QA",
        state="QA",
        acceptance_criteria=[
            AcceptanceCriteria(order=1, text="Validate reports workflow in QA", id="AC-1")
        ],
    )
    chosen = select_local_repository_path(
        PATHS,
        user_story=story,
        require_existing=False,
    )
    assert chosen == LIVE_QA


def test_derive_live_plus_qa_path_preserves_suffix() -> None:
    assert derive_live_plus_qa_path(LIVE) == r"D:\Live_Plus_QA"
    assert derive_live_plus_qa_path(LIVE_QA) is None
