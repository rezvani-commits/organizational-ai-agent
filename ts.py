import json, glob
FB = "خروجی داور قابل تبدیل به JSON نبود یا خطا رخ داد"
failed = {}
for p in sorted(glob.glob("eval/results/*.json")):
    d = json.load(open(p, encoding="utf-8"))
    ids, api_err, ends_brace = set(), 0, 0
    for r in d["main"]:
        v = r.get("validation_result") or {}
        if (v.get("faithfulness") or {}).get("reason") == FB:
            ids.add(r["record_id"])
            raw = (v.get("raw_judge_response") or "").strip()
            api_err += raw.startswith("LLM invoke error")
            ends_brace += raw.endswith("}")
    failed[p] = ids
    print(p, "| judge:", d.get("judge_model"), "| failed:", len(ids),
          "| api_error:", api_err, "| raw_ends_with_}:", ends_brace)
a, b = [ids for p, ids in failed.items() if ids]
print("overlap of failed ids:", len(a & b), "of", len(a), "/", len(b))