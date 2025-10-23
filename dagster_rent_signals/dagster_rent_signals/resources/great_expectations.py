"""Great Expectations resource configuration for Tampa Rent Signals pipeline."""

import os
from pathlib import Path
from dagster import EnvVar, resource
from dagster_great_expectations import GreatExpectationsResource

# Get the absolute path to the Great Expectations project
GE_PROJECT_DIR = Path(__file__).parent.parent.parent.parent / "great_expectations"

great_expectations_resource = GreatExpectationsResource(
    data_context_root_dir=str(GE_PROJECT_DIR),
)