# (C) British Crown Copyright 2025, Met Office.
# Please see LICENSE.md for license details.
"""
This script generates the variable lists for each CMIP experiment for each data request version.

This script scans two source files containing CMIP experiments, their associated variables and the variable metadata
such as priority level and production labels. Each variable is labelled accordingly and commented out as necessary.
Each variable list is then saved to a plain text file containing the variables for that experiment.

THIS SCRIPT CURRENTLY CONSIDERS GLOBAL VARIABLES ONLY. NON-GLOBAL VARIABLES ARE FILTERED OUT WITHIN THE FUNCTION
format_variable_names().

Example command line usage:
"python scripts/generate_variable_lists.py reference_information/dr-1.2.2.2_all.json reference_information/mappings.json
1pctCO2 1pctCO2-rad 1pctCO2-bgc"

"""

import argparse
import json
import os
from itertools import chain
from pathlib import Path
from typing import Union

IGNORED_PRIORITIES = ("med", "low")
PRIORITY_ORDER = {"# priority=medium": 1, "# priority=low": 2, "# do-not-produce": 3}


def set_arg_parser() -> argparse.Namespace:
    """Creates an argument parser to take source file paths from the command line.

    Returns
    -------
    argparse.Namespace
        The argument parser to handle source file paths.

    """
    parser = argparse.ArgumentParser(description="Generate a variable list (global variables only) for a given list "
                                     "experiments using provided data request and mapping information")

    dr_info_description = ("The path to the file containing all included experiments and their associated "
                           "variables grouped by priority e.g. reference_information/dr-1.2.2.2_all.json")
    parser.add_argument("dr_info", help=dr_info_description)

    mapping_info_description = ("The path to the file containing mapping information associated with each individual "
                                "variable such as the associated title, labels and stash entries. "
                                "e.g. reference_information/mappings.json)")
    parser.add_argument("mappings", help=mapping_info_description)

    parser.add_argument("experiments", help="The experiments to generate variable lists for.", nargs="+")

    return parser.parse_args()


def open_source_jsons(path: Path) -> Union[dict, list[dict]]:
    """Opens and reads a single JSON file.

    Parameters
    ----------
    path: Path
        The path of the file to be opened.

    Returns
    -------
    Union[dict, list[dict]]
        The JSON file content.

    Raises
    ------
    FileNotFoundError
        If the file does not exist at the given path.
    json.JSONDecodeError
        If the JSON file structure is invalid.
    """
    try:
        with open(path, "r") as f:
            file = json.load(f)

    except FileNotFoundError:
        print(f"File not found: {path}.")
    except json.JSONDecodeError as err:
        print(f"Invalid JSON formatting: {err}")

    return file


def get_grouped_priority_labels(experiment_dict: dict, experiment: str) -> dict[str, set]:
    """Creates a dictionary of labels grouped by priority (core, high, med, low) for a single experiment.

    Parameters
    ----------
    experiment_dict: dict
        The dictionary containing all experiments and their associated variables.
    experiment: str
        The experiment whose variables are being updated.

    Returns
    -------
    dict[str, set]
        A dictionary of labels grouped by priority (core, high, med, low).
    """
    experiment_data = experiment_dict["experiment"][experiment]

    return {
        "core": set(experiment_data.get("Core", [])),
        "high": set(experiment_data.get("High", [])),
        "med": set(experiment_data.get("Medium", [])),
        "low": set(experiment_data.get("Low", [])),
    }


def set_priority_comments(experiment_dict: dict, experiment: str) -> dict[str, str]:
    """Sets the comment to be appended to each variable based off of their priority level for a single experiment.

    Parameters
    ----------
    experiment_dict: dict
        The dictionary containing all experiments and their associated variables.
    experiment: str
        The experiment whose variables are being updated.

    Returns
    -------
    dict[str, str]
        A dictionary of comments created based on priority level.
    """
    priority_comments = {}
    priority_dict = get_grouped_priority_labels(experiment_dict, experiment)
    for level, variables in priority_dict.items():
        if level in IGNORED_PRIORITIES:
            for variable in variables:
                priority_comments[variable] = f" # priority={'medium' if level == 'med' else 'low'}"

    return priority_comments


