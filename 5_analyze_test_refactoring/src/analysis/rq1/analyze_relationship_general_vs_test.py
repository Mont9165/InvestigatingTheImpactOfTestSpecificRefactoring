import pandas as pd
import matplotlib.pyplot as plt
import os
from typing import Dict, List, Tuple
import seaborn as sns

BASE_DIR = "/Users/horikawa/Dev/Research-repo/InvestigatingTheImpactOfTestSpecificRefactoring"
DATA_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/src/analysis/rq1/output"
TEST_REFACTORING_PATH = f"{DATA_DIR}/test/all_commits_test_refactoring.csv"
GENERAL_REFACTORING_PATH = f"{DATA_DIR}/general/all_commits_refactoring.csv"
TEST_TYPE_PATH = f"{DATA_DIR}/test/test_refactoring_counts.csv"
GENERAL_TYPE_PATH = f"{DATA_DIR}/general/general_refactoring_counts.csv"
RESULTS_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/src/analysis/rq1/output/relationship"

def load_data() -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """テストリファクタリングと一般リファクタリングのデータを読み込む"""
    test_refactoring = pd.read_csv(TEST_REFACTORING_PATH)
    general_refactoring = pd.read_csv(GENERAL_REFACTORING_PATH)
    test_types = pd.read_csv(TEST_TYPE_PATH)
    general_types = pd.read_csv(GENERAL_TYPE_PATH)
    return test_refactoring, general_refactoring, test_types, general_types

def analyze_quantitative_comparison(test_df: pd.DataFrame, general_df: pd.DataFrame) -> Dict:
    """量的な比較分析を実施"""
    results = {}
    
    # リファクタリングを含むコミットの割合
    test_commits_with_refactoring = len(test_df[test_df['refactoring_count'] > 0])
    general_commits_with_refactoring = len(general_df[general_df['refactoring_count'] > 0])
    total_commits = len(test_df)
    
    results['test_refactoring_ratio'] = test_commits_with_refactoring / total_commits
    results['general_refactoring_ratio'] = general_commits_with_refactoring / total_commits
    
    # 1コミットあたりの平均リファクタリング数
    results['test_avg_refactoring'] = test_df['refactoring_count'].mean()
    results['general_avg_refactoring'] = general_df['refactoring_count'].mean()
    
    return results

def analyze_correlation(test_df: pd.DataFrame, general_df: pd.DataFrame) -> Dict:
    """テストリファクタリングと一般リファクタリングの相関関係を分析"""
    results = {}
    
    # 両方のリファクタリングを含むコミット数
    merged_df = pd.merge(test_df, general_df, on='commit_id', suffixes=('_test', '_general'))
    both_refactoring = len(merged_df[(merged_df['refactoring_count_test'] > 0) & 
                                   (merged_df['refactoring_count_general'] > 0)])
    
    results['both_refactoring_ratio'] = both_refactoring / len(merged_df)
    
    # リファクタリング数の相関
    correlation = merged_df['refactoring_count_test'].corr(merged_df['refactoring_count_general'])
    results['refactoring_count_correlation'] = correlation
    
    return results

def analyze_refactoring_types(test_types: pd.DataFrame, general_types: pd.DataFrame) -> Dict:
    """リファクタリングタイプの比較分析を実施"""
    results = {}
    
    # カラム名を統一
    test_types = test_types.rename(columns={'type_name': 'refactoring_type'})
    
    # リファクタリングタイプの総数
    results['test_type_count'] = len(test_types)
    results['general_type_count'] = len(general_types)
    
    # 上位5つのリファクタリングタイプ
    results['top_test_types'] = test_types.nlargest(5, 'count')
    results['top_general_types'] = general_types.nlargest(5, 'count')
    
    return results

def visualize_comparison(test_df: pd.DataFrame, general_df: pd.DataFrame):
    """比較結果を可視化"""
    # リファクタリング数の分布を比較
    plt.figure(figsize=(12, 6))
    plt.hist(test_df['refactoring_count'], bins=50, alpha=0.5, label='Test Refactoring')
    plt.hist(general_df['refactoring_count'], bins=50, alpha=0.5, label='General Refactoring')
    plt.xlabel('Number of Refactorings per Commit')
    plt.ylabel('Frequency')
    plt.title('Distribution of Refactoring Counts')
    plt.legend()
    plt.savefig(f"{RESULTS_DIR}/refactoring_distribution_comparison.png")
    plt.close()

