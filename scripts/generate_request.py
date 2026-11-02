# (C) British Crown Copyright 2026, Met Office.
# Please see LICENSE.md for license details.
"""A script to generate a functional request file using information provided from a given workflow metadata
configuration file.

NOTE: This script relies on inputs given from '.github/ISSUE_TEMPLATE/generate_request_file.yml' and is utilised by the
'.github/workflows/generate_request.yml' workflow automatically upon issue submission.

"""
import os
import re
import sys

from configparser import ConfigParser, SectionProxy
from pathlib import Path
from datetime import datetime

from constants import MIP_TABLE_DIR, CMOR_CV_JSON, DR_VERSION, LATEST_CDDS_RELEASE

WORKFLOW_METADATA_DIR = "workflow_metadata"
VARIABLE_LIST_DIR = f"variables/v{DR_VERSION}"
REQUEST_TEMPLATE = {
    "metadata": {
        "base_date": "",
        "branch_method": "",
        "calendar": "",
        "experiment_id": "",
        "institution_id": "",
        "license": "CC-BY-4.0",
        "mip": "",
        "mip_era": "",
        "model_id": "",
        "variant_label": "",
        "branch_date_in_child": "",
        "branch_date_in_parent": "",
        "parent_experiment_id": "",
        "parent_mip": "",
        "parent_mip_era": "",
        "parent_model_id": "",
        "parent_time_units": "",
        "parent_variant_label": "",
    },
    "netcdf_global_attributes": {
        "data_specs_version": "MIP-DS7.1.0.0",
        "drs_specs": "MIP-DRS7",
        "region": "glb"
    },
    "common": {
        "external_plugin": "",
        "external_plugin_location": "",
        "log_level": "INFO",
        "mip_table_dir": MIP_TABLE_DIR,
        "mode": "strict",
        "package": "",
        "root_ancil_dir": "$CDDS_ETC/ancil/",
        "root_hybrid_heights_dir": "$CDDS_ETC/vertical_coordinates/",
        "root_replacement_coordinates_dir": "$CDDS_ETC/horizontal_coordinates/",
        "root_proc_dir": "$CDDS_DATA/$USER/proc",
        "root_data_dir": "$CDDS_DATA/$USER/data",
        "sites_file": "$CDDS_ETC/cfmip2/cfmip2-sites-orog.txt",
        "standard_names_dir": "$CDDS_ETC/standard_names/",
        "standard_names_version": "93",
        "workflow_basename": ""
    },
    "data": {
        "data_version": f"v{datetime.today().strftime('%Y%m%d')}",
        "end_date": "",
        "mass_data_class": "",
        "mass_ensemble_member": "",
        "model_workflow_id": "",
        "output_mass_suffix": "production",
        "output_mass_root": "moose:/adhoc/projects/cdds",
        "start_date": "",
        "streams": "",
        "variable_list_file": ""
    },
    "misc": {
        "atmos_timestep": ""
    },
    "conversion": {
        "continue_if_mip_convert_failed": "False",
        "cylc_args": "-v",
        "mip_convert_plugin": "",
        "skip_extract": "False",
        "skip_extract_validation": "False",
        "skip_configure": "False",
        "skip_qc": "False",
        "skip_archive": "False"
    }
}


def process_issue_form() -> dict[str, str]:
    """Extracts the issue body from the submitted issue form.

    Returns
    -------
    dict[str, str]
        The issue body as a dictionary.
    """
    issue_info = {}
    issue_body = os.environ.get("ISSUE_BODY")
    match = re.findall(r"### (.+?)\n\s*\n?(.+)", issue_body)
    for key, value in set(match):
        clean = key.strip().lower().replace(" ", "_")
        issue_info[clean] = value.strip()

    return issue_info


def identify_mip_convert_plugin(metadata: SectionProxy) -> str:
    """Identifies the relevant MIP convert plugin using the model id given in the workflow metadata configuration file.

    Parameters
    ----------
    metadata: SectionProxy
        The metadata section of the workflow metadata configuration file.

    Returns
    -------
    str
        The MIP convert plugin.

    Raises
    ------
    RuntimeError
        If a valid plugin cannot be identified from the given model_id.
    """
    model = metadata["model_id"]
    if model in ["UKCM2-0-LL", "UKCM2a-0-HH"]:
        return "UKCM2"
    elif model == "UKESM1-3-LL":
        return "UKESM1p3"
    elif model == "HadGEM3-GC31-MM":
        return "HadGEM3"
    else:
        raise RuntimeError(f"Unable to map model {model} to a valid plugin")


def update_request(request: dict, config: ConfigParser, issue_info: dict) -> dict:
    """Blanket updates the request template with the information given in the configuration file.

    Parameters
    ----------
    request: dict
        The request template fields and values as a dictionary.
    config: ConfigParser
        The full workflow metadata configuration file.
    issue_info: dict
         The issue body as a dictionary.

    Returns
    -------
    dict
        The fully populated request template.
    """
    sections = ["metadata", "data", "misc"]

    for section in sections:
        for key in request[section]:
            if key in config[section]:
                request[section][key] = config[section][key]

    if request["metadata"]["calendar"] == "gregorian":
        request["metadata"]["calendar"] = "proleptic_gregorian"

    var_file = (f'{VARIABLE_LIST_DIR}/{config["data"]["model_workflow_id"]}_{config["metadata"]["experiment_id"]}'
                f'_{config["metadata"]["model_id"]}.txt')
    basename = (f'{config["metadata"]["model_id"]}_{config["metadata"]["experiment_id"]}'
                f'_{config["metadata"]["variant_label"]}_{issue_info["package_name"]}')
    request["data"]["variable_list_file"] = f"<UPDATE_WITH_PATH>/{var_file}"
    request["data"]["streams"] = issue_info["streams"].replace(",", "")
    request["common"]["workflow_basename"] = basename
    request["common"]["package"] = issue_info["package_name"]
    request["conversion"]["mip_convert_plugin"] = identify_mip_convert_plugin(config["metadata"])

    return request


