import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
from scipy.stats import wilcoxon

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
    Extract relevant columns and reshape the data for Wilcoxon signed-rank test.
    期待するカラムは、"_diff"（差分値）に対応する、
    リファクタリング前は"_before"、後は"_after"の各カラムが存在する前提です。
    """
    test_smell_columns = [col for col in df.columns if "_diff" in col]
    if not test_smell_columns:
        raise ValueError("No '_diff' columns found in the dataset.")

    # 対応するbeforeとafterのカラム名を生成
    before_cols = [col.replace("_diff", "_before") for col in test_smell_columns]
    after_cols = [col.replace("_diff", "_after") for col in test_smell_columns]

    missing_cols = [col for col in before_cols + after_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing columns in the dataset: {missing_cols}")

    # データをlong形式に変換
    melted_df = df.melt(id_vars=["commit_url", "type_name"],
                        value_vars=test_smell_columns,
                        var_name="test_smell",
                        value_name="diff_value")

    # before_value, after_value の抽出（NaNは0で埋める）
    melted_df["before_value"] = df.melt(id_vars=["commit_url", "type_name"],
                                        value_vars=before_cols,
                                        var_name="test_smell",
                                        value_name="before_value")["before_value"].fillna(0)
    melted_df["after_value"] = df.melt(id_vars=["commit_url", "type_name"],
                                       value_vars=after_cols,
                                       var_name="test_smell",
                                       value_name="after_value")["after_value"].fillna(0)
    # test_smell名から"_diff"を除去
    melted_df["test_smell"] = melted_df["test_smell"].str.replace("_diff", "")
    print("Data transformation completed.")
    return melted_df


def wilcoxon_signed_rank_test(df, level):
    """
    各テストスメルについて Wilcoxon signed-rank test を実施し、
    統計量、p値、効果量（r値）を求める。
    ※ 同一テストスメル内で before と after が全く同じ場合はスキップします。
    """
    results = []
    skipped_smells = []  # スキップしたテストスメル名を記録

    for test_smell in df["test_smell"].unique():
        subset = df[df["test_smell"] == test_smell]
        before = subset["before_value"].fillna(0)
        after = subset["after_value"].fillna(0)
        min_len = min(len(before), len(after))
        before = before.iloc[:min_len]
        after = after.iloc[:min_len]

        if (before == after).all():
            skipped_smells.append(test_smell)
            continue

        try:
            stat, p_value = wilcoxon(before, after)
            r_value = stat / np.sqrt(len(before))  # 効果量 r の計算
            results.append({
                "test_smell": test_smell,
                "Wilcoxon_stat": stat,
                "p_value": p_value,
                "effect_size_r": r_value
            })
        except ValueError as e:
            skipped_smells.append(test_smell)

    results_df = pd.DataFrame(results)
    results_df.to_csv(f"{RESULTS_DIR}/wilcoxon_test_results_{level}.csv", index=False)
    return results_df


def plot_results(df, level):
    """Plot bar charts for p-values and effect sizes for overall test smells."""
    plt.figure(figsize=(12, 6))
    sns.barplot(data=df, x="test_smell", y="p_value", palette="coolwarm")
    plt.axhline(0.05, color="red", linestyle="--", label="Significance threshold (0.05)")
    plt.xticks(rotation=90)
    plt.xlabel("Test Smell")
    plt.ylabel("p-value")
    plt.title(f"Wilcoxon p-values for {level} Level")
    plt.legend()
    plt.savefig(f"{RESULTS_DIR}/wilcoxon_p_values_{level}.png", bbox_inches="tight")
    # plt.show()

    plt.figure(figsize=(12, 6))
    sns.barplot(data=df, x="test_smell", y="effect_size_r", palette="viridis")
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
                effect_size = stat / np.sqrt(len(before))
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
    annot_p = pivot_p.applymap(lambda x: f"{x:.3f}*" if x <= 0.05 else f"{x:.3f}")

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
    annot_effect = pivot_effect.applymap(lambda x: f"{x:.3f}")

    plt.figure(figsize=(14, 8))
    cmap_effect = sns.diverging_palette(240, 10, as_cmap=True)
    sns.heatmap(pivot_effect, cmap=cmap_effect, annot=annot_effect, fmt="", center=0,
                vmin=pivot_effect.min().min(), vmax=pivot_effect.max().max())
    plt.title(f"Wilcoxon Effect Sizes by Test Refactoring Type - {level} Level")
    plt.savefig(f"{RESULTS_DIR}/wilcoxon_by_type_effect_sizes_{level}.png", bbox_inches="tight")
    # plt.show()

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

    # Wilcoxon test grouped by test refactoring type (type_name)
    file_by_type = wilcoxon_by_type(file_melted_df, "file")
    method_by_type = wilcoxon_by_type(method_melted_df, "method")
    file_by_type.to_csv(f"{RESULTS_DIR}/wilcoxon_by_type_file.csv", index=False)
    method_by_type.to_csv(f"{RESULTS_DIR}/wilcoxon_by_type_method.csv", index=False)
    plot_results_by_type(file_by_type, "file")
    plot_results_by_type(method_by_type, "method")


if __name__ == "__main__":
    main()