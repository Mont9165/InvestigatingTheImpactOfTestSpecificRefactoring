import pandas as pd

df1 = pd.read_csv('../../../2_sampling_test_refactor_commits/result/sampling_test_commits.csv')
df2 = pd.read_csv('../../result/not_use/annotation_2025-01-16.csv')

# merged_df = pd.merge(df2, df1, left_on="URL", right_on="commit_url", how="inner")

# 比較を行い、一致した場合にインデックスを取得
df2['Index'] = df2['URL'].apply(lambda url: df1.index[df1['commit_url'] == url].tolist())

df2.to_csv('../result/annotation_2025-01-16_with_index.csv', index=False)