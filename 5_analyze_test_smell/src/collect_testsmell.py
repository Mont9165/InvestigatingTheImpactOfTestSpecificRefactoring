from sqlalchemy import create_engine, text
import pandas as pd
import json
from datetime import datetime

DATABASE_URL = "postgresql://rhuser:rhpass@localhost:5435/refactorhub"
engine = create_engine(DATABASE_URL)


def get_refactoring_data():
    query = text("""
        SELECT
            cm.id AS commit_id,
            cm.experiment_id AS experiment_id,
            e.title AS experiment_title,
            cm.order_index AS order_index,
            c.type_name,
            c.description,
            c.parameter_data,
            c.snapshot_id,
            u.name AS annotator_name,
            cm.url
        FROM changes c
        JOIN snapshots s ON c.snapshot_id = s.id
        JOIN annotations a ON s.annotation_id = a.id
        JOIN commits cm ON a.commit_id = cm.id
        JOIN experiments e ON cm.experiment_id = e.id
        JOIN users u ON a.owner_id = u.id
        WHERE e.title IN ('test-refactoring-1', 'test-refactoring-2')
        AND c.type_name != 'Non-Refactoring'
    """)

    with engine.connect() as connection:
        result = connection.execute(query)
    return pd.DataFrame(result.fetchall(), columns=result.keys())


def process_parameter_data(parameter_data):
    # Process the data as needed
    # For example, print the keys and values
    for key, value in parameter_data.items():
        print(f"{key}: {value}")
        for k, v in value.items():
            print(f"  {k}: {v}")


def main():
    df = get_refactoring_data()
    grouped = df.groupby('url')

    for url, group in grouped:
        print(f"Processing URL: {url}")
        for index, row in group.iterrows():
            print(f"Type Name: {row['type_name']}")
            process_parameter_data(row['parameter_data'])
        exit(1)


if __name__ == '__main__':
    main()