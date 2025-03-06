import json
import logging
import os

import pandas as pd

BASE_DIR = "/Users/horikawa/Dev/Research-repo/InvestigatingTheImpactOfTestSpecificRefactoring"
JAR_PATH = f"{BASE_DIR}/5_analyze_test_smell/TestSmellDetector/jar/TestSmellDetector-0.1-jar-with-dependencies.jar"
TEST_SMELL_DIR = f"{BASE_DIR}/5_analyze_test_smell/TestSmellDetector/"
RESULTS_DIR = f"{BASE_DIR}/5_analyze_test_smell/src/results"

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="logfile.log",
    filemode="a"
)
logger = logging.getLogger(__name__)


def get_refactoring_data_from_annotation_data():
    """Retrieve refactoring data from annotation data."""
    return pd.read_json(f"{RESULTS_DIR}/annotation_result_2024-02-20.json")


def get_parent_commit_id(df2, commit_id):
    """Get the parent commit ID (performance improved)."""
    row = df2.loc[df2["commit_id"] == commit_id]
    return row["parent_commit_id"].iloc[0] if not row.empty else None


def load_csv_smell_data(commit_dir: str) -> pd.DataFrame:
    """
    Load the CSV file (smell_number.csv) corresponding to the commit directory and return a DataFrame.
    """
    csv_path = f"{TEST_SMELL_DIR}/results/smells/{commit_dir}/smells_number.csv"
    try:
        return pd.read_csv(csv_path)
    except Exception as e:
        logger.error(f"Failed to load CSV file: {csv_path} - {e}")
        return pd.DataFrame()


def load_json_smell_data(commit_dir: str) -> list:
    """
    Load the JSON file (smell_result.json) corresponding to the commit directory and return a list.
    """
    json_path = f"{TEST_SMELL_DIR}/results/smells/{commit_dir}/smell_result.json"
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load JSON file: {json_path} - {e}")
        return []


def compare_file_level_smells(file_path: str, commit_df: pd.DataFrame, parent_df: pd.DataFrame) -> dict:
    """
    Compare file-level test smell differences for the specified file path using CSV data.
    Returns a dictionary with test smell type as key and difference as value.
    """
    result = {}
    file_name = os.path.basename(file_path)

    # Use str.endswith() to check if TestFilePath ends with the extracted file name
    commit_file = commit_df[commit_df['TestFilePath'].str.endswith(file_name)]
    parent_file = parent_df[parent_df['TestFilePath'].str.endswith(file_name)]

    if commit_file.empty or parent_file.empty:
        logger.warning(f"Data for file {file_path} not found in CSV")
        return result

    # List of test smell columns (match the CSV column names)
    smell_columns = [
        'Assertion Roulette', 'Conditional Test Logic', 'Constructor Initialization',
        'Default Test', 'EmptyTest', 'Exception Catching Throwing', 'General Fixture',
        'Mystery Guest', 'Print Statement', 'Redundant Assertion', 'Sensitive Equality',
        'Verbose Test', 'Sleepy Test', 'Eager Test', 'Lazy Test', 'Duplicate Assert', 'Unknown Test'
    ]

    for smell in smell_columns:
        try:
            old_count = parent_file[smell].iloc[0]
            new_count = commit_file[smell].iloc[0]
            diff = new_count - old_count
            if diff != 0:
                result[smell] = diff
        except Exception as e:
            logger.error(f"Error comparing smell '{smell}' for file {file_path}: {e}")

    return result


def compare_method_level_smells(file_path: str, method_range: dict, commit_json: list, parent_json: list) -> dict:
    """
    Compare method-level test smell differences for the specified file path and method range using JSON data.
    The method_range is expected to be a dict containing keys like 'startLine' and 'endLine'.
    Returns a dictionary with test smell type as key and difference as value.
    """
    result = {}

    # Filter JSON entries matching the file path
    commit_entries = [entry for entry in commit_json if entry["testFilePath"].endswith(file_path)]
    parent_entries = [entry for entry in parent_json if entry["testFilePath"].endswith(file_path)]

    def extract_method_smells_by_range(entries: list) -> list:
        method_smells = []
        for entry in entries:
            for s in entry.get("smells", []):
                # Check if the smell is method-level and its begin/end lines match the provided range
                if s.get("smellParentType") == "Method":
                    if (s.get("beginLine") == method_range.get("startLine") and
                        s.get("endLine") == method_range.get("endLine")):
                        method_smells.append(s)
        return method_smells

    def count_smells(smells: list) -> dict:
        counts = {}
        for s in smells:
            name = s.get("smellName")
            counts[name] = counts.get(name, 0) + 1
        return counts

    commit_method_smells = extract_method_smells_by_range(commit_entries)
    parent_method_smells = extract_method_smells_by_range(parent_entries)

    commit_counts = count_smells(commit_method_smells)
    parent_counts = count_smells(parent_method_smells)

    # Combine all smell types present in either commit
    all_smells = set(commit_counts.keys()).union(parent_counts.keys())
    for smell in all_smells:
        diff = commit_counts.get(smell, 0) - parent_counts.get(smell, 0)
        if diff != 0:
            result[smell] = diff

    return result


def calculate_testsmell_change_amount(commit_df, parent_df, commit_json, parent_json, all_data_types, after_data,
                                      before_data, refactoring_diff):
    pass


