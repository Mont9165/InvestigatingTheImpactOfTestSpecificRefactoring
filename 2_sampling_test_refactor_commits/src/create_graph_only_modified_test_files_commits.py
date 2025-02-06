import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

# CSVデータを読み込む
data = pd.read_csv(
    "1_collect_test_refactoring_commits/src/main/resources/output/refactor_commit_only_modified_test_files_projects_info.csv")

# プロットのスタイルを設定
sns.set(style="whitegrid")

# 変更ファイル数のバイオリンプロット
plt.figure(figsize=(8, 6))
sns.violinplot(y='changed_files_count', data=data, color="skyblue", inner=None)
mean_val = data['changed_files_count'].mean()
median_val = data['changed_files_count'].median()
plt.axhline(mean_val, color='red', linestyle='--', label=f'Mean: {mean_val:.2f}')
plt.axhline(median_val, color='green', linestyle='-', label=f'Median: {median_val:.2f}')
plt.title('Changed Files Count Distribution')
plt.legend()
plt.savefig('graph/changed_files_count_distribution.png')
plt.close()

# 追加行数のバイオリンプロット
plt.figure(figsize=(8, 6))
sns.violinplot(y='total_addition_lines', data=data, color="lightgreen", inner=None)
mean_val = data['total_addition_lines'].mean()
median_val = data['total_addition_lines'].median()
plt.axhline(mean_val, color='red', linestyle='--', label=f'Mean: {mean_val:.2f}')
plt.axhline(median_val, color='green', linestyle='-', label=f'Median: {median_val:.2f}')
plt.title('Total Addition Lines Distribution')
plt.legend()
plt.savefig('graph/total_addition_lines_distribution.png')
plt.close()

# 削除行数のバイオリンプロット
plt.figure(figsize=(8, 6))
sns.violinplot(y='total_deletions_lines', data=data, color="salmon", inner=None)
mean_val = data['total_deletions_lines'].mean()
median_val = data['total_deletions_lines'].median()
plt.axhline(mean_val, color='red', linestyle='--', label=f'Mean: {mean_val:.2f}')
plt.axhline(median_val, color='green', linestyle='-', label=f'Median: {median_val:.2f}')
plt.title('Total Deletions Lines Distribution')
plt.legend()
plt.savefig('graph/total_deletions_lines_distribution.png')
plt.close()


