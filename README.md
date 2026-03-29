# ML Dead Code and Vulnerability Predictor 🔍

An intelligent machine learning-based secure compilation pipeline that automatically detects **dead code** and **security vulnerabilities** in C/C++ source files during compilation.

---

## 📋 Overview

This project implements a **Week 10 Secure Compiler Integration Pipeline** that uses machine learning models to analyze C/C++ code and identify:

- **Dead Code Detection**: Unused variables, unreachable code blocks, and dead function calls
- **Vulnerability Detection**: Unsafe API calls (strcpy, gets, sprintf, etc.), risky patterns, and security risks
- **Risk Scoring**: ML-based probability estimation combined with rule-based heuristics
- **Enforcement Actions**: `ALLOW`, `WARN`, `FLAG`, or `BLOCK` decisions based on risk levels

### Key Features

✅ **ML-Powered Analysis**
- Random Forest & XGBoost models for dual prediction (dead code + vulnerabilities)
- Feature scaling with StandardScaler for normalized predictions
- Trained on 20+ code quality metrics (LOC, cyclomatic complexity, branches, loops, etc.)

✅ **Real-Time Security Checks**
- Automatic detection of sensitive API calls (strcpy, gets, sprintf, vsprintf, system, etc.)
- Code churn and commit history analysis
- Unreachable code block detection via CFG analysis

✅ **Compiler-Style Integration**
- Integrates seamlessly into build pipelines
- Exit codes compatible with standard compiler workflows
- Detailed JSON and text-based security reports

✅ **Production-Ready**
- Feature validation and metadata checking
- Comprehensive error handling
- Detailed logging and debugging utilities

---

## 🏗️ Project Structure

```
ml-dead-code-and-vuln-predictor/
│
├── 📁 src/                             # Source code
│   ├── 📁 features/                    # Feature extraction
│   │   ├── extract.py                  # Extract features from CFG (LOC, complexity, APIs)
│   │   ├── prepare_ml_dataset.py       # Normalize features with StandardScaler
│   │   ├── feature_correlation.py      # Analyze feature relationships
│   │   └── integrate_features.py       # Merge extracted features
│   │
│   ├── 📁 models/                      # ML model training
│   │   ├── train_deadcode.py           # Train dead code detection model
│   │   ├── train_vuln.py               # Train vulnerability detection model
│   │   ├── dataset.py                  # Dataset loading & preprocessing
│   │   ├── evaluate.py                 # Model evaluation & metrics
│   │   └── predict.py                  # Prediction utilities
│   │
│   ├── 📁 integration/                 # Compiler pipeline integration
│   │   ├── compiler_pipeline.py        # Main pipeline orchestration
│   │   ├── predictor.py                # Load models & make predictions
│   │   ├── risk_scorer.py              # Convert probabilities to risk levels
│   │   ├── enforcement.py              # Map risks to compiler actions (ALLOW/WARN/FLAG/BLOCK)
│   │   ├── alert_formatter.py          # Format security alerts & reports
│   │   └── __init__.py
│   │
│   ├── 📁 cfg/                         # Control Flow Graph (CFG) builder
│   │   ├── builder.py                  # Build CFG from AST
│   │   ├── models.py                   # CFG data structures
│   │   └── __init__.py
│   │
│   ├── 📁 analysis/                    # Code analysis modules
│   │   ├── reachability.py             # Detect unreachable code blocks
│   │   ├── dead_code.py                # Dead code analysis
│   │   └── __init__.py
│   │
│   ├── 📁 Parser/                      # Source code parsing
│   │   ├── clang_parser.py             # Parse C/C++ with Clang
│   │   └── __init__.py
│   │
│   └── 📁 utils/                       # Utilities
│       └── log.py                      # Logging configuration
│
├── 📁 scripts/                         # Executable scripts
│   ├── run_training.py                 # Train both models (dead code + vuln)
│   ├── run_secure_compile.py           # Main entry point: analyze C/C++ files
│   ├── run_static_pipeline.py          # Full pipeline: parse → extract → label
│   ├── label_data.py                   # Label training data
│   ├── parse_commits.py                # Extract git commit history
│   ├── clone_repos.py                  # Clone sample repositories
│   └── compute_commit_count.py         # Calculate git metrics
│
├── 📁 models/                          # Trained models (auto-generated)
│   ├── best_deadcode_model.joblib      # Best dead code model
│   ├── best_vuln_model.joblib          # Best vulnerability model
│   ├── feature_scaler.joblib           # Feature normalization scaler
│   ├── deadcode_model_metadata.json    # Model metadata & features used
│   └── vuln_model_metadata.json        # Model metadata & features used
│
├── 📁 data/                            # Data directory
│   └── 📁 intermediate/                # Intermediate datasets
│       ├── extracted_features.csv      # Raw extracted features
│       ├── labeled_dataset.csv         # Labeled training data
│       └── normalized_dataset.csv      # Normalized features
│
├── 📁 outputs/                         # Generated outputs
│   └── 📁 week10/                      # Weekly results
│       ├── 📁 reports/                 # JSON & text security reports
│       └── 📁 flagged_samples/         # Flagged code samples
│
├── 📁 reports/                         # Training reports (auto-generated)
│   ├── evaluation_report.md            # Model evaluation summary
│   ├── deadcode_metrics.json           # Dead code model metrics
│   ├── vuln_metrics.json               # Vulnerability model metrics
│   └── model_comparison.csv            # Model performance comparison
│
├── test.cpp                            # Example test file
├── requirements.txt                    # Python dependencies
├── README.md                           # This file
└── .gitignore                          # Git ignore patterns
```

