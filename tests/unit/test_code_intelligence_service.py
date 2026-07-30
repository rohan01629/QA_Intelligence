"""Unit tests for Code Intelligence Engine."""

from __future__ import annotations

from pathlib import Path

import pytest

from qa_intelligence.domain.models.code_intelligence import CodeArtifactRole
from qa_intelligence.domain.models.user_story import AcceptanceCriteria, UserStory
from qa_intelligence.infrastructure.errors import NotFoundError
from qa_intelligence.services.code_intelligence_service import CodeIntelligenceService
from qa_intelligence.services.test_case_generation_service import TestCaseGenerationService
from tests.unit.test_test_case_generation_service import _strategy, _story


def _write_sample_repo(root: Path) -> None:
    (root / "src").mkdir(parents=True)
    (root / "src" / "RenameFluidCommand.cs").write_text(
        """
using System.ComponentModel.DataAnnotations;
public class RenameFluidCommand {
  [Required]
  [MaxLength(100)]
  public string Name { get; set; }
  // Duplicate names not allowed
  public void Validate() {
    if (string.IsNullOrWhiteSpace(Name)) throw new Exception();
    Name = Name.Trim();
  }
}
""",
        encoding="utf-8",
    )
    (root / "src" / "RenameFluidHandler.cs").write_text(
        """
[HttpPatch("materials/{id}")]
public async Task Rename(int id, RenameFluidCommand cmd) {
  await _repository.UpdateAsync(id, cmd.Name);
}
""",
        encoding="utf-8",
    )
    (root / "ui" ).mkdir(parents=True)
    (root / "ui" / "MaterialSelectionDialog.tsx").write_text(
        """
export function MaterialSelectionDialog() {
  // refresh search sorting filtering after rename
  return <div>Material Search</div>;
}
""",
        encoding="utf-8",
    )
    (root / "noise" / "UnrelatedBilling.py").parent.mkdir(parents=True, exist_ok=True)
    (root / "noise" / "UnrelatedBilling.py").write_text("print('billing')\n", encoding="utf-8")


def _rename_story() -> UserStory:
    return UserStory(
        id=42,
        title="Rename Fluid",
        description="Allow renaming fluid materials with validation.",
        acceptance_criteria=[
            AcceptanceCriteria(order=1, text="User can rename a fluid", id="AC-1"),
            AcceptanceCriteria(order=2, text="Duplicate names are rejected", id="AC-2"),
        ],
        tags=["materials", "fluid"],
    )


def test_code_intelligence_finds_relevant_files_and_rules(tmp_path: Path) -> None:
    _write_sample_repo(tmp_path)
    summary = CodeIntelligenceService().analyze(_rename_story(), str(tmp_path))

    assert summary.feature == "Rename Fluid"
    paths = {f.path for f in summary.affected_files}
    assert any("RenameFluidCommand.cs" in p for p in paths)
    assert any("RenameFluidHandler.cs" in p for p in paths)
    assert summary.files_read > 0
    assert any("Duplicate" in rule for rule in summary.validation_rules)
    assert any("Maximum length" in rule for rule in summary.validation_rules)
    assert any("trim" in rule.lower() for rule in summary.validation_rules)
    assert summary.affected_apis
    assert any(
        "material" in api.path.lower() or api.method.upper() in {"PATCH", "ANY", "POST", "PUT"}
        for api in summary.affected_apis
    )
    assert summary.regression_areas


def test_code_intelligence_missing_repo_raises(tmp_path: Path) -> None:
    missing = tmp_path / "does-not-exist"
    with pytest.raises(NotFoundError):
        CodeIntelligenceService().analyze(_rename_story(), str(missing))


def test_generation_enriches_from_implementation_summary(tmp_path: Path) -> None:
    _write_sample_repo(tmp_path)
    summary = CodeIntelligenceService().analyze(_rename_story(), str(tmp_path))
    result = TestCaseGenerationService().generate(
        _strategy(estimated_new=8),
        _story(),
        existing_test_cases=[],
        implementation_summary=summary,
    )
    assert result.generated
    titles = " ".join(case.title for case in result.generated).lower()
    assert "duplicate" in titles or "maximum" in titles or "api" in titles or "regression" in titles


def test_infer_roles() -> None:
    from qa_intelligence.services.repository_search_service import RepositorySearchService

    svc = RepositorySearchService()
    assert svc._infer_role("src/RenameFluidCommand.cs", "renamefluidcommand.cs") == CodeArtifactRole.COMMAND
    assert svc._infer_role("ui/MaterialSelectionDialog.tsx", "materialselectiondialog.tsx") in {
        CodeArtifactRole.COMPONENT,
        CodeArtifactRole.PAGE,
        CodeArtifactRole.OTHER,
    }
