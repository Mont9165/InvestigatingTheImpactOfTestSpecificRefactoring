from sqlalchemy import create_engine, text
import pandas as pd
import json
from datetime import datetime

DATABASE_URL = "postgresql://rhuser:rhpass@localhost:5435/refactorhub"
engine = create_engine(DATABASE_URL)

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
""")

with engine.connect() as connection:
    result = connection.execute(query)
    df = pd.DataFrame(result.fetchall(), columns=result.keys())

def process_parameter_data(parameter_data):
    try:
        if isinstance(parameter_data, str):
            param = json.loads(parameter_data)
        elif isinstance(parameter_data, dict):
            param = parameter_data
        else:
            raise TypeError("Invalid parameter_data format")

        before_elements = next(iter(param.get("before", {}).values()), {}).get("elements", [])
        after_elements = next(iter(param.get("after", {}).values()), {}).get("elements", [])

        before_fragment = before_elements[0] if before_elements else []
        after_fragment = after_elements[0] if after_elements else []
        before_location = {}
        after_location = {}
        if before_elements != [] and before_fragment["location"] is not None:
            before_location = before_fragment["location"]
        if after_elements != [] and after_fragment["location"] is not None:
            after_location = after_fragment["location"]

        return {
            "file_path": before_location.get("path"),
            "start_line_before": before_location.get("range", {}).get("startLine"),
            "end_line_before": before_location.get("range", {}).get("endLine"),
            "start_line_after": after_location.get("range", {}).get("startLine"),
            "end_line_after": after_location.get("range", {}).get("endLine"),
        }
    except (TypeError, json.JSONDecodeError, AttributeError) as e:
        print(f"Error processing parameter_data: {e}")
        return {
            "file_path": None,
            "start_line_before": None,
            "end_line_before": None,
            "start_line_after": None,
            "end_line_after": None,
        }

param_data_df = df["parameter_data"].apply(process_parameter_data).apply(pd.Series)
output_df = pd.concat([
    df[["commit_id", "experiment_id", "experiment_title", "order_index", "url", "type_name", "description", "annotator_name"]],
    param_data_df
], axis=1)

output_df["order_index"] = output_df["order_index"] + 1
output_df.insert(output_df.columns.get_loc("description") + 1, "Memo", "")
output_df.insert(output_df.columns.get_loc("Memo") + 1, "Agreement", "")

output_df = output_df.sort_values(by="order_index").reset_index(drop=True)

output_df.columns = [
    "Commit Id",
    "Experiment Id",
    "Experiment Title",
    "Order Index",
    "URL",
    "Type Name",
    "Description",
    "Memo",
    "Agreement",
    "Annotator Name",
    "File Path",
    "Start Line (Before)",
    "End Line (Before)",
    "Start Line (After)",
    "End Line (After)"
]

current_time = datetime.now()
formatted_time = current_time.strftime("%Y-%m-%d")
titles_to_split = ["test-refactoring-1", "test-refactoring-2"]

for title in titles_to_split:
    subset_df = output_df[output_df["Experiment Title"] == title]
    if not subset_df.empty:
        subset_df = subset_df.drop(columns=["Experiment Title", "Experiment Id", "Commit Id"])
        subset_df = subset_df.sort_values(by="Order Index").reset_index(drop=True)
        output_file = f"../result/annotation_{title}_{formatted_time}.csv"
        subset_df.to_csv(output_file, index=False)
        print(f"データが {output_file} に保存されました。")