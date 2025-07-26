import pandas as pd
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# List of all test smell column names
FILE_SMELL_COLUMNS = [
    "Assertion Roulette", "Conditional Test Logic", "Constructor Initialization", "Default Test", "EmptyTest",
    "Exception Catching Throwing", "General Fixture", "Mystery Guest", "Print Statement", "Redundant Assertion",
    "Sensitive Equality", "Verbose Test", "Sleepy Test", "Eager Test", "Lazy Test", "Duplicate Assert",
    "Unknown Test", "IgnoredTest", "Resource Optimism", "Magic Number Test", "Dependent Test", "NumberOfMethods"
]

def calculate_diff(pair):
    # pair = { "commit_url": ..., "type_name": ..., "before": {...}, "after": {...} }
    diff = {
        "before_file_path": pair.get("before_file_path", ""),
        "after_file_path": pair.get("after_file_path", ""),
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
    """差分結果をCSVファイルに保存する"""
    try:
        df = pd.DataFrame(diff_results)
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        logger.info(f"Successfully saved {len(diff_results)} records to {out_path}")
    except Exception as e:
        logger.error(f"Failed to save CSV file {out_path}: {e}")
        raise

def calculate_file_level_diff(parameter_data, before_df, after_df, smell_columns=FILE_SMELL_COLUMNS):
    """
    Calculate file-level test smell counts and their differences for before/after.
    Returns (before_counts, after_counts, diff_counts) as dicts.
    """
    def get_file_smell_counts(param_data, df):
        total_counts = defaultdict(int)
        processed_files = set()
        for data_type, data_dict in param_data.items():
            elements = data_dict.get("elements", [])
            for elem in elements:
                file_path = elem["location"]["path"]
                file_name = file_path.split("/")[-1]
                if file_name in processed_files:
                    continue
                processed_files.add(file_name)
                matches = df[df["TestFilePath"].str.endswith(file_name)]
                for _, row in matches.iterrows():
                    for col in smell_columns:
                        total_counts[col] += row.get(col, 0)
        return dict(total_counts)
    before_counts = get_file_smell_counts(parameter_data.get("before", {}), before_df)
    after_counts = get_file_smell_counts(parameter_data.get("after", {}), after_df)
    diff_counts = {k: after_counts.get(k, 0) - before_counts.get(k, 0) for k in set(before_counts) | set(after_counts)}
    return before_counts, after_counts, diff_counts

def calculate_method_level_diff(parameter_data, before_json, after_json, smell_columns=FILE_SMELL_COLUMNS):
    """
    Calculate method-level test smell counts and their differences for before/after.
    Returns (before_counts, after_counts, diff_counts) as dicts.
    """
    def extract_method_smells(entries, start_line, end_line, file_name):
        method_smells = []
        for entry in entries:
            if not entry["testFilePath"].endswith(file_name):
                continue
            for s in entry.get("smells", []):
                if s.get("smellParentType") == "Method":
                    s_begin = s.get("beginLine")
                    s_end = s.get("endLine")
                    if not (s_begin > end_line or s_end < start_line):
                        method_smells.append(s)
        return method_smells
    def get_range_smell_count(param_data, commit_json):
        total_counts = defaultdict(int)
        for data_type, data_dict in param_data.items():
            elements = data_dict.get("elements", [])
            for elem in elements:
                file_path = elem["location"]["path"]
                file_name = file_path.split("/")[-1]
                rng = elem["location"].get("range")
                if rng:
                    start_line = rng.get("startLine")
                    end_line = rng.get("endLine")
                    matched = extract_method_smells(commit_json, start_line, end_line, file_name)
                    for ms in matched:
                        smell_name = ms.get("smellName")
                        total_counts[smell_name] += 1
        return dict(total_counts)
    before_counts = get_range_smell_count(parameter_data.get("before", {}), before_json)
    after_counts = get_range_smell_count(parameter_data.get("after", {}), after_json)
    diff_counts = {k: after_counts.get(k, 0) - before_counts.get(k, 0) for k in set(before_counts) | set(after_counts)}
    return before_counts, after_counts, diff_counts

def build_wide_row(commit_url, type_name, before_counts, after_counts, diff_counts, smell_columns=FILE_SMELL_COLUMNS):
    """
    Build a row (dict) for wide-format CSV output.
    """
    row = {"commit_url": commit_url, "type_name": type_name}
    for smell in smell_columns:
        row[f"{smell}_before"] = before_counts.get(smell, 0)
        row[f"{smell}_after"] = after_counts.get(smell, 0)
        row[f"{smell}_diff"] = diff_counts.get(smell, 0)
    return row

def build_json_object(commit_url, type_name, file_diff, before_file, after_file, method_diff, before_method, after_method):
    """
    Build a JSON object for output, containing file and method level smell diffs.
    """
    file_list = []
    file_keys = set(before_file.keys()).union(after_file.keys())
    for smell in sorted(file_keys):
        file_list.append({
            "smellName": smell,
            "before": before_file.get(smell, 0),
            "after": after_file.get(smell, 0),
            "diff": file_diff.get(smell, 0)
        })
    method_list = []
    method_keys = set(before_method.keys()).union(after_method.keys())
    for smell in sorted(method_keys):
        method_list.append({
            "smellName": smell,
            "before": before_method.get(smell, 0),
            "after": after_method.get(smell, 0),
            "diff": method_diff.get(smell, 0)
        })
    return {
        "commitUrl": commit_url,
        "typeName": type_name,
        "fileLevelSmells": file_list,
        "methodLevelSmells": method_list
    }