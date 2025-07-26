import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# データのディレクトリ
BASE_DIR = "/Users/horikawa/Dev/Research-repo/InvestigatingTheImpactOfTestSpecificRefactoring"
JSON_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/src/results"
RESULTS_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/src/analysis/rq2"

# 出力ディレクトリを作成（存在しない場合）
os.makedirs(RESULTS_DIR, exist_ok=True)


def analyze_test_refactoring(df):
    """
    1コミットあたりのリファクタリング回数を分析し、統計情報をCSVに保存する
    """
    # 各コミットにおけるリファクタリングの種類ごとの出現回数を集計
    refactoring_counts_per_commit = df.groupby(['commit_id', 'type_name']).size().reset_index(name='count')

    # 1コミットあたりのリファクタリング回数を分析
    summary_stats = refactoring_counts_per_commit.groupby('type_name')['count'].describe()

    # 統計情報をCSVに保存
    summary_csv_path = f"{RESULTS_DIR}/test_refactoring_per_commit_summary.csv"
    summary_stats.to_csv(summary_csv_path, index=True, header=True)

    print(f"統計情報を {summary_csv_path} に保存しました。")

    return refactoring_counts_per_commit, summary_stats


def plot_refactoring_distribution(refactoring_counts_per_commit, summary_stats):
    """
    1コミットあたりのリファクタリング回数の分布をボックスプロットで表示
    """
    plt.figure(figsize=(14, 9))

    # 中央値の降順で並び替え
    order = summary_stats['50%'].sort_values(ascending=False).index

    # ボックスプロット作成
    sns.boxplot(
        data=refactoring_counts_per_commit,
        x="count",
        y="type_name",
        order=order,
        palette="coolwarm"
    )

    # グラフの設定
    # plt.title("Distribution of Refactorings per Commit", fontsize=16)
    plt.xlabel("Number of Occurrences per Commit", fontsize=14)
    plt.ylabel("Refactoring Type", fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=10)
    plt.subplots_adjust(left=0.25)
    # グラフ表示
    plt.show()


def main():
    # JSONファイルを読み込む
    json_file_path = f"{JSON_DIR}/annotation_result_2024-02-20.json"
    df = pd.read_json(json_file_path)

    # データ分析
    refactoring_counts_per_commit, summary_stats = analyze_test_refactoring(df)

    # グラフの描画
    plot_refactoring_distribution(refactoring_counts_per_commit, summary_stats)


if __name__ == "__main__":
    main()