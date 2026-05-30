"""
main.py
========
Wrapper entry point for the Risk Intelligence Engine.
Executes the validation pipeline defined in validate.py.
"""

from validate import run_validation_pipeline

if __name__ == "__main__":
    run_validation_pipeline()
