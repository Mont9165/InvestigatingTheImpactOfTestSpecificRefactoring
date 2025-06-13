import json
import subprocess
from urllib.parse import urlparse
import os
import git
import logging
import pandas as pd

logging.basicConfig(
    level=logging.INFO, # ログレベルをINFOに設定
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', # ログのフォーマットを設定
    filename='../logfile.log', # ログを保存するファイル名を指定
    filemode='a' # ログファイルを追記モードで開く
)

logger = logging.getLogger(__name__)


FILE_PATH = os.path.abspath('../data/Inspected_changes_with_commit_urls.json')


def load_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data


def conduct_testsmell(project_dir, src_dir, commit_id):
    logger.info(f'Starting conduct_testsmell with project_dir={project_dir}, src_main_path={src_dir}, commit_id={commit_id}')

    jar_path = "/Users/horikawa/Dev/sakigake/Database-mining/RefactorHub-mining/tool/TestSmellDetector/target/TestSmellDetector-0.1-jar-with-dependencies.jar"
    project_dir = os.path.abspath(project_dir)
    src_dir = os.path.abspath(src_dir)
    os.chdir("/Users/horikawa/Dev/sakigake/Database-mining/RefactorHub-mining/tool/TestSmellDetector")
    print(["java", "-jar", jar_path, project_dir, src_dir, commit_id])

    subprocess.run(["java", "-jar", jar_path, project_dir, src_dir, commit_id])
    logger.info(f'Finished conduct_testsmell with project_dir={project_dir}, src_main_path={src_dir}, commit_id={commit_id}')


def extract_owner_and_repo(url):
    parsed_url = urlparse(url)
    path = parsed_url.path
    owner, repo = path.split('/')[1:3]
    return owner + "/" + repo


def parse_src_path(path):
    index = path.find('/src/') + len('/src/')
    if index != -1:
        return path[:index]


def extract_parent_commit_id(commit_id):
    csv_path = "/result_sigss/data/inspection_commit_data.csv"
    df = pd.read_csv(csv_path)
    for i, row in df.iterrows():
        if row['commit_id'] == commit_id:
            return row['parent_commit_id']
    pass


def collect_testsmell(project_dir, commit_url, commit_id, repo_owner_and_name, row):
    try:
        for after_data in row['Parameter Data']['after']['added codes']['elements']:
            src_main_path = f'{project_dir}/{parse_src_path(after_data["location"]["path"])}main'
            conduct_testsmell(project_dir, src_main_path, commit_id)

    except Exception as e:
        logger.error(f'Error occurred in {repo_owner_and_name} with commit_id={commit_id}')
        print(e)


def main():
    json_data = load_json(FILE_PATH)

    for row in json_data:
        refactoring_type = row['Type Name']
        if refactoring_type == 'Non-Refactoring':
            continue
        commit_url = row['Commit URL']
        commit_id = commit_url.split('/')[-1]
        parent_commit_id = extract_parent_commit_id(commit_id)
        print(parent_commit_id)
        repo_owner_and_name = extract_owner_and_repo(commit_url)

        project_resource_dir = os.path.abspath("../../tool/TestSmellDetector/repos")
        project_dir = project_resource_dir + "/" + repo_owner_and_name
        # print(f'project_dir={project_dir}, commit_url={commit_url}, commit_id={commit_id}')

        collect_testsmell(project_dir, commit_url, commit_id, repo_owner_and_name, row)
        collect_testsmell(project_dir, commit_url, parent_commit_id, repo_owner_and_name, row)


if __name__ == '__main__':
    main()