def get_all_variables(experiment_dict: dict, experiment: str) -> chain:
    """Creates a chain of all variables used for a single experiment.

    Parameters
    ----------
    experiment_dict: dict
        The dictionary containing all experiments and their associated variables.
    experiment: str
        The experiment whose variables are being updated.

    Returns
    -------
    chain
        A chain of all priority labels.
    """
    priority_dict = get_grouped_priority_labels(experiment_dict, experiment)

    return chain(priority_dict["core"], priority_dict["high"], priority_dict["med"], priority_dict["low"])


def update_variables_with_priority(experiment_dict: dict, experiment: str, variable_dict: dict) -> dict[str, str]:
    """Update the variables for a single experiment with priority comments.

    Parameters
    ----------
    experiment_dict: dict
        The dictionary containing all experiments and their associated variables.
    experiment: str
        The experiment whose variables are being updated.
    variable_dict: dict
        A dictionary to populate with the updated variable data.

    Returns
    -------
    dict[str, str]
        A dictionary of variable name and priority level key-value pairs for a single experiment.
    """
    priority_comments = set_priority_comments(experiment_dict, experiment)
    all_labels = get_all_variables(experiment_dict, experiment)

    # Check all labels against their priority status and comment accordingly.
    for variable in all_labels:
        variable_dict[variable] = priority_comments.get(variable, "")

    return variable_dict


def get_mapping(mappings_dict: list[dict], variable: str) -> dict:
    """Identifies the correct dictionary within the mappings.json to read from.

    Parameters
    ----------
    mappings_dict: list[dict]
        The dictionary containing mapping information for all variables.
    variable: str
        The variable whose mapping information is required.

    Returns
    -------
    dict
        The mapping information for a single variable.
    """
    for mapping in mappings_dict:
        if variable == mapping["branded_variable"]:
            mapping = mapping
            break

    return mapping


def identify_not_produced(
    experiment_dict: dict, experiment: str, mappings_dict: list[dict], variable_dict: dict[str, str]
) -> dict[str, str]:
    """Identify all variables marked as "do not produce" in a single experiment. Overriding any existing "priority"
    value in the dict is acceptable since do-not-produce takes precedence.

    Parameters
    ----------
    experiment_dict: dict
        The dictionary containing all experiments and their associated variables.
    experiment: str
        The experiment whose variables are being updated.
    mappings_dict: list[dict]
        The dictionary containing mapping information for all variables.
    variable_dict: dict[str, str]
        The dictionary of name and priority level key-value pairs for a single experiment.

    Returns
    -------
    dict[str, str]
        An updated dictionary containing production status for variables marked "do-not-produce".
    """
    all_labels = get_all_variables(experiment_dict, experiment)
    for variable in all_labels:
        mapping = get_mapping(mappings_dict, variable)
        labels = mapping.get("labels")

        if "do-not-produce" in labels:
            variable_dict[variable] = " # do-not-produce"

    return variable_dict


def get_streams(experiment_dict: dict, experiment: str, mappings_dict: list[dict]) -> dict[str, str]:
    """Creates a dictionary for variables and their associated output stream for a single experiment.

    Parameters
    ----------
    experiment_dict: dict
        The dictionary containing all experiments and their associated variables.
    experiment: str
        The experiment whose variables are being updated.
    mappings_dict: list[dict]
        The dictionary containing mapping information for all variables.

    Returns
    -------
    dict[str, str]
        A dictionary containing variables and their associated output stream.
    """
    streams = {}

    # Access stash entries for each variable and check if it contains values.
    all_labels = get_all_variables(experiment_dict, experiment)
    for variable in all_labels:
        mapping = get_mapping(mappings_dict, variable)
        streams[variable] = mapping.get("stream")

    return streams


