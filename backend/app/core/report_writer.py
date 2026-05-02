from pathlib import Path

from pydantic import BaseModel


def write_json_report(report: BaseModel, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if hasattr(report, "model_dump_json"):
        report_json = report.model_dump_json(indent=2)
    else:
        report_json = report.json(indent=2)

    output_path.write_text(report_json, encoding="utf-8")

    return output_path