def visualize_refactoring_types(test_types: pd.DataFrame, general_types: pd.DataFrame):
    """リファクタリングタイプの分布を可視化"""
    # カラム名を統一
    test_types = test_types.rename(columns={'type_name': 'refactoring_type'})
    
    # 上位10タイプの比較
    top_n = 10
    test_top = test_types.nlargest(top_n, 'count')
    general_top = general_types.nlargest(top_n, 'count')
    
    # テストリファクタリングタイプの分布
    plt.figure(figsize=(15, 6))
    plt.subplot(1, 2, 1)
    sns.barplot(data=test_top, x='count', y='refactoring_type')
    plt.title('Top 10 Test Refactoring Types')
    plt.xlabel('Count')
    plt.ylabel('Refactoring Type')
    
    # 一般リファクタリングタイプの分布
    plt.subplot(1, 2, 2)
    sns.barplot(data=general_top, x='count', y='refactoring_type')
    plt.title('Top 10 General Refactoring Types')
    plt.xlabel('Count')
    plt.ylabel('Refactoring Type')
    
    plt.tight_layout()
    plt.savefig(f"{RESULTS_DIR}/refactoring_types_comparison.png")
    plt.close()
    
    # リファクタリングタイプ数の比較
    plt.figure(figsize=(8, 6))
    type_counts = pd.DataFrame({
        'Category': ['Test Refactoring', 'General Refactoring'],
        'Number of Types': [len(test_types), len(general_types)]
    })
    sns.barplot(data=type_counts, x='Category', y='Number of Types')
    plt.title('Number of Refactoring Types')
    plt.savefig(f"{RESULTS_DIR}/refactoring_type_counts.png")
    plt.close()

def analyze_coexistence(test_df: pd.DataFrame, general_df: pd.DataFrame) -> Dict:
    """リファクタリングの共存関係を分析"""
    results = {}
    
    # 両方のデータフレームをマージ
    merged_df = pd.merge(test_df, general_df, on='commit_id', suffixes=('_test', '_general'))
    
    # 各カテゴリのコミット数を計算
    test_only = len(merged_df[(merged_df['refactoring_count_test'] > 0) & (merged_df['refactoring_count_general'] == 0)])
    general_only = len(merged_df[(merged_df['refactoring_count_test'] == 0) & (merged_df['refactoring_count_general'] > 0)])
    both = len(merged_df[(merged_df['refactoring_count_test'] > 0) & (merged_df['refactoring_count_general'] > 0)])
    neither = len(merged_df[(merged_df['refactoring_count_test'] == 0) & (merged_df['refactoring_count_general'] == 0)])
    
    results['test_only'] = test_only
    results['general_only'] = general_only
    results['both'] = both
    results['neither'] = neither
    results['total'] = len(merged_df)
    
    # 各カテゴリの割合を計算
    results['test_only_ratio'] = test_only / len(merged_df)
    results['general_only_ratio'] = general_only / len(merged_df)
    results['both_ratio'] = both / len(merged_df)
    results['neither_ratio'] = neither / len(merged_df)
    
    return results

def analyze_relationship(test_df: pd.DataFrame, general_df: pd.DataFrame) -> Dict:
    """リファクタリングの関連性を分析"""
    results = {}
    
    # 両方のデータフレームをマージ
    merged_df = pd.merge(test_df, general_df, on='commit_id', suffixes=('_test', '_general'))
    
    # リファクタリング数の相関
    correlation = merged_df['refactoring_count_test'].corr(merged_df['refactoring_count_general'])
    results['correlation'] = correlation
    
    # リファクタリング数の比率
    results['test_to_general_ratio'] = merged_df['refactoring_count_test'].mean() / merged_df['refactoring_count_general'].mean()
    
    # リファクタリングの同時発生の傾向
    test_refactoring_commits = merged_df[merged_df['refactoring_count_test'] > 0]
    general_refactoring_commits = merged_df[merged_df['refactoring_count_general'] > 0]
    
    # テストリファクタリングを含むコミットで一般リファクタリングが発生する確率
    results['general_given_test'] = len(test_refactoring_commits[test_refactoring_commits['refactoring_count_general'] > 0]) / len(test_refactoring_commits)
    
    # 一般リファクタリングを含むコミットでテストリファクタリングが発生する確率
    results['test_given_general'] = len(general_refactoring_commits[general_refactoring_commits['refactoring_count_test'] > 0]) / len(general_refactoring_commits)
    
    return results

