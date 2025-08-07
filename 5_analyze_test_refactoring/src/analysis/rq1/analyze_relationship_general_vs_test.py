import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib_venn import venn2
import os
from typing import Dict, Any

class Config:
    """設定を管理するクラス"""
    # スクリプトの場所を基準とした相対パスに変更
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "output") # 仮のデータディレクトリ名

    TEST_REFACTORING_PATH = os.path.join(DATA_DIR, "test", "all_commits_test_refactoring.csv")
    GENERAL_REFACTORING_PATH = os.path.join(DATA_DIR, "general", "all_commits_refactoring.csv")
    TEST_TYPE_PATH = os.path.join(DATA_DIR, "test", "test_refactoring_counts.csv")
    GENERAL_TYPE_PATH = os.path.join(DATA_DIR, "general", "general_refactoring_counts.csv")

    RESULTS_DIR = os.path.join(BASE_DIR, "results")
    REPORT_PATH = os.path.join(RESULTS_DIR, "analysis_report.txt")

    TOP_N_TYPES = 10

class RefactoringAnalyzer:
    """
    テストリファクタリングと一般リファクタリングの分析を行うクラス
    """
    def __init__(self, config: Config):
        self.config = config
        self.results: Dict[str, Any] = {}
        os.makedirs(self.config.RESULTS_DIR, exist_ok=True)
        self._load_and_preprocess_data()

    def _load_and_preprocess_data(self):
        """データの読み込みと前処理を一度に行う"""
        try:
            test_df = pd.read_csv(self.config.TEST_REFACTORING_PATH)
            general_df = pd.read_csv(self.config.GENERAL_REFACTORING_PATH)
            self.test_types_df = pd.read_csv(self.config.TEST_TYPE_PATH).rename(columns={'type_name': 'refactoring_type'})
            self.general_types_df = pd.read_csv(self.config.GENERAL_TYPE_PATH)

            # commit_idの重複をチェック (ここでは警告のみ)
            if test_df['commit_id'].duplicated().any() or general_df['commit_id'].duplicated().any():
                print("Warning: Duplicate commit_ids found. Aggregating counts.")
                test_df = test_df.groupby('commit_id').sum().reset_index()
                general_df = general_df.groupby('commit_id').sum().reset_index()

            # データフレームをマージしてインスタンス変数として保持
            self.merged_df = pd.merge(test_df, general_df, on='commit_id', suffixes=('_test', '_general'))

        except FileNotFoundError as e:
            print(f"Error: Data file not found. {e}")
            raise

    def run_analysis(self):
        """全ての分析を実行し、結果をself.resultsに格納する"""
        self._analyze_prevalence()
        self._analyze_statistics()
        self._analyze_coexistence()
        self._analyze_correlation()
        self._analyze_types()
        print("Analysis complete.")

    def _analyze_prevalence(self):
        total_commits = len(self.merged_df)
        self.results['prevalence'] = {
            'total_commits': total_commits,
            'test_refactoring_commits': len(self.merged_df[self.merged_df['refactoring_count_test'] > 0]),
            'general_refactoring_commits': len(self.merged_df[self.merged_df['refactoring_count_general'] > 0]),
            'test_ratio': len(self.merged_df[self.merged_df['refactoring_count_test'] > 0]) / total_commits,
            'general_ratio': len(self.merged_df[self.merged_df['refactoring_count_general'] > 0]) / total_commits,
        }

    def _analyze_statistics(self):
        self.results['statistics'] = {
            'test': self.merged_df['refactoring_count_test'].describe().to_dict(),
            'general': self.merged_df['refactoring_count_general'].describe().to_dict()
        }

    def _analyze_coexistence(self):
        test_exists = self.merged_df['refactoring_count_test'] > 0
        general_exists = self.merged_df['refactoring_count_general'] > 0
        total_commits = len(self.merged_df)

        self.results['coexistence'] = {
            'test_only': (test_exists & ~general_exists).sum(),
            'general_only': (~test_exists & general_exists).sum(),
            'both': (test_exists & general_exists).sum(),
            'neither': (~test_exists & ~general_exists).sum(),
            'total': total_commits
        }

    def _analyze_correlation(self):
        test_commits = self.merged_df[self.merged_df['refactoring_count_test'] > 0]
        general_commits = self.merged_df[self.merged_df['refactoring_count_general'] > 0]

        self.results['correlation'] = {
            'spearman_corr': self.merged_df['refactoring_count_test'].corr(self.merged_df['refactoring_count_general'], method='spearman'),
            'general_given_test_prob': len(test_commits[test_commits['refactoring_count_general'] > 0]) / len(test_commits) if len(test_commits) > 0 else 0,
            'test_given_general_prob': len(general_commits[general_commits['refactoring_count_test'] > 0]) / len(general_commits) if len(general_commits) > 0 else 0,
        }

    def _analyze_types(self):
        self.results['types'] = {
            'test_type_count': len(self.test_types_df),
            'general_type_count': len(self.general_types_df),
            'top_test_types': self.test_types_df.nlargest(self.config.TOP_N_TYPES, 'count'),
            'top_general_types': self.general_types_df.nlargest(self.config.TOP_N_TYPES, 'count')
        }

    def generate_visualizations(self):
        """全ての可視化を実行し、ファイルに保存する"""
        self._visualize_distributions()
        self._visualize_coexistence()
        self._visualize_venn_diagram()
        self._visualize_types()
        print(f"Visualizations saved to {self.config.RESULTS_DIR}")

    def _visualize_distributions(self):
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        sns.histplot(self.merged_df['refactoring_count_test'], bins=50, ax=axes[0], kde=True, color='skyblue').set_title('Distribution of Test Refactoring Counts')
        sns.histplot(self.merged_df['refactoring_count_general'], bins=50, ax=axes[1], kde=True, color='lightcoral').set_title('Distribution of General Refactoring Counts')
        for ax in axes:
            ax.set_xlabel('Number of Refactorings per Commit')
            ax.set_ylabel('Frequency')
            ax.set_yscale('log') # データが歪んでいるため対数スケールを推奨
        plt.tight_layout()
        plt.savefig(os.path.join(self.config.RESULTS_DIR, "refactoring_distributions.png"))
        plt.close()

    def _visualize_coexistence(self):
        coexistence = self.results['coexistence']
        labels = ['Test Only', 'General Only', 'Both', 'Neither (False Positive)']
        sizes = [coexistence['test_only'], coexistence['general_only'], coexistence['both'], coexistence['neither']]

        plt.figure(figsize=(10, 7))
        bars = plt.bar(labels, sizes, color=['skyblue', 'lightcoral', 'darkslateblue', 'grey'])
        plt.ylabel('Number of Commits')
        plt.title('Commit Categories by Refactoring Type')
        plt.bar_label(bars)
        plt.savefig(os.path.join(self.config.RESULTS_DIR, "refactoring_coexistence.png"))
        plt.close()

    def _visualize_venn_diagram(self):
        coexistence = self.results['coexistence']
        plt.figure(figsize=(8, 8))
        v = venn2(subsets=(coexistence['test_only'], coexistence['general_only'], coexistence['both']),
                  set_labels=('Test Refactoring', 'General Refactoring'))
        v.get_patch_by_id('10').set_color('skyblue')
        v.get_patch_by_id('01').set_color('lightcoral')
        v.get_patch_by_id('11').set_color('darkslateblue')
        v.get_patch_by_id('11').set_alpha(0.6)
        plt.title(f"Coexistence of Refactoring Types (N={coexistence['total']})\n"
                  f"Commits with No Refactoring: {coexistence['neither']}", fontsize=14)
        plt.savefig(os.path.join(self.config.RESULTS_DIR, "refactoring_venn_diagram.png"))
        plt.close()

    def _visualize_types(self):
        types = self.results['types']
        fig, axes = plt.subplots(1, 2, figsize=(18, 8))
        sns.barplot(data=types['top_test_types'], x='count', y='refactoring_type', ax=axes[0], palette='Blues_r').set_title(f'Top {self.config.TOP_N_TYPES} Test Refactoring Types')
        sns.barplot(data=types['top_general_types'], x='count', y='refactoring_type', ax=axes[1], palette='Reds_r').set_title(f'Top {self.config.TOP_N_TYPES} General Refactoring Types')
        plt.tight_layout()
        plt.savefig(os.path.join(self.config.RESULTS_DIR, "refactoring_types_comparison.png"))
        plt.close()

    def generate_and_save_report(self):
        """分析結果を整形し、コンソールに出力およびファイルに保存する"""
        report_lines = []
        report_lines.append("="*50)
        report_lines.append("Refactoring Analysis Report")
        report_lines.append("="*50)

        # Prevalence
        prevalence = self.results['prevalence']
        report_lines.append("\n## 1. Prevalence of Refactoring in Commits")
        report_lines.append(f"Total commits analyzed: {prevalence['total_commits']}")
        report_lines.append(f"Commits with test refactoring: {prevalence['test_refactoring_commits']} ({prevalence['test_ratio']:.2%})")
        report_lines.append(f"Commits with general refactoring: {prevalence['general_refactoring_commits']} ({prevalence['general_ratio']:.2%})")

        # Statistics
        stats = self.results['statistics']
        report_lines.append("\n## 2. Descriptive Statistics (per commit)")
        report_lines.append(f"Test Refactoring: Mean={stats['test']['mean']:.2f}, Median={stats['test']['50%']:.2f}, Std={stats['test']['std']:.2f}, Max={stats['test']['max']:.0f}")
        report_lines.append(f"General Refactoring: Mean={stats['general']['mean']:.2f}, Median={stats['general']['50%']:.2f}, Std={stats['general']['std']:.2f}, Max={stats['general']['max']:.0f}")

        # Coexistence
        coexistence = self.results['coexistence']
        report_lines.append("\n## 3. Coexistence Analysis")
        report_lines.append(f"Test Only: {coexistence['test_only']} ({coexistence['test_only']/coexistence['total']:.2%})")
        report_lines.append(f"General Only: {coexistence['general_only']} ({coexistence['general_only']/coexistence['total']:.2%})")
        report_lines.append(f"Both: {coexistence['both']} ({coexistence['both']/coexistence['total']:.2%})")
        report_lines.append(f"Neither (False Positive): {coexistence['neither']} ({coexistence['neither']/coexistence['total']:.2%})")

        # Correlation
        correlation = self.results['correlation']
        report_lines.append("\n## 4. Correlation Analysis")
        report_lines.append(f"Spearman's correlation of counts: {correlation['spearman_corr']:.3f}")
        report_lines.append(f"P(General | Test): {correlation['general_given_test_prob']:.2%} (Probability of general refactoring given test refactoring exists)")
        report_lines.append(f"P(Test | General): {correlation['test_given_general_prob']:.2%} (Probability of test refactoring given general refactoring exists)")

        # Types
        types_res = self.results['types']
        report_lines.append("\n## 5. Refactoring Types Analysis")
        report_lines.append(f"Distinct test refactoring types: {types_res['test_type_count']}")
        report_lines.append(f"Distinct general refactoring types: {types_res['general_type_count']}")
        report_lines.append("\nTop 5 Test Refactoring Types:")
        for _, row in types_res['top_test_types'].head(5).iterrows():
            report_lines.append(f"  - {row['refactoring_type']}: {row['count']}")
        report_lines.append("\nTop 5 General Refactoring Types:")
        for _, row in types_res['top_general_types'].head(5).iterrows():
            report_lines.append(f"  - {row['refactoring_type']}: {row['count']}")

        report = "\n".join(report_lines)
        print(report)

        with open(self.config.REPORT_PATH, 'w') as f:
            f.write(report)
        print(f"\nReport saved to {self.config.REPORT_PATH}")


def main():
    """メインの実行関数"""
    try:
        config = Config()
        analyzer = RefactoringAnalyzer(config)
        analyzer.run_analysis()
        analyzer.generate_and_save_report()
        analyzer.generate_visualizations()
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()