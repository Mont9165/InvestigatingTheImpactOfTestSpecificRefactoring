import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy.stats import wilcoxon, norm
from statsmodels.stats.multitest import multipletests

# --- ディレクトリ設定 ---
BASE_DIR = "/Users/horikawa/Dev/Research-repo/InvestigatingTheImpactOfTestSpecificRefactoring"
CSV_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/src/smells_result"
# 結果の保存先を明確に区別
RESULTS_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/src/analysis/rq3/refactoring_smell_relationship_corrected"

# 出力ディレクトリが存在しない場合は作成
os.makedirs(RESULTS_DIR, exist_ok=True)


def load_data():
    """データセットをCSVファイルからロードする"""
    file_level_path = f"{CSV_DIR}/file_level_wide.csv"
    method_level_path = f"{CSV_DIR}/method_level_wide.csv"
    file_df = pd.read_csv(file_level_path)
    method_df = pd.read_csv(method_level_path)
    return file_df, method_df


def preprocess_data(df):
    """
    データを整形し、コミット、タイプリファクタリング、テストスメルごとに
    before/afterのペアが対応するようにする
    """
    test_smell_columns = [col for col in df.columns if "_diff" in col]
    before_cols = [col.replace("_diff", "_before") for col in test_smell_columns]
    after_cols = [col.replace("_diff", "_after") for col in test_smell_columns]
    data = []
    for idx, row in df.iterrows():
        for smell, before_col, after_col in zip(test_smell_columns, before_cols, after_cols):
            data.append({
                "commit_url": row["commit_url"],
                "type_name": row["type_name"],
                "test_smell": smell.replace("_diff", ""),
                "before_value": row[before_col] if pd.notnull(row[before_col]) else 0,
                "after_value": row[after_col] if pd.notnull(row[after_col]) else 0,
                "diff_value": row[smell] if pd.notnull(row[smell]) else 0
            })
    return pd.DataFrame(data)


def calculate_effect_size_r(p_value, n, before, after):
    """
    p値から効果量rを計算する（ハイブリッド版）。
    まず中央値で方向を判断し、0なら平均値をタイブレークに使う。
    """
    if n == 0 or p_value is None or p_value >= 1:
        return 0.0

    diff = after.values - before.values
    diff_median = np.median(diff)

    sign = 0
    # まず中央値で判断
    if diff_median != 0:
        sign = np.sign(diff_median)
    # 中央値が0の場合、タイブレークとして平均値で判断
    else:
        diff_mean = np.mean(diff)
        if diff_mean != 0:
            sign = np.sign(diff_mean)
        else:
            # 平均値も0なら、方向性はない
            return 0.0

    z_score = abs(norm.ppf(p_value / 2.0))
    r = sign * (z_score / np.sqrt(n))
    return r


def run_statistical_analysis(df, group_by_cols, level):
    """
    指定された列でグループ化し、統計分析を実行する共通関数
    """
    print(f"\n=== Running analysis for: {group_by_cols} at {level} level ===")
    results = []
    for group_keys, group_data in df.groupby(group_by_cols):
        total_pairs = len(group_data)
        if total_pairs < 5:
            continue

        improvements = (group_data["after_value"] < group_data["before_value"]).sum()
        degradations = (group_data["after_value"] > group_data["before_value"]).sum()
        no_changes = total_pairs - improvements - degradations

        p_value, effect_size_r, stat = 1.0, 0.0, np.nan

        if no_changes < total_pairs:
            try:
                stat, p_value = wilcoxon(group_data["before_value"], group_data["after_value"])
                effect_size_r = calculate_effect_size_r(p_value, total_pairs, group_data["before_value"],
                                                        group_data["after_value"])
            except ValueError:
                p_value = 1.0

        # 結果を辞書として作成
        res = {
            "level": level,
            "total_pairs": total_pairs,
            "improvements": improvements,
            "degradations": degradations,
            "no_changes": no_changes,
            "improvement_rate": improvements / total_pairs * 100,
            "degradation_rate": degradations / total_pairs * 100,
            "wilcoxon_stat": stat,
            "p_value": p_value,
            "effect_size_r": effect_size_r
        }

        # グループ化のキーを結果に追加
        if isinstance(group_keys, str):
            res[group_by_cols[0]] = group_keys
        else:
            for i, key in enumerate(group_by_cols):
                res[key] = group_keys[i]

        results.append(res)

    return pd.DataFrame(results)