def validate_request(request: dict) -> list:
    """Validates the request file content against the cmor CMIP7 cvs.

    Parameters
    ----------
    request: dict
        request: dict
        The fully populated request template fields and values as a dictionary.

    Returns
    -------
    list
        A list containing any validation errors
    """
    cv = CMOR_CV_JSON
    cv_errors = []

    if request["metadata"]["institution_id"] not in cv["CV"]["institution_id"]:
        cv_errors.append(f"institution_id could not be found in the cvs")
    if request["metadata"]["license"] not in cv["CV"]["license"]["license_id"]:
        cv_errors.append(f"license does not match one of the expected values given in the cvs")
    if request["metadata"]["experiment_id"] not in cv["CV"]["experiment_id"]:
        cv_errors.append(f"experiment id could not be found in the cvs")
        raise RuntimeError(f"Unable to locate experiment id against cvs, unable to continue validation:\n{cv_errors}")

    experiment_cv_info = cv["CV"]["experiment_id"][request["metadata"]["experiment_id"]]
    if request["metadata"]["mip"] not in experiment_cv_info["activity_id"]:
        cv_errors.append(f"mip does not match one of the expected values given in the cvs")
    if request["metadata"]["branch_method"] == "standard":
        if request["metadata"]["parent_experiment_id"] not in experiment_cv_info["parent_experiment_id"]:
            cv_errors.append(f"parent experiment id does not match one of the expected values given in the cvs")
        if request["metadata"]["parent_mip"] not in experiment_cv_info["parent_activity_id"]:
            cv_errors.append(f"parent mip does not match one of the expected values given in the cvs")

    return cv_errors


def write_request(filename_prefix, data: SectionProxy, request: dict) -> str:
    """Writes out the fully populated REQUEST TEMPLATE dictionary to a configuration file format.

    Parameters
    ----------
    data: SectionProxy
        The data section of the workflow metadata configuration file.
    request: dict
        The fully populated request template fields and values as a dictionary.

    Returns
    -------
    str
        The request filename.
    """
    filename = f"{filename_prefix}_request_{data['model_workflow_id']}_{request['common']['package']}.cfg"
    with open(Path("requests") / filename, "w") as f:
        f.write(f"# At the point of request generation the latest CDDS release is {LATEST_CDDS_RELEASE}.\n")
        f.write("# You can activate this by running the command `source ~cdds/bin/setup_env_for_cdds "
                f"{LATEST_CDDS_RELEASE.lstrip('v')}`\n")
        for section_header, content in request.items():
            f.write(f"[{section_header}]\n")
            if isinstance(content, dict):
                for parameter, value in content.items():
                    f.write(f"{parameter} = {value}\n")
                f.write("\n")

    return filename


def generate_request_config() -> None:
    """Generates a functional request file using the information given in the workflow metadata issue form."""
    issue_info = process_issue_form()
    request = REQUEST_TEMPLATE

    # If the user needs a JASMIN request, an additional field is needed to identify their JASMIN account (to be updated
    # locally by the user once the request has been downloaded).
    if issue_info["request_type"] == "JASMIN Request":
        request["conversion"].update({"jasmin_account": ""})
        filename_prefix = "jasmin"  # Required to help immedietly identify JASMIN based requests
    elif issue_info["request_type"] == "Standard Met Office Request":
        filename_prefix = "mo"  # Required to help immedietly identify Met Office based requests
    else:
        err_msg = (f"Unrecognised request type: '{issue_info["request_type"]}'. Expected 'JASMIN Request' or "
                   "'Standard Met Office Request'")
        with open(os.environ["GITHUB_OUTPUT"], "a") as gh:
            gh.write(f"err_msg={err_msg}")
            sys.exit(1)

    # Identify the workflow metadata config file associated with the workflow ID given in the issue. This file must
    # exist to proceed.
    cfg_file = f"{WORKFLOW_METADATA_DIR}/{issue_info['model_workflow_id']}.cfg"
    if not os.path.exists(cfg_file):
        err_msg = (f"The given model workflow ID {issue_info['model_workflow_id']} does not have an associated "
                   "metadata configuration file.")
        with open(os.environ["GITHUB_OUTPUT"], "a") as gh:
            gh.write(f"err_msg={err_msg}")
            sys.exit(1)
    config = ConfigParser()
    config.read(cfg_file)

    # Populate the request template with values from the workflow metadata config file and re validate where possible.
    update_request(request, config, issue_info)
    errors = validate_request(request)
    filename = write_request(filename_prefix, config["data"], request)
    delim = "EOF"

    # Note the relative path to the generated request and assocaited variable list to help with user navigation.
    with open(os.environ["GITHUB_OUTPUT"], "a") as gh:
        gh.write(f"var_list={request['data']['variable_list_file'].replace("<UPDATE_WITH_PATH>/", "")}\n")
        gh.write(f"request_filename={filename}\n")
        gh.write(f"errors<<{delim}\n")
        gh.write(f"{errors}\n")
        gh.write(f"{delim}\n")

    if errors:
        sys.exit(1)


if __name__ == "__main__":
    generate_request_config()