def reformat_variable_names(
    experiment_dict: dict, experiment: str, mappings_dict: list[dict], variable_dict: dict
) -> dict[str, str]:
    """Reformats the name of each variable from realm.variable.branding.frequency.region to
    realm/variable_branding@frequency:stream for a single experiment.

    Parameters
    ----------
    experiment_dict: dict
        The dictionary containing all experiments and their associated variables.
    experiment: str
        The experiment whose variables are being updated.
    mappings_dict: list[dict]
        The dictionary containing mapping information for all variables.
    variable_dict: dict
        An updated dictionary containing production status for variables marked "do-not-produce".

    Returns
    -------
    dict[str, str]
        An updated dictionary containing the reformatted variable names as keys and priority/production status as
        values.

    Raises
    ------
    KeyError
        If the original variable name cannot be split into parts as expected.
    """
    renamed_variable_dict = {}
    streams = get_streams(experiment_dict, experiment, mappings_dict)

    # Reformat all original variable names to realm/variable_branding@frequency:stream.
    for variable, comment in variable_dict.items():
        parts = variable.split(".")
        if len(parts) < 5:
            raise KeyError(f"{variable} has unexpected format. Expected: realm.variable.branding.frequency.region")

        realm, variable_name, branding, frequency, region = parts[:5]
        stream = streams.get(variable, "")

        # Filter out any non global variables
        if region in ("glb", "GLB"):
            new_variable_name = (f"{realm}/{variable_name}_{branding}@{frequency}:{stream}" if stream else
                                 f"{realm}/{variable_name}_{branding}@{frequency}")

            # Create new dictionary with the reformatted variable names to avoid key errors in the original dict.
            renamed_variable_dict[new_variable_name] = comment

    return renamed_variable_dict


def format_outfile_content(renamed_variable_dict: dict[str, str]) -> list[str]:
    """Reformats the key value pairs into single line plain text for a single experiment.

    Parameters
    ----------
    renamed_variable_dict: dict[str, str]
        An updated dictionary containing the reformatted variable names as keys and priority/production status as
        values.

    Returns
    -------
    list[str]
        A list of lines to populate the plain text file with.
    """
    lines = []
    for variable, comment in renamed_variable_dict.items():
        lines.append(f"#{variable}{comment}\n" if comment else f"{variable}{comment}\n")

    return lines


def sort_key(line: str) -> tuple[dict[str, int], int]:
    """The custom sort function passed to the sorted() function to define the variable order for a single experiment.

    Parameters
    ----------
    line: str
        A single line containing a single variable name and associated comments.

    Returns
    -------
    tuple[dict[str, int], int]
        The order of each label based on priority, variables with no specified priority will be assigned order 0 so that
        they appear at the top of the variable list.
    """
    for label in PRIORITY_ORDER:
        if label in line:
            return PRIORITY_ORDER[label]

    return 0


def save_outfile(outdir: Path, experiment: str, renamed_variable_dict: dict[str, str]) -> None:
    """Saves a single file to a plain text format.

    Parameters
    ----------
    outdir: Path
        The output directory.
    experiment: str
        The experiment whose variables are being saved.
    renamed_variable_dict: dict[str, str]
        An updated dictionary containing the reformatted variable names as keys and priority/production status as
        values.
    """
    outfile = outdir / f"{experiment}.txt"
    lines = format_outfile_content(renamed_variable_dict)

    with open(outfile, "w") as f:
        for line in sorted(lines, key=sort_key):
            f.write(line)


def generate_variable_lists() -> None:
    """
    Generates the variable list files for all experiments.
    """
    # Call required source files.
    args = set_arg_parser()
    experiment_dict = open_source_jsons(Path(args.dr_info))
    mappings_dict = open_source_jsons(Path(args.mappings))

    # Create output file path.
    outdir = Path(f"variables_glb/{experiment_dict['Header']['dreq content version']}")
    os.makedirs(outdir, exist_ok=True)

    # Loop over all listed experiments.
    for experiment in args.experiments:
        variable_dict = {}

        functions = [
            update_variables_with_priority(experiment_dict, experiment, variable_dict),
            identify_not_produced(experiment_dict, experiment, mappings_dict, variable_dict),
            reformat_variable_names(experiment_dict, experiment, mappings_dict, variable_dict),
        ]
        for f in functions:
            variable_dict = f

        save_outfile(outdir, experiment, variable_dict)

    print(f"SUCCESSFULLY GENERATED {len(args.experiments)} FILES")


if __name__ == "__main__":
    generate_variable_lists()
