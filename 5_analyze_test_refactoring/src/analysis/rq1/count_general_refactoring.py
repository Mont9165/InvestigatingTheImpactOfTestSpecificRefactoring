
# 2_sampling_test_refactor_commits/result/sampling_test_commits.csvを読み込み，370サンプルのコミット一覧を取得

# 5_analyze_test_refactoring/src/analysis/rq1/input/refactoring_10000.csv（サンプルデータ）を読み込み，370コミットにて実施されているリファクタリングがあるかどうか分析
# 分析に関しては，370コミットに対して，リファクタリング有無を分析
# また，5_analyze_test_refactoring/src/analysis/rq1/output/test_refactoring_counts.csv，5_analyze_test_refactoring/src/analysis/rq1/output/test_refactoring_per_commit.csvのようにも分析

import pandas as pd
import os

# 現在の作業ディレクトリを基準にパスを設定
PWD = os.getcwd()

# 入力ファイルのパス
SAMPLE_COMMITS_PATH = os.path.join(PWD, "2_sampling_test_refactor_commits", "result", "sampling_test_commits.csv")
REFACTORING_DATA_PATH = os.path.join(PWD, "5_analyze_test_refactoring", "src", "analysis", "rq1", "input", "refactoring_10000.csv")

# 出力ファイルのパス
OUTPUT_DIR = os.path.join(PWD, "5_analyze_test_refactoring", "src", "analysis", "rq1", "output")
OUTPUT_COUNTS_PATH = os.path.join(OUTPUT_DIR, "general_refactoring_counts.csv")
OUTPUT_PER_COMMIT_PATH = os.path.join(OUTPUT_DIR, "general_refactoring_per_commit.csv")

def main():
    # 出力ディレクトリの作成（存在しない場合）
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # サンプルコミットの読み込み
    sample_commits = pd.read_csv(SAMPLE_COMMITS_PATH)
    
    # リファクタリングデータの読み込み
    refactoring_data = pd.read_csv(REFACTORING_DATA_PATH)
    
    # サンプルコミットのハッシュリストを取得
    sample_hashes = set(sample_commits['commit_id'])
    
    # サンプルコミットに関連するリファクタリングを抽出
    sample_refactorings = refactoring_data[refactoring_data['refactoring_commit_id'].isin(sample_hashes)]
    
    # リファクタリングタイプごとの集計
    refactoring_counts = sample_refactorings['refactoring_name'].value_counts().reset_index()
    refactoring_counts.columns = ['refactoring_type', 'count']
    
    # コミットごとのリファクタリング数を集計
    refactoring_per_commit = sample_refactorings.groupby('refactoring_commit_id').size().reset_index()
    refactoring_per_commit.columns = ['commit_id', 'refactoring_count']
    
    # 結果の出力
    refactoring_counts.to_csv(OUTPUT_COUNTS_PATH, index=False)
    refactoring_per_commit.to_csv(OUTPUT_PER_COMMIT_PATH, index=False)
    
    # 基本統計情報の表示
    print(f"総リファクタリング数: {len(sample_refactorings)}")
    print(f"リファクタリングを含むコミット数: {len(refactoring_per_commit)}")
    print(f"リファクタリングタイプ数: {len(refactoring_counts)}")
    
    # リファクタリングタイプの一覧を表示
    print("\nリファクタリングタイプ一覧:")
    for _, row in refactoring_counts.iterrows():
        print(f"{row['refactoring_type']}: {row['count']}")

if __name__ == "__main__":
    main()