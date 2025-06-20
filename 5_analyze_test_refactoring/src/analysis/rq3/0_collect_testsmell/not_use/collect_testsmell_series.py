import logging
import os
import subprocess
import pandas as pd

# Constants
BASE_DIR = "/Users/horikawa/Dev/Research-repo/InvestigatingTheImpactOfTestSpecificRefactoring"
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


def already_exists(commit_url: str) -> bool:
    """
    Check if test smell output files (smells_number.csv and smells_result.json)
    already exist for the given commit_url.
    If they exist, we assume test smell detection is already done and skip.
    """
    commit_dir = commit_url.replace("https://github.com/", "").replace("commit/", "")
    # The directory where results are expected
    output_dir = os.path.join(TEST_SMELL_DIR, "results", "smells", commit_dir)
    smells_number_csv = os.path.join(output_dir, "smells_number.csv")
    smells_result_json = os.path.join(output_dir, "smells_result.json")

    if os.path.isfile(smells_number_csv) and os.path.isfile(smells_result_json):
        logger.info(f"Skip {commit_url} because {smells_number_csv} and {smells_result_json} both exist.")
        return True
    return False


def collect_testsmell(commit_url: str):
    """Detect test smells using the Jar file, if not exist already."""
    # すでに出力が存在すればスキップ
    if already_exists(commit_url):
        return

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
    """Process grouped data (sequential version)."""
    try:
        commit_id = commit_url.split("/")[-1]
        repo_url = "/".join(commit_url.split("/")[:5])
        parent_commit_id = get_parent_commit_id(df2, commit_id)

        if parent_commit_id is None:
            logger.warning(f"Parent commit not found for {commit_url}")
            return

        parent_commit_url = f"{repo_url}/commit/{parent_commit_id}"

        # 直列実行: commit_url -> parent_commit_urlの順に処理
        collect_testsmell(commit_url)
        collect_testsmell(parent_commit_url)

        # Optionally, do something with the 'group' / 'row' data
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

        # ----★ 並列実行をやめて、直列で実行 ★----
        for commit_url, group in grouped:
            logger.info(f"Processing refactoring data for {commit_url}")
            process_grouped_data(commit_url, df2, group)

    except Exception as e:
        logger.error(f"Error in main function: {e}")


if __name__ == "__main__":
    main()