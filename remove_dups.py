import pandas as pd
df = pd.read_csv('./road_features.csv')
df = df.drop(columns=['Unnamed: 0'])
columns = list(df.columns)
print(columns)
columns.remove('safety')
columns.remove('test_duration')
columns.remove('test_id')
df = df[~df.duplicated(subset=columns)]
df.to_csv('road_features1.csv')
