import json
import subprocess
from urllib.parse import urlparse
import os
import git
import logging
import pandas as pd

logging.basicConfig(
    level=logging.INFO,  # ログレベルをINFOに設定
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # ログのフォーマットを設定
    filename='calculate_testsmell_change_amount.log',  # ログを保存するファイル名を指定
    filemode='a'  # ログファイルを追記モードで開く
)

logger = logging.getLogger(__name__)

FILE_PATH = os.path.abspath(
    '/result_sigss/data/Inspected_changes_with_commit_urls.json')
CSV_PATH = "/result_sigss/data/inspection_commit_data.csv"


def load_json(file_path):
    with open(file_path, 'r') as f:
        data = json.load(f)
    return data


def extract_owner_and_repo(url):
    parsed_url = urlparse(url)
    path = parsed_url.path
    owner, repo = path.split('/')[1:3]
    return owner + "/" + repo


def git_clone(project_resource_dir, commit_url):
    repo_url = '/'.join(commit_url.split('/')[:5]) + '.git'
    git.Repo.clone_from(repo_url, project_resource_dir)


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


def get_test_file_path(json_row):
    path_list = []
    for after_data in json_row['Parameter Data']['after']['added codes']['elements']:
        path_list.append(after_data["location"]["path"])
    return path_list


def get_path_range(json_row):
    range_list = []
    for after_data in json_row['Parameter Data']['after']['added codes']['elements']:
        range_list.append(after_data["location"]["range"])
    return range_list


def get_smells(commit_smell_json, test_file_path):
    for data in commit_smell_json:
        if test_file_path in data['testFilePath']:
            return data['smells']


def count_testsmell():
    pass


def get_parent_name(commit_smells, path_range):
    for commit_smell in commit_smells:
        if ranges_overlap(commit_smell, path_range):
            return commit_smell['parentName']
    pass


def ranges_overlap(commit_smell, path_range):
    return not (commit_smell['endLine'] < path_range['startLine'] or commit_smell['beginLine'] > path_range['endLine'])


def get_smell_count(smell_list):
    testsmell_dict = {}
    for smell in smell_list:
        smell_name = smell['smellName']
        if smell_name in testsmell_dict:
            testsmell_dict[smell_name] += 1
        else:
            testsmell_dict[smell_name] = 1
    return testsmell_dict


def compare_testsmell(commit_smell_list, parent_commit_smell_list):
    testsmell_dict = {'commit_smells': {},
                      'parent_commit_smells': {},
                      'diff_smells': {}
                      }

    if len(commit_smell_list) != len(parent_commit_smell_list):
        testsmell_dict['commit_smells'] = get_smell_count(commit_smell_list)
        testsmell_dict['parent_commit_smells'] = get_smell_count(parent_commit_smell_list)
    else:
        testsmell_dict['commit_smells'] = get_smell_count(commit_smell_list)
        testsmell_dict['parent_commit_smells'] = get_smell_count(parent_commit_smell_list)

    # Calculate the diff
    all_smells = set(testsmell_dict['commit_smells'].keys()).union(testsmell_dict['parent_commit_smells'].keys())
    for smell in all_smells:
        commit_count = testsmell_dict['commit_smells'].get(smell, 0)
        parent_count = testsmell_dict['parent_commit_smells'].get(smell, 0)
        testsmell_dict['diff_smells'][smell] = commit_count - parent_count

    return testsmell_dict


def calculate_testsmell_change_amount(commit_smell_path, parent_commit_smell_path, test_file_path, path_range,
                                      method_name):
    commit_smell_json = json.load(open(commit_smell_path))
    parent_commit_smell_json = json.load(open(parent_commit_smell_path))
    commit_smells = get_smells(commit_smell_json, test_file_path)
    parent_commit_smells = get_smells(parent_commit_smell_json, test_file_path)

    testsmell_dict = {}

    try:
        if method_name is None:
            parent_name = get_parent_name(commit_smells, path_range)
            commit_smell_list = [smell for smell in commit_smells if smell['parentName'] == parent_name]
            parent_commit_smell_list = [smell for smell in parent_commit_smells if smell['parentName'] == parent_name]
            testsmell_dict = compare_testsmell(commit_smell_list, parent_commit_smell_list)
        else:
            commit_smell_list = [smell for smell in commit_smells if smell['parentName'] == method_name]
            parent_commit_smell_list = [smell for smell in parent_commit_smells if smell['parentName'] == method_name]
            testsmell_dict = compare_testsmell(commit_smell_list, parent_commit_smell_list)
    except Exception as e:
        logger.error(f'Error occurred in {commit_smell_path} or {parent_commit_smell_path}')
        # print(e)
    return testsmell_dict


def extract_method_name(json_row):
    method_name_list = []
    for after_data in json_row['Parameter Data']['after']['added codes']['elements']:
        method_name_list.append(after_data['methodName'])
    return method_name_list


def main():
    save_test_smell_json = []
    json_data = load_json(FILE_PATH)
    for json_row in json_data:
        refactoring_type = json_row['Type Name']
        if refactoring_type == 'Non-Refactoring':
            continue

        commit_url = json_row['Commit URL']
        commit_id = commit_url.split('/')[-1]

        df = pd.read_csv(CSV_PATH)
        parent_commit_id = None

        for i, row in df.iterrows():
            if row['commit_id'] == commit_id:
                parent_commit_id = row['parent_commit_id']
                break

        refactoring_data = {'refactoring_type': refactoring_type,
                            'commit_id': commit_id,
                            'parent_commit_id': parent_commit_id,
                            'smells': []
                            }

        repo_owner_and_name = extract_owner_and_repo(commit_url)
        project_resource_dir = os.path.abspath("../../tool/TestSmellDetector/results/smells")
        project_dir = project_resource_dir + "/" + repo_owner_and_name
        commit_smell_path = project_resource_dir + "/" + repo_owner_and_name + "/" + commit_id + "/smells_result.json"
        parent_commit_smell_path = project_resource_dir + "/" + repo_owner_and_name + "/" + parent_commit_id + "/smells_result.json"

        test_file_path_list = get_test_file_path(json_row)
        path_range_list = get_path_range(json_row)
        method_name_list = extract_method_name(json_row)

        if len(test_file_path_list) == 1:
            test_file_path = test_file_path_list[0]
            path_range = path_range_list[0]
            method_name = method_name_list[0]
            testsmell_dict = calculate_testsmell_change_amount(commit_smell_path, parent_commit_smell_path,
                                                               test_file_path, path_range, method_name)
            if testsmell_dict:
                refactoring_data['smells'].append(testsmell_dict)
        else:
            for index in range(len(test_file_path_list)):
                test_file_path = test_file_path_list[index]
                path_range = path_range_list[index]
                method_name = method_name_list[index]
                testsmell_dict = calculate_testsmell_change_amount(commit_smell_path, parent_commit_smell_path,
                                                                   test_file_path, path_range,method_name)
                if testsmell_dict:
                    refactoring_data['smells'].append(testsmell_dict)

        save_test_smell_json.append(refactoring_data)
    with open('test_smell_result.json', 'w') as f:
        json.dump(save_test_smell_json, f, indent=4)


if __name__ == '__main__':
    main()
