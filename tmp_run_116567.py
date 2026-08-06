"""Run QA Intelligence analysis for US 116567."""
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
from qa_intelligence.mcp.tools.generate_coverage_report import generate_coverage_report

US = 116567
MINIFRAC = r"C:\Users\WalkingTree.LAPTOP-UNM23JON\Desktop\Minifrac\fracpro-agile"
LIVE_PLUS = r"D:\Live_Plus_UAT"
OUT = Path(".")


def dump(name: str, obj: object) -> None:
    path = OUT / f"tmp_out_116567_{name}.json"
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
    print("DESC:", (story.get("description") or "")[:300])
    for ac in story.get("acceptance_criteria") or []:
        print("AC:", (ac.get("text") or "")[:500])

    ar = await analyze_requirement(user_story_id=US)
    dump("analysis", ar)
    data = ar.get("data") or {}
    fa = data.get("feature_analysis") or {}
    qa = data.get("qa_strategy") or {}
    print(
        "ANALYSIS blocked=",
        data.get("requirement_gaps"),
        "risk=",
        fa.get("risk_level"),
        "type=",
        fa.get("feature_type"),
        "required=",
        qa.get("testing_required"),
        "deny-ish=",
        [x.get("category") for x in (qa.get("testing_not_required") or [])[:5]],
    )
    if data.get("requirement_gaps"):
        for g in data["requirement_gaps"]:
            print(" GAP:", g)

    # Prefer story-aware selection: try Live+ first for Minifrac stub, also Minifrac path
    for label, repo in (("live_plus", LIVE_PLUS), ("minifrac", MINIFRAC)):
        code = await analyze_codebase(user_story_id=US, repository_path=repo)
        dump(f"codebase_{label}", code)
        impl = code.get("data") or {}
        files = impl.get("affected_files") or []
        print(f"CODE {label} ok=", code.get("ok"), "files=", len(files))
        for f in files[:8]:
            print(" ", f.get("path"), f.get("score"), f.get("reason"))

    existing = await get_existing_test_cases(user_story_id=US)
    dump("existing", existing)
    ex = existing.get("data") or []
    print("EXISTING", len(ex) if isinstance(ex, list) else ex)

    bugs = await get_related_bugs(user_story_id=US)
    dump("bugs", bugs)
    bug_list = bugs.get("data") or []
    print("BUGS", len(bug_list) if isinstance(bug_list, list) else type(bug_list))

    title = story.get("title") or ""
    query = " ".join(w for w in title.replace("-", " ").split() if len(w) > 2)[:120]
    similar = await search_similar_test_cases(query=query or "Minifrac LogLog", top=25)
    dump("similar", similar)
    sim = similar.get("data") or []
    print("SIMILAR", len(sim) if isinstance(sim, list) else sim)
    if isinstance(sim, list):
        for c in sim[:8]:
            print("-", c.get("id"), c.get("title"))

    cov = await generate_coverage_report(user_story_id=US)
    dump("coverage", cov)
    cd = cov.get("data") or {}
    print("directive=", cd.get("generation_directive"))
    missing = cd.get("missing_scenarios") or []
    print("missing=", len(missing))
    for m in missing[:15]:
        print(" M:", (m.get("title") or m.get("intent") or m.get("description") or m)[:200])
    qs = cd.get("qa_strategy_final") or {}
    print("estimates=", qs.get("estimates"))


if __name__ == "__main__":
    asyncio.run(main())
