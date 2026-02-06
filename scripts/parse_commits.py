import os
import csv
from pathlib import Path
from pydriller import Repository
REPOS_DIR=Path("data/raw/repos")
OUT_DIR=Path("data/intermediate")
OUT_FILE=OUT_DIR/"version_hist.csv"
OUT_DIR.mkdir(parents=True,exist_ok=True)
header=[
    "repo_name",
    "commit_hash",
    "author",
    "commit_date",
    "commit_message",
    "file_name",
    "lines_added",
    "lines_deleted",
    "churn"
]
with open(OUT_FILE,"w",newline="",encoding="utf-8") as f:
    writer=csv.writer(f)
    writer.writerow(header)
    for repo_name in os.listdir(REPOS_DIR):
        repo_path=REPOS_DIR/repo_name
        if not repo_path.is_dir():
            continue
        print(f"[MINE] {repo_name}")
        for commit in Repository(str(repo_path)).traverse_commits():
            msg=commit.msg.strip().replace("\n"," ")
            for modf in commit.modified_files:
                added=modf.added_lines or 0
                deleted=modf.deleted_lines or 0
                churn=added+deleted
                writer.writerow([
                    repo_name,
                    commit.hash,
                    commit.author.name if commit .author else "",
                    commit.author_date,
                    msg,
                    modf.filename,
                    added,
                    deleted,
                    churn
                ])
print("completed...")