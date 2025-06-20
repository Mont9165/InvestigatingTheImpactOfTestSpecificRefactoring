from testsmell_data_loader import load_testsmell_data
from testsmell_diff_calculator import calculate_diff, save_diff_csv

def main():
    # ファイルレベル
    file_pairs = load_testsmell_data(level="file")
    file_diff_results = [calculate_diff(pair) for pair in file_pairs]
    save_diff_csv(file_diff_results, "testsmell_diff_result_file.csv")

    # メソッドレベル
    method_pairs = load_testsmell_data(level="method")
    method_diff_results = [calculate_diff(pair) for pair in method_pairs]
    save_diff_csv(method_diff_results, "testsmell_diff_result_method.csv")

if __name__ == "__main__":
    main()