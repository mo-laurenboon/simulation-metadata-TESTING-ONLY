# (C) British Crown Copyright 2025, Met Office.
# Please see LICENSE.md for license details.
"""This script takes the body of an issue and uses its content to generate a structured metadata configuration file.

The issue body content generated from an issue form is cleaned, validated and sorted into the required formatting for
metadata cfg files. This is then passed on into a workflow as an output file along with any errors that may have been
flagged.
"""

import os
import re
import sys
from pathlib import Path

import metomi.isodatetime.parsers as parse
from constants import (
    DATA,
    DATETIME_FIELDS,
    META_FIELDS,
    METADATA,
    MISC,
    PARENT_REQUIRED,
    REGEX_FORMAT,
    REQUIRED,
)
from metomi.isodatetime.data import Calendar
from metomi.isodatetime.exceptions import ISO8601SyntaxError, IsodatetimeError

REGEX_DICT = {
    "workflow_pattern": re.compile(REGEX_FORMAT["model_workflow_id"]),
    "variant_pattern": re.compile(REGEX_FORMAT["variant_label"]),
}


def get_issue() -> dict[str, str]:
    """Extracts the issue body from the submitted issue form.

    Returns
    -------
    dict[str, str]
        The issue body as a dictionary.
    """
    return {
        "body": os.environ.get("ISSUE_BODY"),
    }


