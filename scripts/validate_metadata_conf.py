# (C) British Crown Copyright 2025, Met Office.
# Please see LICENSE.md for license details.
"""Scan workflow metadata files and validate their structure and contents.

This script checks for missing sections, unexpected keys, and invalid values
in workflow configuration files.
"""

import configparser
import glob
import re
import sys
from pathlib import Path

import metomi.isodatetime.parsers as parse
from constants import (
    DATA,
    DATETIME_FIELDS,
    METADATA,
    MISC,
    PARENT_REQUIRED,
    REGEX_FORMAT,
    REQUIRED,
    SECTIONS,
)
from metomi.isodatetime.exceptions import ISO8601SyntaxError, IsodatetimeError

REGEX_DICT = {
    "workflow_pattern": re.compile(REGEX_FORMAT["model_workflow_id"]),
    "variant_pattern": re.compile(REGEX_FORMAT["variant_label"]),
}


def get_metadata_files() -> list[str]:
    """Creates a list of all existing cfg files to be checked.

    Returns
    -------
    list[str]
        List of cfg files to be checked.
    """
    glob_string = Path("workflow_metadata/*.cfg")
    cfg_files = glob.glob(str(glob_string))

    return cfg_files


def validate_structure(config: configparser, result: dict, file: str) -> dict:
    """Validates the structure of a single .cfg file.

    Parameters
    ----------
    config : configparser
        The config parser.
    result : dict
        The dictionary containing the details of any validation failures.
    file : str
        The file being validated.

    Returns
    -------
    dict
        The dictionary containing the details of any validation failures.
    """
    file_results = result[file]
    sections_in_config = set(config.sections())
    SECTION_DICT = {"metadata": METADATA, "data": DATA, "misc": MISC}

    # Verify the correct sections are present in the correct order
    unexpected_sections = set()
    missing_sections = set()
    if sections_in_config != SECTIONS:
        unexpected_sections = list(sections_in_config - SECTIONS)
        missing_sections = list(SECTIONS - sections_in_config)

    # Verify the correct keys are in the correct section
    for section in SECTIONS:
        keys = set(config[section].keys()) if section in config else set()
        target = set(SECTION_DICT[section])

        missing_keys = target - keys
        unexpected_keys = keys - target if section not in missing_sections else set()

    if any([missing_keys, unexpected_keys, unexpected_sections, missing_sections]):
        file_results["failures"] = True
        file_results["missing_sections"] = list(missing_sections)
        file_results["unexpected_sections"] = list(unexpected_sections)
        file_results["missing_keys"] = list(missing_keys)
        file_results["unexpected_keys"] = list(unexpected_keys)

    return result


def validate_required_fields(config: configparser, result: dict, file: str) -> dict:
    """Validates the contents of the required fields for a single .cfg file.

    Parameters
    ----------
    config : configparser
        The config parser.
    result : dict
        The dictionary containing the details of any validation failures.
    file : str
        The file being validated.

    Returns
    -------
    dict
        The dictionary containing the details of any validation failures.
    """
    file_results = result[file]
    missing_values = set()
    unexpected_values = set()

    # Verify that all required fields are not None
    for section in config.sections():
        section_data = config[section]
        for key, value in section_data.items():
            if key in REQUIRED and not value:
                missing_values.add(key)

            if key == "branch_method":
                if value == "standard":
                    for parent_key in PARENT_REQUIRED:
                        if section_data.get(parent_key) in (None, ""):
                            missing_values.add(key)
                elif value == "no parent":
                    for parent_key in PARENT_REQUIRED:
                        if section_data.get(parent_key) not in (None, ""):
                            unexpected_values.add(key)

            if key == "mass_data_class":
                if value == "ens" and not section_data.get("mass_ensemble_member"):
                    missing_values.add(key)
                if value == "crum" and section_data.get("mass_ensemble_member"):
                    unexpected_values.add(key)

    if any([missing_values, unexpected_values]):
        file_results["failures"] = True
        file_results["missing_values"] = list(missing_values)
        file_results["unexpected_values"] = list(unexpected_values)

    return result


def validate_field_inputs(config: configparser, result: dict, file: str) -> dict:
    """Validates the inputs of a single .cfg file.

    Parameters
    ----------
    config : configparser
        The config parser.
    result : dict
        The dictionary containing the details of any validation failures.
    file : str
        The file being validated.

    Returns
    -------
    dict
        The dictionary containing the details of any validation failures.
    """
    file_results = result[file]
    invalid_values = set()
    parser = parse.TimePointParser()
    for section in config.sections():
        for key, value in config[section].items():
            # Verify datetime inputs
            if key == "branch_method" and value == "standard":
                DATETIME_FIELDS.add("branch_date_in_child")
                DATETIME_FIELDS.add("branch_date_in_parent")
            if key in DATETIME_FIELDS:
                try:
                    parser.parse(value)
                except (IsodatetimeError, ISO8601SyntaxError):
                    invalid_values.add(key)

            # Verify workflow model ID structure
            if key == "model_workflow_id" and not REGEX_DICT["workflow_pattern"].fullmatch(value):
                invalid_values.add(key)

            # Verify variant label structure
            if key == "variant_label" and not REGEX_DICT["variant_pattern"].fullmatch(value):
                invalid_values.add(key)

            # Verify that atmospheric timestep is an integer
            if key == "atmos_timestep" and (not value.isdigit() or int(value) < 0):
                invalid_values.add(key)

            # Verify that no fields have the value "_No response_"
            if value == "_No response_":
                invalid_values.add(key)

    if invalid_values:
        file_results["failures"] = True
        file_results["invalid_values"] = list(invalid_values)

    return result


def create_failure_report(result: dict) -> None:
    """Prints back any validation errors to the user.

    Parameters
    ----------
    result : dict
        The dictionary containing the details of any validation failures.
    """
    success = True
    print("\nFILE VALIDATION FAILURE REPORT:\n")
    for f in result.values():
        if f["failures"]:
            success = False
            print("=" * 60)
            print(f"FILE: {f.get('file')}")
            for key, value in f.items():
                if value and key not in ("file", "failures"):
                    print(f"    --> ERROR: {key.replace('_', ' ')}")
                    print(f"        --> {', '.join(f.get(key))}")
    if success:
        print("=" * 60)
        print("ALL FILES SUCCESSFULY VALIDATED")

    else:
        sys.exit(1)


def main() -> None:
    """Holds the main body of the script."""
    result = {}

    cfg_files = get_metadata_files()
    for file in cfg_files:
        result[file] = {
            "file": file,
            "failures": False,
        }

        # A new parser must be created for each file since ConfigParser.read() is cumulative
        config = configparser.ConfigParser()
        config.read(file)

        # Perform validation
        validators = [
            validate_structure(config, result, file),
            validate_required_fields(config, result, file),
            validate_field_inputs(config, result, file),
        ]
        for v in validators:
            result = v

    create_failure_report(result)


if __name__ == "__main__":
    main()
