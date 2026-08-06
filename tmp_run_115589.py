"""QA Intelligence analysis for US 115589."""
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

US = 115589
MINIFRAC = r"C:\Users\WalkingTree.LAPTOP-UNM23JON\Desktop\Minifrac\fracpro-agile"
LIVE_PLUS = r"D:\Live_Plus_UAT"
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
    print("DESC:", (story.get("description") or "")[:400])
    for ac in story.get("acceptance_criteria") or []:
        print("AC:", (ac.get("text") or "")[:800])
    print("TAGS:", story.get("tags"))

    ar = await analyze_requirement(user_story_id=US)
    dump("analysis", ar)
    data = ar.get("data") or {}
    fa = data.get("feature_analysis") or {}
    qa = data.get("qa_strategy") or {}
    print(
        "ANALYSIS risk=",
        fa.get("risk_level"),
        "type=",
        fa.get("feature_type"),
        "required=",
        qa.get("testing_required"),
        "gaps=",
        len(data.get("requirement_gaps") or []),
    )
    if data.get("requirement_gaps"):
        for g in data["requirement_gaps"]:
            print(" GAP:", g)

    title = (story.get("title") or "").lower()
    desc = (story.get("description") or "").lower()
    corpus = title + " " + desc
    # Prefer Minifrac path for minifrac/loglog; Live+ for reports/ascii
    primary = MINIFRAC if any(
        k in corpus for k in ("minifrac", "loglog", "g-func", "isip", "closure", "tangent")
    ) else LIVE_PLUS
    secondary = LIVE_PLUS if primary == MINIFRAC else MINIFRAC

    for label, repo in (("primary", primary), ("secondary", secondary)):
        code = await analyze_codebase(user_story_id=US, repository_path=repo)
        dump(f"codebase_{label}", code)
        impl = code.get("data") or {}
        files = impl.get("affected_files") or []
        print(f"CODE {label}={repo} ok=", code.get("ok"), "files=", len(files))
        for f in files[:10]:
            print(" ", f.get("path"), f.get("score"), (f.get("reason") or "")[:80])

    existing = await get_existing_test_cases(user_story_id=US)
    dump("existing", existing)
    ex = existing.get("data") or []
    print("EXISTING", len(ex) if isinstance(ex, list) else ex)

    bugs = await get_related_bugs(user_story_id=US)
    dump("bugs", bugs)
    bug_list = bugs.get("data") or []
    print("BUGS", len(bug_list) if isinstance(bug_list, list) else type(bug_list))

    query_words = [w for w in (story.get("title") or "").replace("-", " ").split() if len(w) > 2]
    query = " ".join(query_words)[:120] or "FracPro"
    similar = await search_similar_test_cases(query=query, top=25)
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
    qs = cd.get("qa_strategy_final") or {}
    print("estimates=", qs.get("estimates"))
    print("testing_required=", qs.get("testing_required"))
    missing = cd.get("missing_scenarios") or []
    print("missing=", len(missing))
    for m in missing[:20]:
        print(" M:", (m.get("title") or m.get("intent") or m.get("description") or str(m))[:220])


if __name__ == "__main__":
    asyncio.run(main())
