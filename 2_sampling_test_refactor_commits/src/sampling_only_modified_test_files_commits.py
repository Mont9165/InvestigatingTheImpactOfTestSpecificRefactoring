import csv
import json
import pandas as pd
import os

SAMPLE_SIZE = 370


def main():
    csv_file = '../../1_collect_test_refactoring_commits/src/main/resources/output/refactor_commit_only_modified_test_files_projects_info.csv'
    output_csv_file = '../result/sampling_test_commits_all.csv'
    output_ndjson_file = '../result/sampling_test_commits.ndjson'

    random_to_csv(csv_file, output_csv_file)
    # csv_to_ndjson(output_csv_file, output_ndjson_file)


def csv_to_ndjson(csv_file, output_file):
    with open(output_file, 'w', encoding='utf-8') as w_file:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # ヘッダーをスキップ
            for row in reader:
                owner, repository = row[0].split('/')
                sha = row[2]
                ndjson_data = {
                    "sha": sha,
                    "owner": owner,
                    "repository": repository
                }
                # NDJSON形式で1行ずつ書き込み
                w_file.write(json.dumps(ndjson_data) + "\n")


def random_to_csv(csv_file, output_file):
    df = pd.read_csv(csv_file)
    df_sampled = df.sample(SAMPLE_SIZE)
    df_sampled.to_csv(output_file, index=False)


if __name__ == '__main__':
    os.makedirs('../result', exist_ok=True)
    main()
