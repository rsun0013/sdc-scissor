import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from scipy import stats
import numpy as np
df = pd.read_csv('./road_features.csv')

safety = df['safety']
columns = list(df.columns)
print(columns)
columns.remove('safety')
columns.remove('test_duration')
columns.remove('test_id')
df = df.drop(columns=['safety','test_duration','test_id'])
#print(df.to_string())

#indexing = (np.abs(stats.zscore(df)) < 3).all(axis=1)
#df = df[indexing]
#safety = safety[indexing]

#print(df.to_string())
df[columns] = MinMaxScaler().fit_transform(df[columns])
df = df.add_prefix("feature_")
#df_out['safety'] = list(safety)
df['algo_safety'] = [0 if i == 'FAIL' else 1 for i in list(safety)]
corrmat = df.corr()
corrfeatures = {}
uncorr = set()
corr = set()

for i in range(len(corrmat)-1):# this for loop from open solurce
    for j in range(i):
        if abs(corrmat.iloc[i,j]) > 0.7:
            print(corrmat.columns[i],corrmat.columns[j])
            try:
                corrfeatures[corrmat.columns[i]] += 1
            except:
                corrfeatures[corrmat.columns[i]] = 1
            try:
                corrfeatures[corrmat.columns[j]] += 1
            except:
                corrfeatures[corrmat.columns[j]] = 1
for i in range(len(corrmat)-1):# this for loop from open solurce
    for j in range(i):
        if abs(corrmat.iloc[i,j]) > 0.7:
            if corrfeatures[corrmat.columns[i]] > corrfeatures[corrmat.columns[j]]:
                corr.add(corrmat.columns[i])
            else:
                corr.add(corrmat.columns[j])
i += 1
#print(corrmat.columns)
for j in range(i):
    if abs(corrmat.iloc[i, j]) < 0.2:
        uncorr.add(corrmat.columns[j])
dropcols = list(uncorr.union(corr))
#dropcols.remove("feature_uturns")
df = df.drop(columns=dropcols)
try:
    df = df.drop(columns=['feature_Unnamed: 0'])
except:
    pass
df = df[~df.duplicated()]


print(df.columns)
print(corr)
print(uncorr)
print(df.head())
df.to_csv('processed_features1.csv')
