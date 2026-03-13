import pandas as pd


def export_excel(data):

    df = pd.DataFrame(data)

    df.to_excel("extracted_specs.xlsx", index=False)