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
"""

import os
import re
import sys
from pathlib import Path

import metomi.isodatetime.parsers as parse
from metomi.isodatetime.data import Calendar
from metomi.isodatetime.exceptions import ISO8601SyntaxError, IsodatetimeError

from common import get_issue, process_metadata
from constants import (
    DATA,
    DATETIME_FIELDS,
    METADATA,
    MISC,
    PARENT_REQUIRED,
    REGEX_FORMAT,
    REQUIRED,
    CMOR_CV_JSON
)

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


def normalise_datetime(datetime: str, errors: dict[str, str], field: str) -> tuple[str, dict[str, str]]:
    """Normalises any acceptable datetime string into yyyy-mm-ddTHH:MM:SSZ format.

    Parameters
    ----------
    datetime : str
        The datetime string to normalise.
    errors : dict[str, str]
        A dictionary containing any errors caused by user input from the form.
    field : str
        The datetime field being normalised.

    Returns
    -------
    tuple[str, dict[str, str]]
        The normalised string and the dictionary of errors.
    """
    try:
        parser = parse.TimePointParser()
        normalised_str = str(parser.parse(datetime)).replace("+01:00", "Z")  # Handles changes daylight saving hours.
    except (IsodatetimeError, ISO8601SyntaxError):
        errors["datetime"] = f"invalid datetime format for {field}"
        normalised_str = datetime

    return normalised_str, errors


def check_for_missing_inputs(meta_dict: dict[str, str], errors: dict[str, str]) -> dict[str, str]:
    """Checks for missing inputs in any of the required fields.

    Parameters
    ----------
    meta_dict: dict[str, str]
        The dictionary containing the submitted metadata information.
    errors: dict[str, str]
        The dictionary containing any triggered error messages.

    Returns
    -------
    dict[str, str]
        The dictionary containing any triggered error messages.
    """
    missing = []
    for parameter in REQUIRED:
        if meta_dict.get(parameter) in (None, "", "_No response_"):
            missing.append(f"Missing field {parameter}")

    if missing:
        errors["missing_required_field"] = missing

    return errors


def check_parent_fields(meta_dict: dict[str, str], errors: dict[str, str]) -> dict[str, str]:
    """Checks that parent attributes are present if branch method is 'stanard' and checks that they are not present if
    branch method is 'no parent'.

    Parameters
    ----------
    meta_dict: dict[str, str]
        The dictionary containing the submitted metadata information.
    errors: dict[str, str]
        The dictionary containing any triggered error messages.

    Returns
    -------
    dict[str, str]
        The dictionary containing any triggered error messages.
    """
    missing_parent_fields = []
    unexpected_parent_fields = []
    branch_method = meta_dict.get("branch_method")

    if branch_method == "standard":
        for parent_key in PARENT_REQUIRED:
            if meta_dict.get(parent_key) in (None, "", "_No response_"):
                missing_parent_fields.append(f"missing required parent field: {parent_key}")
    elif branch_method == "no parent":
        for parent_key in PARENT_REQUIRED:
            if meta_dict.get(parent_key) not in (None, "", "_No response_"):
                unexpected_parent_fields.append(f"unexpected field: {parent_key}")

    if missing_parent_fields:
        errors["missing_parent_field"] = missing_parent_fields
    if unexpected_parent_fields:
        errors["unexpected_parent_field"] = unexpected_parent_fields

    return errors


def check_mass_data_class_attributes(meta_dict: dict[str, str], errors: dict[str, str]) -> dict[str, str]:
    """Checks that attributes related to mass_data_class are present as expected. If mass_data_class is 'crum' no mass
    ensemble member ID should be given. If mass_data_class is 'ens' then a mass ensemble member ID is required.

    Parameters
    ----------
    meta_dict: dict[str, str]
        The dictionary containing the submitted metadata information.
    errors: dict[str, str]
        The dictionary containing any triggered error messages.

    Returns
    -------
    dict[str, str]
        The dictionary containing any triggered error messages.
    """
    mass_data_class = meta_dict.get("mass_data_class")
    mass_ensemble_member = meta_dict.get("mass_ensemble_member")

    if mass_data_class == "ens" and not mass_ensemble_member:
        errors["missing_mass_field"] = f"missing field: mass_ensemble_member"
    if mass_data_class == "crum" and mass_ensemble_member:
        errors["unexpected_mass_field"] = f"unexpected field: mass_ensemble_member"

    return errors


def check_datetime_fields(meta_dict: dict[str, str], errors: dict[str, str]) -> dict[str, str]:
    """Checks that all datetime inputs are of the expected format: 'YYYY-MM-DDTHH:mm:ssZ'.

    Parameters
    ----------
    meta_dict: dict[str, str]
        The dictionary containing the submitted metadata information.
    errors: dict[str, str]
        The dictionary containing any triggered error messages.

    Returns
    -------
    dict[str, str]
        The dictionary containing any triggered error messages.
    """
    # Check parent time fields only when branch_method is 'standard'. Otherwise, these fields should be none.
    if meta_dict.get("branch_method") == "standard":
        DATETIME_FIELDS.add("branch_date_in_child")
        DATETIME_FIELDS.add("branch_date_in_parent")
    for field in DATETIME_FIELDS:
        normal_datetime, errors = normalise_datetime(meta_dict.get(field), errors, field)
        meta_dict[field] = normal_datetime

    return errors


def check_model_workflow_id(meta_dict: dict[str, str], errors: dict[str, str]) -> dict[str, str]:
    """Checks that model_workflow_id follows the expected format of 'a-bc123'(most common) or 'ab-cd123'(rare but not
    impossible).

    Parameters
    ----------
    meta_dict: dict[str, str]
        The dictionary containing the submitted metadata information.
    errors: dict[str, str]
        The dictionary containing any triggered error messages.

    Returns
    -------
    dict[str, str]
        The dictionary containing any triggered error messages.
    """
    if not REGEX_DICT["workflow_pattern"].fullmatch(meta_dict.get("model_workflow_id")):
        errors["workflow_id_format"] = "model workflow ID is incorrectly formatted: expected a-bc123 or ab-cd123"

    return errors


def check_variant_labels(meta_dict: dict[str, str], errors: dict[str, str]) -> dict[str, str]:
    """Checks that variant labels follow the expected regex r{[1-9]}i{[1-9]}p{[1-9]}f{[1-9]}.

    Parameters
    ----------
    meta_dict: dict[str, str]
        The dictionary containing the submitted metadata information.
    errors: dict[str, str]
        The dictionary containing any triggered error messages.

    Returns
    -------
    dict[str, str]
        The dictionary containing any triggered error messages.
    """
    labels = [meta_dict.get("variant_label")]
    # Check the parent variable label only if branch method is standard. Otherwise this should be None.
    if meta_dict.get("branch_method") == "standard":
        labels.append(meta_dict.get("parent_variant_label"))

    for label in labels:
        if not REGEX_DICT["variant_pattern"].fullmatch(label):
            errors["label_format"] = ("variant label or parent variant label is incorrectly formatted: expected "
                                      "r1i1p1f1 like format")

    return errors


def check_atmos_timestep(meta_dict: dict[str, str], errors: dict[str, str]) -> dict[str, str]:
    """Checks that the atmospheric timestep is of logical value ( a postivie, non-zero integer ).

    Parameters
    ----------
    meta_dict: dict[str, str]
        The dictionary containing the submitted metadata information.
    errors: dict[str, str]
        The dictionary containing any triggered error messages.

    Returns
    -------
    dict[str, str]
        The dictionary containing any triggered error messages.
    """
    atmos_timestep = meta_dict.get("atmos_timestep")
    if not atmos_timestep.isdigit() or int(atmos_timestep) < 0:
        errors["timestep_logic"] = "atmospheric timestep is invalid"

    return errors


def check_start_end_logic(meta_dict: dict[str, str], errors: dict[str, str]) -> dict[str, str]:
    """Checks that start date and end date are logical.

    Parameters
    ----------
    meta_dict: dict[str, str]
        The dictionary containing the submitted metadata information.
    errors: dict[str, str]
        The dictionary containing any triggered error messages.

    Returns
    -------
    dict[str, str]
        The dictionary containing any triggered error messages.
    """
    parser = parse.TimePointParser()
    start_date = meta_dict.get("start_date")
    end_date = meta_dict.get("end_date")
    base_date = meta_dict.get("base_date")
    start_date_err_msg = "invalid datetime format for start_date"
    end_date_err_msg = "invalid datetime format for end_date"

    try:
        if start_date_err_msg not in errors["datetime"] and end_date_err_msg not in errors["datetime"]:
            if parser.parse(end_date) < parser.parse(start_date):
                errors["datetime_logic"] = "end date cannot be earlier than start date"
            if parser.parse(start_date) < parser.parse(base_date):
                errors["datetime_logic"] = "Start date cannot be earlier than the base date: 1850-01-01"
    except KeyError:
        if parser.parse(end_date) < parser.parse(start_date):
            errors["datetime_logic"] = "end date cannot be earlier than start date"
        if parser.parse(start_date) < parser.parse(base_date):
            errors["datetime_logic"] = "Start date cannot be earlier than the base date: 1850-01-01"

    return errors


def check_fixed_fields(meta_dict: dict[str, str], errors: dict[str, str]) -> dict[str, str]:
    """Checks that all fields that can only be a fixed value or one of a set of fixed values are as expected.

    Many of these fields are restricted by a dropdown menu in the issue form. However, since issues can be editted
    manually, it is still important to verify these.

    Parameters
    ----------
    meta_dict: dict[str, str]
        The dictionary containing the submitted metadata information.
    errors: dict[str, str]
        The dictionary containing any triggered error messages.

    Returns
    -------
    dict[str, str]
        The dictionary containing any triggered error messages.
    """
    unrecognised_inputs = []

    # Check that branch method is either 'no parent' or 'standard'
    if meta_dict.get("branch_method") not in ("no parent", "standard"):
        unrecognised_inputs.append("branch_method must have the value 'no parent' or 'standard'")

    # Confirm that mip era and parent mip era are both CMIP7
    if meta_dict.get("branch_method") == "standard":
        eras = (meta_dict.get("mip_era"), meta_dict.get("parent_mip_era"))
        for era in eras:
            if era != "CMIP7":
                unrecognised_inputs.append("mip_era and parent_mip_era must have the value 'CMIP7'")

    # Confirm that model ID is valid
    model_id = meta_dict.get("model_id")
    if model_id not in ("UKCM2-0-LL", "UKCM2a-0-HH", "UKESM1-3-LL", "HadGEM3-GC31-MM"):
        unrecognised_inputs.append("model_id must have the value 'UKCM2-0-LL', 'UKCM2a-0-HH', 'UKESM1-3-LL' or "
                                   "'HadGEM3-GC31-MM'")

    if meta_dict.get("branch_method") == "standard":
        # The parent model ID and model ID should match
        if model_id != meta_dict.get("parent_model_id"):
            unrecognised_inputs.append(f"parent_model_id must match model_id '{model_id}'")

        if meta_dict.get("parent_time_units") != "days since 1850-01-01":
            unrecognised_inputs.append("parent_time_units must have the value 'days since 1850-01-01'")

    # Confirm that mass_data_class is either ens or crum (default)
    if meta_dict.get("mass_data_class") not in ("ens", "crum"):
        unrecognised_inputs.append("mass_data_class must have the value 'ens' or 'crum'")

    if unrecognised_inputs:
        errors["unrecognised_input"] = unrecognised_inputs

    return errors


def check_cvs(meta_dict: dict[str, str], errors: dict[str, str], warnings: dict[str, str]) -> dict[str, str]:
    """Checks that inputs are present within the CV and are the expected value for a given experiment. Each experiment
    is expected to have one of a specific list of parent experiments, mips etc. This must be checked and consistent to
    avoid errors in CDDS. There may be cases where what is expected by the CVs does not match what was used in real
    life. These cases should be handled independently so an erata can be issued noting that the metadata for that
    workflow is not accurate. Complete transparency is important in these situations.

    Parameters
    ----------
    meta_dict: dict[str, str]
        The dictionary containing the submitted metadata information.
    errors: dict[str, str]
        The dictionary containing any triggered error messages.
    warnings: dict[str, str]
            The dictionary containing any triggered warning messages.

    Returns
    -------
    dict[str, str]
        The dictionary containing any triggered error messages.
    """
    cv = CMOR_CV_JSON
    branch_method = meta_dict.get("branch_method")
    cv_errors = []

    institution = meta_dict.get("institution_id")
    if institution not in cv["CV"]["institution_id"]:
        cv_errors.append(f"institution_id '{institution}' could not be found in the cvs")

    experiment = meta_dict.get("experiment_id")
    if experiment not in cv["CV"]["experiment_id"]:
        cv_errors.append(f"experiment id '{experiment}' could not be found in the cvs")
        errors["cv_error"] = cv_errors
        return errors

    experiment_cv_info = cv["CV"]["experiment_id"][experiment]
    mip = meta_dict.get("mip")
    mip_in_cv = experiment_cv_info["activity_id"]
    if mip not in mip_in_cv:
        cv_errors.append(f"mip '{mip}' does not match one of the expected values '{mip_in_cv}' given in the cvs")

    # Check parent fields only when branch method is 'standard', otherwise these should be None.
    if branch_method == "standard":
        parent_experiment = meta_dict.get("parent_experiment_id")
        parent_experiment_in_cv = experiment_cv_info["parent_experiment_id"]
        if parent_experiment not in parent_experiment_in_cv:
            cv_errors.append(f"parent experiment id '{parent_experiment}' does not match one of the expected values "
                            f"'{parent_experiment_in_cv}' given in the cvs")
        parent_mip = meta_dict.get("parent_mip")
        parent_mip_in_cv = experiment_cv_info["parent_activity_id"]
        if parent_mip not in parent_mip_in_cv:
            cv_errors.append(f"parent mip '{parent_mip}' does not match one of the expected values "
                             f"'{parent_mip_in_cv}' given in the cvs")

    cv_end_year = experiment_cv_info["end_year"]
    if cv_end_year:
        end_year = meta_dict.get("end_date").split("-")[0]
        if str(end_year) != str(cv_end_year):
            warnings["end_date"] = ("end date does not match the value in the CVs. Expected an end year of "
                                    f"{cv_end_year}, got {end_year}")

    if cv_errors:
        errors["cv_error"] = cv_errors

    return errors, warnings


def validate_meta_content(meta_dict: dict[str, str]) -> tuple[dict[str, str], dict[str, str]]:
    """Wrapper function to handle all validation tasks.

    Parameters
    ----------
    meta_dict : dict[str, str]
        A cleaned dictionary containing the metadata keys and values from the issue form.

    Returns
    -------
    tuple[dict[str, str], dict[str, str])
        A dictionary containing any errors and a dictionary containing any warnings caused by user input from the form.
    """
    errors = set_calendar(meta_dict.get("calendar"))
    warnings = {}
    check_for_missing_inputs(meta_dict, errors)
    check_parent_fields(meta_dict, errors)
    check_datetime_fields(meta_dict, errors)
    check_start_end_logic(meta_dict, errors)
    check_fixed_fields(meta_dict, errors)
    check_cvs(meta_dict, errors, warnings)
    check_mass_data_class_attributes(meta_dict, errors)
    check_model_workflow_id(meta_dict, errors)
    check_variant_labels(meta_dict, errors)
    check_atmos_timestep(meta_dict, errors)

    return errors, warnings


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
    errors, warnings = validate_meta_content(meta_dict)
    organised_metadata = sort_to_categories(meta_dict)

    # Create output file.
    filename = create_filename(meta_dict)
    delimiter = "EOF"

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
