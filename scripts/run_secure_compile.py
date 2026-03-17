from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.integration.compiler_pipeline import SecureCompilerPipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Week 10 Secure Compiler Integration Pipeline"
    )
    parser.add_argument("--input", required=True, help="Path to source file to analyze")
    parser.add_argument("--model-dir", default="models", help="Directory containing trained models")
    parser.add_argument("--output-dir", default="outputs/week10", help="Directory to save generated reports")

    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    pipeline = SecureCompilerPipeline(model_dir=args.model_dir)
    result = pipeline.run(str(input_path))
    pipeline.save_reports(result, output_dir=args.output_dir)

    print("\n" + "#" * 80)
    print("SECURE COMPILATION RESULT")
    print("#" * 80)
    print(f"Input File        : {result.file_path}")
    print(f"Final Decision    : {result.file_decision.upper()}")
    print(f"Functions Analyzed: {len(result.prediction_results)}")
    print("#" * 80 + "\n")

    for alert in result.alerts:
        print(alert)
        print()

    if result.file_decision == "block":
        print("[BLOCKED] Compilation stopped due to critical security risk.")
        sys.exit(2)
    elif result.file_decision == "flag":
        print("[FLAGGED] Compilation completed with suspicious code flagged for review.")
        sys.exit(1)
    elif result.file_decision == "warn":
        print("[WARNING] Compilation completed with warnings.")
        sys.exit(0)
    else:
        print("[ALLOW] Compilation completed successfully.")
        sys.exit(0)


if __name__ == "__main__":
    main()