def visualize_coexistence(coexistence_results: Dict):
    """共存関係を可視化"""
    # カテゴリ別のコミット数を可視化
    plt.figure(figsize=(10, 6))
    categories = ['Test Only', 'General Only', 'Both', 'Neither']
    counts = [
        coexistence_results['test_only'],
        coexistence_results['general_only'],
        coexistence_results['both'],
        coexistence_results['neither']
    ]
    
    plt.bar(categories, counts)
    plt.title('Distribution of Refactoring Types in Commits')
    plt.ylabel('Number of Commits')
    
    # 数値を棒グラフの上に表示
    for i, count in enumerate(counts):
        plt.text(i, count, str(count), ha='center', va='bottom')
    
    plt.savefig(f"{RESULTS_DIR}/refactoring_coexistence.png")
    plt.close()
    
    # パーセンテージを可視化
    plt.figure(figsize=(10, 6))
    percentages = [
        coexistence_results['test_only_ratio'],
        coexistence_results['general_only_ratio'],
        coexistence_results['both_ratio'],
        coexistence_results['neither_ratio']
    ]
    
    plt.bar(categories, percentages)
    plt.title('Distribution of Refactoring Types in Commits (Percentage)')
    plt.ylabel('Percentage')
    
    # パーセンテージを棒グラフの上に表示
    for i, pct in enumerate(percentages):
        plt.text(i, pct, f'{pct:.1%}', ha='center', va='bottom')
    
    plt.savefig(f"{RESULTS_DIR}/refactoring_coexistence_percentage.png")
    plt.close()

def check_duplicate_commits(test_df: pd.DataFrame, general_df: pd.DataFrame):
    """重複しているコミットIDを確認"""
    # テストリファクタリングの重複を確認
    test_duplicates = test_df[test_df.duplicated(subset=['commit_id'], keep=False)]
    if not test_duplicates.empty:
        print("\nテストリファクタリングで重複しているコミットID:")
        for commit_id in test_duplicates['commit_id'].unique():
            print(f"コミットID: {commit_id}")
            print(f"  出現回数: {len(test_duplicates[test_duplicates['commit_id'] == commit_id])}")
            print(f"  リファクタリング数: {test_duplicates[test_duplicates['commit_id'] == commit_id]['refactoring_count'].tolist()}")
    
    # 一般リファクタリングの重複を確認
    general_duplicates = general_df[general_df.duplicated(subset=['commit_id'], keep=False)]
    if not general_duplicates.empty:
        print("\n一般リファクタリングで重複しているコミットID:")
        for commit_id in general_duplicates['commit_id'].unique():
            print(f"コミットID: {commit_id}")
            print(f"  出現回数: {len(general_duplicates[general_duplicates['commit_id'] == commit_id])}")
            print(f"  リファクタリング数: {general_duplicates[general_duplicates['commit_id'] == commit_id]['refactoring_count'].tolist()}")
    
    # 重複がない場合のメッセージ
    if test_duplicates.empty and general_duplicates.empty:
        print("\n重複しているコミットIDはありません。")

def analyze_statistics(test_df: pd.DataFrame, general_df: pd.DataFrame):
    """リファクタリング数の詳細な統計情報を分析"""
    print("\nテストリファクタリングの統計情報:")
    test_stats = test_df['refactoring_count'].describe()
    print(f"全コミット数: {len(test_df)}")
    print(f"平均: {test_stats['mean']:.3f}")
    print(f"標準偏差: {test_stats['std']:.3f}")
    print(f"最小値: {test_stats['min']:.0f}")
    print(f"25%タイル: {test_stats['25%']:.0f}")
    print(f"中央値: {test_stats['50%']:.0f}")
    print(f"75%タイル: {test_stats['75%']:.0f}")
    print(f"最大値: {test_stats['max']:.0f}")
    
    print("\n一般リファクタリングの統計情報:")
    general_stats = general_df['refactoring_count'].describe()
    print(f"全コミット数: {len(general_df)}")
    print(f"平均: {general_stats['mean']:.3f}")
    print(f"標準偏差: {general_stats['std']:.3f}")
    print(f"最小値: {general_stats['min']:.0f}")
    print(f"25%タイル: {general_stats['25%']:.0f}")
    print(f"中央値: {general_stats['50%']:.0f}")
    print(f"75%タイル: {general_stats['75%']:.0f}")
    print(f"最大値: {general_stats['max']:.0f}")
    
    # リファクタリング数の分布を可視化
    plt.figure(figsize=(12, 6))
    
    # テストリファクタリングの分布
    plt.subplot(1, 2, 1)
    plt.hist(test_df['refactoring_count'], bins=50, alpha=0.7, color='skyblue')
    plt.title('Distribution of Test Refactoring Counts')
    plt.xlabel('Number of Refactorings')
    plt.ylabel('Frequency')
    plt.axvline(test_stats['mean'], color='red', linestyle='dashed', linewidth=1, label=f'Mean: {test_stats["mean"]:.2f}')
    plt.axvline(test_stats['50%'], color='green', linestyle='dashed', linewidth=1, label=f'Median: {test_stats["50%"]:.2f}')
    plt.legend()
    
    # 一般リファクタリングの分布
    plt.subplot(1, 2, 2)
    plt.hist(general_df['refactoring_count'], bins=50, alpha=0.7, color='lightcoral')
    plt.title('Distribution of General Refactoring Counts')
    plt.xlabel('Number of Refactorings')
    plt.ylabel('Frequency')
    plt.axvline(general_stats['mean'], color='red', linestyle='dashed', linewidth=1, label=f'Mean: {general_stats["mean"]:.2f}')
    plt.axvline(general_stats['50%'], color='green', linestyle='dashed', linewidth=1, label=f'Median: {general_stats["50%"]:.2f}')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig(f"{RESULTS_DIR}/refactoring_statistics_distribution.png")
    plt.close()

