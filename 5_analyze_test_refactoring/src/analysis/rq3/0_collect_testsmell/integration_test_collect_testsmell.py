import unittest
import os
import shutil
import time
import pandas as pd
from collect_testsmell import collect_testsmell, get_parent_commit_id

class TestCollectTestSmellIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # テスト用のパスを設定
        cls.BASE_DIR = "/Users/horikawa/Dev/Research-repo/InvestigatingTheImpactOfTestSpecificRefactoring"
        cls.JAR_PATH = f"{cls.BASE_DIR}/5_analyze_test_refactoring/TestSmellDetector/jar/TestSmellDetector-0.1-jar-with-dependencies.jar"
        cls.TEST_SMELL_DIR = f"{cls.BASE_DIR}/5_analyze_test_refactoring/TestSmellDetector/"
        # テスト用のコミットURL（例: toyリポジトリのコミット）
        cls.commit_url = "https://github.com/jenkinsci/workflow-durable-task-step-plugin/commit/537e864aae80f3dd49e37f5528f81980013743a1"
        # 必要に応じて親コミットも指定
        cls.parent_commit_url = "https://github.com/jenkinsci/workflow-durable-task-step-plugin/commit/c61e7caae7370c003561ec8524a156a4f5e658db"
        # 出力ディレクトリ
        cls.commit_dir = cls.commit_url.replace("https://github.com/", "").replace("commit/", "")
        cls.output_dir = os.path.join(cls.TEST_SMELL_DIR, "results", "smells", cls.commit_dir)

    # def tearDown(self):
    #     # テスト後に出力ファイルを削除
    #     if os.path.exists(self.output_dir):
    #         shutil.rmtree(self.output_dir)

    def test_collect_testsmell_integration(self):
        # 実際にjarを実行
        collect_testsmell(self.commit_url, self.JAR_PATH, self.TEST_SMELL_DIR)
        collect_testsmell(self.parent_commit_url, self.JAR_PATH, self.TEST_SMELL_DIR)
        # 少し待つ（ファイル生成のタイミング調整）
        time.sleep(2)
        # 出力ファイルの存在確認
        smells_number_csv = os.path.join(self.output_dir, "smells_number.csv")
        smells_result_json = os.path.join(self.output_dir, "smells_result.json")
        self.assertTrue(os.path.isfile(smells_number_csv), "smells_number.csvが生成されていません")
        self.assertTrue(os.path.isfile(smells_result_json), "smells_result.jsonが生成されていません")
        # ファイル内容の簡易チェック（例: CSVが空でない）
        df = pd.read_csv(smells_number_csv)
        self.assertFalse(df.empty, "smells_number.csvが空です")

if __name__ == '__main__':
    unittest.main()