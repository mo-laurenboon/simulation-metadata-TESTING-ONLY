"""
This script takes the body of an issue and uses its content to generate and structured metadata configuration file.
"""

import os
import re
import metomi.isodatetime.parsers as parse
from pathlib import Path
import sys

def get_issue():
    """
    Extracts information from the submitted issue.

        :returns: Issue body, labels, number, title and author as a dictionary.
    """
    return {
        'body': os.environ.get('ISSUE_BODY'),
    }


def create_meta_dict(match):
    """
    Generates a dictionary format from the loaded issue body and cleans the key-value pairs to ensure consistent 
    formatting prior to sanity checks.

        :param match: The identified key value pairs from the issue body.
        :returns: Dictionary containing the grid parameters from the issue form.
    """
    meta_dict = {}
    meta_fields = {
        "issue_type": "issue_type",
        "base_date": "base_date",
        "branch_method": "branch_method",
        "child_branch_date": "branch_date_in_child",
        "parent_branch_date": "branch_date_in_parent",
        "parent_experiemnt_id": "parent_experiemnt_id",
        "parent_activity_id_(mip)": "parent_mip",
        "parent_model_id": "parent_model_id",
        "parent_time_units": "parent_time_units",
        "parent_varient_label": "parent_varient_label",
        "calendar_type": "calendar",
        "experiment_id": "experiment_id",
        "institution_id": "institution_id",
        "activity_id_(mip)": "mip",
        "mip_era": "mip_era",
        "varient_label": "varient_label",
        "model_id": "model_id",
        "start_date": "start_date",
        "end_date": "end_date",
        "mass_data_class": "mass_data_class",
        "mass_ensemble_member_id": "mass_ensemble_member",
        "model_workflow_id": "model_workflow_id",
        "atmospheric_timestep": "atmos_timestep"
    }

    # Clean parsed data
    for key, value in match:
        clean = key.strip().lower().replace(" ", "_")
        meta_dict[clean] = value.strip()
    # Re map keys to correct CV format
    for old_key, new_key in meta_fields.items():
        meta_dict[new_key] = meta_dict.pop(old_key)

    return meta_dict


def list_warnings(warnings, warning):
    """
    Creates a list of warnings.

        :param warnings: The current list of warnings.
        :param warning: The new warning to add to the list.
        :returns: An updated list of warnings.
    """
    warnings.append(warning)

    return warnings
    

def validate_meta_content(meta_dict, warnings):
    """
    Vaidates the metadta dictionary contents.

        :param meta_dict: Dictionary containing the grid parameters from the issue form.
        :param warnings: The current list of warnings.
        :returns: An updated list of warnings.
    """

    # Confirm that conditional fields are present
    if meta_dict["mass_data_class"] == "ens" and meta_dict["mass_ensemble_member"] == "_No response_":
        list_warnings(warnings, "WARNING: Missing required field... Where 'mass_data_class' is 'ens', " \
        "'mass_ensamble_member' must be identified.")

    parent_reliant_fields = ["branch_date_in_child", "branch_date_in_parent", "parent_experiment_id", "parent_mip", 
                             "parent_model_mip", "paernt_time_units", "parent_varient_label"]
    if meta_dict["branch_method"] == "standard":
        for field in parent_reliant_fields:
            if meta_dict[field] == "_No response_":
                list_warnings(warnings, f"WARNING: Missing required parent reliant field: {field}.")

    # Confirm that input fields are correctly formatted
    date_formatted_fields = ["base_date", "start_date", "end_date"]
    if meta_dict["branch_method"] == "standard":
        date_formatted_fields.append("branch_date_in_child", "branch_date_in_parent")
    for field in date_formatted_fields:
        try:
            parse.TimePointParser().parse(field)
        except Exception:
            list_warnings(warnings, f"WARNING: {field} is incorrectly formatted: use the format yyyy-mm-ddTHH:MM:SSZ.")

    workflow_id_format = r"^[a-z]{1,2}-[a-z]{2}\d{3}$"
    if bool(re.match(workflow_id_format, meta_dict["model_workflow_id"])) == False:
        list_warnings(warnings, "WARNING: model_workflow_id is incorrectly formatted, please use the format a-bc123 " \
        "OR ab-cd123.")

    return warnings


