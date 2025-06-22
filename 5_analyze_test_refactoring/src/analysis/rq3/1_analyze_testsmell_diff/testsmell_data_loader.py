import pandas as pd
import os
import json

BASE_DIR = "/Users/horikawa/Dev/Research-repo/InvestigatingTheImpactOfTestSpecificRefactoring"
TEST_SMELL_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/TestSmellDetector"
ANNOTATION_RESULTS_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/src/results"
SAMPLING_CSV = f"{BASE_DIR}/2_sampling_test_refactor_commits/result/sampling_test_commits_all.csv"

def load_method_smell_counts(smells_json_path):
    if not os.path.isfile(smells_json_path):
        return {}
    with open(smells_json_path, encoding="utf-8") as f:
        data = json.load(f)
    # メソッドレベルのスメルを集計
    method_smells = {}
    for entry in data:
        for smell in entry.get("smells", []):
            if smell.get("smellParentType") == "Method":
                name = smell.get("smellName")
                method_smells[name] = method_smells.get(name, 0) + 1
    return method_smells

def load_testsmell_data(level="file"):
    df_ann = pd.read_json(f"{ANNOTATION_RESULTS_DIR}/annotation_result_2024-02-20.json")
    df_commits = pd.read_csv(SAMPLING_CSV)
    results = []
    for _, row in df_ann.iterrows():
        commit_url = row["url"]
        commit_id = commit_url.split("/")[-1]
        repo_url = "/".join(commit_url.split("/")[:5])
        parent_row = df_commits[df_commits["commit_id"] == commit_id]
        if parent_row.empty:
            continue
        parent_commit_id = parent_row["parent_commit_id"].iloc[0]
        parent_commit_url = f"{repo_url}/commit/{parent_commit_id}"
        def load_counts(url):
            commit_dir = url.replace("https://github.com/", "").replace("commit/", "")
            if level == "file":
                csv_path = os.path.join(TEST_SMELL_DIR, "results", "smells", commit_dir, "smells_number.csv")
                if not os.path.isfile(csv_path):
                    print("Not Found: "+ csv_path)
                    return {}, csv_path
                df = pd.read_csv(csv_path)
                print("Found")
                return df.sum(numeric_only=True).to_dict(), csv_path
            elif level == "method":
                json_path = os.path.join(TEST_SMELL_DIR, "results", "smells", commit_dir, "smells_result.json")
                return load_method_smell_counts(json_path), json_path
            else:
                raise ValueError("levelは 'file' または 'method' を指定してください")
        before, before_path = load_counts(parent_commit_url)
        after, after_path = load_counts(commit_url)
        results.append({
            "commit_url": commit_url,
            "type_name": row.get("type_name", ""),
            "before": before,
            "after": after,
            "before_file_path": before_path,
            "after_file_path": after_path
        })
    return results