import subprocess
from pathlib import Path
REPOS_FILE="config/repos.txt"
OUTPUT_DIR=Path("data/raw/repos")
OUTPUT_DIR.mkdir(parents=True,exist_ok=True)
with open(REPOS_FILE,"r",encoding="utf-8") as f:
    repo_urls=[
        line.strip()
        for line in f
        if line.strip() and not line.strip().startswith("#")
    ]
if not repo_urls:
    raise ValueError("repos.txt is empty add github repos urls")
for url in repo_urls:
    repo_name=url.rstrip("/").split("/")[-1].replace(".git","")
    repo_path=OUTPUT_DIR/repo_name
    if repo_path.exists():
        print(f"[SKIP] {repo_name} already cloned")
        continue
    print(f"[CLONE] {url}")
    subprocess.run(
        ["git","clone",url,str(repo_path)],
        check=True
    )
print("completed...")