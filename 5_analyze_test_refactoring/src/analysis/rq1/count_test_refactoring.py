import pandas as pd
import matplotlib.pyplot as plt

BASE_DIR = "/Users/horikawa/Dev/Research-repo/InvestigatingTheImpactOfTestSpecificRefactoring"
JSON_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/src/results"
RESULTS_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/src/analysis/rq1/output"


def analyze_test_refactoring(df):
    """
    Analyze the number of test refactoring occurrences per commit and refactoring type distribution.
    """
    # 何コミットでリファクタリングが行われたか
    unique_commits = df['url'].nunique()
    print(f"Total commits with test refactoring: {unique_commits}")

    # どのリファクタリングが多いか
    refactoring_counts = df['type_name'].value_counts()

    # CSV に保存
    refactoring_counts.to_csv(f"{RESULTS_DIR}/test_refactoring_counts.csv", index=True, header=["count"])
    print("Saved refactoring type counts to CSV.")

    # グラフ化 (リファクタリングの種類別)
    plt.figure(figsize=(12, 6))
    refactoring_counts.plot(kind='barh', color="skyblue")
    plt.xlabel("Number of Occurrences")
    plt.ylabel("Refactoring Type")
    plt.title("Frequency of Test Refactoring Types")
    plt.gca().invert_yaxis()  # 上位のリファクタリングを上に表示
    plt.tight_layout()
    plt.savefig(f"{RESULTS_DIR}/test_refactoring_counts.png")
    plt.show()

    # 1コミットあたりのリファクタリング回数
    refactoring_per_commit = df.groupby('url').size()

    # 統計情報
    print(refactoring_per_commit.describe())

    # CSV に保存
    refactoring_per_commit.to_csv(f"{RESULTS_DIR}/test_refactoring_per_commit.csv", index=True, header=["refactoring_count"])

    # ヒストグラムで可視化
    plt.figure(figsize=(8, 6))
    plt.hist(refactoring_per_commit, bins=20, color='lightcoral', edgecolor='black', alpha=0.7)
    plt.xlabel("Number of Refactorings per Commit")
    plt.ylabel("Frequency")
    plt.title("Distribution of Test Refactoring per Commit")
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.savefig(f"{RESULTS_DIR}/test_refactoring_per_commit.png")
    plt.show()


def main():
    df = pd.read_json(f"{JSON_DIR}/annotation_result_2024-02-20.json")
    analyze_test_refactoring(df)


if __name__ == "__main__":
    main()