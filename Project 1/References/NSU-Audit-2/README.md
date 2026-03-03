# NSU Audit System

A powerful, modular CLI toolset designed to audit academic transcripts for North South University (NSU) students, specifically tailored for CSE and BBA (Curriculum 143) programs.

## 🚀 Overview

The system is divided into **Levels**, allowing you to perform specific checks or generate a unified "Pro" report. 

- **Level 1**: Credit Tallying (Attempted vs. Earned).
- **Level 2**: CGPA & Academic Standing (Probation Phases P1, P2, Dismissal).
- **Level 3**: Graduation Audit & Eligibility (Course Deficiencies).
- **Audit Core**: Unified reporting with a prioritized "Path to Graduation" Roadmap.

## 🛠️ Installation

1.  **Clone the Repository**:
    ```bash
    git clone <your-repo-url>
    cd "NSU Audit 2"
    ```
2.  **Install Dependencies**:
    ```bash
    pip install colorama
    ```

## 📖 Usage Tutorial

### 1. The Unified Audit (Recommended)
This is the main tool. It automatically detects BBA concentrations and generates a full roadmap.

*   **Quick Summary**:
    ```bash
    python audit.py transcripts/student_sample.csv BBA --normal-report
    ```
*   **Full Detailed Report**:
    ```bash
    python audit.py transcripts/student_sample.csv CSE --full-report
    ```

### 2. Level 1 — Credits Only
Use this to check exactly how many credits a student has earned without seeing GPA or graduation status.
```bash
python level_1.py test_transcripts/BBA_FIN_eligible.csv
```

### 3. Level 2 — CGPA & Probation
Use this to calculate a student's standing. It tracks **consecutive probation semesters** (P1, P2) and warns about Dismissal risk.
```bash
python level_2.py test_transcripts/BBA_probation_P2.csv BBA
```

### 4. Level 3 — Audit & Deficiencies
Use this to see exactly which courses are missing from the curriculum.
```bash
python level_3.py test_transcripts/CSE_eligible.csv CSE
```

---

## ✨ Advanced Features

### 🏢 Undeclared Major Mode (BBA)
If a BBA student hasn't declared a major, run the audit without a concentration flag. The tool will:
- Label them as `[UNDECLARED]`.
- Perform a baseline audit of School Core, BBA Core, and GED.
- Alert the student if they have passed **60+ credits** and must declare urgently.

### 📉 Probation Phase Tracking
The system accurately follows NSU policy (Revised Spring 2017):
- **P1**: First semester below 2.0 CGPA.
- **P2**: Second consecutive semester below 2.0.
- **Dismissal**: Third consecutive semester below 2.0.
*The tool looks back at the entire chronological transcript to identify these phases.*

### 🔍 Auto-Concentration Detection
For BBA students, the tool can guess your major (FIN, MKT, ACT, etc.) if the filename includes the code (e.g., `student_FIN_trans.csv`).

## 📊 Transcript format
Ensure your CSV follows this structure:
`course_code, course_name, credits, grade, semester`

Example:
`CSE115, Programming Language I, 3, A, Spring2022`

---
*Developed for North South University Academic Auditing.*
