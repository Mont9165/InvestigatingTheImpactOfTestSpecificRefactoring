import pandas as pd
import json
from glob import glob


def json_to_custom_csv_with_index(json_files_pattern, sampling_commits_path, output_csv_path):
    sampling_commits_df = pd.read_csv(sampling_commits_path)
    sampling_commits_mapping = {
        commit_url: idx for idx, commit_url in enumerate(sampling_commits_df["commit_url"])
    }

    # List all JSON files matching the pattern
    json_files = glob(json_files_pattern)
    if not json_files:
        print("No JSON files found.")
        return

    extracted_data = []

    # Process each JSON file
    for json_file_path in json_files:
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        for record in data:
            annotator_name = record.get("annotatorName", "")
            commit_owner = record["commit"].get("owner", "")
            commit_repository = record["commit"].get("repository", "")
            commit_sha = record["commit"].get("sha", "")
            commit_url = f"https://github.com/{commit_owner}/{commit_repository}/commit/{commit_sha}"

            # Find index for the commit URL
            index = sampling_commits_mapping.get(commit_url.lower(), "N/A")

            for snapshot in record.get("snapshots", []):
                for change in snapshot.get("changes", []):
                    type_name = change.get("typeName", "")
                    description = change.get("description", "")

                    try:
                        before_range = change["parameterData"]["before"]["removed codes"].get("elements", [])
                        after_range = change["parameterData"]["after"]["added codes"].get("elements", [])

                        if before_range == [] or after_range == []:
                            append_extract_data(extracted_data, index, commit_url, type_name, description,
                                                annotator_name,"", "", "", "", "")

                        # Extract line ranges for before and after
                        for elem_before, elem_after in zip(before_range, after_range):
                            before_path = elem_before["location"]["path"]
                            startline_before = elem_before["location"]["range"]["startLine"]
                            endline_before = elem_before["location"]["range"]["endLine"]
                            startline_after = elem_after["location"]["range"]["startLine"]
                            endline_after = elem_after["location"]["range"]["endLine"]
                            append_extract_data(extracted_data, index, commit_url, type_name, description,
                                                annotator_name, before_path, startline_before, endline_before,
                                                startline_after, endline_after)

                    except KeyError as e:
                        append_extract_data(extracted_data, index, commit_url, type_name, description, annotator_name,
                                            "", "", "", "", "")

    # Convert to DataFrame and save to CSV
    df = pd.DataFrame(extracted_data)
    df.to_csv(output_csv_path, index=False, encoding='utf-8')
    print(f"CSV file has been saved to {output_csv_path}")


def append_extract_data(extracted_data, index, commit_url, type_name, description, annotator_name, before_path, startline_before, endline_before, startline_after, endline_after):
    extracted_data.append({
        "Index": index,
        "Commit URL": commit_url,
        "Type Name": type_name,
        "Description": description,
        "Memo": "",
        "Agreement": "",
        "Annotator Name": annotator_name,
        "Path": before_path,
        "Start Line (Before)": startline_before,
        "End Line (Before)": endline_before,
        "Start Line (After)": startline_after,
        "End Line (After)": endline_after
    })


# Usage example
# json_files_pattern = "../annotation_result/test-refactoring-1/horikawa/*.json"  # Pattern to match JSON files
json_files_pattern = "../annotation_result/test-refactoring-2/horikawa/*.json"  # Pattern to match JSON files
sampling_commits_path = "../../../2_sampling_test_refactor_commits/result/sampling_test_commits.csv"  # Path to sampling_test_commits.csv
output_csv_path = "../../result/not_use/output.csv"
json_to_custom_csv_with_index(json_files_pattern, sampling_commits_path, output_csv_path)
