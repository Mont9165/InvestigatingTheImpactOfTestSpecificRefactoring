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
RESULTS_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/src/analysis/rq3/descriptive_analysis"

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


def analyze_change_patterns(df, level):
    """
    Analyze patterns of change (improvement, degradation, no change) for each test smell.
    """
    print(f"\n=== Change Pattern Analysis for {level} Level ===")
    
    results = []
    
    for test_smell in df["test_smell"].unique():
        subset = df[df["test_smell"] == test_smell]
        
        # Calculate change patterns
        improvements = (subset["after_value"] < subset["before_value"]).sum()
        degradations = (subset["after_value"] > subset["before_value"]).sum()
        no_changes = (subset["after_value"] == subset["before_value"]).sum()
        total = len(subset)
        
        # Calculate percentages
        improvement_rate = improvements / total * 100
        degradation_rate = degradations / total * 100
        no_change_rate = no_changes / total * 100
        
        # Calculate effect size (Cohen's d for paired samples)
        if improvements + degradations > 0:  # Only if there are changes
            changed_subset = subset[subset["after_value"] != subset["before_value"]]
            if len(changed_subset) > 1:
                diff = changed_subset["after_value"] - changed_subset["before_value"]
                effect_size = np.mean(diff) / np.std(diff) if np.std(diff) > 0 else 0
            else:
                effect_size = 0
        else:
            effect_size = 0
        
        results.append({
            "test_smell": test_smell,
            "total_pairs": total,
            "improvements": improvements,
            "degradations": degradations,
            "no_changes": no_changes,
            "improvement_rate": improvement_rate,
            "degradation_rate": degradation_rate,
            "no_change_rate": no_change_rate,
            "effect_size": effect_size,
            "has_changes": improvements + degradations > 0
        })
        
        print(f"{test_smell}:")
        print(f"  Total: {total}, Improvements: {improvements} ({improvement_rate:.1f}%), "
              f"Degradations: {degradations} ({degradation_rate:.1f}%), "
              f"No change: {no_changes} ({no_change_rate:.1f}%)")
    
    return pd.DataFrame(results)


def analyze_by_refactoring_type(df, level):
    """
    Analyze change patterns by refactoring type and save as CSV, including Wilcoxon p-value and significance.
    """
    print(f"\n=== Change Pattern Analysis by Refactoring Type for {level} Level ===")
    
    results = []
    detailed_rows = []
    
    for type_name in df["type_name"].unique():
        type_data = df[df["type_name"] == type_name]
        total_pairs = len(type_data)
        improvements = (type_data["after_value"] < type_data["before_value"]).sum()
        degradations = (type_data["after_value"] > type_data["before_value"]).sum()
        no_changes = (type_data["after_value"] == type_data["before_value"]).sum()
        improvement_rate = improvements / total_pairs * 100
        degradation_rate = degradations / total_pairs * 100
        no_change_rate = no_changes / total_pairs * 100
        smell_results = []
        for test_smell in type_data["test_smell"].unique():
            smell_data = type_data[type_data["test_smell"] == test_smell]
            smell_improvements = (smell_data["after_value"] < smell_data["before_value"]).sum()
            smell_degradations = (smell_data["after_value"] > smell_data["before_value"]).sum()
            smell_no_changes = (smell_data["after_value"] == smell_data["before_value"]).sum()
            smell_total = len(smell_data)
            # 効果量（Cohen's d）
            if smell_improvements + smell_degradations > 0:
                changed = smell_data[smell_data["after_value"] != smell_data["before_value"]]
                if len(changed) > 1:
                    diff = changed["after_value"] - changed["before_value"]
                    effect_size = np.mean(diff) / np.std(diff) if np.std(diff) > 0 else 0
                else:
                    effect_size = 0
            else:
                effect_size = 0
            # Wilcoxon検定
            if smell_improvements + smell_degradations > 0 and len(smell_data[smell_data["after_value"] != smell_data["before_value"]]) >= 5:
                changed = smell_data[smell_data["after_value"] != smell_data["before_value"]]
                try:
                    from scipy.stats import wilcoxon
                    stat, p_value = wilcoxon(changed["before_value"], changed["after_value"])
                    significant = p_value < 0.05
                except Exception:
                    p_value = None
                    significant = False
            else:
                p_value = None
                significant = False
            smell_results.append({
                "type_name": type_name,
                "test_smell": test_smell,
                "total": smell_total,
                "improvements": smell_improvements,
                "degradations": smell_degradations,
                "no_changes": smell_no_changes,
                "improvement_rate": smell_improvements / smell_total * 100 if smell_total > 0 else 0,
                "degradation_rate": smell_degradations / smell_total * 100 if smell_total > 0 else 0,
                "no_change_rate": smell_no_changes / smell_total * 100 if smell_total > 0 else 0,
                "effect_size": effect_size,
                "p_value": p_value,
                "significant": significant
            })
            # CSV用に詳細行を追加
            detailed_rows.append({
                "type_name": type_name,
                "test_smell": test_smell,
                "total": smell_total,
                "improvements": smell_improvements,
                "degradations": smell_degradations,
                "no_changes": smell_no_changes,
                "improvement_rate": smell_improvements / smell_total * 100 if smell_total > 0 else 0,
                "degradation_rate": smell_degradations / smell_total * 100 if smell_total > 0 else 0,
                "no_change_rate": smell_no_changes / smell_total * 100 if smell_total > 0 else 0,
                "effect_size": effect_size,
                "p_value": p_value,
                "significant": significant
            })
        results.append({
            "type_name": type_name,
            "total_pairs": total_pairs,
            "improvements": improvements,
            "degradations": degradations,
            "no_changes": no_changes,
            "improvement_rate": improvement_rate,
            "degradation_rate": degradation_rate,
            "no_change_rate": no_change_rate,
            "smell_details": smell_results
        })
        print(f"{type_name}:")
        print(f"  Total: {total_pairs}, Improvements: {improvements} ({improvement_rate:.1f}%), "
              f"Degradations: {degradations} ({degradation_rate:.1f}%), "
              f"No change: {no_changes} ({no_change_rate:.1f}%)")
    # 詳細をCSVで保存
    detailed_df = pd.DataFrame(detailed_rows)
    detailed_df.to_csv(f"{RESULTS_DIR}/refactoring_type_testsmell_summary_{level}.csv", index=False)
    return results


