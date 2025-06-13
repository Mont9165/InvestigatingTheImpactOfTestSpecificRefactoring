import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

from joblib.parallel import method
from scipy.stats import stats

# Directory settings
BASE_DIR = "/Users/horikawa/Dev/Research-repo/InvestigatingTheImpactOfTestSpecificRefactoring"
CSV_DIR = f"{BASE_DIR}/5_analyze_test_smell/src/smells_result"
RESULTS_DIR = f"{BASE_DIR}5_analyze_test_smell/src/analysis/rq3/analysis_result"

# Create output directory if it does not exist
os.makedirs(RESULTS_DIR, exist_ok=True)


def load_data():
    """
    Load the dataset from a CSV file.
    """
    file_level_path = f"{CSV_DIR}/file_level_wide.csv"
    method_level_path = f"{CSV_DIR}/method_level_wide.csv"
    file_df = pd.read_csv(file_level_path)
    method_df = pd.read_csv(method_level_path)
    return file_df, method_df


def preprocess_data(df):
    """
    Extract relevant columns and reshape the data for heatmap visualization.
    """
    # Select only columns containing "_diff" (indicating test smell changes)
    test_smell_columns = [col for col in df.columns if "_diff" in col]

    if not test_smell_columns:
        raise ValueError("No '_diff' columns found in the dataset.")

    # Transform the dataset from wide format to long format
    melted_df = df.melt(id_vars=["commit_url", "type_name"],
                         value_vars=test_smell_columns,
                         var_name="test_smell",
                         value_name="diff_value")

    # Remove "_diff" suffix from the test smell names
    melted_df["test_smell"] = melted_df["test_smell"].str.replace("_diff", "")

    print("Data transformation completed.")
    return melted_df


def analyze_statistics(df):
    """
    Perform statistical analysis on the relationship between refactoring types and test smells.
    Save the results as a CSV file.
    """
    # Compute summary statistics for each refactoring type
    stats = df.groupby("type_name")["diff_value"].describe()

    # Compute variance and add it to the statistics
    stats["variance"] = df.groupby("type_name")["diff_value"].var()

    # Save the statistics to a CSV file
    stats_csv_path = f"{RESULTS_DIR}/test_smell_refactoring_stats.csv"
    stats.to_csv(stats_csv_path, index=True)
    print(f"Statistics saved to {stats_csv_path}")

    return stats


def plot_heatmap(df, level):
    """
    Generate a heatmap to visualize the relationship between refactoring types and test smells.
    Make 0 values appear as white.
    """
    # Create a pivot table (Refactoring Type vs. Test Smell)
    pivot_df = df.pivot_table(index="type_name", columns="test_smell", values="diff_value", aggfunc="median").fillna(0)

    plt.figure(figsize=(18, 12))  # Increase figure size for better readability


    sns.heatmap(
        pivot_df,
        cmap=sns.diverging_palette(240, 10, as_cmap=True),  # Custom colormap for better contrast
        annot=True,  # Show values in cells
        fmt=".2f",  # Format numbers with two decimal places
        linewidths=0.5,  # Set border thickness to improve visibility
        center=0,  # Make zero values neutral in color mapping
        cbar_kws={'label': 'Change in Test Smell Frequency'}  # Label for the color bar
    )

    # Adjust titles and labels for better readability
    plt.title(f"Impact of Refactoring on Test Smells - {level} level", fontsize=18, fontweight='bold')
    plt.xlabel("Test Smell", fontsize=14, labelpad=10)
    plt.ylabel("Refactoring Type", fontsize=14, labelpad=10)

    # Improve font sizes for x and y labels
    plt.xticks(rotation=90, fontsize=12)
    plt.yticks(fontsize=12)
    plt.subplots_adjust(left=0.21, right=0.95, top=0.95, bottom=0.25)  # Adjust plot margins
    plt.savefig(f"{RESULTS_DIR}/test_smell_refactoring_heatmap_{level}.pdf", format="pdf")

def wilcoxon_signed_rank_test(df):
    """
    Apply Wilcoxon signed-rank test to determine statistical significance
    and calculate the effect size for test smell changes.
    """
    results = []

    for test_smell in df["test_smell"].unique():
        subset = df[df["test_smell"] == test_smell]

        # Before and After values
        before = subset["before_value"]
        after = subset["after_value"]

        # Ensure at least some variation exists before testing
        if (before == after).all():
            continue

        # Perform Wilcoxon signed-rank test
        stat, p_value = stats.wilcoxon(before, after)

        # Compute effect size (r-value)
        r_value = stat / np.sqrt(len(before))

        results.append({
            "test_smell": test_smell,
            "Wilcoxon_stat": stat,
            "p_value": p_value,
            "effect_size_r": r_value
        })

    # Convert to DataFrame
    results_df = pd.DataFrame(results)

    # Save results to CSV
    results_df.to_csv(f"{RESULTS_DIR}/wilcoxon_test_results.csv", index=False)

    print(f"Wilcoxon signed-rank test results saved to {RESULTS_DIR}/wilcoxon_test_results.csv")
    return results_df

def main():
    """
    Main function to execute the analysis.
    """
    # Load the dataset
    file_df, method_df = load_data()

    # Preprocess the data
    file_melted_df = preprocess_data(file_df)
    method_melted_df = preprocess_data(method_df)

    # Perform statistical analysis
    # file_stats = analyze_statistics(file_melted_df)
    # file_stats.to_csv(f"{RESULTS_DIR}/test_smell_refactoring_stats_file.csv", index=True)
    # method_stats = analyze_statistics(method_melted_df)
    # method_stats.to_csv(f"{RESULTS_DIR}/test_smell_refactoring_stats_method.csv", index=True)
    #
    # wilcoxon_signed_rank_test(file_melted_df)
    # wilcoxon_signed_rank_test(method_melted_df)
    # Generate heatmap
    plot_heatmap(file_melted_df, "file")
    plot_heatmap(method_melted_df, "method")


if __name__ == "__main__":
    main()