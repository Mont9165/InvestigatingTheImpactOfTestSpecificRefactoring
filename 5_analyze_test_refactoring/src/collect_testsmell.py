import logging
import os
import subprocess
from concurrent.futures import ProcessPoolExecutor
import pandas as pd

# Constants
BASE_DIR = "/work/kosei-ho/InvestigatingTheImpactOfTestSpecificRefactoring"
JAR_PATH = f"{BASE_DIR}/5_analyze_test_smell/TestSmellDetector/jar/TestSmellDetector-0.1-jar-with-dependencies.jar"
TEST_SMELL_DIR = f"{BASE_DIR}/5_analyze_test_smell/TestSmellDetector/"
RESULTS_DIR = f"{BASE_DIR}/5_analyze_test_smell/src/results"

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="logfile.log",
    filemode="a"
)
logger = logging.getLogger(__name__)


def get_refactoring_data_from_annotation_data():
    """Retrieve refactoring data from annotation data."""
    return pd.read_json(f"{RESULTS_DIR}/annotation_result_2024-02-20.json")


def get_parent_commit_id(df2, commit_id):
    """Get the parent commit ID (performance improved)."""
    row = df2.loc[df2["commit_id"] == commit_id]
    return row["parent_commit_id"].iloc[0] if not row.empty else None


def collect_testsmell(commit_url):
    """Detect test smells using the Jar file."""
    try:
        logger.info(f"Running TestSmellDetector for {commit_url} using {JAR_PATH}")

        result = subprocess.run(
            ["java", "-jar", JAR_PATH, commit_url],
            capture_output=True,
            text=True,
            cwd=TEST_SMELL_DIR
        )

        if result.returncode == 0:
            logger.info(f"Test smell detection successful for {commit_url}")
            print(result.stdout)
        else:
            logger.error(f"Test smell detection failed for {commit_url}: {result.stderr}")

    except Exception as e:
        logger.error(f"Error running TestSmellDetector for {commit_url}: {e}")


def process_grouped_data(commit_url, df2, group):
    """Process grouped data."""
    try:
        commit_id = commit_url.split("/")[-1]
        repo_url = "/".join(commit_url.split("/")[:5])
        parent_commit_id = get_parent_commit_id(df2, commit_id)

        if parent_commit_id is None:
            logger.warning(f"Parent commit not found for {commit_url}")
            return

        parent_commit_url = f"{repo_url}/commit/{parent_commit_id}"

        # Run Jar files in parallel
        collect_testsmell(commit_url)
        collect_testsmell(parent_commit_url)

        # Process parameter data
        for _, row in group.iterrows():
            logger.info(f"Processing refactoring type: {row['type_name']} for commit: {commit_url}")

    except Exception as e:
        logger.error(f"Error in process_grouped_data for {commit_url}: {e}")


def main():
    """Main function."""
    try:
        df1 = get_refactoring_data_from_annotation_data()
        df2 = pd.read_csv(f"{BASE_DIR}/2_sampling_test_refactor_commits/result/sampling_test_commits_all.csv")
        grouped = df1.groupby("url")

        # Parallel processing (Process pool)
        with ProcessPoolExecutor(max_workers=32) as executor:
            futures = {
                executor.submit(process_grouped_data, commit_url, df2, group) for commit_url, group in grouped
            }
            for future in futures:
                try:
                    future.result()
                except Exception as e:
                    logger.error(f"Parallel execution error: {e}")

    except Exception as e:
        logger.error(f"Error in main function: {e}")


if __name__ == "__main__":
    main()