import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy.stats import wilcoxon, norm
from statsmodels.stats.multitest import multipletests

# Directory settings
BASE_DIR = "/Users/horikawa/Dev/Research-repo/InvestigatingTheImpactOfTestSpecificRefactoring"
CSV_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/src/smells_result"
RESULTS_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/src/analysis/rq3/statistical_analysis"

# Create output directory if it does not exist
os.makedirs(RESULTS_DIR, exist_ok=True)


def load_data():
    """Load the dataset from a CSV file."""
    file_level_path = f"{CSV_DIR}/file_level_wide.csv"
    method_level_path = f"{CSV_DIR}/method_level_wide.csv"
    file_df = pd.read_csv(file_level_path)
    method_df = pd.read_csv(method_level_path)
    return file_df, method_df


def preprocess_data(df):
    """
    Reshape data to ensure before/after values are paired for each commit, type, and test smell.
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


def wilcoxon_signed_rank_test(df, level):
    """
    Perform Wilcoxon signed-rank test for each test smell, with effect size and multiple testing correction.
    """
    results = []
    p_values = []
    test_smell_list = []
    for test_smell in df["test_smell"].unique():
        subset = df[df["test_smell"] == test_smell]
        before = subset["before_value"]
        after = subset["after_value"]
        n = len(subset)
        
        if (before == after).all():
            continue
        try:
            stat, p_value = wilcoxon(before, after)
            # Z値の推定
            z = norm.ppf(1 - p_value / 2) * (-1 if stat < 0 else 1)
            r = z / np.sqrt(len(before))
            results.append({
                "test_smell": test_smell,
                "sample_size": n,
                "Wilcoxon_stat": stat,
                "p_value": p_value,
                "effect_size_r": r,
                "sample_size_adequate": n >= 20
            })
            p_values.append(p_value)
            test_smell_list.append(test_smell)
        except ValueError:
            continue
    # 多重検定補正
    if p_values:
        _, pvals_corrected, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')
        for i, res in enumerate(results):
            res["p_value_corrected"] = pvals_corrected[i]
    results_df = pd.DataFrame(results)
    results_df.to_csv(f"{RESULTS_DIR}/wilcoxon_test_results_{level}.csv", index=False)
    return results_df


def plot_results(df, level):
    """Plot bar charts for p-values and effect sizes for overall test smells."""
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df, x="test_smell", y="p_value", hue="test_smell", palette="coolwarm", legend=False)
    plt.axhline(0.05, color="red", linestyle="--", label="Significance threshold (0.05)")
    plt.xticks(rotation=90)
    plt.xlabel("Test Smell")
    plt.ylabel("p-value")
    plt.title(f"Wilcoxon p-values for {level} Level")
    plt.legend()
    plt.savefig(f"{RESULTS_DIR}/wilcoxon_p_values_{level}.png", bbox_inches="tight")
    # plt.show()

    plt.figure(figsize=(12, 6))
    sns.barplot(data=df, x="test_smell", y="effect_size_r", hue="test_smell", palette="viridis", legend=False)
    plt.xticks(rotation=90)
    plt.xlabel("Test Smell")
    plt.ylabel("Effect Size (r)")
    plt.title(f"Wilcoxon Effect Sizes for {level} Level")
    plt.savefig(f"{RESULTS_DIR}/wilcoxon_effect_sizes_{level}.png", bbox_inches="tight")
    # plt.show()


def plot_boxplot(df, level):
    """Plot boxplot of before and after values for each test smell."""
    plt.figure(figsize=(14, 8))
    melted_data = df.melt(id_vars=["test_smell"], value_vars=["before_value", "after_value"],
                          var_name="Condition", value_name="Value")
    sns.boxplot(data=melted_data, x="test_smell", y="Value", hue="Condition", palette="Set2")
    plt.xticks(rotation=90)
    plt.xlabel("Test Smell")
    plt.ylabel("Value")
    plt.title(f"Boxplot of Test Smells Before and After Refactoring ({level} Level)")
    plt.savefig(f"{RESULTS_DIR}/boxplot_{level}.png", bbox_inches="tight")
    # plt.show()


def wilcoxon_by_type(df, level):
    """
    各テストリファクタリング（type_name）ごとに、各テストスメルの before/after 値に対して
    Wilcoxon signed-rank test を実施し、統計量、p値、効果量（r）を算出する。
    結果はCSVとして保存します。
    """
    results = []
    for type_name, group in df.groupby("type_name"):
        for test_smell in group["test_smell"].unique():
            subset = group[group["test_smell"] == test_smell]
            before = subset["before_value"].fillna(0)
            after = subset["after_value"].fillna(0)
            # 必要ならば、両者の長さを合わせる
            min_len = min(len(before), len(after))
            before = before.iloc[:min_len]
            after = after.iloc[:min_len]
            if (before == after).all():
                continue
            try:
                stat, p_value = wilcoxon(before, after)
                # Calculate Z from p-value (two-sided)
                z = norm.ppf(1 - p_value / 2) * (-1 if stat < 0 else 1)
                effect_size = z / np.sqrt(len(before))
                results.append({
                    "type_name": type_name,
                    "test_smell": test_smell,
                    "Wilcoxon_stat": stat,
                    "p_value": p_value,
                    "effect_size_r": effect_size
                })
            except Exception as e:
                print(f"Error processing test smell {test_smell} for type {type_name}: {e}")
    results_df = pd.DataFrame(results)
    results_df.to_csv(f"{RESULTS_DIR}/wilcoxon_by_type_{level}.csv", index=False)
    return results_df


def plot_results_by_type(results_df, level):
    """
    各テストリファクタリング（type_name）ごとのp値と効果量をヒートマップで可視化します。
    p値については、0.05以下のセルにアスタリスクを付け、太字・赤文字で強調します。
    """
    # ----- p値のヒートマップ -----
    # Pivot table for p-values: type_name x test_smell
    pivot_p = results_df.pivot(index="type_name", columns="test_smell", values="p_value").fillna(1.0)
    # アノテーション用：p値が0.05以下の場合にアスタリスクを付与
    annot_p = pivot_p.map(lambda x: f"{x:.3f}*" if x <= 0.05 else f"{x:.3f}")

    plt.figure(figsize=(14, 8))
    cmap_p = sns.diverging_palette(220, 170, as_cmap=True)
    ax = sns.heatmap(pivot_p, cmap=cmap_p, annot=annot_p, fmt="", center=0.05, vmin=0, vmax=1)

    # セルのテキストを走査し、p値が0.05以下の場合に太字・赤文字に変更
    for t in ax.texts:
        try:
            value = float(t.get_text().replace("*", ""))
            if value <= 0.05:
                t.set_weight("bold")
                t.set_color("red")
        except Exception:
            pass

    plt.title(f"Wilcoxon p-values by Test Refactoring Type - {level} Level")
    plt.savefig(f"{RESULTS_DIR}/wilcoxon_by_type_p_values_{level}.png", bbox_inches="tight")
    # plt.show()

    # ----- 効果量のヒートマップ -----
    # Pivot table for effect sizes: type_name x test_smell
    pivot_effect = results_df.pivot(index="type_name", columns="test_smell", values="effect_size_r").fillna(0.0)
    # アノテーションは単純に数値を表示（必要に応じて条件付きの強調も可能）
    annot_effect = pivot_effect.map(lambda x: f"{x:.3f}")

    plt.figure(figsize=(14, 8))
    cmap_effect = sns.diverging_palette(240, 10, as_cmap=True)
    sns.heatmap(pivot_effect, cmap=cmap_effect, annot=annot_effect, fmt="", center=0,
                vmin=pivot_effect.min().min(), vmax=pivot_effect.max().max())
    plt.title(f"Wilcoxon Effect Sizes by Test Refactoring Type - {level} Level")
    plt.savefig(f"{RESULTS_DIR}/wilcoxon_by_type_effect_sizes_{level}.png", bbox_inches="tight")
    # plt.show()


def plot_corrected_pvalues(df, level):
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df, x="test_smell", y="p_value_corrected", hue="test_smell", palette="coolwarm", legend=False)
    plt.axhline(0.05, color="red", linestyle="--", label="Significance threshold (0.05)")
    plt.xticks(rotation=90)
    plt.xlabel("Test Smell")
    plt.ylabel("Corrected p-value (FDR)")
    plt.title(f"Corrected p-values (FDR) for {level} Level")
    plt.legend()
    plt.savefig(f"{RESULTS_DIR}/corrected_p_values_{level}.png", bbox_inches="tight")


def categorize_effect_size(r):
    if abs(r) < 0.1:
        return "negligible"
    elif abs(r) < 0.3:
        return "small"
    elif abs(r) < 0.5:
        return "medium"
    else:
        return "large"


def plot_violin(df, level):
    plt.figure(figsize=(16, 8))
    melted = df.melt(id_vars=["test_smell"], value_vars=["before_value", "after_value"],
                     var_name="Condition", value_name="Value")
    sns.violinplot(data=melted, x="test_smell", y="Value", hue="Condition", split=True)
    plt.xticks(rotation=90)
    plt.title(f"Before/After Distribution for Each Test Smell ({level} Level)")
    plt.savefig(f"{RESULTS_DIR}/violin_{level}.png", bbox_inches="tight")


def plot_heatmap_with_significance(results_df, level):
    # p_value_corrected列が存在しない場合はp_value列を使用
    value_column = "p_value_corrected" if "p_value_corrected" in results_df.columns else "p_value"
    pivot = results_df.pivot(index="type_name", columns="test_smell", values=value_column).fillna(1.0)
    annot = pivot.map(lambda x: "*" if x <= 0.05 else "")
    plt.figure(figsize=(14, 8))
    sns.heatmap(pivot, annot=annot, fmt="", cmap="coolwarm", center=0.05, vmin=0, vmax=1)
    plt.title(f"{value_column.replace('_', ' ').title()} by Type ({level} Level)")
    plt.savefig(f"{RESULTS_DIR}/heatmap_corrected_p_{level}.png", bbox_inches="tight")


def analyze_sample_sizes(df, level):
    """
    各テストスメルのサンプルサイズを分析し、統計的検出力の観点から評価する
    """
    print(f"\n=== Sample Size Analysis for {level} Level ===")
    
    sample_sizes = []
    for test_smell in df["test_smell"].unique():
        subset = df[df["test_smell"] == test_smell]
        n = len(subset)
        sample_sizes.append({
            "test_smell": test_smell,
            "sample_size": n,
            "status": "adequate" if n >= 20 else "small" if n >= 10 else "very_small"
        })
        print(f"{test_smell}: n = {n} ({'adequate' if n >= 20 else 'small' if n >= 10 else 'very small'})")
    
    # 統計的検出力の評価
    adequate_count = sum(1 for s in sample_sizes if s["status"] == "adequate")
    small_count = sum(1 for s in sample_sizes if s["status"] == "small")
    very_small_count = sum(1 for s in sample_sizes if s["status"] == "very_small")
    
    print(f"\nSummary:")
    print(f"Adequate sample size (≥20): {adequate_count}/{len(sample_sizes)}")
    print(f"Small sample size (10-19): {small_count}/{len(sample_sizes)}")
    print(f"Very small sample size (<10): {very_small_count}/{len(sample_sizes)}")
    
    return sample_sizes


def main():
    """Main function to execute the analysis."""
    # Load the dataset
    file_df, method_df = load_data()

    # Preprocess the data
    file_melted_df = preprocess_data(file_df)
    method_melted_df = preprocess_data(method_df)

    # Overall Wilcoxon signed-rank test (aggregated by test smell)
    file_results = wilcoxon_signed_rank_test(file_melted_df, "file")
    method_results = wilcoxon_signed_rank_test(method_melted_df, "method")
    plot_results(file_results, "file")
    plot_results(method_results, "method")
    plot_boxplot(file_melted_df, "file")
    plot_boxplot(method_melted_df, "method")
    plot_violin(file_melted_df, "file")
    plot_violin(method_melted_df, "method")

    # Wilcoxon test grouped by test refactoring type (type_name)
    file_by_type = wilcoxon_by_type(file_melted_df, "file")
    method_by_type = wilcoxon_by_type(method_melted_df, "method")
    file_by_type.to_csv(f"{RESULTS_DIR}/wilcoxon_by_type_file.csv", index=False)
    method_by_type.to_csv(f"{RESULTS_DIR}/wilcoxon_by_type_method.csv", index=False)
    plot_results_by_type(file_by_type, "file")
    plot_results_by_type(method_by_type, "method")

    # p_values: list of p-values
    p_values = file_results["p_value"].tolist() + method_results["p_value"].tolist()
    rejected, pvals_corrected, _, _ = multipletests(p_values, alpha=0.05, method='fdr_bh')
    # pvals_correctedが補正後のp値

    plot_corrected_pvalues(file_results, "file")
    plot_corrected_pvalues(method_results, "method")

    # Add effect size category
    file_results["effect_size_category"] = file_results["effect_size_r"].apply(categorize_effect_size)
    method_results["effect_size_category"] = method_results["effect_size_r"].apply(categorize_effect_size)

    # plot_heatmap_with_significanceにはtype_name列を含むデータフレームを渡す
    plot_heatmap_with_significance(file_by_type, "file")
    plot_heatmap_with_significance(method_by_type, "method")

    # Analyze sample sizes
    analyze_sample_sizes(file_melted_df, "file")
    analyze_sample_sizes(method_melted_df, "method")


if __name__ == "__main__":
    main()