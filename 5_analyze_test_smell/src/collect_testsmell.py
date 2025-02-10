import logging
import os
import subprocess
from concurrent.futures import ProcessPoolExecutor

from sqlalchemy import create_engine
import pandas as pd

DATABASE_URL = "postgresql://rhuser:rhpass@localhost:5435/refactorhub"
JAR_PATH = "../TestSmellDetector/jar/TestSmellDetector-0.1-jar-with-dependencies.jar"
engine = create_engine(DATABASE_URL)


logging.basicConfig(
    level=logging.INFO, # ログレベルをINFOに設定
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', # ログのフォーマットを設定
    filename='logfile.log', # ログを保存するファイル名を指定
    filemode='a' # ログファイルを追記モードで開く
)

logger = logging.getLogger(__name__)


def get_refactoring_data_from_annotation_data():
    return pd.read_json('results/annotation_result.json')


def process_parameter_data(parameter_data, commit_url, parent_commit_url):
    commit_dir = commit_url.replace('https://github.com', '').replace('commit/', '')
    parent_commit_dir = parent_commit_url.replace(' https://github.com', '').replace('commit/', '')

    try:
        commit_df = pd.read_csv(f"results/smells/{commit_dir}/smells_number.csv")
        for key, value in parameter_data.items():
            print(f"{key}: ")
            for k, v in value.items():
                for element in v['elements']:
                    print(f"    {element['location']['path']}")
    except Exception as e:
        print(e)


def get_parent_commit_id(df2, commit_id):
    for i, row in df2.iterrows():
        if row['commit_id'] == commit_id:
            return row['parent_commit_id']
    pass


def collect_testsmell(commit_url):
    try:
        jar_path = os.path.abspath(JAR_PATH)
        os.chdir("../TestSmellDetector/")
        logger.info(f"Running TestSmellDetector for {commit_url} using {jar_path}")

        result = subprocess.run(["java", "-jar", jar_path, commit_url], capture_output=True, text=True)

        if result.returncode == 0:
            logger.info(f"Test smell detection successful for {commit_url}")
            print(result.stdout)
        else:
            logger.error(f"Test smell detection failed for {commit_url}: {result.stderr}")

    except Exception as e:
        logger.error(f"Error running TestSmellDetector for {commit_url}: {e}")


def process_grouped_data(commit_url, df2, group):
    commit_id = commit_url.split('/')[-1]
    repo_url = '/'.join(commit_url.split('/')[:5])
    parent_commit_url = f"{repo_url}/commit/{get_parent_commit_id(df2, commit_id)}"

    collect_testsmell(commit_url)
    collect_testsmell(parent_commit_url)

    for _, row in group.iterrows():
        logger.info(f"Processing refactoring type: {row['type_name']} for commit: {commit_url}")
        # process_parameter_data(row["parameter_data"], commit_url, parent_commit_url)


def main():
    df1 = get_refactoring_data_from_annotation_data()
    df2 = pd.read_csv("../../2_sampling_test_refactor_commits/result/sampling_test_commits_all.csv")
    grouped = df1.groupby("url")

    # parallel processing
    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = {executor.submit(process_grouped_data, commit_url, df2, group) for commit_url, group in grouped}
        for future in futures:
            future.result()


if __name__ == '__main__':
    main()