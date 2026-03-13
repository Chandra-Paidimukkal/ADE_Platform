import pandas as pd


def build_catalog(products):

    df = pd.DataFrame(products)

    df.to_csv("catalog.csv", index=False)

    return "catalog generated"