def plot_change_patterns(results_df, level):
    """
    Create simple horizontal bar visualizations for change patterns (exclude NumberOfMethods, no bold, no value labels).
    """
    # NumberOfMethodsを除外
    results_df = results_df[results_df["test_smell"] != "NumberOfMethods"]

    # 改善率降順で並び替え
    results_df = results_df.sort_values('improvement_rate', ascending=False)
    y = np.arange(len(results_df))
    no_changes = results_df["no_change_rate"].values
    improvements = results_df["improvement_rate"].values
    degradations = results_df["degradation_rate"].values
    test_smells = results_df["test_smell"].values

    color_nochange = '#bdbdbd'
    color_improve = '#4daf4a'
    color_degrade = '#e41a1c'

    plt.figure(figsize=(12, 8))
    plt.barh(y, no_changes, color=color_nochange, label='No Change')
    plt.barh(y, improvements, left=no_changes, color=color_improve, label='Improvements')
    plt.barh(y, degradations, left=no_changes+improvements, color=color_degrade, label='Degradations')

    plt.yticks(y, test_smells,  fontsize=16)
    plt.xlabel('Percentage (%)', fontsize=16)
    plt.xticks(fontsize=16)
    # plt.ylabel('Test Smells')
    plt.legend(loc='upper right', fontsize=16)
    plt.tight_layout()
    plt.savefig(f"{RESULTS_DIR}/change_patterns_{level}_better.pdf", dpi=600)
    plt.close()


