def severity_value(sev: str) -> int:
    return {"low": 1, "medium": 2, "high": 3}.get(sev, 0)

def test_decision():
    # test block beats nudge beats allow
    checks = ["clarity", "context", "privacy"]
    severity = "high"
    
    # ... we will implement this inside analyzer.py
