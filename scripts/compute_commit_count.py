import pandas as pd
from pathlib import Path
INP=Path("data/intermediate/version_hist.csv")
OUT=Path("data/intermediate/version_history_final.csv")
df=pd.read_csv(INP)
df["commit_count"]=df.groupby(["repo_name","file_name"])["commit_hash"].transform("nunique")
df.to_csv(OUT,index=False)
print("saved")