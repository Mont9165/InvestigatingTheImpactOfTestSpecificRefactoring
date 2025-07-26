import pandas as pd
import os
import json
import argparse
import platform

# --- 設定 ---
def get_default_base_dir():
    """実行OSに応じてデフォルトのBASE_DIRを返す"""
    if platform.system() == "Darwin":  # macOS
        return "/Users/horikawa/Dev/Research-repo/InvestigatingTheImpactOfTestSpecificRefactoring"
    return "/work/kosei-ho/InvestigatingTheImpactOfTestSpecificRefactoring" # デフォルトはLinux/サーバー

# グローバル変数（main関数で設定される）
BASE_DIR = None
TEST_SMELL_DIR = None
ANNOTATION_RESULTS_DIR = None
SAMPLING_CSV = None

def set_paths(base_dir):
    """パスを設定する"""
    global BASE_DIR, TEST_SMELL_DIR, ANNOTATION_RESULTS_DIR, SAMPLING_CSV
    BASE_DIR = base_dir
    TEST_SMELL_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/TestSmellDetector"
    ANNOTATION_RESULTS_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/src/results"
    SAMPLING_CSV = f"{BASE_DIR}/2_sampling_test_refactor_commits/result/sampling_test_commits_all.csv"

def extract_method_smells(entries, start_line, end_line, file_name):
    method_smells = {}
    for entry in entries:
        if not entry["testFilePath"].endswith(file_name):
            continue
        for s in entry.get("smells", []):
            if s.get("smellParentType") == "Method":
                s_begin = s.get("beginLine")
                s_end   = s.get("endLine")
                if not (s_begin > end_line or s_end < start_line):
                    name = s.get("smellName")
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

        # parameter_dataを取得
        param_data = row.get("parameter_data", {})

        def load_counts(url, param_data):
            commit_dir = url.replace("https://github.com/", "").replace("commit/", "")
            if level == "file":
                csv_path = os.path.join(TEST_SMELL_DIR, "results", "smells", commit_dir, "smells_number.csv")
                if not os.path.isfile(csv_path):
                    print("Not Found: "+ csv_path)
                    return {}, csv_path
                df = pd.read_csv(csv_path)
                total_counts = {}
                processed_files = set()
                # parameter_dataのelementsに含まれるファイルのみ
                for data_type, data_dict in param_data.items():
                    elements = data_dict.get("elements", [])
                    for elem in elements:
                        if not elem or "location" not in elem or elem["location"] is None:
                            continue
                        file_path = elem["location"]["path"]
                        file_name = os.path.basename(file_path)
                        if file_name in processed_files:
                            continue
                        processed_files.add(file_name)
                        matches = df[df["TestFilePath"].str.endswith(file_name, na=False)]
                        for _, row2 in matches.iterrows():
                            for col in df.select_dtypes(include=["number"]).columns:
                                value = row2.get(col, 0)
                                total_counts[col] = total_counts.get(col, 0) + value
                return total_counts, csv_path
            elif level == "method":
                json_path = os.path.join(TEST_SMELL_DIR, "results", "smells", commit_dir, "smells_result.json")
                if not os.path.isfile(json_path):
                    return {}, json_path
                with open(json_path, encoding="utf-8") as f:
                    data = json.load(f)
                total_counts = {}
                # parameter_dataのelementsに含まれる範囲のみ
                for data_type, data_dict in param_data.items():
                    elements = data_dict.get("elements", [])
                    for elem in elements:
                        if not elem or "location" not in elem or elem["location"] is None:
                            continue
                        file_path = elem["location"]["path"]
                        file_name = os.path.basename(file_path)
                        rng = elem["location"].get("range")
                        if rng:
                            start_line = rng.get("startLine")
                            end_line = rng.get("endLine")
                            method_smells = extract_method_smells(data, start_line, end_line, file_name)
                            for k, v in method_smells.items():
                                total_counts[k] = total_counts.get(k, 0) + v
                return total_counts, json_path
            else:
                raise ValueError("levelは 'file' または 'method' を指定してください")

        before, before_path = load_counts(parent_commit_url, param_data.get("before", {}))
        after, after_path = load_counts(commit_url, param_data.get("after", {}))
        results.append({
            "commit_url": commit_url,
            "type_name": row.get("type_name", ""),
            "before": before,
            "after": after,
            "before_file_path": before_path,
            "after_file_path": after_path
        })
    return results

def main():
    """テスト用のメイン関数"""
    parser = argparse.ArgumentParser(description="Load test smell data.")
    parser.add_argument("--base-dir", type=str, default=get_default_base_dir(), help="Base directory of the project.")
    args = parser.parse_args()
    
    set_paths(args.base_dir)
    print(f"Loaded test smell data with base directory: {BASE_DIR}")

def load_annotation_data(json_path):
    """
    Load refactoring annotation data from a JSON file.
    Returns a pandas DataFrame.
    """
    return pd.read_json(json_path)

def load_commit_data(csv_path):
    """
    Load commit and parent commit information from a CSV file.
    Returns a pandas DataFrame.
    """
    return pd.read_csv(csv_path)

def get_parent_commit_url(commit_url, commit_data_df):
    """
    Given a commit URL and commit data DataFrame,
    return the parent commit URL. Returns None if not found.
    """
    commit_id = commit_url.split("/")[-1]
    repo_url = "/".join(commit_url.split("/")[:5])
    row = commit_data_df.loc[commit_data_df["commit_id"] == commit_id]
    if row.empty:
        return None
    parent_commit_id = row["parent_commit_id"].iloc[0]
    return f"{repo_url}/commit/{parent_commit_id}"

def load_smell_csv(csv_path):
    """
    Load file-level test smell data from a CSV file.
    Returns a pandas DataFrame. Returns empty DataFrame if not found.
    """
    try:
        return pd.read_csv(csv_path)
    except Exception:
        return pd.DataFrame()

def load_smell_json(json_path):
    """
    Load method-level test smell data from a JSON file.
    Returns a list of dicts. Returns empty list if not found.
    """
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

if __name__ == "__main__":
    main()