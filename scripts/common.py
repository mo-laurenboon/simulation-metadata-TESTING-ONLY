# (C) British Crown Copyright 2026, Met Office.
# Please see LICENSE.md for license details.
"""Holds common functions used throughout `scripts`"""

from pathlib import Path
import json
import os

from constants import META_FIELDS


def read_json(source_path: Path):
    """Opens a single json file and returns the contents as a dictionary.

    Parameters
    ----------
    source_path: Path
        The path to the source JSON file.

    Returns
    -------
    dict
        The JSON file contents as a dictionary.
    """
    with open(source_path, 'r') as f:
        dictionary = json.load(f)

    return dictionary


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


def process_metadata(match: list) -> dict[str, str]:
    """Generates a dictionary from the loaded issue body and cleans the contents to ensure consistent formatting.

    Parameters
    ----------
    match: list
        The identified key-value pairs from the issue body.

    Returns
    -------
    dict[str, str]
        The dictionary containing the submitted metadata information.
    """
    meta_dict = {}

    # Manually populate base_date, this is a fixed value that should** be the same for all workflows
    match.append(('Base date', '1850-01-01T00:00:00Z'))

    # Clean parsed data
    for key, value in set(match):
        clean = key.strip().lower().replace(" ", "_")
        meta_dict[clean] = value.strip()

    # Re map keys to correct CV format
    for old_key, new_key in META_FIELDS.items():
        meta_dict[new_key] = meta_dict.pop(old_key)

    # Reformat blank fields.
    for key, value in meta_dict.items():
        if meta_dict[key].lower() == "_no response_":
            meta_dict[key] = ""

    return meta_dict


def format_message(msg: dict[str, str], msg_type) -> str:
    """Formats the a human readable warning message to be returned to the user in the comments of the issue but the
    GitHub Actions bot.

    Parameters
    ----------
    msg : dict[str, str]
        A dictionary containing any messages to be returned to the user.
    msg_type: str
        The type of message. Error or warning.

    Returns
    -------
    str
        A human readable message detailing all warnings.
    """
    warnings = []
    for key, value in msg.items():
        clean_key = key.strip().capitalize().replace("_", " ")
        if isinstance(value, list):
            for item in value:
                list_value = item
                clean_value = list_value.strip().replace("_", " ")
                warning = clean_key + " " + msg_type + ": " + clean_value + "."
                warnings.append(warning)
        else:
            clean_value = value.strip().replace("_", " ")
            warning = clean_key + " " + msg_type + ": " + clean_value + "."
            warnings.append(warning)

    warning_str = "\n".join(warnings)

    return warning_str
