import pandas as pd
import json

def write_csv(rows, path):
    """
    Write a list of dicts or a pandas DataFrame to a CSV file.
    """
    if not isinstance(rows, pd.DataFrame):
        df = pd.DataFrame(rows)
    else:
        df = rows
    df.to_csv(path, index=False, encoding="utf-8-sig")

def write_json(obj, path):
    """
    Write a list of dicts to a JSON file.
    """
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2) 