def analyze_by_smell_only(df, level, adequate_sample_size=20):
    """
    【新規追加】テストスメル単体で集計し、統計分析を行う関数
    リファクタリングの種類は問わず、全体でのスメルの変化を評価する
    """
    print(f"\n=== Analysis by Test Smell Only for {level} Level ===")
    results = []
    for test_smell, group_data in df.groupby('test_smell'):
        sample_size = len(group_data)
        if sample_size < 5:
            continue

        no_change_pairs = (group_data["after_value"] == group_data["before_value"]).sum()
        change_pairs = sample_size - no_change_pairs

        p_value, effect_size_r, stat = 1.0, 0.0, np.nan

        if change_pairs > 0:
            try:
                stat, p_value = wilcoxon(group_data["before_value"], group_data["after_value"])
                effect_size_r = calculate_effect_size_r(p_value, sample_size, group_data["before_value"],
                                                        group_data["after_value"])
            except ValueError:
                p_value = 1.0

        results.append({
            "test_smell": test_smell,
            "sample_size": sample_size,
            "no_change_pairs": no_change_pairs,
            "change_pairs": change_pairs,
            "Wilcoxon_stat": stat,
            "p_value": p_value,
            "effect_size_r": effect_size_r,
            "sample_size_adequate": sample_size >= adequate_sample_size
        })

    # このレベル（file/method）内で多重比較補正
    results_df = pd.DataFrame(results)
    if not results_df.empty:
        p_values_to_correct = results_df['p_value'].dropna()
        if not p_values_to_correct.empty:
            reject, pvals_corrected, _, _ = multipletests(p_values_to_correct, alpha=0.05, method='fdr_bh')
            results_df['p_value_corrected'] = pvals_corrected
        else:
            results_df['p_value_corrected'] = 1.0

    return results_df

def analyze_refactoring_smell_effectiveness(df, level):
    """
    【修正版】リファクタリングタイプが各テストスメルに与える影響を、統計的に正しく分析する。
    選択バイアスを排除し、適切な効果量を計算する。
    """
    print(f"\n=== Corrected Refactoring-Smell Effectiveness Analysis for {level} Level ===")

    results = []

    for (refactoring_type, test_smell), group_data in df.groupby(['type_name', 'test_smell']):
        total_pairs = len(group_data)
        if total_pairs < 5:  # サンプルサイズが小さすぎる場合はスキップ
            continue

        # 記述統計の計算
        improvements = (group_data["after_value"] < group_data["before_value"]).sum()
        degradations = (group_data["after_value"] > group_data["before_value"]).sum()
        no_changes = total_pairs - improvements - degradations

        improvement_rate = improvements / total_pairs * 100
        degradation_rate = degradations / total_pairs * 100
        change_rate = (improvements + degradations) / total_pairs * 100

        p_value = 1.0
        effect_size_r = 0.0
        stat = np.nan

        # 【重要】検定はすべてのペアを対象に行い、選択バイアスを排除
        if no_changes < total_pairs:
            try:
                stat, p_value = wilcoxon(group_data["before_value"], group_data["after_value"])
                effect_size_r = calculate_effect_size_r(
                    p_value, total_pairs, group_data["before_value"], group_data["after_value"]
                )
            except ValueError:
                p_value = 1.0
                effect_size_r = 0.0

        results.append({
            "level": level,
            "refactoring_type": refactoring_type,
            "test_smell": test_smell,
            "total_pairs": total_pairs,
            "improvements": improvements,
            "degradations": degradations,
            "no_changes": no_changes,
            "improvement_rate": improvement_rate,
            "degradation_rate": degradation_rate,
            "change_rate": change_rate,
            "wilcoxon_stat": stat,
            "p_value": p_value,
            "effect_size_r": effect_size_r
        })

    return pd.DataFrame(results)


