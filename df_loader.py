import pathlib
import pandas as pd
# get relative data folder
PATH = pathlib.Path(__file__).parent
DATA_PATH = PATH.joinpath("data").resolve()
df = pd.read_excel(
    DATA_PATH.joinpath("sample_data.xlsx"), index_col='Quarter'
)
print(df)
print(df.transpose())
