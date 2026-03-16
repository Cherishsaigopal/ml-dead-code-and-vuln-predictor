from __future__ import annotations

import subprocess
import sys


def run_cmd(cmd: list[str]) -> None:
    print("[RUN]", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    dataset_path = "data/intermediate/normalized_dataset.csv"

    run_cmd([
        sys.executable,
        "-m", "src.models.train_deadcode",
        "--input", dataset_path,
        "--models_dir", "models",
        "--reports_dir", "reports",
    ])

    run_cmd([
        sys.executable,
        "-m", "src.models.train_vuln",
        "--input", dataset_path,
        "--models_dir", "models",
        "--reports_dir", "reports",
    ])

    print("[DONE] Week 9 training pipeline completed.")


if __name__ == "__main__":
    main()