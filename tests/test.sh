#!/bin/bash
set -e

mkdir -p /logs/verifier
python3 /tests/verify.py 2>&1 | tee /logs/verifier/test-output.log
