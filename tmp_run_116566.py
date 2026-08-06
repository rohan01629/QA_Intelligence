"""Run QA Intelligence analysis for US 116566 (dry-run draft prep)."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from qa_intelligence.mcp.tools.get_user_story import get_user_story
from qa_intelligence.mcp.tools.analyze_requirement import analyze_requirement
from qa_intelligence.mcp.tools.analyze_codebase import analyze_codebase
from qa_intelligence.mcp.tools.get_existing_test_cases import get_existing_test_cases
from qa_intelligence.mcp.tools.get_related_bugs import get_related_bugs
from qa_intelligence.mcp.tools.search_similar_test_cases import search_similar_test_cases
from qa_intelligence.mcp.tools.detect_duplicate_test_cases import detect_duplicate_test_cases
from qa_intelligence.mcp.tools.generate_coverage_report import generate_coverage_report

US = 116566
MINIFRAC = r"C:\Users\WalkingTree.LAPTOP-UNM23JON\Desktop\Minifrac\fracpro-agile"
OUT = Path(".")


def dump(name: str, obj: object) -> None:
    path = OUT / f"tmp_out_116566_{name}.json"
    path.write_text(json.dumps(obj, indent=2, default=str), encoding="utf-8")
    print(f"wrote {path}")


async def main() -> None:
    story_resp = await get_user_story(US)
    dump("story", story_resp)
    if not story_resp.get("ok"):
        print("STORY FAILED", story_resp.get("error"))
        return
    story = story_resp["data"]
    print("TITLE:", story.get("title"))
    ac = story.get("acceptance_criteria") or {}
    print("AC text length:", len((ac.get("raw_text") or ac.get("text") or "") if isinstance(ac, dict) else str(ac)))

    ar = await analyze_requirement(user_story_id=US)
    dump("analysis", ar)
    data = ar.get("data") or {}
    print(
        "ANALYSIS ok=",
        ar.get("ok"),
        "blocked=",
        data.get("generation_blocked"),
        "risk=",
        data.get("risk_level"),
        "feature=",
        data.get("feature_type"),
    )
    qa = data.get("qa_strategy") or {}
    print(
        "directive=",
        qa.get("generation_directive"),
        "core=",
        qa.get("core_categories"),
        "deny=",
        qa.get("denied_categories"),
    )
    if data.get("generation_blocked") or (qa.get("generation_directive") == "blocked"):
        print("BLOCKED — stopping before draft generation")
        gaps = data.get("requirement_gaps") or data.get("gaps") or []
        for g in gaps:
            print(" GAP:", g)
        return

    code = await analyze_codebase(
        user_story_id=US,
        repository_path=MINIFRAC,
    )
    dump("codebase", code)
    impl = (code.get("data") or {}) if code.get("ok") else {}
    print(
        "CODE ok=",
        code.get("ok"),
        "files=",
        len(impl.get("relevant_files") or impl.get("files") or []),
        "summary_keys=",
        list(impl.keys())[:12] if isinstance(impl, dict) else type(impl),
    )
    if not code.get("ok"):
        print("CODE ERR", code.get("error"))

    existing = await get_existing_test_cases(user_story_id=US)
    dump("existing", existing)
    ex_data = existing.get("data") or {}
    cases = ex_data.get("test_cases") or ex_data.get("items") or ex_data
    if isinstance(cases, list):
        print("EXISTING count=", len(cases))
    else:
        print("EXISTING keys=", list(ex_data.keys()) if isinstance(ex_data, dict) else type(ex_data))

    bugs = await get_related_bugs(user_story_id=US)
    dump("bugs", bugs)
    bug_data = bugs.get("data") or {}
    bug_list = bug_data.get("bugs") or bug_data.get("items") or []
    print("BUGS count=", len(bug_list) if isinstance(bug_list, list) else bug_data)

    similar = await search_similar_test_cases(
        query="LogLog magenta circle Closure Meas'd Btmh Press Minifrac",
    )
    dump("similar", similar)
    sim_data = similar.get("data") or {}
    print("SIMILAR keys=", list(sim_data.keys()) if isinstance(sim_data, dict) else type(sim_data))

    # Coverage + dupes need draft candidates — skip full create until we draft
    # Still call coverage with empty proposed if supported
    try:
        cov = await generate_coverage_report(user_story_id=US)
        dump("coverage", cov)
        print("COVERAGE ok=", cov.get("ok"))
    except TypeError as exc:
        print("COVERAGE signature note:", exc)


if __name__ == "__main__":
    asyncio.run(main())
