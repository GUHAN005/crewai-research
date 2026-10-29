"""Command-line version:  python main.py "your topic" """
import os
import sys

from report_runner import run_report

if __name__ == "__main__":
    topic = " ".join(sys.argv[1:]) or os.getenv("TOPIC", "Docker for beginners")
    data = run_report(topic, on_step=lambda name: print(f"\n>>> finished: {name}\n"))

    print("\n==================== FINAL REPORT ====================\n")
    print(data["report"])
    print(f"\nSaved in folder: {data['folder']}  (draft.md and report.md)")
