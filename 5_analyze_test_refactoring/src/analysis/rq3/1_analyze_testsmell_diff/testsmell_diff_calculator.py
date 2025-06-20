import pandas as pd

def calculate_diff(pair):
    # pair = { "commit_url": ..., "type_name": ..., "before": {...}, "after": {...} }
    diff = {
        "commit_url": pair["commit_url"],
        "type_name": pair.get("type_name", "")
    }
    all_keys = set(pair["before"].keys()).union(pair["after"].keys())
    for key in all_keys:
        b = pair["before"].get(key, 0)
        a = pair["after"].get(key, 0)
        diff[f"{key}_before"] = b
        diff[f"{key}_after"] = a
        diff[f"{key}_diff"] = a - b
    return diff

def save_diff_csv(diff_results, out_path):
    df = pd.DataFrame(diff_results)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")