import pandas as pd
from collections import Counter


def count_commits_per_repo(csv_file, output_file):
    df = pd.read_csv(csv_file)
    counter = Counter(df['repository_name'])

    # CSVに書き出すためのリスト
    rows = [['repository_name', 'commit_count']]

    total = sum(counter.values())
    rows.append(['Total', total])

    for key, value in counter.items():
        rows.append([key, value])

    # pandasを使ってCSVに出力
    output_df = pd.DataFrame(rows)
    output_df.to_csv(output_file, index=False, header=False, encoding='utf-8')
    print(f"Data written to {output_file}")


def main():
    # csv_file = '../../1_collect_test_refactoring_commits/src/main/resources/output/refactor_commits_projects_info.csv'
    csv_file = '1_collect_test_refactoring_commits/src/main/resources/output/refactor_commit_only_modified_test_files_projects_info.csv'
    output_file = '../result/commits_per_repo/refactor_commits_projects_info.csv'
    count_commits_per_repo(csv_file, output_file)


if __name__ == '__main__':
    main()
