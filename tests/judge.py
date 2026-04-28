import json
import math
from pathlib import Path


OUTPUT = Path("/logs/agent/output.json")
ORACLE = Path("/tests/oracle.json")
REWARD = Path("/logs/verifier/reward.txt")


def close_enough(actual, expected):
    if isinstance(expected, float):
        try:
            return math.isclose(float(actual), expected, abs_tol=0.01)
        except Exception:
            return False
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(
            key in actual and close_enough(actual[key], value)
            for key, value in expected.items()
        )
    if isinstance(expected, list):
        return actual == expected
    return actual == expected


def main():
    REWARD.parent.mkdir(parents=True, exist_ok=True)
    if not OUTPUT.exists() or not ORACLE.exists():
        REWARD.write_text("0")
        return 1
    try:
        actual = json.loads(OUTPUT.read_text())
        expected = json.loads(ORACLE.read_text())
    except Exception:
        REWARD.write_text("0")
        return 1
    score = 1.0 if close_enough(actual, expected) else 0.0
    REWARD.write_text(str(score))
    print(f"reward: {score}")
    return 0 if score == 1.0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
