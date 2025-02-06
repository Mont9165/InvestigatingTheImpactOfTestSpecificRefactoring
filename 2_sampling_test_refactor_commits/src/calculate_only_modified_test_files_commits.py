import pandas as pd

# CSVデータを読み込む
data = pd.read_csv(
    "1_collect_test_refactoring_commits/src/main/resources/output/refactor_commit_only_modified_test_files_projects_info.csv")

# 変更ファイル数、追加行数、削除行数の基本統計量を計算
statistics = {
    'changed_files_count': {
        'max': data['changed_files_count'].max(),
        'min': data['changed_files_count'].min(),
        'mean': data['changed_files_count'].mean(),
        'median': data['changed_files_count'].median()
    },
    'total_addition_lines': {
        'max': data['total_addition_lines'].max(),
        'min': data['total_addition_lines'].min(),
        'mean': data['total_addition_lines'].mean(),
        'median': data['total_addition_lines'].median()
    },
    'total_deletions_lines': {
        'max': data['total_deletions_lines'].max(),
        'min': data['total_deletions_lines'].min(),
        'mean': data['total_deletions_lines'].mean(),
        'median': data['total_deletions_lines'].median()
    }
}

# 結果をデータフレームとして表示
statistics_df = pd.DataFrame(statistics)
statistics_df = statistics_df.T  # 転置して列と行を入れ替える

print(statistics_df)