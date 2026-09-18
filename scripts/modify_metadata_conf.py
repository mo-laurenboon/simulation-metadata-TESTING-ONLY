# (C) British Crown Copyright 2026, Met Office.
# Please see LICENSE.md for license details.
"""This script ......
"""
import re
import configparser
import os
import sys

from datetime import datetime

from common import get_issue, process_metadata, format_message
from constants import WORKFLOW_METADATA_DIR, METADATA, DATA, MISC
from validate_metadata import Validate

DATE = datetime.today().strftime('%Y-%m-%d')


def read_issue_body() -> dict:
    """Reads the issue body and generates a dictionary mapping the form field to its entry.

    Returns
    -------
    dict:
        Dictionary mapping the form field to its entry.
    """
    issue_body = get_issue()["body"]

    # Find key-value pairs and map them to dictionary.
    match = re.findall(r"### (.+?)\n\s*\n?(.+)", issue_body)
    meta_dict = process_metadata(match)

    # Remove the auto populated version of base date
    if meta_dict["base_date"] == "1850-01-01T00:00:00Z":
        meta_dict["base_date"] = ""
    print("Extracting issue body...  SUCCESSFUL")

    return meta_dict


def read_metadata_file(filename: str):
    """Reads in the existing workflow metadata file to be editted."""
    config = configparser.ConfigParser()
    if not os.path.exists(filename):
        raise FileNotFoundError(f"{filename} does not exist.")
    config.read(filename)

    return config


def identify_changes(meta_dict):
    changes = []
    for field, value in meta_dict.items():
        if field == "model_workflow_id":
            continue
        if value:
            changes.append({field: value})

    return changes


def identify_config_section(field_to_update: str):
    if field_to_update in METADATA:
        return "metadata"
    elif field_to_update in DATA:
        return "data"
    elif field_to_update in MISC:
        return "misc"
    else:
        raise RuntimeError(f"Unrecognised field: {field_to_update}")


def log_update(metadata_config, field, old_value, new_value):
    update_str = f". {field.capitalize()} was updated from `{old_value}` to `{new_value}` ({DATE})"
    metadata_config["ADDITIONAL INFO"]["updates"] = (f'"{metadata_config["ADDITIONAL INFO"]["updates"].strip('"')}'
                                                     f'{update_str}"')


def save_modified_metadata(filename, metadata_config):
    with open(filename, 'w') as conf:
        metadata_config.write(conf)

    print(f"Saving updates to {filename}... Success")


def main():
    meta_dict = read_issue_body()
    workflow_id = meta_dict.get("model_workflow_id")
    if not workflow_id:
        raise RuntimeError("No model workflow ID specified")
    filename = f"{WORKFLOW_METADATA_DIR}/{workflow_id}.cfg"

    changes = identify_changes(meta_dict)
    metadata_config = read_metadata_file(filename)
    for change in changes:
        for field, new_value in change.items():
            config_section = identify_config_section(field)
            old_value = metadata_config[config_section][field]
            print(f"Updating {field} from {old_value} to {new_value}")
            metadata_config[config_section][field] = new_value
            log_update(metadata_config, field, old_value, new_value)

    # Validate the new metadata file before saving
    validator = Validate(metadata_config)
    validation_result = validator.validate_all()

    # Add any warnings to the GitHub env. These are returned to the user on both validation success and failure.
    delimiter = "EOF"
    if validation_result.warnings:
        warnings = format_message(validation_result.warnings, "warning")
        print(warnings)
        with open(os.environ["GITHUB_OUTPUT"], "a") as gh:
            gh.write(f"warnings<<{delimiter}\n")
            gh.write(f"{warnings}\n")
            gh.write(f"{delimiter}\n")

    if not validation_result.errors:
        print("Validating inputs...  SUCCESSFUL")  # Printed to the action logs for debugging
        save_modified_metadata(filename, metadata_config)

        # Note the output filename to be provided to the user in the issue comments by the GitHub Actions bot.
        with open(os.environ["GITHUB_OUTPUT"], "a") as gh:
            gh.write(f"filename={filename}")
        print(f"Saving metadata file as {filename}...  SUCCESSFUL")  # Printed to the action logs for debugging

    else:
        print("Validating issue form inputs...  FAILED")  # Printed to the action logs for debugging purposes
        errors = format_message(validation_result.errors, "error")
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
