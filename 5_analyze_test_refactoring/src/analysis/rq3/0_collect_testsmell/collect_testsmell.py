import logging
import os
import subprocess
from concurrent.futures import ProcessPoolExecutor
import pandas as pd
import argparse
import platform

# --- 設定 ---
def get_default_base_dir():
    """実行OSに応じてデフォルトのBASE_DIRを返す"""
    if platform.system() == "Darwin":  # macOS
        return "/Users/horikawa/Dev/Research-repo/InvestigatingTheImpactOfTestSpecificRefactoring"
    return "/work/kosei-ho/InvestigatingTheImpactOfTestSpecificRefactoring" # デフォルトはLinux/サーバー

# --- ロギング設定 ---
def setup_logging(log_file="logfile.log"):
    """ロギングをファイルとコンソールに設定する"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        filename=log_file,
        filemode="a"
    )
    # コンソールにも出力
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logging.getLogger('').addHandler(console_handler)

# --- コアロジック ---
def get_refactoring_data_from_annotation_data(results_dir):
    """アノテーションデータからリファクタリングデータを取得する"""
    return pd.read_json(f"{results_dir}/annotation_result_2024-02-20.json")


def get_parent_commit_id(df, commit_id):
    """親コミットIDを取得する"""
    row = df.loc[df["commit_id"] == commit_id]
    return row["parent_commit_id"].iloc[0] if not row.empty else None


def already_exists(commit_url: str, test_smell_dir: str) -> bool:
    """テストスメル検出の出力ファイルが既に存在するか確認する"""
    commit_dir = commit_url.replace("https://github.com/", "").replace("commit/", "")
    output_dir = os.path.join(test_smell_dir, "results", "smells", commit_dir)
    smells_number_csv = os.path.join(output_dir, "smells_number.csv")
    smells_result_json = os.path.join(output_dir, "smells_result.json")

    if os.path.isfile(smells_number_csv) and os.path.isfile(smells_result_json):
        logging.info(f"Skip {commit_url} because output already exists.")
        return True
    return False


def remove_index_lock_if_exists(commit_url: str, test_smell_dir: str):
    """対象リポジトリの .git/index.lock が存在すれば削除する"""
    commit_dir = commit_url.replace("https://github.com/", "").replace("commit/", "")
    repo_dir = os.path.join(test_smell_dir, "repos", "/".join(commit_dir.split("/")[:-1]))
    index_lock_path = os.path.join(repo_dir, ".git", "index.lock")
    if os.path.isfile(index_lock_path):
        try:
            os.remove(index_lock_path)
            logging.warning(f"Removed stale index.lock: {index_lock_path}")
        except Exception as e:
            logging.error(f"Failed to remove index.lock: {index_lock_path} ({e})")


def collect_testsmell(commit_url: str, jar_path: str, test_smell_dir: str):
    """Jarファイルを使ってテストスメルを検出する (存在確認付き)"""
    if already_exists(commit_url, test_smell_dir):
        return

    # ここで index.lock の削除を試みる
    remove_index_lock_if_exists(commit_url, test_smell_dir)

    try:
        logging.info(f"Running TestSmellDetector for {commit_url}")
        result = subprocess.run(
            ["java", "-jar", jar_path, commit_url],
            capture_output=True,
            text=True,
            check=True,  # これで returncode != 0 の場合に例外が発生する
            cwd=test_smell_dir
        )
        logging.info(f"Test smell detection successful for {commit_url}")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        logging.error(f"Test smell detection failed for {commit_url}: {e.stderr}")
    except Exception as e:
        logging.error(f"Error running TestSmellDetector for {commit_url}: {e}")


def process_commit(commit_url: str, df_commits: pd.DataFrame, jar_path: str, test_smell_dir: str):
    """単一のコミットURLを処理し、親コミットと合わせてテストスメルを検出する"""
    try:
        commit_id = commit_url.split("/")[-1]
        repo_url = "/".join(commit_url.split("/")[:5])
        parent_commit_id = get_parent_commit_id(df_commits, commit_id)

        if parent_commit_id is None:
            logging.warning(f"Parent commit not found for {commit_url}")
            return

        parent_commit_url = f"{repo_url}/commit/{parent_commit_id}"

        # 対象コミットと親コミットのスメルを検出
        collect_testsmell(commit_url, jar_path, test_smell_dir)
        collect_testsmell(parent_commit_url, jar_path, test_smell_dir)

    except Exception as e:
        logging.error(f"Error in process_commit for {commit_url}: {e}")


def main():
    """メイン関数: コマンドライン引数を解釈し、処理を実行する"""
    parser = argparse.ArgumentParser(description="Run TestSmellDetector on a list of commits.")
    parser.add_argument("--base-dir", type=str, default=get_default_base_dir(), help="Base directory of the project.")
    parser.add_argument("--parallel", action="store_true", help="Run in parallel mode.")
    parser.add_argument("--workers", type=int, default=os.cpu_count(), help="Number of parallel workers.")
    parser.add_argument("--log-file", type=str, default="logfile.log", help="Path to the log file.")
    args = parser.parse_args()

    # 引数に基づき定数を設定
    BASE_DIR = args.base_dir
    JAR_PATH = f"{BASE_DIR}/5_analyze_test_refactoring/TestSmellDetector/jar/TestSmellDetector-0.1-jar-with-dependencies.jar"
    TEST_SMELL_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/TestSmellDetector/"
    ANNOTATION_RESULTS_DIR = f"{BASE_DIR}/5_analyze_test_refactoring/src/results"

    setup_logging(args.log_file)
    logging.info(f"Starting script with config: {args}")

    try:
        df_refactorings = get_refactoring_data_from_annotation_data(ANNOTATION_RESULTS_DIR)
        df_commits = pd.read_csv(f"{BASE_DIR}/2_sampling_test_refactor_commits/result/sampling_test_commits_all.csv")
        
        # 重複を除いたコミットURLのリストを取得
        commit_urls = df_refactorings["url"].unique()

        if args.parallel:
            logging.info(f"Running in PARALLEL mode with {args.workers} workers.")
            with ProcessPoolExecutor(max_workers=args.workers) as executor:
                futures = {executor.submit(process_commit, url, df_commits, JAR_PATH, TEST_SMELL_DIR) for url in commit_urls}
                for future in futures:
                    future.result()  # エラーハンドリング
        else:
            logging.info("Running in SERIAL mode.")
            for url in commit_urls:
                process_commit(url, df_commits, JAR_PATH, TEST_SMELL_DIR)

        logging.info("Script finished successfully.")

    except Exception as e:
        logging.critical(f"A critical error occurred in main function: {e}", exc_info=True)


if __name__ == "__main__":
    main()