def perform_statistical_tests(df, level):
    """
    Perform statistical tests only where meaningful changes exist.
    """
    print(f"\n=== Statistical Analysis for {level} Level ===")
    
    results = []
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
    RESULTS_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/src/analysis/rq3/descriptive_analysis"

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

    def analyze_change_patterns(df, level):
        """
        Analyze patterns of change (improvement, degradation, no change) for each test smell.
        """
        print(f"\n=== Change Pattern Analysis for {level} Level ===")

        results = []

        for test_smell in df["test_smell"].unique():
            subset = df[df["test_smell"] == test_smell]

            # Calculate change patterns
            improvements = (subset["after_value"] < subset["before_value"]).sum()
            degradations = (subset["after_value"] > subset["before_value"]).sum()
            no_changes = (subset["after_value"] == subset["before_value"]).sum()
            total = len(subset)

            # Calculate percentages
            improvement_rate = improvements / total * 100
            degradation_rate = degradations / total * 100
            no_change_rate = no_changes / total * 100

            # Calculate effect size (Cohen's d for paired samples)
            if improvements + degradations > 0:  # Only if there are changes
                changed_subset = subset[subset["after_value"] != subset["before_value"]]
                if len(changed_subset) > 1:
                    diff = changed_subset["after_value"] - changed_subset["before_value"]
                    effect_size = np.mean(diff) / np.std(diff) if np.std(diff) > 0 else 0
                else:
                    effect_size = 0
            else:
                effect_size = 0

            results.append({
                "test_smell": test_smell,
                "total_pairs": total,
                "improvements": improvements,
                "degradations": degradations,
                "no_changes": no_changes,
                "improvement_rate": improvement_rate,
                "degradation_rate": degradation_rate,
                "no_change_rate": no_change_rate,
                "effect_size": effect_size,
                "has_changes": improvements + degradations > 0
            })

            print(f"{test_smell}:")
            print(f"  Total: {total}, Improvements: {improvements} ({improvement_rate:.1f}%), "
                  f"Degradations: {degradations} ({degradation_rate:.1f}%), "
                  f"No change: {no_changes} ({no_change_rate:.1f}%)")

        return pd.DataFrame(results)

    def analyze_by_refactoring_type(df, level):
        """
        Analyze change patterns by refactoring type and save as CSV, including Wilcoxon p-value and significance.
        """
        print(f"\n=== Change Pattern Analysis by Refactoring Type for {level} Level ===")

        results = []
        detailed_rows = []

        for type_name in df["type_name"].unique():
            type_data = df[df["type_name"] == type_name]
            total_pairs = len(type_data)
            improvements = (type_data["after_value"] < type_data["before_value"]).sum()
            degradations = (type_data["after_value"] > type_data["before_value"]).sum()
            no_changes = (type_data["after_value"] == type_data["before_value"]).sum()
            improvement_rate = improvements / total_pairs * 100
            degradation_rate = degradations / total_pairs * 100
            no_change_rate = no_changes / total_pairs * 100
            smell_results = []
            for test_smell in type_data["test_smell"].unique():
                smell_data = type_data[type_data["test_smell"] == test_smell]
                smell_improvements = (smell_data["after_value"] < smell_data["before_value"]).sum()
                smell_degradations = (smell_data["after_value"] > smell_data["before_value"]).sum()
                smell_no_changes = (smell_data["after_value"] == smell_data["before_value"]).sum()
                smell_total = len(smell_data)
                # 効果量（Cohen's d）
                if smell_improvements + smell_degradations > 0:
                    changed = smell_data[smell_data["after_value"] != smell_data["before_value"]]
                    if len(changed) > 1:
                        diff = changed["after_value"] - changed["before_value"]
                        effect_size = np.mean(diff) / np.std(diff) if np.std(diff) > 0 else 0
                    else:
                        effect_size = 0
                else:
                    effect_size = 0
                # Wilcoxon検定
                if smell_improvements + smell_degradations > 0 and len(
                        smell_data[smell_data["after_value"] != smell_data["before_value"]]) >= 5:
                    changed = smell_data[smell_data["after_value"] != smell_data["before_value"]]
                    try:
                        from scipy.stats import wilcoxon
                        stat, p_value = wilcoxon(changed["before_value"], changed["after_value"])
                        significant = p_value < 0.05
                    except Exception:
                        p_value = None
                        significant = False
                else:
                    p_value = None
                    significant = False
                smell_results.append({
                    "type_name": type_name,
                    "test_smell": test_smell,
                    "total": smell_total,
                    "improvements": smell_improvements,
                    "degradations": smell_degradations,
                    "no_changes": smell_no_changes,
                    "improvement_rate": smell_improvements / smell_total * 100 if smell_total > 0 else 0,
                    "degradation_rate": smell_degradations / smell_total * 100 if smell_total > 0 else 0,
                    "no_change_rate": smell_no_changes / smell_total * 100 if smell_total > 0 else 0,
                    "effect_size": effect_size,
                    "p_value": p_value,
                    "significant": significant
                })
                # CSV用に詳細行を追加
                detailed_rows.append({
                    "type_name": type_name,
                    "test_smell": test_smell,
                    "total": smell_total,
                    "improvements": smell_improvements,
                    "degradations": smell_degradations,
                    "no_changes": smell_no_changes,
                    "improvement_rate": smell_improvements / smell_total * 100 if smell_total > 0 else 0,
                    "degradation_rate": smell_degradations / smell_total * 100 if smell_total > 0 else 0,
                    "no_change_rate": smell_no_changes / smell_total * 100 if smell_total > 0 else 0,
                    "effect_size": effect_size,
                    "p_value": p_value,
                    "significant": significant
                })
            results.append({
                "type_name": type_name,
                "total_pairs": total_pairs,
                "improvements": improvements,
                "degradations": degradations,
                "no_changes": no_changes,
                "improvement_rate": improvement_rate,
                "degradation_rate": degradation_rate,
                "no_change_rate": no_change_rate,
                "smell_details": smell_results
            })
            print(f"{type_name}:")
            print(f"  Total: {total_pairs}, Improvements: {improvements} ({improvement_rate:.1f}%), "
                  f"Degradations: {degradations} ({degradation_rate:.1f}%), "
                  f"No change: {no_changes} ({no_change_rate:.1f}%)")
        # 詳細をCSVで保存
        detailed_df = pd.DataFrame(detailed_rows)
        detailed_df.to_csv(f"{RESULTS_DIR}/refactoring_type_testsmell_summary_{level}.csv", index=False)
        return results

    def plot_change_patterns(results_df, level):
        """
        Create simple horizontal bar visualizations for change patterns (exclude NumberOfMethods, no bold, no value labels).
        """
        # NumberOfMethodsを除外
        results_df = results_df[results_df["test_smell"] != "NumberOfMethods"]

        # 改善率降順で並び替え
        results_df = results_df.sort_values('improvement_rate', ascending=False)
        y = np.arange(len(results_df))
        no_changes = results_df["no_change_rate"].values
        improvements = results_df["improvement_rate"].values
        degradations = results_df["degradation_rate"].values
        test_smells = results_df["test_smell"].values

        color_nochange = '#bdbdbd'
        color_improve = '#4daf4a'
        color_degrade = '#e41a1c'

        plt.figure(figsize=(12, 8))
        plt.barh(y, no_changes, color=color_nochange, label='No Change')
        plt.barh(y, improvements, left=no_changes, color=color_improve, label='Improvements')
        plt.barh(y, degradations, left=no_changes + improvements, color=color_degrade, label='Degradations')

        plt.yticks(y, test_smells, fontsize=16)
        plt.xlabel('Percentage (%)', fontsize=14)
        plt.xticks(fontsize=14)
        # plt.ylabel('Test Smells')
        plt.legend(loc='upper right')
        plt.tight_layout()
        plt.savefig(f"{RESULTS_DIR}/change_patterns_{level}_better.pdf", dpi=600)
        plt.close()

    def perform_statistical_tests(df, level):
        """
        Perform statistical tests only where meaningful changes exist.
        """
        print(f"\n=== Statistical Analysis for {level} Level ===")

        results = []

        for test_smell in df["test_smell"].unique():
            subset = df[df["test_smell"] == test_smell]

            # Only perform test if there are actual changes
            changes = subset[subset["after_value"] != subset["before_value"]]

            if len(changes) < 5:  # Too few changes for meaningful test
                results.append({
                    "test_smell": test_smell,
                    "total_pairs": len(subset),
                    "changed_pairs": len(changes),
                    "test_performed": False,
                    "reason": "Insufficient changes"
                })
                continue

            try:
                # Perform Wilcoxon test only on changed pairs
                stat, p_value = wilcoxon(changes["before_value"], changes["after_value"])

                # Calculate effect size
                diff = changes["after_value"] - changes["before_value"]
                effect_size = np.mean(diff) / np.std(diff) if np.std(diff) > 0 else 0

                results.append({
                    "test_smell": test_smell,
                    "total_pairs": len(subset),
                    "changed_pairs": len(changes),
                    "test_performed": True,
                    "wilcoxon_stat": stat,
                    "p_value": p_value,
                    "effect_size": effect_size,
                    "significant": p_value < 0.05
                })

            except Exception as e:
                results.append({
                    "test_smell": test_smell,
                    "total_pairs": len(subset),
                    "changed_pairs": len(changes),
                    "test_performed": False,
                    "reason": str(e)
                })

        return pd.DataFrame(results)

    def main():
        """Main function to execute the descriptive analysis."""
        # Load data
        file_df_raw, method_df_raw = load_data()

        # Preprocess data
        file_df = preprocess_data(file_df_raw)
        method_df = preprocess_data(method_df_raw)

        # Analyze change patterns
        file_patterns = analyze_change_patterns(file_df, "file")
        method_patterns = analyze_change_patterns(method_df, "method")

        # Analyze by refactoring type
        file_by_type = analyze_by_refactoring_type(file_df, "file")
        method_by_type = analyze_by_refactoring_type(method_df, "method")

        # Create visualizations
        plot_change_patterns(file_patterns, "file")
        plot_change_patterns(method_patterns, "method")

        # Perform statistical tests where appropriate
        file_stats = perform_statistical_tests(file_df, "file")
        method_stats = perform_statistical_tests(method_df, "method")

        # Save results
        file_patterns.to_csv(f"{RESULTS_DIR}/change_patterns_file.csv", index=False)
        method_patterns.to_csv(f"{RESULTS_DIR}/change_patterns_method.csv", index=False)
        file_stats.to_csv(f"{RESULTS_DIR}/statistical_results_file.csv", index=False)
        method_stats.to_csv(f"{RESULTS_DIR}/statistical_results_method.csv", index=False)

        print(f"\n=== Analysis Complete ===")
        print(f"Results saved to: {RESULTS_DIR}")

    if __name__ == "__main__":
        main()
    for test_smell in df["test_smell"].unique():
        subset = df[df["test_smell"] == test_smell]
        
        # Only perform test if there are actual changes
        changes = subset[subset["after_value"] != subset["before_value"]]
        
        if len(changes) < 5:  # Too few changes for meaningful test
            results.append({
                "test_smell": test_smell,
                "total_pairs": len(subset),
                "changed_pairs": len(changes),
                "test_performed": False,
                "reason": "Insufficient changes"
            })
            continue
        
        try:
            # Perform Wilcoxon test only on changed pairs
            stat, p_value = wilcoxon(changes["before_value"], changes["after_value"])
            
            # Calculate effect size
            diff = changes["after_value"] - changes["before_value"]
            effect_size = np.mean(diff) / np.std(diff) if np.std(diff) > 0 else 0
            
            results.append({
                "test_smell": test_smell,
                "total_pairs": len(subset),
                "changed_pairs": len(changes),
                "test_performed": True,
                "wilcoxon_stat": stat,
                "p_value": p_value,
                "effect_size": effect_size,
                "significant": p_value < 0.05
            })
            
        except Exception as e:
            results.append({
                "test_smell": test_smell,
                "total_pairs": len(subset),
                "changed_pairs": len(changes),
                "test_performed": False,
                "reason": str(e)
            })
    
    return pd.DataFrame(results)


