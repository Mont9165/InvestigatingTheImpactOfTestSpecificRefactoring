import json
import logging
import os
import argparse
import platform
from collections import defaultdict

import pandas as pd

# --- 設定 ---
def get_default_base_dir():
    """実行OSに応じてデフォルトのBASE_DIRを返す"""
    if platform.system() == "Darwin":  # macOS
        return "/Users/horikawa/Dev/Research-repo/InvestigatingTheImpactOfTestSpecificRefactoring"
    return "/work/kosei-ho/InvestigatingTheImpactOfTestSpecificRefactoring" # デフォルトはLinux/サーバー

# --- ロギング設定 ---
def setup_logging(log_file="logfile.log"):
    """ロギングをファイルとコンソールに設定する"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        filename=log_file,
        filemode="a"
    )
    # コンソールにも出力
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger('').addHandler(console_handler)

# グローバル変数（main関数で設定される）
BASE_DIR = None
TEST_SMELL_DIR = None
RESULTS_DIR = None
SMELL_RESULT_DIR = None

FILE_SMELL_COLUMNS = [
    "Assertion Roulette",
    "Conditional Test Logic",
    "Constructor Initialization",
    "Default Test",
    "EmptyTest",
    "Exception Catching Throwing",
    "General Fixture",
    "Mystery Guest",
    "Print Statement",
    "Redundant Assertion",
    "Sensitive Equality",
    "Verbose Test",
    "Sleepy Test",
    "Eager Test",
    "Lazy Test",
    "Duplicate Assert",
    "Unknown Test",
    "IgnoredTest",
    "Resource Optimism",
    "Magic Number Test",
    "Dependent Test",
    "NumberOfMethods"
]

logger = logging.getLogger(__name__)


def get_refactoring_data_from_annotation_data():
    return pd.read_json(f"{RESULTS_DIR}/annotation_result_2024-02-20.json")


def get_parent_commit_id(df2, commit_id):
    row = df2.loc[df2["commit_id"] == commit_id]
    return row["parent_commit_id"].iloc[0] if not row.empty else None


def load_csv_smell_data(commit_dir: str) -> pd.DataFrame:
    csv_path = f"{TEST_SMELL_DIR}/results/smells/{commit_dir}/smells_number.csv"
    try:
        return pd.read_csv(csv_path)
    except Exception as e:
        logger.error(f"Failed to load CSV file: {csv_path} - {e}")
        return pd.DataFrame()


def load_json_smell_data(commit_dir: str) -> list:
    json_path = f"{TEST_SMELL_DIR}/results/smells/{commit_dir}/smells_result.json"
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON file: {json_path} - {e}")
        return []


# ---------------------------
# ファイルレベル
def get_file_smell_counts(param_data: dict, df: pd.DataFrame) -> dict:
    from collections import defaultdict
    total_counts = defaultdict(int)
    processed_files = set()

    for data_type, data_dict in param_data.items():
        elements = data_dict.get("elements", [])
        for elem in elements:
            file_path = elem["location"]["path"]
            file_name = os.path.basename(file_path)

            if file_name in processed_files:
                continue
            processed_files.add(file_name)

            matches = df[df["TestFilePath"].str.endswith(file_name)]
            for _, row in matches.iterrows():
                for col in FILE_SMELL_COLUMNS:
                    total_counts[col] += row.get(col, 0)
    return dict(total_counts)

def diff_file_smell_counts(before_counts: dict, after_counts: dict) -> dict:
    result = {}
    all_keys = set(before_counts.keys()).union(after_counts.keys())
    for smell in all_keys:
        b_val = before_counts.get(smell, 0)
        a_val = after_counts.get(smell, 0)
        result[smell] = a_val - b_val
    return result

# ---------------------------
# メソッド(range)レベル
def extract_method_smells(entries: list, start_line, end_line, file_name) -> list:
    method_smells = []
    for entry in entries:
        if not entry["testFilePath"].endswith(file_name):
            continue
        for s in entry.get("smells", []):
            if s.get("smellParentType") == "Method":
                s_begin = s.get("beginLine")
                s_end   = s.get("endLine")
                if not (s_begin > end_line or s_end < start_line):
                    method_smells.append(s)
    return method_smells

def get_range_smell_count(param_data: dict, commit_json: list) -> dict:
    from collections import defaultdict
    total_counts = defaultdict(int)

    for data_type, data_dict in param_data.items():
        elements = data_dict.get("elements", [])
        for elem in elements:
            file_path = elem["location"]["path"]
            file_name = os.path.basename(file_path)
            rng = elem["location"].get("range")
            if rng:
                start_line = rng.get("startLine")
                end_line   = rng.get("endLine")
                matched    = extract_method_smells(commit_json, start_line, end_line, file_name)
                for ms in matched:
                    smell_name = ms.get("smellName")
                    total_counts[smell_name] += 1
    return dict(total_counts)

def compare_method_level_smells(after_smells: dict, before_smells: dict) -> dict:
    result = {}
    all_keys = set(after_smells.keys()).union(before_smells.keys())
    for smell in all_keys:
        a_val = after_smells.get(smell, 0)
        b_val = before_smells.get(smell, 0)
        result[smell] = a_val - b_val
    return result

# ---------------------------
# ワイド形式の列を準備
def create_filelevel_wide_df() -> pd.DataFrame:
    """
    ファイルレベル: 1行 = 1リファクタリング, 各テストスメルで3列(before, after, diff)
    """
    columns = ["commit_url", "type_name"]
    for smell in FILE_SMELL_COLUMNS:
        columns.append(f"{smell}_before")
        columns.append(f"{smell}_after")
        columns.append(f"{smell}_diff")
    return pd.DataFrame(columns=columns)


def create_rangelevel_wide_df() -> pd.DataFrame:
    """
    メソッド(range)レベル: 1行 = 1リファクタリング, 各テストスメルで3列(before, after, diff)
    """
    columns = ["commit_url", "type_name"]
    for smell in FILE_SMELL_COLUMNS:
        columns.append(f"{smell}_before")
        columns.append(f"{smell}_after")
        columns.append(f"{smell}_diff")
    return pd.DataFrame(columns=columns)

# ---------------------------
# JSON用(階層構造)
def build_json_object(commit_url: str, type_name: str,
                      file_diff: dict, before_file_counts: dict, after_file_counts: dict,
                      range_diff: dict, before_range_counts: dict, after_range_counts: dict) -> dict:
    # fileLevelSmells
    file_list = []
    file_keys = set(before_file_counts.keys()).union(after_file_counts.keys())
    for smell in sorted(file_keys):
        file_list.append({
            "smellName": smell,
            "before": before_file_counts.get(smell, 0),
            "after":  after_file_counts.get(smell, 0),
            "diff":   file_diff.get(smell, 0)
        })

    # methodLevelSmells
    method_list = []
    range_keys = set(before_range_counts.keys()).union(after_range_counts.keys())
    for smell in sorted(range_keys):
        method_list.append({
            "smellName": smell,
            "before": before_range_counts.get(smell, 0),
            "after":  after_range_counts.get(smell, 0),
            "diff":   range_diff.get(smell, 0)
        })

    return {
        "commitUrl": commit_url,
        "typeName": type_name,
        "fileLevelSmells": file_list,
        "methodLevelSmells": method_list
    }

# ---------------------------
def process_parameter_data(
    ref_type: str,
    parameter_data: dict,
    commit_url: str,
    parent_commit_url: str,
    file_wide_df: pd.DataFrame,
    range_wide_df: pd.DataFrame,
    json_list: list
):
    # CSV読み込み
    commit_dir = commit_url.replace("https://github.com/", "").replace("commit/", "")
    parent_commit_dir = parent_commit_url.replace("https://github.com/", "").replace("commit/", "")
    commit_df = load_csv_smell_data(commit_dir)
    parent_df = load_csv_smell_data(parent_commit_dir)
    # JSON読み込み
    commit_json = load_json_smell_data(commit_dir)
    parent_json = load_json_smell_data(parent_commit_dir)

    # ファイルレベル: before/after/diff
    before_file = get_file_smell_counts(parameter_data.get("before", {}), parent_df)
    after_file  = get_file_smell_counts(parameter_data.get("after", {}), commit_df)
    diff_file   = diff_file_smell_counts(before_file, after_file)

    # rangeレベル: before/after/diff
    before_range = get_range_smell_count(parameter_data.get("before", {}), parent_json)
    after_range  = get_range_smell_count(parameter_data.get("after", {}), commit_json)
    diff_range   = compare_method_level_smells(after_range, before_range)

    # --- ファイルレベル (ワイド形式) ---
    file_row = {
        "commit_url": commit_url,
        "type_name": ref_type
    }
    for smell in FILE_SMELL_COLUMNS:
        b_val = before_file.get(smell, 0)
        a_val = after_file.get(smell, 0)
        d_val = diff_file.get(smell, 0)
        file_row[f"{smell}_before"] = b_val
        file_row[f"{smell}_after"]  = a_val
        file_row[f"{smell}_diff"]   = d_val

    file_wide_df.loc[len(file_wide_df)] = file_row

    # --- rangeレベル (ワイド形式) ---
    range_row = {
        "commit_url": commit_url,
        "type_name": ref_type
    }
    for smell in FILE_SMELL_COLUMNS:
        b_val = before_range.get(smell, 0)
        a_val = after_range.get(smell, 0)
        d_val = diff_range.get(smell, 0)
        range_row[f"{smell}_before"] = b_val
        range_row[f"{smell}_after"]  = a_val
        range_row[f"{smell}_diff"]   = d_val

    range_wide_df.loc[len(range_wide_df)] = range_row

    # --- JSON (階層構造) ---
    json_obj = build_json_object(
        commit_url, ref_type,
        diff_file, before_file, after_file,
        diff_range, before_range, after_range
    )
    json_list.append(json_obj)


def process_grouped_data(commit_url, df2, group,
                         file_wide_df: pd.DataFrame,
                         range_wide_df: pd.DataFrame,
                         json_list: list):
    try:
        commit_id = commit_url.split("/")[-1]
        repo_url = "/".join(commit_url.split("/")[:5])
        parent_commit_id = get_parent_commit_id(df2, commit_id)
        if parent_commit_id is None:
            logger.warning(f"Parent commit not found for {commit_url}")
            return

        parent_commit_url = f"{repo_url}/commit/{parent_commit_id}"
        for i, row in group.iterrows():
            ref_type = row.get("type_name", "UnknownRefactoring")
            param_data = row["parameter_data"]
            process_parameter_data(ref_type, param_data,
                                   commit_url, parent_commit_url,
                                   file_wide_df, range_wide_df,
                                   json_list)
    except Exception as e:
        logger.error(f"Error in process_grouped_data for {commit_url}: {e}")
        return


def main():
    """メイン関数: コマンドライン引数を解釈し、処理を実行する"""
    parser = argparse.ArgumentParser(description="Calculate test smell changes from refactoring data.")
    parser.add_argument("--base-dir", type=str, default=get_default_base_dir(), help="Base directory of the project.")
    parser.add_argument("--log-file", type=str, default="logfile.log", help="Path to the log file.")
    args = parser.parse_args()

    # グローバル変数を設定
    global BASE_DIR, TEST_SMELL_DIR, RESULTS_DIR, SMELL_RESULT_DIR
    BASE_DIR = args.base_dir
    TEST_SMELL_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/TestSmellDetector"
    RESULTS_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/src/results"
    SMELL_RESULT_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/src/smells_result"

    setup_logging(args.log_file)
    logger.info(f"Starting calculate_testsmell_changed_amount with config: {args}")

    try:
        df1 = get_refactoring_data_from_annotation_data()
        df2 = pd.read_csv(f"{BASE_DIR}/2_sampling_test_refactor_commits/result/sampling_test_commits_all.csv")

        # ワイド形式のDataFrame(ファイルレベル/メソッドレベル)
        file_wide_df = create_filelevel_wide_df()
        range_wide_df = create_rangelevel_wide_df()

        # JSON出力用のリスト
        json_list = []

        grouped = df1.groupby("url")
        for commit_url, group in grouped:
            logger.info(f"Processing refactoring data for {commit_url}")
            process_grouped_data(commit_url, df2, group,
                                 file_wide_df, range_wide_df,
                                 json_list)

        # CSV出力
        file_csv = f"{SMELL_RESULT_DIR}/file_level_wide.csv"
        range_csv = f"{SMELL_RESULT_DIR}/method_level_wide.csv"
        file_wide_df.to_csv(file_csv, index=False, encoding="utf-8-sig")
        range_wide_df.to_csv(range_csv, index=False, encoding="utf-8-sig")

        logger.info(f"File-level wide CSV saved to: {file_csv}")
        logger.info(f"Method-level wide CSV saved to: {range_csv}")

        # JSON出力 (1リファクタリング1オブジェクト)
        output_json = f"{SMELL_RESULT_DIR}/test_smell_analysis.json"
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(json_list, f, ensure_ascii=False, indent=2)
        logger.info(f"JSON saved to: {output_json}")

    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)


if __name__ == "__main__":
    main()