def create_filename(meta_dict, warnings):
    """
    Generates a filename based off of the input model workflow id and mass ensemble member.

        :param meta_dict: Dictionary containing the grid parameters from the issue form.
        :param warnings: The current list of warnings.
        :returns: New metadata filename and an updated list of warnings.
        :raises KeyError: If required key cannot be found.
    """
    try:
        model_workflow_id = meta_dict["model_workflow_id"]
        if meta_dict["mass_data_class"] == "ens":
            mass_ensemble_member_id = meta_dict["mass_ensemble_member"]
            filename = f"{model_workflow_id}-{mass_ensemble_member_id}.cfg"
        else:
            filename = f"{model_workflow_id}.cfg"
    except KeyError as e:
        list_warnings(warnings, f"WARNING: Required key missing from metadata form: {e}.")

    return filename, warnings


def sort_to_categories(meta_dict):
    """
    Sorts metadata dictionary into appropriate categories.

        :param meta_dict: Dictionary containing the metadata form contents.
        :returns: Organised metadata dictionary.
    """
    metadata_dict = {}
    data_dict = {}
    misc_dict = {}
    organised_metadata = {}

    # Categorise keys into sections that match the request.cfg mapping
    metadata_section = ["base_date", "branch_date_in_child", "branch_date_in_parent", "branch_method", "calendar", 
                "experiment_id", "institution_id", "mip", "mip_era", "parent_experiment_id", "parent_mip", 
                "parent_model_id", "parent_time_units", "parent_variant_label", "variant_label", "model_id"]
    data_section = ["end_date", "start_date", "mass_data_class", "mass_ensemble_member", "model_workflow_id"] 
    misc_section = ["atmos_timestep"]
    for key, value in meta_dict.items():
        if key in metadata_section:
            metadata_dict[key] = value
        elif key in data_section:
            data_dict[key] = value
        elif key in misc_section:
            misc_dict[key] = value

    # Re map organised keys as nested dictionaries
    organised_metadata["[metadata]"] = meta_dict
    organised_metadata["[data]"] = data_dict
    organised_metadata["[misc]"] = misc_dict

    return organised_metadata


def format_cfg_file(output_file, organised_metadata):
    """
    Write the required metadata to a structured output file.

        :param output_file: The complete path of the output file.
        :param organised_metadata: Organised metadata dictionary.
    """
    with open(output_file, "w") as f:
        for key, value in organised_metadata.items():
            f.write(f"{key}\n")
            if isinstance(value, dict):
                for k, v in value.items():
                    f.write(f"{k} = {v}\n")
                f.write("\n")


def main():
    """
    Holds the main body of the script.
    """
    warnings = []

    issue = get_issue()
    issue_body = issue['body']
    
    # Find key-value pairs and map them to dictionary format
    match = re.findall(r"### (.+?)\n\s*\n?(.+)", issue_body)
    meta_dict = create_meta_dict(match)
    print("Extracting issue body...  SUCCESSFUL")

    #validate and organise dictionary content
    warnings = validate_meta_content(meta_dict, warnings)
    organised_metadata = sort_to_categories(meta_dict)

    # Create output file
    filename, warnings = create_filename(meta_dict, warnings)
    print(filename)
    if not warnings:
        print("Validating issue form inputs...  SUCCESSFUL")
        output_dir = Path("workflow_metadata")
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{filename}"
        format_cfg_file(output_file, organised_metadata)
        print(f"Saving metadata file as {output_file}...  SUCCESSFUL")
    else:
        print("Validating issue form inputs...  FAILED")
        for warning in warnings:
            print(f" - {warning}")
        sys.exit()


if __name__ == "__main__":
    main()