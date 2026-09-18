# (C) British Crown Copyright 2025-2026, Met Office.
# Please see LICENSE.md for license details.
"""This script takes the body of the issue form 'Add/Modify Workflow Metadata' and uses its content to generate a
structured metadata configuration file. The config file is split into 3 sections: metadata, data and misc. The files
produced by this script are used to populate request files generated through '.github/workflows/generate_request.yml'.

NOTE: This script is the backbone of '.github/workflows/process_new_metadata.yml' and relies upon
'.github/ISSUE_TEMPLATE/add_workflow_metadata.yml'. Changes to any of these files may result in errors in the others.

The issue body content generated from the issue form is cleaned, validated and sorted into the required formatting for
metadata cfg files. This is then passed on into a workflow as an output file along with any errors that may have been
flagged. Valid files will automatically be commited back to the repository by the action.

Information given from the issue body is automatically checked and can trigger either an error or warning if a problem
is found. Errors hold the same weight as a logger.critical flag: these are problems that would prevent processing
and will result in validation failure. Warnings hold the same weight as a logger.warning flag: these are used to alert
the user that a piece of information provided **may** be incorrect but will not cause any direct processing issues.
If you are unsure whether a check should flag an error or warning, please contact Lauren Boon or Matthew Mizielinski
for guidance.
"""

import os
import re
import sys
from pathlib import Path

from metomi.isodatetime.data import Calendar

from common import get_issue, process_metadata, format_message
from constants import (
    DATA,
    METADATA,
    MISC,
    REGEX_FORMAT,
)
from validate_metadata import Validate

REGEX_DICT = {
    "workflow_pattern": re.compile(REGEX_FORMAT["model_workflow_id"]),
    "variant_pattern": re.compile(REGEX_FORMAT["variant_label"]),
}


def set_calendar(calendar_type: str) -> dict[str, str]:
    """Sets the metomi.isodatetime calendar. If the calendar is not '360_day' or 'proleptic_gregorian' an error is noted
    to be returned to the user.

    Parameters
    ----------
    calendar_type : str
        The type of calendar used.

    Returns
    -------
    dict[str, str]
        A dictionary containing any errors caused by user input from the form.
    """
    errors = {}

    if calendar_type == "360_day":
        Calendar.default().set_mode(calendar_type)
    elif calendar_type == "proleptic_gregorian":
        Calendar.default().set_mode("gregorian")
    else:
        errors["calendar"] = "incompatible calendar: expected 360_day or proleptic_gregorian"

    return errors


def create_filename(meta_dict: dict[str, str]) -> str:
    """Generates a filename based off of the input model workflow id and mass ensemble member (if given).

    Parameters
    ----------
    meta_dict : dict[str, str]
        A cleaned dictionary containing the metadata keys and values from the issue form.

    Returns
    -------
    str
        The name of the metadata configuration file.
    """
    model_workflow_id = meta_dict["model_workflow_id"]
    if meta_dict["mass_data_class"] == "ens":
        mass_ensemble_member_id = meta_dict["mass_ensemble_member"]
        filename = f"{model_workflow_id}-{mass_ensemble_member_id}.cfg"
    else:
        filename = f"{model_workflow_id}.cfg"

    return filename


def sort_to_categories(meta_dict: dict[str, str]) -> dict:
    """Sorts the metadata dictionary into appropriate categories as nested dictionaries.

    Parameters
    ----------
    meta_dict : dict[str, str]
        A cleaned dictionary containing the metadata keys and values from the issue form.

    Returns
    -------
    dict
        A cleaned, organised dictionary containing the validated metadata keys and values from the issue form.
    """
    metadata_dict = {}
    data_dict = {}
    misc_dict = {}
    organised_metadata = {}

    # Categorise keys into sections that match the request.cfg mapping.
    for key, value in meta_dict.items():
        if key in METADATA:
            metadata_dict[key] = value
        elif key in DATA:
            data_dict[key] = value
        elif key in MISC:
            misc_dict[key] = value

    # Re map organised keys as nested dictionaries.
    organised_metadata["[metadata]"] = metadata_dict
    organised_metadata["[data]"] = data_dict
    organised_metadata["[misc]"] = misc_dict
    organised_metadata["[ADDITIONAL INFO]"] = {
        "notes": meta_dict.get("additional_notes"),
        "updates": ""
    }

    return organised_metadata


def format_cfg_file(output_file: Path, organised_metadata: dict[str, str]) -> None:
    """Writes the cleaned, organised and validated metadata to a structured configuration file.

    Parameters
    ----------
    output_file : Path
        The complete path of the output file.
    organised_metadata : dict[str, str]
        A cleaned, organised dictionary containing the validated metadata keys and values from the issue form.
    """
    with open(output_file, "w") as f:
        for key, value in organised_metadata.items():
            f.write(f"{key}\n")
            if isinstance(value, dict):
                for k, v in value.items():
                    f.write(f"{k} = {v}\n")
                f.write("\n")


def main() -> None:
    """Holds the main body of the script."""
    issue_body = get_issue()['body']

    # Find key-value pairs and map them to dictionary process.
    match = re.findall(r"### (.+?)\n\s*\n?(.+)", issue_body)
    meta_dict = process_metadata(match)
    print("Extracting issue body...  SUCCESSFUL")

    # Validate and organise dictionary content.
    organised_metadata = sort_to_categories(meta_dict)

    # Validate the new metadata file before saving
    validator = Validate(organised_metadata)
    validation_result = validator.validate_all()
    errors = validation_result.errors
    warnings = validation_result.warnings

    # Create output file.
    filename = create_filename(meta_dict)
    delimiter = "EOF"

    # Add any warnings to the GitHub env. These are returned to the user on both validation success and failure.
    if warnings:
        warnings = format_message(warnings, "warning")
        print(warnings)
        with open(os.environ["GITHUB_OUTPUT"], "a") as gh:
            gh.write(f"warnings<<{delimiter}\n")
            gh.write(f"{warnings}\n")
            gh.write(f"{delimiter}\n")

    if not errors:
        print("Validating issue form inputs...  SUCCESSFUL")  # Printed to the action logs for debugging
        output_dir = Path("workflow_metadata")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{filename}"

        # Note the output filename to be provided to the user in the issue comments by the GitHub Actions bot.
        with open(os.environ["GITHUB_OUTPUT"], "a") as gh:
            gh.write(f"filename={output_file}")

        format_cfg_file(output_file, organised_metadata)
        print(f"Saving metadata file as {output_file}...  SUCCESSFUL")  # Printed to the action logs for debugging

    else:
        print("Validating issue form inputs...  FAILED")  # Printed to the action logs for debugging purposes
        errors = format_message(errors, "error")
        print(errors)  # Printed to the action logs for debugging purposes
        # Note any warnings to be provided to the user in the issue comments by the GitHub Actions bot. This must be
        # written to the the github env in a way that can be interpreted rather than read line by line.
        with open(os.environ["GITHUB_OUTPUT"], "a") as gh:
            gh.write(f"errors<<{delimiter}\n")
            gh.write(f"{errors}\n")
            gh.write(f"{delimiter}\n")

        sys.exit(1)


if __name__ == "__main__":
    main()
