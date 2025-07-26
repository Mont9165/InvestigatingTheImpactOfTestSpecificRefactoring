import logging
import os
import subprocess
from concurrent.futures import ProcessPoolExecutor
import pandas as pd
import argparse
import platform
import fcntl
import time

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


def record_failed_commit(commit_url: str, error_msg: str, failed_log_path: str):
    """失敗したコミットをログファイルに記録"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    with open(failed_log_path, 'a', encoding='utf-8') as f:
        f.write(f"{timestamp},{commit_url},{error_msg}\n")


def collect_testsmell(commit_url: str, jar_path: str, test_smell_dir: str, max_retries=3, failed_log_path="failed_commits.csv"):
    """Jarファイルを使ってテストスメルを検出する (存在確認付き、リトライ機能付き)"""
    if already_exists(commit_url, test_smell_dir):
        return

    # ここで index.lock の削除を試みる
    remove_index_lock_if_exists(commit_url, test_smell_dir)

    for attempt in range(max_retries):
        try:
            logging.info(f"Running TestSmellDetector for {commit_url} (attempt {attempt + 1}/{max_retries})")
            result = subprocess.run(
                ["java", "-jar", jar_path, commit_url],
                capture_output=True,
                text=True,
                check=True,  # これで returncode != 0 の場合に例外が発生する
                cwd=test_smell_dir,
                timeout=600  # 10分のタイムアウト
            )
            logging.info(f"Test smell detection successful for {commit_url}")
            print(result.stdout)
            return  # 成功したら終了
            
        except subprocess.TimeoutExpired:
            error_msg = f"Timeout after {600} seconds"
            logging.error(f"Test smell detection timed out for {commit_url} (attempt {attempt + 1})")
            if attempt == max_retries - 1:
                logging.error(f"Failed after {max_retries} attempts for {commit_url}")
                record_failed_commit(commit_url, error_msg, failed_log_path)
            else:
                time.sleep(5)  # 5秒待機してリトライ
                
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else str(e)
            if "Connection reset" in error_msg or "TransportException" in error_msg:
                logging.warning(f"Network error for {commit_url} (attempt {attempt + 1}): {error_msg[:200]}...")
                if attempt == max_retries - 1:
                    logging.error(f"Failed after {max_retries} attempts for {commit_url}")
                    record_failed_commit(commit_url, f"Network error: {error_msg[:200]}", failed_log_path)
                else:
                    time.sleep(10)  # ネットワークエラーの場合は10秒待機
            else:
                logging.error(f"Test smell detection failed for {commit_url}: {error_msg}")
                record_failed_commit(commit_url, error_msg, failed_log_path)
                break  # ネットワーク以外のエラーはリトライしない
                
        except Exception as e:
            logging.error(f"Unexpected error running TestSmellDetector for {commit_url}: {e}")
            record_failed_commit(commit_url, str(e), failed_log_path)
            break  # 予期しないエラーはリトライしない


def get_repo_lock_path(commit_url: str, test_smell_dir: str) -> str:
    """リポジトリ単位のロックファイルパスを取得"""
    commit_dir = commit_url.replace("https://github.com/", "").replace("commit/", "")
    repo_name = "/".join(commit_dir.split("/")[:-1])  # コミットIDを除いたリポジトリ名
    return os.path.join(test_smell_dir, "locks", f"{repo_name.replace('/', '_')}.lock")

def acquire_repo_lock(commit_url: str, test_smell_dir: str, timeout=300):
    """リポジトリ単位のロックを取得（タイムアウト付き）"""
    lock_path = get_repo_lock_path(commit_url, test_smell_dir)
    os.makedirs(os.path.dirname(lock_path), exist_ok=True)
    
    lock_file = open(lock_path, 'w')
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            logging.info(f"Acquired lock for repo: {commit_url}")
            return lock_file
        except IOError:
            logging.info(f"Waiting for lock: {lock_path}")
            time.sleep(1)
    
    lock_file.close()
    raise TimeoutError(f"Failed to acquire lock for {commit_url} within {timeout} seconds")

def release_repo_lock(lock_file):
    """リポジトリ単位のロックを解放"""
    try:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
        lock_file.close()
        logging.info("Released repo lock")
    except Exception as e:
        logging.error(f"Error releasing lock: {e}")

def process_commit(commit_url: str, df_commits: pd.DataFrame, jar_path: str, test_smell_dir: str):
    """単一のコミットURLを処理し、親コミットと合わせてテストスメルを検出する（ロック付き）"""
    lock_file = None
    try:
        # リポジトリ単位のロックを取得
        lock_file = acquire_repo_lock(commit_url, test_smell_dir)
        
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
    finally:
        # ロックを解放
        if lock_file:
            release_repo_lock(lock_file)


def group_commits_by_repo(commit_urls):
    """コミットURLをリポジトリ単位でグループ化"""
    repo_groups = {}
    for url in commit_urls:
        commit_dir = url.replace("https://github.com/", "").replace("commit/", "")
        repo_name = "/".join(commit_dir.split("/")[:-1])
        if repo_name not in repo_groups:
            repo_groups[repo_name] = []
        repo_groups[repo_name].append(url)
    return repo_groups

def process_repo_group(repo_commits, df_commits, jar_path, test_smell_dir):
    """リポジトリ単位でコミット群を処理"""
    for commit_url in repo_commits:
        process_commit(commit_url, df_commits, jar_path, test_smell_dir)

def main():
    """メイン関数: コマンドライン引数を解釈し、処理を実行する"""
    parser = argparse.ArgumentParser(description="Run TestSmellDetector on a list of commits.")
    parser.add_argument("--base-dir", type=str, default=get_default_base_dir(), help="Base directory of the project.")
    parser.add_argument("--parallel", action="store_true", help="Run in parallel mode.")
    parser.add_argument("--workers", type=int, default=os.cpu_count(), help="Number of parallel workers.")
    parser.add_argument("--log-file", type=str, default="logfile.log", help="Path to the log file.")
    parser.add_argument("--safe-parallel", action="store_true", help="Use safe parallel mode (repo-level grouping).")
    parser.add_argument("--max-retries", type=int, default=3, help="Maximum number of retries for failed commits.")
    parser.add_argument("--timeout", type=int, default=600, help="Timeout in seconds for each commit processing.")
    parser.add_argument("--failed-log", type=str, default="failed_commits.csv", help="Path to log failed commits.")
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

        if args.safe_parallel:
            # 安全な並列処理：リポジトリ単位でグループ化
            logging.info(f"Running in SAFE PARALLEL mode with {args.workers} workers.")
            repo_groups = group_commits_by_repo(commit_urls)
            logging.info(f"Grouped {len(commit_urls)} commits into {len(repo_groups)} repositories")
            
            with ProcessPoolExecutor(max_workers=args.workers) as executor:
                futures = {
                    executor.submit(process_repo_group, commits, df_commits, JAR_PATH, TEST_SMELL_DIR) 
                    for commits in repo_groups.values()
                }
                for future in futures:
                    future.result()
                    
        elif args.parallel:
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