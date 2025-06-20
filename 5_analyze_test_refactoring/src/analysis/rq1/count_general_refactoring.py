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
REFACTORING_DATA_PATH = os.path.join(PWD, "5_analyze_test_refactoring", "src", "analysis", "rq1", "input", "refactorings_output.csv")

# 出力ファイルのパス
OUTPUT_DIR = os.path.join(PWD, "5_analyze_test_refactoring", "src", "analysis", "rq1", "output")
OUTPUT_COUNTS_PATH = os.path.join(OUTPUT_DIR, "general_refactoring_counts.csv")
OUTPUT_PER_COMMIT_PATH = os.path.join(OUTPUT_DIR, "general_refactoring_per_commit.csv")
OUTPUT_SUMMARY_PATH = os.path.join(OUTPUT_DIR, "general_refactoring_summary.csv")
OUTPUT_ALL_COMMITS_PATH = os.path.join(OUTPUT_DIR, "all_commits_refactoring.csv")

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
    
    # refactoring_hashで重複を排除
    unique_refactorings = sample_refactorings.drop_duplicates(subset=['refactoring_commit_id', 'refactoring_hash'])
    
    # リファクタリングタイプごとの集計
    refactoring_counts = unique_refactorings['refactoring_name'].value_counts().reset_index()
    refactoring_counts.columns = ['refactoring_type', 'count']
    
    # コミットごとのリファクタリング数を集計
    refactoring_per_commit = unique_refactorings.groupby('refactoring_commit_id').size().reset_index()
    refactoring_per_commit.columns = ['commit_id', 'refactoring_count']
    
    # すべてのサンプルコミットに対してリファクタリング数を集計（0を含む）
    all_commits_refactoring = pd.DataFrame({'commit_id': list(sample_hashes)})
    all_commits_refactoring = all_commits_refactoring.merge(
        refactoring_per_commit,
        on='commit_id',
        how='left'
    ).fillna(0)
    all_commits_refactoring['refactoring_count'] = all_commits_refactoring['refactoring_count'].astype(int)
    
    # 基本統計情報の作成
    summary_data = {
        'metric': ['総リファクタリング数（重複排除後）', 'リファクタリングを含むコミット数', 'リファクタリングタイプ数'],
        'value': [len(sample_refactorings), len(unique_refactorings), len(refactoring_per_commit), len(refactoring_counts)]
    }
    summary_df = pd.DataFrame(summary_data)
    
    # 結果の出力
    refactoring_counts.to_csv(OUTPUT_COUNTS_PATH, index=False)
    refactoring_per_commit.to_csv(OUTPUT_PER_COMMIT_PATH, index=False)
    summary_df.to_csv(OUTPUT_SUMMARY_PATH, index=False)
    all_commits_refactoring.to_csv(OUTPUT_ALL_COMMITS_PATH, index=False)
    
    # 基本統計情報の表示
    print(f"総リファクタリング数（重複排除前）: {len(sample_refactorings)}")
    print(f"総リファクタリング数（重複排除後）: {len(unique_refactorings)}")
    print(f"リファクタリングを含むコミット数: {len(refactoring_per_commit)}")
    print(f"リファクタリングタイプ数: {len(refactoring_counts)}")
    
    # リファクタリングタイプの一覧を表示
    print("\nリファクタリングタイプ一覧:")
    for _, row in refactoring_counts.iterrows():
        print(f"{row['refactoring_type']}: {row['count']}")
    
    # リファクタリング数の分布を表示
    print("\nリファクタリング数の分布:")
    distribution = all_commits_refactoring['refactoring_count'].value_counts().sort_index()
    for count, num_commits in distribution.items():
        print(f"{count}回のリファクタリング: {num_commits}コミット")

if __name__ == "__main__":
    main()