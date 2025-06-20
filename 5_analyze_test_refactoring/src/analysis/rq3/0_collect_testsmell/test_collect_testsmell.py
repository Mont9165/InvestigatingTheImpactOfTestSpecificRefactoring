import unittest
from unittest.mock import patch, MagicMock, call
import pandas as pd
import platform
import logging

# テスト対象のスクリプトをインポート
import collect_testsmell

# テスト中はログ出力を抑制する
logging.disable(logging.CRITICAL)

class TestCollectTestSmell(unittest.TestCase):
    """collect_testsmell.pyのユニットテスト"""

    @patch('platform.system')
    def test_get_default_base_dir(self, mock_system):
        """OSに応じてデフォルトのBASE_DIRが正しく返されることをテストする"""
        # macOSの場合
        mock_system.return_value = "Darwin"
        self.assertEqual(collect_testsmell.get_default_base_dir(), "/Users/horikawa/Dev/Research-repo/InvestigatingTheImpactOfTestSpecificRefactoring")

        # Linux/その他の場合
        mock_system.return_value = "Linux"
        self.assertEqual(collect_testsmell.get_default_base_dir(), "/work/kosei-ho/InvestigatingTheImpactOfTestSpecificRefactoring")

    def test_get_parent_commit_id(self):
        """親コミットIDの取得ロジックをテストする"""
        data = {'commit_id': ['abc', 'def'], 'parent_commit_id': ['123', '456']}
        df_commits = pd.DataFrame(data)

        # commit_idが存在する場合
        self.assertEqual(collect_testsmell.get_parent_commit_id(df_commits, 'abc'), '123')

        # commit_idが存在しない場合
        self.assertIsNone(collect_testsmell.get_parent_commit_id(df_commits, 'xyz'))

    @patch('os.path.isfile')
    def test_already_exists(self, mock_isfile):
        """出力ファイルの存在確認ロジックをテストする"""
        commit_url = "https://github.com/owner/repo/commit/abcde"
        test_smell_dir = "/path/to/test_smell_dir"

        # 2つのファイルが両方存在する場合
        mock_isfile.return_value = True
        self.assertTrue(collect_testsmell.already_exists(commit_url, test_smell_dir))
        # isfileが2回呼ばれることを確認
        self.assertEqual(mock_isfile.call_count, 2)
        
        mock_isfile.reset_mock()

        # ファイルが存在しない場合
        mock_isfile.return_value = False
        self.assertFalse(collect_testsmell.already_exists(commit_url, test_smell_dir))

    @patch('collect_testsmell.already_exists')
    @patch('subprocess.run')
    def test_collect_testsmell_skips_if_exists(self, mock_subprocess_run, mock_already_exists):
        """ファイルが既に存在する場合に処理をスキップすることをテストする"""
        mock_already_exists.return_value = True
        collect_testsmell.collect_testsmell("some_url", "jar_path", "test_smell_dir")
        mock_subprocess_run.assert_not_called()

    @patch('collect_testsmell.already_exists')
    @patch('subprocess.run')
    def test_collect_testsmell_runs_if_not_exists(self, mock_subprocess_run, mock_already_exists):
        """ファイルが存在しない場合にjarを実行することをテストする"""
        mock_already_exists.return_value = False
        commit_url = "https://github.com/owner/repo/commit/abcde"
        jar_path = "path/to/TestSmellDetector.jar"
        test_smell_dir = "path/to/detector"
        
        collect_testsmell.collect_testsmell(commit_url, jar_path, test_smell_dir)
        
        mock_subprocess_run.assert_called_once_with(
            ["java", "-jar", jar_path, commit_url],
            capture_output=True,
            text=True,
            check=True,
            cwd=test_smell_dir
        )

    @patch('collect_testsmell.get_parent_commit_id')
    @patch('collect_testsmell.collect_testsmell')
    def test_process_commit_success(self, mock_collect_testsmell, mock_get_parent_id):
        """親コミットが見つかった場合に、対象・親の両方でスメル検出が呼ばれることをテストする"""
        mock_get_parent_id.return_value = "parent123"
        commit_url = "https://github.com/owner/repo/commit/child456"
        df_commits = pd.DataFrame({'commit_id':[]}) # dummy
        jar_path = "path/to/jar"
        test_smell_dir = "path/to/dir"
        
        collect_testsmell.process_commit(commit_url, df_commits, jar_path, test_smell_dir)
        
        mock_get_parent_id.assert_called_once_with(df_commits, "child456")
        
        parent_commit_url = "https://github.com/owner/repo/commit/parent123"
        expected_calls = [
            call(commit_url, jar_path, test_smell_dir),
            call(parent_commit_url, jar_path, test_smell_dir)
        ]
        mock_collect_testsmell.assert_has_calls(expected_calls, any_order=False)

    @patch('collect_testsmell.get_parent_commit_id')
    @patch('collect_testsmell.collect_testsmell')
    def test_process_commit_no_parent(self, mock_collect_testsmell, mock_get_parent_id):
        """親コミットが見つからない場合に、スメル検出が呼ばれないことをテストする"""
        mock_get_parent_id.return_value = None
        commit_url = "https://github.com/owner/repo/commit/child456"
        
        collect_testsmell.process_commit(commit_url, pd.DataFrame(), "jar", "dir")
        
        mock_collect_testsmell.assert_not_called()

if __name__ == '__main__':
    unittest.main(verbosity=2)