def main():
    """Main function to execute the descriptive analysis."""
    # Load data
    file_df_raw, method_df_raw = load_data()
    
    # Preprocess data
    file_df = preprocess_data(file_df_raw)
    method_df = preprocess_data(method_df_raw)
    
    # Analyze change patterns
    file_patterns = analyze_change_patterns(file_df, "file")
    method_patterns = analyze_change_patterns(method_df, "method")
    
    # # Analyze by refactoring type
    # file_by_type = analyze_by_refactoring_type(file_df, "file")
    # method_by_type = analyze_by_refactoring_type(method_df, "method")
    #
    # Create visualizations
    plot_change_patterns(file_patterns, "file")
    plot_change_patterns(method_patterns, "method")
    
    # Perform statistical tests where appropriate
    # file_stats = perform_statistical_tests(file_df, "file")
    # method_stats = perform_statistical_tests(method_df, "method")
    
    # Save results
    # file_patterns.to_csv(f"{RESULTS_DIR}/change_patterns_file.csv", index=False)
    # method_patterns.to_csv(f"{RESULTS_DIR}/change_patterns_method.csv", index=False)
    # file_stats.to_csv(f"{RESULTS_DIR}/statistical_results_file.csv", index=False)
    # method_stats.to_csv(f"{RESULTS_DIR}/statistical_results_method.csv", index=False)
    
    print(f"\n=== Analysis Complete ===")
    print(f"Results saved to: {RESULTS_DIR}")


if __name__ == "__main__":
    main() 