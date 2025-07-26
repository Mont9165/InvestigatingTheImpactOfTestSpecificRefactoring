import argparse
import os
from testsmell_data_loader import (
    load_annotation_data, load_commit_data, get_parent_commit_url, load_smell_csv, load_smell_json
)
from testsmell_diff_calculator import (
    calculate_file_level_diff, calculate_method_level_diff, build_wide_row, build_json_object, FILE_SMELL_COLUMNS
)
from testsmell_diff_writer import (
    write_csv, write_json
)

def main():
    """
    Main function: orchestrates the test smell diff analysis.
    Loads annotation and commit data, processes each refactoring,
    calculates file/method level diffs, and writes results.
    """
    parser = argparse.ArgumentParser(description="Analyze test smell differences.")
    parser.add_argument("--base-dir", type=str, required=True, help="Base directory of the project.")
    parser.add_argument("--output-dir", type=str, default=".", help="Output directory for result files.")
    parser.add_argument("--annotation-json", type=str, required=True, help="Path to annotation JSON file.")
    parser.add_argument("--commit-csv", type=str, required=True, help="Path to commit info CSV file.")
    args = parser.parse_args()

    os.makedirs(args.output_dir, exist_ok=True)

    # Load annotation and commit data
    annotation_df = load_annotation_data(args.annotation_json)
    commit_df = load_commit_data(args.commit_csv)

    file_level_rows = []
    method_level_rows = []
    json_results = []

    grouped = annotation_df.groupby("url")
    for commit_url, group in grouped:
        parent_commit_url = get_parent_commit_url(commit_url, commit_df)
        if parent_commit_url is None:
            continue
        for _, row in group.iterrows():
            type_name = row.get("type_name", "UnknownRefactoring")
            parameter_data = row["parameter_data"]
            # Prepare commit dir names (replace as needed)
            commit_dir = commit_url.replace("https://github.com/", "").replace("commit/", "")
            parent_commit_dir = parent_commit_url.replace("https://github.com/", "").replace("commit/", "")
            # Load smell data
            before_df = load_smell_csv(os.path.join(args.base_dir, "5_analyze_test_refactoring/TestSmellDetector/results/smells", parent_commit_dir, "smells_number.csv"))
            after_df = load_smell_csv(os.path.join(args.base_dir, "5_analyze_test_refactoring/TestSmellDetector/results/smells", commit_dir, "smells_number.csv"))
            before_json = load_smell_json(os.path.join(args.base_dir, "5_analyze_test_refactoring/TestSmellDetector/results/smells", parent_commit_dir, "smells_result.json"))
            after_json = load_smell_json(os.path.join(args.base_dir, "5_analyze_test_refactoring/TestSmellDetector/results/smells", commit_dir, "smells_result.json"))
            # Calculate diffs
            before_file, after_file, diff_file = calculate_file_level_diff(parameter_data, before_df, after_df)
            before_method, after_method, diff_method = calculate_method_level_diff(parameter_data, before_json, after_json)
            # Build rows/objects
            file_level_rows.append(build_wide_row(commit_url, type_name, before_file, after_file, diff_file))
            method_level_rows.append(build_wide_row(commit_url, type_name, before_method, after_method, diff_method))
            json_results.append(build_json_object(commit_url, type_name, diff_file, before_file, after_file, diff_method, before_method, after_method))

    # Write results
    write_csv(file_level_rows, os.path.join(args.output_dir, "file_level_wide.csv"))
    write_csv(method_level_rows, os.path.join(args.output_dir, "method_level_wide.csv"))
    write_json(json_results, os.path.join(args.output_dir, "test_smell_analysis.json"))

if __name__ == "__main__":
    main()