def process_parameter_data(parameter_data: dict, commit_url: str, parent_commit_url: str):
    """
    Process the parameter_data for refactoring instances and output the file-level, method-level,
    and overall refactoring-level test smell differences.
    """
    # Extract commit directory strings from URLs
    commit_dir = commit_url.replace("https://github.com", "").replace("commit/", "")
    parent_commit_dir = parent_commit_url.replace("https://github.com", "").replace("commit/", "")

    # Load CSV and JSON data for the commit and its parent commit
    commit_df = load_csv_smell_data(commit_dir)
    parent_df = load_csv_smell_data(parent_commit_dir)
    commit_json = load_json_smell_data(commit_dir)
    parent_json = load_json_smell_data(parent_commit_dir)

    # Retrieve after and before data from parameter_data
    after_data = parameter_data.get("after", {})
    before_data = parameter_data.get("before", {})

    # Get all data types present in either phase
    all_data_types = set(after_data.keys()).union(before_data.keys())

    # Dictionary to aggregate differences at the refactoring level
    refactoring_diff = {}

    # Process each phase (e.g., "after", "before") in parameter_data
    calculate_testsmell_change_amount(commit_df, parent_df, commit_json, parent_json, all_data_types, after_data,
                                      before_data, refactoring_diff)

    for data_type in all_data_types:
        print(f"Data type: {data_type}")

        after_elements = after_data.get(data_type, {}).get("elements", [])
        before_elements = before_data.get(data_type, {}).get("elements", [])

        # Build a dictionary for before elements keyed by file name
        before_files = {}
        for elem in before_elements:
            file_path = elem['location']['path']
            file_name = os.path.basename(file_path)
            before_files[file_name] = elem

        # Process each element in the after phase
        for after_elem in after_elements:
            after_file_path = after_elem['location']['path']
            file_name = os.path.basename(after_file_path)
            print(f"  After file: {after_file_path}")

            # File-level differences for 'after' state (using commit_df and parent_df)
            after_diff = compare_file_level_smells(after_file_path, commit_df, parent_df)
            if after_diff:
                print("    After file-level differences:")
                for smell, diff in after_diff.items():
                    print(f"      {smell}: {diff:+d}")

            # If a matching 'before' element exists (by file name), compare differences
            if file_name in before_files:
                before_elem = before_files[file_name]
                before_file_path = before_elem['location']['path']
                print(f"  Before file: {before_file_path}")
                before_diff = compare_file_level_smells(before_file_path, commit_df, parent_df)
                if before_diff:
                    print("    Before file-level differences:")
                    for smell, diff in before_diff.items():
                        print(f"      {smell}: {diff:+d}")

                # Compute net difference: (after_diff - before_diff)
                net_diff = {}
                for smell in set(after_diff.keys()).union(before_diff.keys()):
                    net = after_diff.get(smell, 0) - before_diff.get(smell, 0)
                    if net != 0:
                        net_diff[smell] = net
                        refactoring_diff[smell] = refactoring_diff.get(smell, 0) + net
                if net_diff:
                    print("    Net difference (After - Before):")
                    for smell, diff in net_diff.items():
                        print(f"      {smell}: {diff:+d}")
            else:
                print(f"  No matching 'before' element found for file: {file_name}")

            # Process method-level differences using range information (if available)
            method_range = after_elem.get("location", {}).get("range")
            if method_range:
                method_diff = compare_method_level_smells(after_file_path, method_range, commit_json, parent_json)
                if method_diff:
                    print(f"    Method with range {method_range} differences:")
                    for smell, diff in method_diff.items():
                        print(f"      {smell}: {diff:+d}")
                        refactoring_diff[smell] = refactoring_diff.get(smell, 0) + diff

    # Output overall refactoring-level test smell differences
    if refactoring_diff:
        print("Overall refactoring-level test smell differences:")
        for smell, diff in refactoring_diff.items():
            print(f"  {smell}: {diff:+d}")

    # Output overall refactoring-level test smell differences
    if refactoring_diff:
        print("Overall refactoring-level test smell differences:")
        for smell, diff in refactoring_diff.items():
            print(f"  {smell}: {diff:+d}")


def process_grouped_data(commit_url, df2, group):
    try:
        commit_id = commit_url.split("/")[-1]
        repo_url = "/".join(commit_url.split("/")[:5])
        parent_commit_id = get_parent_commit_id(df2, commit_id)

        if parent_commit_id is None:
            logger.warning(f"Parent commit not found for {commit_url}")
            return

        parent_commit_url = f"{repo_url}/commit/{parent_commit_id}"
        for i, row in group.iterrows():
            process_parameter_data(row["parameter_data"], commit_url, parent_commit_url)

    except Exception as e:
        logger.error(f"Error in process_grouped_data for {commit_url}: {e}")


def main():
    """Main function."""
    try:
        df1 = get_refactoring_data_from_annotation_data()
        df2 = pd.read_csv(f"{BASE_DIR}/2_sampling_test_refactor_commits/result/sampling_test_commits_all.csv")
        grouped = df1.groupby("url")
        for commit_url, group in grouped:
            print(f"Processing refactoring data for {commit_url}")
            process_grouped_data(commit_url, df2, group)

    except Exception as e:
        logger.error(f"Error in main: {e}")


if __name__ == "__main__":
    main()