import pandas as pd
import os
df = pd.read_csv('./road_features1.csv')
files = df["test_id"]
files = [i.split("\\")[-1] for i in files]
os.mkdir("./unique")
for i in files:
    os.rename(i,"./unique/{}".format(i))