def main():
    # データの読み込み
    test_df, general_df, test_types, general_types = load_data()
    
    # 重複チェック
    check_duplicate_commits(test_df, general_df)
    
    # 統計情報の分析
    analyze_statistics(test_df, general_df)
    
    # 量的な比較分析
    quantitative_results = analyze_quantitative_comparison(test_df, general_df)
    print("\n量的な比較結果:")
    print(f"テストリファクタリングを含むコミットの割合: {quantitative_results['test_refactoring_ratio']:.2%}")
    print(f"一般リファクタリングを含むコミットの割合: {quantitative_results['general_refactoring_ratio']:.2%}")
    print(f"1コミットあたりの平均テストリファクタリング数: {quantitative_results['test_avg_refactoring']:.2f}")
    print(f"1コミットあたりの平均一般リファクタリング数: {quantitative_results['general_avg_refactoring']:.2f}")
    
    # 共存関係の分析
    coexistence_results = analyze_coexistence(test_df, general_df)
    print("\n共存関係の分析結果:")
    print(f"テストリファクタリングのみ: {coexistence_results['test_only']}コミット ({coexistence_results['test_only_ratio']:.1%})")
    print(f"一般リファクタリングのみ: {coexistence_results['general_only']}コミット ({coexistence_results['general_only_ratio']:.1%})")
    print(f"両方のリファクタリング: {coexistence_results['both']}コミット ({coexistence_results['both_ratio']:.1%})")
    print(f"リファクタリングなし: {coexistence_results['neither']}コミット ({coexistence_results['neither_ratio']:.1%})")
    
    # 関連性の分析
    relationship_results = analyze_relationship(test_df, general_df)
    print("\n関連性の分析結果:")
    print(f"リファクタリング数の相関係数: {relationship_results['correlation']:.2f}")
    print(f"テストリファクタリング数/一般リファクタリング数の比率: {relationship_results['test_to_general_ratio']:.2f}")
    print(f"テストリファクタリングを含むコミットで一般リファクタリングが発生する確率: {relationship_results['general_given_test']:.1%}")
    print(f"一般リファクタリングを含むコミットでテストリファクタリングが発生する確率: {relationship_results['test_given_general']:.1%}")
    
    # リファクタリングタイプの分析
    type_results = analyze_refactoring_types(test_types, general_types)
    print("\nリファクタリングタイプの分析結果:")
    print(f"テストリファクタリングタイプ数: {type_results['test_type_count']}")
    print(f"一般リファクタリングタイプ数: {type_results['general_type_count']}")
    
    print("\n上位5つのテストリファクタリングタイプ:")
    for _, row in type_results['top_test_types'].iterrows():
        print(f"{row['refactoring_type']}: {row['count']}")
    
    print("\n上位5つの一般リファクタリングタイプ:")
    for _, row in type_results['top_general_types'].iterrows():
        print(f"{row['refactoring_type']}: {row['count']}")
    
    # 可視化
    visualize_comparison(test_df, general_df)
    visualize_refactoring_types(test_types, general_types)
    visualize_coexistence(coexistence_results)

if __name__ == "__main__":
    main()
