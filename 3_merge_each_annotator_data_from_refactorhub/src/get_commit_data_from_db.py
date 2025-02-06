import pandas as pd
from sqlalchemy import create_engine

# データベース接続設定
DATABASE_URL = "postgresql://rhuser:rhpass@localhost:5434/refactorhub"

# 必要なカラムを取得するSQLクエリ
query = """
SELECT
    id,
    experiment_id,
    order_index,
    owner,
    repository,
    sha,
    parent_sha,
    url
FROM commits;
"""

try:
    # エンジンを作成
    engine = create_engine(DATABASE_URL)

    # データベース接続を安全に管理
    with engine.connect() as connection:
        # クエリを実行してデータを取得
        commits_df = pd.read_sql_query(query, connection)

        # データの表示
        print("データ取得成功:")
        print(commits_df)

        # 必要に応じてデータをCSVファイルとして保存
        commits_df.to_csv('sampling_commits_data_from_db.csv', index=False)
        print("データが 'sampling_commits_data_from_db.csv' に保存されました。")

except Exception as e:
    print(f"エラーが発生しました: {e}")

finally:
    # エンジンを明示的に破棄
    if 'engine' in locals():
        engine.dispose()
        print("データベース接続を閉じました。")