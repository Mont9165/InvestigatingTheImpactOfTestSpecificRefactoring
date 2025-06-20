import pandas as pd
import matplotlib.pyplot as plt
import os


BASE_DIR = "/Users/horikawa/Dev/Research-repo/InvestigatingTheImpactOfTestSpecificRefactoring"
JSON_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/src/results"
RESULTS_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/src/analysis/rq1/output/test"
SAMPLE_COMMITS_PATH = os.path.join(BASE_DIR, "2_sampling_test_refactor_commits", "result", "sampling_test_commits.csv")


def analyze_test_refactoring(df):
    """
    Analyze the number of test refactoring occurrences per commit and refactoring type distribution.
    """
    # サンプルコミットの読み込み
    sample_commits = pd.read_csv(SAMPLE_COMMITS_PATH)
    sample_hashes = set(sample_commits['commit_id'])

    # URLからコミットIDを抽出する関数
    def extract_commit_id(url):
        return url.split('/')[-1]

    # URLからコミットIDを抽出
    df['commit_id'] = df['url'].apply(extract_commit_id)

    # 何コミットでリファクタリングが行われたか
    unique_commits = df['commit_id'].nunique()
    print(f"Total commits with test refactoring: {unique_commits}")

    # どのリファクタリングが多いか
    refactoring_counts = df['type_name'].value_counts()

    # CSV に保存
    refactoring_counts.to_csv(f"{RESULTS_DIR}/test_refactoring_counts.csv", index=True, header=["count"])
    print("Saved refactoring type counts to CSV.")

    # サマリー情報の作成
    summary_data = {
        'metric': ['総リファクタリング数', 'リファクタリングを含むコミット数', 'リファクタリングタイプ数'],
        'value': [len(df), unique_commits, len(refactoring_counts)]
    }
    summary_df = pd.DataFrame(summary_data)
    summary_df.to_csv(f"{RESULTS_DIR}/test_refactoring_summary.csv", index=False)
    print("Saved summary information to CSV.")

    # グラフ化 (リファクタリングの種類別)
    plt.figure(figsize=(12, 6))
    refactoring_counts.plot(kind='barh', color="skyblue")
    plt.xlabel("Number of Occurrences")
    plt.ylabel("Refactoring Type")
    plt.title("Frequency of Test Refactoring Types")
    plt.gca().invert_yaxis()  # 上位のリファクタリングを上に表示
    plt.tight_layout()
    plt.savefig(f"{RESULTS_DIR}/test_refactoring_counts.png")
    # plt.show()

    # 1コミットあたりのリファクタリング回数
    refactoring_per_commit = df.groupby('commit_id').size()

    # すべてのサンプルコミットに対してリファクタリング数を集計（0を含む）
    all_commits_refactoring = pd.DataFrame({'commit_id': list(sample_hashes)})
    all_commits_refactoring = all_commits_refactoring.merge(
        refactoring_per_commit.reset_index().rename(columns={0: 'refactoring_count'}),
        on='commit_id',
        how='left'
    ).fillna(0)
    all_commits_refactoring['refactoring_count'] = all_commits_refactoring['refactoring_count'].astype(int)

    # CSV に保存
    all_commits_refactoring.to_csv(f"{RESULTS_DIR}/all_commits_test_refactoring.csv", index=False)

    # 統計情報
    print("\nリファクタリング数の分布:")
    distribution = all_commits_refactoring['refactoring_count'].value_counts().sort_index()
    for count, num_commits in distribution.items():
        print(f"{count}回のリファクタリング: {num_commits}コミット")

    # ヒストグラムで可視化
    plt.figure(figsize=(8, 6))
    plt.hist(all_commits_refactoring['refactoring_count'], bins=100, color='lightcoral', edgecolor='black', alpha=0.7)
    plt.xlabel("Number of Refactorings per Commit")
    plt.ylabel("Frequency")
    plt.title("Distribution of Test Refactoring per Commit")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig(f"{RESULTS_DIR}/test_refactoring_per_commit.png")
    plt.show()

    # サマリー情報の表示
    print("\nサマリー情報:")
    print(f"総リファクタリング数: {len(df)}")
    print(f"リファクタリングを含むコミット数: {unique_commits}")
    print(f"リファクタリングタイプ数: {len(refactoring_counts)}")


def main():
    df = pd.read_json(f"{JSON_DIR}/annotation_result_2024-02-20.json")
    analyze_test_refactoring(df)


if __name__ == "__main__":
    main()