def set_calendar(calendar_type: str) -> dict[str, str]:
    """Sets the metomi.isodatetime calendar.

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

    if calendar_type == "360_day" or calendar_type == "gregorian":
        Calendar.default().set_mode(calendar_type)
    else:
        errors["calendar"] = "Incompatible calendar: expected 360_day or gregorian"

    return errors


def normalise_datetime(datetime: str, errors: dict[str, str], key: str) -> tuple[str, dict[str, str]]:
    """Normalises any acceptable datetime string into yyyy-mm-ddTHH:MM:SSZ format.

    Parameters
    ----------
    datetime : str
        The datetime string to normalise.
    errors : dict[str, str]
        A dictionary containing any errors caused by user input from the form.
    key : str
        The datetime field being normalised.

    Returns
    -------
    tuple[str, dict[str, str]]
        The normalised string and the dictionary of errors.
    """
    try:
        parser = parse.TimePointParser()
        normalised_str = str(parser.parse(datetime))
    except (IsodatetimeError, ISO8601SyntaxError):
        errors["datetime"] = f"Invalid datetime format for {key}"
        normalised_str = datetime

    return normalised_str, errors


def process_metadata(match: list[tuple[str]]) -> dict[str, str]:
    """Generates a dictionary from the loaded issue body and cleans the contents to ensure consistent formatting.

    Parameters
    ----------
    match : list[tuple[str]]
        The identified key-value pairs from the issue body.

    Returns
    -------
    dict[str, str]
        A cleaned dictionary containing the metadata keys and values from the issue form.
    """
    meta_dict = {}

    # Clean parsed data
    for key, value in set(match):
        clean = key.strip().lower().replace(" ", "_")
        meta_dict[clean] = value.strip()

    # Re map keys to correct CV format
    for old_key, new_key in META_FIELDS.items():
        meta_dict[new_key] = meta_dict.pop(old_key)

    # Reformat blank fields.
    for key, value in meta_dict.items():
        if meta_dict[key] == "_No response_":
            meta_dict[key] = ""

    return meta_dict


def validate_meta_content(meta_dict: dict[str, str]) -> dict[str, str]:
    """Validates the metadata dictionary contents.

    Parameters
    ----------
    meta_dict : dict[str, str]
        A cleaned dictionary containing the metadata keys and values from the issue form.

    Returns
    -------
    dict[str, str]
        A dictionary containing any errors caused by user input from the form.
    """
    errors = set_calendar(meta_dict["calendar"])
    # Confirm that conditional fields are present.
    for key, value in meta_dict.items():
        if key in REQUIRED and not value:
            errors["missing_required_field"] = f"Missing field {key}"

        if key == "mass_data_class":
            if value == "ens" and not meta_dict.get("mass_ensemble_member"):
                errors["missing_mass_field"] = f"Missing field: {key}"
            if value == "crum" and meta_dict.get("mass_ensemble_member"):
                errors["unexpected_mass_field"] = f"Unexpected field: {key}"

        if key == "branch_method":
            if value == "standard":
                for parent_key in PARENT_REQUIRED:
                    if meta_dict.get(parent_key) in (None, "", "_No response_"):
                        errors["missing_parent_field"] = f"Missing required parent field: {parent_key}"
            elif value == "no parent":
                for parent_key in PARENT_REQUIRED:
                    if meta_dict.get(parent_key) not in (None, "", "_No response_"):
                        errors["unexpected_parent_field"] = f"Unexpected field: {parent_key}"

        # Verify datetime inputs
        if key == "branch_method" and value == "standard":
            DATETIME_FIELDS.add("branch_date_in_child")
            DATETIME_FIELDS.add("branch_date_in_parent")
        if key in DATETIME_FIELDS:
            normal_datetime, errors = normalise_datetime(meta_dict[key], errors, key)
            meta_dict[key] = normal_datetime

        # Verify workflow model ID structure
        if key == "model_workflow_id" and not REGEX_DICT["workflow_pattern"].fullmatch(value):
            errors["workflow_id_format"] = "Model workflow ID is incorrectly formatted: expected a-bc123"

        # Verify variant label structure
        if key == "variant_label" and not REGEX_DICT["variant_pattern"].fullmatch(value):
            errors["label_format"] = "Variant label is incorrectly formatted: expected r1i1p1f2 like format"

        # Verify that atmospheric timestep is an integer
        if key == "atmos_timestep" and (not value.isdigit() or int(value) < 0):
            errors["timestep_logic"] = "Atmospheric timestep is invalid"

    # Confirm that end_time is not earlier than start_time.
    parser = parse.TimePointParser()
    if "datetime" not in errors:
        if parser.parse(meta_dict["end_date"]) < parser.parse(meta_dict["start_date"]):
            errors["datetime_logic"] = "End date cannot be earlier than start date"

    return errors


def format_warning_message(errors: dict[str, str]) -> str:
    """Formats the a human readable warning message to be returned to the user.

    Parameters
    ----------
    errors : dict[str, str]
        A dictionary containing any errors caused by user input from the form.

    Returns
    -------
    str
        A human readable message detailing all warnings.
    """
    warnings = []
    for key, value in errors.items():
        clean_key = key.strip().capitalize().replace("_", " ")
        clean_value = value.strip().lower().replace("_", " ")
        warning = clean_key + " warning " + "(" + clean_value + ")."
        warnings.append(warning)

    warnings = "\n".join(warnings)

    return warnings


def create_filename(meta_dict: dict[str, str]) -> str:
    """Generates a filename based off of the input model workflow id and mass ensemble member.

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


def sort_to_categories(meta_dict: dict[str, str]) -> dict[dict[str, str]]:
    """Sorts the metadata dictionary into appropriate categories as nested dictionaries.

    Parameters
    ----------
    meta_dict : dict[str, str]
        A cleaned dictionary containing the metadata keys and values from the issue form.

    Returns
    -------
    dict[dict[str, str]]
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
    errors = validate_meta_content(meta_dict)
    organised_metadata = sort_to_categories(meta_dict)

    # Create output file.
    filename = create_filename(meta_dict)

    if not errors:
        print("Validating issue form inputs...  SUCCESSFUL")
        output_dir = Path("workflow_metadata")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{filename}"

        with open(os.environ["GITHUB_OUTPUT"], "a") as gh:
            gh.write(f"filename={output_file}")

        format_cfg_file(output_file, organised_metadata)
        print(f"Saving metadata file as {output_file}...  SUCCESSFUL")

    else:
        print("Validating issue form inputs...  FAILED")
        warnings = format_warning_message(errors)

        with open(os.environ["GITHUB_OUTPUT"], "a") as gh:
            gh.write(f"warnings={warnings}")

        sys.exit(1)


if __name__ == "__main__":
    main()
