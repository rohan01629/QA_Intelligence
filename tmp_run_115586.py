"""QA Intelligence analysis for US 115586."""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from qa_intelligence.mcp.tools.analyze_codebase import analyze_codebase
from qa_intelligence.mcp.tools.analyze_requirement import analyze_requirement
from qa_intelligence.mcp.tools.generate_coverage_report import generate_coverage_report
from qa_intelligence.mcp.tools.get_existing_test_cases import get_existing_test_cases
from qa_intelligence.mcp.tools.get_related_bugs import get_related_bugs
from qa_intelligence.mcp.tools.get_user_story import get_user_story
from qa_intelligence.mcp.tools.search_similar_test_cases import search_similar_test_cases

US = 115586
OUT = Path(".")


def dump(name: str, obj: object) -> None:
    path = OUT / f"tmp_out_{US}_{name}.json"
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
    print("STATE:", story.get("state"))
    print("DESC:", (story.get("description") or "")[:500])
    for ac in story.get("acceptance_criteria") or []:
        print("AC:", (ac.get("text") or "")[:1500])

    ar = await analyze_requirement(user_story_id=US)
    dump("analysis", ar)
    data = ar.get("data") or {}
    if data.get("blocked"):
        print("BLOCKED - requirement gaps")
        for g in data.get("requirement_gaps") or []:
            print(" GAP:", g)
        return

    code = await analyze_codebase(user_story_id=US)
    dump("codebase", code)
    impl = code.get("data") or {}
    print("CODEBASE:", impl.get("repository_path"))
    print("FEATURE_FOUND:", impl.get("feature_found"))
    print("RELATED:", impl.get("related_implementation_available"))
    for f in (impl.get("affected_files") or [])[:12]:
        print(" ", f.get("path"), f.get("score"))

    existing = await get_existing_test_cases(user_story_id=US)
    dump("existing", existing)
    ex = existing.get("data") or []
    print("EXISTING", len(ex) if isinstance(ex, list) else ex)

    bugs = await get_related_bugs(user_story_id=US)
    dump("bugs", bugs)

    query = " ".join(
        w for w in (story.get("title") or "").replace("-", " ").split() if len(w) > 2
    )[:120]
    similar = await search_similar_test_cases(query=query or "FracPro", top=20)
    dump("similar", similar)

    cov = await generate_coverage_report(user_story_id=US)
    dump("coverage", cov)
    cd = cov.get("data") or {}
    qs = cd.get("qa_strategy_final") or {}
    print("directive=", cd.get("generation_directive"))
    print("estimates=", qs.get("estimates"))
    missing = cd.get("missing_scenarios") or []
    print("missing=", len(missing))


if __name__ == "__main__":
    asyncio.run(main())
