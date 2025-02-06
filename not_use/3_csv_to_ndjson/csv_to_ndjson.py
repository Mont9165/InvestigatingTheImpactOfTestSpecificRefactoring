import csv
import json


def main():
    csv_file = 'input/combined_only_test_commits.csv'
    output_file = 'result/commit_data.ndjson'
    csv_to_ndjson(csv_file, output_file)


def csv_to_ndjson(csv_file, output_file, ndjson=None):
    with open(output_file, 'w', encoding='utf-8') as w_file:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                owner, repository = row[0].split('/')
                sha = row[2]
                ndjson_data = {
                    "sha": sha,
                    "owner": owner,
                    "repository": repository
                }
                w_file.write((json.dumps(ndjson_data)).encode().decode('unicode-escape') + "\n")


if __name__ == '__main__':
    main()
