FROM python:3.11-slim

WORKDIR /workspace

COPY environment/input_artifacts /environment/input_artifacts
COPY tests /tests
COPY instruction.md /instruction.md

RUN chmod +x /tests/test.sh