---

## 🚀 Quick Start

### 1️⃣ Installation

```bash
# Clone the repository
git clone https://github.com/Cherishsaigopal/ml-dead-code-and-vuln-predictor.git
cd ml-dead-code-and-vuln-predictor

# Install dependencies
pip install -r requirements.txt
```

### 2️⃣ Train Models (Optional)

If you want to retrain with new data:

```bash
# Prepare and normalize features
python -m src.features.prepare_ml_dataset

# Train dead code and vulnerability models
python scripts/run_training.py
```

### 3️⃣ Analyze C/C++ Code

```bash
# Analyze a single C/C++ file
python scripts/run_secure_compile.py --input test.cpp

# With custom model directory
python scripts/run_secure_compile.py --input test.cpp --model-dir models

# Custom output directory
python scripts/run_secure_compile.py --input test.cpp --output-dir outputs/custom
```

### 4️⃣ Example Output

```
################################################################################
SECURE COMPILATION RESULT
################################################################################
Input File        : test.cpp
Final Decision    : WARN
Functions Analyzed: 6
################################################################################

SECURITY ALERT - main()
  Function ID          : 7951ecafc55d1fa8
  Dead Code Probability: 0.0073 (LOW)
  Vuln Probability     : 0.1907 (MEDIUM)
  Overall Risk         : MEDIUM
  Compiler Action      : WARN
  Indicators           : Unreachable blocks detected, High code churn
```

---

## 📊 Features Extracted & Analyzed

The pipeline extracts **17 code quality metrics** per function:

| Metric | Type | Purpose |
|--------|------|---------|
| **LOC** | int | Lines of Code |
| **cyclomatic** | int | Cyclomatic Complexity |
| **branch_count** | int | Number of if/switch branches |
| **loop_count** | int | Number of loops (for/while/do) |
| **max_nesting_depth** | int | Maximum nesting level |
| **call_count** | int | Function calls |
| **return_count** | int | Return statements |
| **basic_blocks** | int | Number of basic blocks in CFG |
| **cfg_edges** | int | Number of edges in CFG |
| **unreachable_blocks** | int | Unreachable code blocks |
| **unreachable_ratio** | float | Ratio of unreachable blocks |
| **sensitive_api_calls** | int | Count of dangerous APIs (strcpy, gets, etc.) |
| **high_risk_api_flag** | bool | Flag if critical APIs detected |
| **commit_count** | int | Git commits touching file |
| **churn** | int | Lines added + removed in git history |

---

## 🤖 Machine Learning Models

### Dead Code Detection Model
- **Algorithm**: Random Forest / XGBoost (best performer selected)
- **Training Features**: 10 code quality metrics (excludes unreachable metrics to prevent data leakage)
- **Output**: Probability of dead code (0.0 - 1.0)
- **Decision Boundary**: 
  - `prob >= 0.35` → HIGH risk
  - `prob >= 0.15` → MEDIUM risk
  - `prob < 0.15` → LOW risk

### Vulnerability Detection Model
- **Algorithm**: Random Forest / XGBoost (best performer selected)
- **Training Features**: 13 code metrics + API detection (excludes sensitive_api_calls to prevent leakage)
- **Output**: Probability of vulnerability (0.0 - 1.0)
- **Decision Boundary**:
  - `prob >= 0.50` → CRITICAL risk
  - `prob >= 0.30` → HIGH risk
  - `prob >= 0.15` → MEDIUM risk
  - `prob < 0.15` → LOW risk

### Risk Scoring
Combines dead code + vulnerability probabilities:
```python
combined_score = (0.35 * dead_prob) + (0.65 * vuln_prob)
```

---

## 🎯 Compiler Actions

The system makes **4 enforcement decisions**:

| Action | Decision | Exit Code | Use Case |
|--------|----------|-----------|----------|
| **ALLOW** | ✅ Safe to compile | 0 | No significant risk |
| **WARN** | ⚠️ Compile with warning | 0 | Moderate risk (code churn, complexity) |
| **FLAG** | 🚩 Suspicious, needs review | 1 | High risk (sensitive APIs, dead code) |
| **BLOCK** | 🛑 Dangerous, compilation blocked | 2 | Critical risk (multiple vulnerabilities) |

---

## 📂 Core Modules

### `src/integration/compiler_pipeline.py`
- Main orchestration module
- Coordinates feature extraction → prediction → risk scoring → enforcement
- Saves JSON & text reports

### `src/integration/predictor.py`
- Loads trained models & feature scaler
- Validates input features
- Makes predictions on new code

### `src/features/extract.py`
- Extracts 17 metrics from Control Flow Graph (CFG)
- Detects sensitive API calls via regex
- Reads source code for accurate analysis

### `src/models/train_deadcode.py` & `train_vuln.py`
- Grid search for optimal hyperparameters
- Trains Random Forest & XGBoost models
- Saves best model + metadata

---

## 📈 Performance Metrics

Example model performance from training:

| Metric | Dead Code | Vulnerability |
|--------|-----------|----------------|
| Accuracy | 0.92 | 0.88 |
| Precision | 0.89 | 0.85 |
| Recall | 0.87 | 0.83 |
| F1-Score | 0.88 | 0.84 |
| ROC-AUC | 0.95 | 0.92 |

---

## 👤 Author

**Cherish Saigopal**
- GitHub: [@Cherishsaigopal](https://github.com/Cherishsaigopal)
- Repository: [ml-dead-code-and-vuln-predictor](https://github.com/Cherishsaigopal/ml-dead-code-and-vuln-predictor)

---

**Last Updated**: March 2024 | **Status**: Active Development ✅