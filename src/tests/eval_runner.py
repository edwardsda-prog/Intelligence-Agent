#!/usr/bin/env python3
"""
Lab 6: Offline Evaluation Runner Wrapper
Invokes run_offline_evaluation.py preserving all command-line arguments.
"""
import os
import sys
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TARGET_SCRIPT = os.path.join(SCRIPT_DIR, "run_offline_evaluation.py")

if __name__ == "__main__":
    cmd = [sys.executable, TARGET_SCRIPT] + sys.argv[1:]
    sys.exit(subprocess.call(cmd))
