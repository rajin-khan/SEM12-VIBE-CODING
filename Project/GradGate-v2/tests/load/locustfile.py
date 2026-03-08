"""Locust load test for GradGate API.

Run with:
    locust -f tests/load/locustfile.py \
        --headless -u 20 -r 5 \
        --run-time 120s \
        --host http://192.168.54.214:8000 \
        --html tests/load/report.html
"""

import os
import random
from pathlib import Path

from locust import HttpUser, task, between

# Test CSV files (57 total)
TEST_FILES = [
    "tc01_cse_all_pass.csv",
    "tc02_bba_all_pass.csv",
    "tc03_eee_all_pass.csv",
    "tc04_ete_all_pass.csv",
    "tc05_cee_all_pass.csv",
    "tc06_env_all_pass.csv",
    "tc07_eng_all_pass.csv",
    "tc08_eco_all_pass.csv",
    "tc09_cse_extra_credits.csv",
    "tc10_bba_extra_credits.csv",
    "tc11_cse_with_F.csv",
    "tc12_bba_with_F.csv",
    "tc13_cse_with_I.csv",
    "tc14_bba_with_I.csv",
    "tc15_cse_with_W.csv",
    "tc16_bba_with_W.csv",
    "tc17_cse_mixed_FIW.csv",
    "tc18_bba_mixed_FIW.csv",
    "tc19_no_waivers.csv",
    "tc20_eng102_waived.csv",
    "tc21_mat112_waived.csv",
    "tc22_both_waived.csv",
    "tc23_retake_pass.csv",
    "tc24_retake_still_fail.csv",
    "tc25_multiple_retakes.csv",
    "tc26_transfer_T_grade.csv",
    "tc27_non_nsu_courses.csv",
    "tc28_invalid_grades.csv",
    "tc29_empty_transcript.csv",
    "tc30_probation_P1.csv",
    "tc31_probation_P2.csv",
    "tc32_dismissal.csv",
    "tc33_bba_concentration_FIN.csv",
    "tc34_bba_undeclared.csv",
    "tc35_prereq_violation.csv",
    "tc36_zero_credit_labs_only.csv",
    "tc37_high_cgpa_4.0.csv",
    "tc38_borderline_2.0.csv",
    "tc39_malformed_columns.csv",
    "tc40_empty_fields.csv",
    "tc41_negative_credits.csv",
    "tc42_whitespace_grades.csv",
    "tc43_duplicate_same_semester.csv",
    "tc45_credit_prereq_violation.csv",
    "tc46_corequisite_same_semester.csv",
    "tc47_eee_prereq_violation.csv",
    "tc48_bba_prereq_violation.csv",
    "tc49_cross_program_courses.csv",
    "tc50_bba_wrong_concentration.csv",
    "tc51_i_grade_resolved.csv",
    "tc52_retake_worse_grade.csv",
    "tc53_retake_ineligible.csv",
    "tc54_cse_math_minor_complete.csv",
    "tc55_cse_physics_minor_complete.csv",
    "tc56_cse_math_minor_partial.csv",
    "tc57_cse_minor_missing_prereqs.csv",
]

PROGRAMS = ["CSE", "BBA", "EEE", "ETE", "CEE", "ENV", "ENG", "ECO"]

# Base path to test files (absolute path)
BASE_PATH = "/Users/rajin/Developer/ACTIVE/SEM12-VIBE-CODING/Project/GradGate-v2/tests"


class GradGateUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        """Get a test token when the user starts."""
        response = self.client.get("/test-token")
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("access_token")
            self.headers = {"Authorization": f"Bearer {self.token}"}
        else:
            self.token = None
            self.headers = {}

    @task(7)
    def run_csv_audit(self):
        """Run a degree audit with a random CSV file (70% weight)."""
        if not self.token:
            return

        # Pick a random CSV file
        filename = random.choice(TEST_FILES)
        file_path = os.path.join(BASE_PATH, filename)

        if not os.path.exists(file_path):
            return

        program = random.choice(PROGRAMS)

        with open(file_path, "rb") as f:
            self.client.post(
                "/audit/csv",
                files={"file": (filename, f, "text/csv")},
                data={"program": program},
                headers=self.headers,
                name="/audit/csv",
            )

    @task(3)
    def view_history(self):
        """View audit history (30% weight)."""
        if not self.token:
            return

        self.client.get("/history", headers=self.headers, name="/history")
