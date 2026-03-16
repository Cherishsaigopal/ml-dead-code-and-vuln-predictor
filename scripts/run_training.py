from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def run_cmd(cmd: list[str]) -> None:
    print("[RUN]", " ".join(cmd))
    subprocess.run(cmd, check=True)


def main() -> None:
    dataset_path = "data/intermediate/normalized_dataset.csv"
    reports_dir = Path("reports")
    report_file = reports_dir / "evaluation_report.md"

    reports_dir.mkdir(parents=True, exist_ok=True)

    if report_file.exists():
        report_file.unlink()
        print(f"[INFO] Removed old report: {report_file}")

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