def create_effectiveness_heatmap(results_df, level):
    """【修正版】各リファクタリングタイプの効果をヒートマップで可視化する"""
    # 1. 改善率のヒートマップ
    pivot_improvement = results_df.pivot(index="refactoring_type", columns="test_smell", values="improvement_rate")
    plt.figure(figsize=(18, 12))
    sns.heatmap(pivot_improvement, annot=True, fmt=".1f", cmap="Greens", center=0, vmin=0, vmax=50)
    plt.title(f"Improvement Rate (%) by Refactoring Type and Test Smell ({level} Level)", fontsize=16)
    plt.xlabel("Test Smell", fontsize=12)
    plt.ylabel("Refactoring Type", fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    plt.tight_layout()
    plt.savefig(f"{RESULTS_DIR}/improvement_heatmap_{level}.png", dpi=300)
    plt.close()

    # 2. 効果量rのヒートマップ（統計的に有意なもののみ）
    # 'significant_corrected'列が存在するか確認
    if 'significant_corrected' in results_df.columns:
        significant_results = results_df[results_df["significant_corrected"] == True]
        if not significant_results.empty:
            pivot_effect = significant_results.pivot(index="refactoring_type", columns="test_smell", values="effect_size_r")
            plt.figure(figsize=(18, 12))
            sns.heatmap(pivot_effect, annot=True, fmt=".3f", cmap="RdBu_r", center=0) # 改善(負)が青、悪化(正)が赤
            plt.title(f"Effect Size (r) for Statistically Significant Pairs ({level} Level, Corrected p-value)", fontsize=16)
            plt.xlabel("Test Smell", fontsize=12)
            plt.ylabel("Refactoring Type", fontsize=12)
            plt.xticks(rotation=45, ha='right')
            plt.yticks(rotation=0)
            plt.tight_layout()
            plt.savefig(f"{RESULTS_DIR}/effect_size_heatmap_significant_{level}.png", dpi=300)
            plt.close()


def find_best_refactoring_for_each_smell(results_df, level):
    """【修正版】各テストスメルに対して最も効果的なリファクタリングを見つける"""
    print(f"\n=== Best Refactoring Types for Each Test Smell ({level} Level) ===")

    best_refactorings = []
    if 'significant_corrected' not in results_df.columns:
        print("Warning: `significant_corrected` column not found. Cannot determine best by effect size.")
        return pd.DataFrame()

    for test_smell in results_df["test_smell"].unique():
        smell_results = results_df[results_df["test_smell"] == test_smell]

        # サンプルサイズが十分な結果にフィルタリング
        valid_results = smell_results[smell_results["total_pairs"] >= 5]
        if valid_results.empty:
            continue

        # 改善率で最良のものを探す
        best_improvement = valid_results.loc[valid_results["improvement_rate"].idxmax()]

        # 効果量で最良のものを探す（有意な改善の中から）
        significant_improvements = valid_results[(valid_results["significant_corrected"] == True) & (valid_results["effect_size_r"] < 0)]
        if not significant_improvements.empty:
            best_effect = significant_improvements.loc[significant_improvements["effect_size_r"].idxmin()]
        else:
            best_effect = None

        best_refactorings.append({
            "test_smell": test_smell,
            "best_by_improvement_rate": best_improvement["refactoring_type"],
            "improvement_rate": best_improvement["improvement_rate"],
            "total_pairs": best_improvement["total_pairs"],
            "best_by_effect_size": best_effect["refactoring_type"] if best_effect is not None else "None",
            "effect_size_r": best_effect["effect_size_r"] if best_effect is not None else 0,
            "p_value_corrected": best_effect["p_value_corrected"] if best_effect is not None else None
        })

    return pd.DataFrame(best_refactorings)


def analyze_refactoring_impact_summary(results_df, level):
    """【修正版】各リファクタリングタイプの全体的な影響を要約する"""
    print(f"\n=== Refactoring Impact Summary ({level} Level) ===")

    summary_list = []
    if 'significant_corrected' not in results_df.columns:
        print("Warning: `significant_corrected` column not found. Summary will be incomplete.")
        results_df['significant_corrected'] = False # 計算を続けるために列を追加

    for refactoring_type in results_df["refactoring_type"].unique():
        type_results = results_df[results_df["refactoring_type"] == refactoring_type]

        total_pairs = type_results["total_pairs"].sum()
        total_improvements = type_results["improvements"].sum()
        total_degradations = type_results["degradations"].sum()

        # 加重平均を計算
        weighted_improvement_rate = np.average(type_results["improvement_rate"], weights=type_results["total_pairs"])
        weighted_effect_size_r = np.average(type_results["effect_size_r"], weights=type_results["total_pairs"])

        # 有意な改善の数をカウント
        significant_improvements_count = len(type_results[
                                                 (type_results["significant_corrected"] == True) & (type_results["effect_size_r"] < 0)
                                                 ])

        summary_list.append({
            "refactoring_type": refactoring_type,
            "total_pairs": total_pairs,
            "total_improvements": total_improvements,
            "total_degradations": total_degradations,
            "overall_improvement_rate": weighted_improvement_rate,
            "overall_effect_size_r": weighted_effect_size_r,
            "significant_improvements_count": significant_improvements_count,
            "smells_affected": len(type_results[type_results["change_rate"] > 0])
        })

    return pd.DataFrame(summary_list)


def create_summary_visualizations(summary_df, level):
    """リファクタリング効果のサマリーを可視化する"""
    if summary_df.empty:
        return

    # 1. 全体的な改善率
    plt.figure(figsize=(12, 8))
    summary_df_sorted = summary_df.sort_values("overall_improvement_rate", ascending=True)
    plt.barh(summary_df_sorted["refactoring_type"], summary_df_sorted["overall_improvement_rate"])
    plt.xlabel("Overall Improvement Rate (%)")
    plt.title(f"Overall Improvement Rate by Refactoring Type ({level} Level)")
    plt.tight_layout()
    plt.savefig(f"{RESULTS_DIR}/summary_improvement_rate_{level}.png", dpi=300)
    plt.close()

    # 2. 影響を与えたスメルの数
    plt.figure(figsize=(12, 8))
    summary_df_sorted = summary_df.sort_values("smells_affected", ascending=True)
    plt.barh(summary_df_sorted["refactoring_type"], summary_df_sorted["smells_affected"])
    plt.xlabel("Number of Test Smells Affected")
    plt.title(f"Number of Test Smells Affected by Each Refactoring Type ({level} Level)")
    plt.tight_layout()
    plt.savefig(f"{RESULTS_DIR}/summary_smells_affected_{level}.png", dpi=300)
    plt.close()


def main():
    """メインの実行関数（最終改善版）"""
    # データのロードと前処理
    file_df_raw, method_df_raw = load_data()
    file_df = preprocess_data(file_df_raw)
    method_df = preprocess_data(method_df_raw)

    # --- 1. 全ての分析を実行（この時点ではp値は未補正） ---
    # a) リファクタリング種別×スメル種別での詳細分析
    detailed_file_results = run_statistical_analysis(file_df, ['type_name', 'test_smell'], "file")
    detailed_method_results = run_statistical_analysis(method_df, ['type_name', 'test_smell'], "method")

    # b) テストスメル単体での集計分析
    smell_only_file_results = run_statistical_analysis(file_df, ['test_smell'], "file")
    smell_only_method_results = run_statistical_analysis(method_df, ['test_smell'], "method")

    # --- 2. 【改善点】グローバル多重比較補正 ---
    # 全ての分析結果を一度結合し、どの分析からのp値か分かるようにラベルを付ける
    detailed_file_results['analysis_type'] = 'detailed_by_type_and_smell'
    detailed_method_results['analysis_type'] = 'detailed_by_type_and_smell'
    smell_only_file_results['analysis_type'] = 'summary_by_smell_only'
    smell_only_method_results['analysis_type'] = 'summary_by_smell_only'

    all_results = pd.concat([
        detailed_file_results,
        detailed_method_results,
        smell_only_file_results,
        smell_only_method_results
    ], ignore_index=True)

    # p値補正を一括で実行
    if not all_results.empty:
        p_values_to_correct = all_results['p_value'].dropna()
        if not p_values_to_correct.empty:
            reject, pvals_corrected, _, _ = multipletests(p_values_to_correct, alpha=0.05, method='fdr_bh')

            # 元のDataFrameのインデックスを使って結果を正しくマッピング
            all_results.loc[p_values_to_correct.index, 'p_value_corrected'] = pvals_corrected
            all_results.loc[p_values_to_correct.index, 'significant_corrected'] = reject
        else:
            all_results['p_value_corrected'] = 1.0
            all_results['significant_corrected'] = False

    print("\n=== Global multiple testing correction complete for all analyses. ===")

    # --- 3. 結果の保存 ---
    # 補正済みの全結果を1つのファイルに保存するのが最も透明性が高い
    all_results.to_csv(f"{RESULTS_DIR}/all_analyses_globally_corrected.csv", index=False)

    # 必要であれば、再度分割して個別のファイルとして保存することも可能
    all_results[all_results['analysis_type'] == 'detailed_by_type_and_smell'].to_csv(
        f"{RESULTS_DIR}/detailed_analysis_final.csv", index=False)
    all_results[all_results['analysis_type'] == 'summary_by_smell_only'].to_csv(
        f"{RESULTS_DIR}/smell_summary_final.csv", index=False)

    print(f"\n=== Analysis Complete ===")
    print(f"All final results saved to: {RESULTS_DIR}")


if __name__ == "__main__":
    main()