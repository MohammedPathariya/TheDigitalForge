import csv

def read_csv_to_dicts(file_path):
    """
    Read a CSV file and return a list of dictionaries.
    
    Each dictionary corresponds to a row in the CSV file, with the keys being the column headers.

    Args:
    - file_path (str): The path to the CSV file to read.

    Returns:
    - List[dict]: A list of dictionaries representing the rows of the CSV.
    """
    with open(file_path, mode='r', encoding='utf-8') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        return [row for row in csv_reader]