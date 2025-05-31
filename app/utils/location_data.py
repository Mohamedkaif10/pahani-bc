import pandas as pd
from collections import defaultdict


def load_location_data(file_path="location.xlsx"):
    df = pd.read_excel(file_path)
    structured_data = defaultdict(lambda: defaultdict(list))

    for _, row in df.iterrows():
        district = row["District Name"].strip()
        mandal = row["Mandal Name"].strip()
        village = row["Village Name"].strip()
        structured_data[district][mandal].append(village)

    return structured_data
