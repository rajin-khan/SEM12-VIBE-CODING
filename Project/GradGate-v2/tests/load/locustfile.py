"""Locust load test for GradGate API.

Run with:
    locust -f tests/load/locustfile.py \
        --headless -u 20 -r 5 \
        --run-time 120s \
        --host http://192.168.54.214:8000 \
        --html tests/load/report.html
"""

import json
import os
import random
from pathlib import Path

from locust import HttpUser, task, between

BASE_PATH = Path("/Users/rajin/Developer/ACTIVE/SEM12-VIBE-CODING/Project/GradGate-v2/tests")
MANIFEST_PATH = BASE_PATH / "canonical_fixture_expectations.json"
MANIFEST = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
FIXTURES = [
    {"filename": filename, "program": payload["program"]}
    for filename, payload in sorted(MANIFEST.items())
]


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
        fixture = random.choice(FIXTURES)
        filename = fixture["filename"]
        file_path = BASE_PATH / filename

        if not file_path.exists():
            return

        program = fixture["program"]

        with file_path.open("rb") as f:
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
