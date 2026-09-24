"""Run invai-docs/calc/cost_model.py with overridden assumptions, without editing it.

Usage (from the invai workspace root):
    python3 .claude/skills/unit-economics-model/run_scenarios.py                 # baseline as written
    python3 .claude/skills/unit-economics-model/run_scenarios.py code-prices     # label fees as in PLAN_CATALOG
    python3 .claude/skills/unit-economics-model/run_scenarios.py concept-prices  # $0.10/label, EasyPost at $0.05

Add a scenario to OVERRIDES below for each question you model, and record it in the model file.
"""

import sys
from pathlib import Path

SRC = Path("invai-docs/calc/cost_model.py")

OVERRIDES = {
    "baseline": {},
    # Label fee as charged in code today (billing PLAN_CATALOG: starter 5c, growth 4c, pro 3c, scale 2c).
    # Pilot and Growth scenarios run 300-400 orders/day = 9,000-12,000 orders/month, i.e. the Growth/Pro tiers.
    "code-prices": {"LABEL_PRICE": 0.04},
    # Concept doc recommendation: $0.10/label, EasyPost negotiated to $0.05.
    "concept-prices": {"LABEL_PRICE": 0.10, "LABEL_COST": 0.05},
    # AI design generation is cut from v1 (decisions/0006-v1-cuts.md): drop its cost line.
    "no-design-gen": {"_drop_fixed": ["AI: design generation"]},
}


def load():
    code = SRC.read_text()
    # The file prints tables at import (main block and a bare sensitivity() call); keep only definitions.
    code = code.replace('if __name__ == "__main__":', "if False:")
    code = "\n".join(line for line in code.splitlines() if line.strip() != "sensitivity()")
    ns: dict = {"__name__": "cost_model"}
    exec(compile(code, str(SRC), "exec"), ns)
    return ns


def main():
    name = sys.argv[1] if len(sys.argv) > 1 else "baseline"
    if name not in OVERRIDES:
        sys.exit(f"unknown scenario {name!r}; choose from {', '.join(OVERRIDES)}")
    ns = load()
    for key, value in OVERRIDES[name].items():
        if key == "_drop_fixed":
            for line in value:
                ns["FIXED"].pop(line, None)
        else:
            ns[key] = value
    print(f"## Scenario: {name}  (LABEL_PRICE ${ns['LABEL_PRICE']:.2f}, LABEL_COST ${ns['LABEL_COST']:.2f})")
    for model in ns["CLAUDE"]:
        print(ns["fmt"](ns["run"](model), model))
    ns["sensitivity"]()


if __name__ == "__main__":
    main()
