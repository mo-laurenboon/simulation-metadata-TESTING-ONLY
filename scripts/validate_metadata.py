# (C) British Crown Copyright 2026, Met Office.
# Please see LICENSE.md for license details.

import metomi.isodatetime.parsers as parse

from configparser import ConfigParser
from metomi.isodatetime.exceptions import ISO8601SyntaxError, IsodatetimeError
from metomi.isodatetime.data import Calendar

from constants import REQUIRED, PARENT_REQUIRED, DATETIME_FIELDS, REGEX_DICT, CMOR_CV_JSON


class Validate:
    """A class for validate metadata files."""
    def __init__(self, metadata_info):
        """Setup self"""
        self.errors = {}
        self.warnings = {}

        if isinstance(metadata_info, dict):
            self.metadata_info = metadata_info
        elif isinstance(metadata_info, ConfigParser):
            self.metadata_info = self._config_to_dict(metadata_info)

    def _config_to_dict(self, metadata_info):
        """Converts ConfigParser objects to nested dictionary."""
        config_dict = {}
        for section in metadata_info:
            config_dict.update({section: {}})
            for key, value in metadata_info[section].items():
                config_dict[section].update({key: value})

        return config_dict

    def set_calendar(self):
        """Sets the metomi.isodatetime calendar. If the calendar is not '360_day' or 'proleptic_gregorian' an error is
        noted to be returned to the user."""
        calendar_type = self.metadata_info["metadata"].get("calendar")
        if calendar_type == "360_day":
            Calendar.default().set_mode(calendar_type)
        elif calendar_type == "proleptic_gregorian":
            Calendar.default().set_mode("gregorian")
        else:
            self.errors["calendar"] = "incompatible calendar: expected 360_day or proleptic_gregorian"

    def check_for_missing_inputs(self):
        """Checks for missing inputs in any of the required fields."""
        missing = []
        for parameter in REQUIRED:
            for item in self.metadata_info.keys():
                if parameter in self.metadata_info[item].keys():
                    section = item
                    break

            if self.metadata_info[section].get(parameter) in (None, "", "_No response_"):
                missing.append(f"Missing field {parameter}")

        if missing:
            self.errors["missing_required_field"] = missing

    def check_parent_fields(self):
        """Checks that parent attributes are present if branch method is 'stanard' and checks that they are not present
        if branch method is 'no parent'."""
        missing_parent_fields = []
        unexpected_parent_fields = []
        branch_method = self.metadata_info["metadata"].get("branch_method")

        if branch_method == "standard":
            for parent_key in PARENT_REQUIRED:
                if self.metadata_info["metadata"].get(parent_key) in (None, "", "_No response_"):
                    missing_parent_fields.append(f"missing required parent field: {parent_key}")
        elif branch_method == "no parent":
            for parent_key in PARENT_REQUIRED:
                if self.metadata_info["metadata"].get(parent_key) not in (None, "", "_No response_"):
                    unexpected_parent_fields.append(f"unexpected field: {parent_key}")

        if missing_parent_fields:
            self.errors["missing_parent_field"] = missing_parent_fields
        if unexpected_parent_fields:
            self.errors["unexpected_parent_field"] = unexpected_parent_fields

    def check_mass_data_class_attributes(self):
        """Checks that attributes related to mass_data_class are present as expected. If mass_data_class is 'crum' no
        mass ensemble member ID should be given. If mass_data_class is 'ens' then a mass ensemble member ID is required.
        """
        mass_data_class = self.metadata_info["data"].get("mass_data_class")
        mass_ensemble_member = self.metadata_info["data"].get("mass_ensemble_member")

        if mass_data_class == "ens" and not mass_ensemble_member:
            self.errors["missing_mass_field"] = f"missing field: mass_ensemble_member"
        if mass_data_class == "crum" and mass_ensemble_member:
            self.errors["unexpected_mass_field"] = f"unexpected field: mass_ensemble_member"

    def normalise_datetime(self, datetime: str, field: str):
        """Normalises any acceptable datetime string into yyyy-mm-ddTHH:MM:SSZ format.

        Parameters
        ----------
        datetime : str
            The datetime string to normalise.
        field : str
            The datetime field being normalised.

        Returns
        -------
        str
            The normalised string.
        """
        try:
            parser = parse.TimePointParser()
            normalised_str = str(parser.parse(datetime)).replace("+01:00", "Z")  # Handles changes daylight saving hours
        except (IsodatetimeError, ISO8601SyntaxError):
            self.errors["datetime"] = f"invalid datetime format for {field}"
            normalised_str = datetime

        return normalised_str

    def check_datetime_fields(self):
        """Checks that all datetime inputs are of the expected format: 'YYYY-MM-DDTHH:mm:ssZ'."""
        # Check parent time fields only when branch_method is 'standard'. Otherwise, these fields should be none.
        if self.metadata_info["metadata"].get("branch_method") == "standard":
            DATETIME_FIELDS.add("branch_date_in_child")
            DATETIME_FIELDS.add("branch_date_in_parent")
        for field in DATETIME_FIELDS:
            for item in self.metadata_info.keys():
                if field in self.metadata_info[item].keys():
                    section = item
                    break
            normal_datetime = Validate.normalise_datetime(self, self.metadata_info[section].get(field),
                                                                       field)
            self.metadata_info[section][field] = normal_datetime

    def check_model_workflow_id(self):
        """Checks that model_workflow_id follows the expected format of 'a-bc123'(most common) or 'ab-cd123'(rare but
        not impossible)."""
        if not REGEX_DICT["workflow_pattern"].fullmatch(self.metadata_info["data"].get("model_workflow_id")):
            self.errors["workflow_id_format"] = (
                "model workflow ID is incorrectly formatted: expected a-bc123 or ab-cd123"
            )

    def check_variant_labels(self):
        """Checks that variant labels follow the expected regex r{[1-9]}i{[1-9]}p{[1-9]}f{[1-9]}."""
        labels = [self.metadata_info["metadata"].get("variant_label")]
        # Check the parent variable label only if branch method is standard. Otherwise this should be None.
        if self.metadata_info["metadata"].get("branch_method") == "standard":
            labels.append(self.metadata_info["metadata"].get("parent_variant_label"))

        for label in labels:
            if not REGEX_DICT["variant_pattern"].fullmatch(label):
                self.errors["label_format"] = (
                    "variant label or parent variant label is incorrectly formatted: expected r1i1p1f1 like format"
                )

    def check_atmos_timestep(self):
        """Checks that the atmospheric timestep is of logical value ( a postivie, non-zero integer )."""
        atmos_timestep = self.metadata_info["misc"].get("atmos_timestep")
        if not atmos_timestep.isdigit() or int(atmos_timestep) < 0:
            self.errors["timestep_logic"] = "atmospheric timestep is invalid"

    def check_start_end_logic(self):  # TO DO: Clean this one up
        """Checks that start date and end date are logical."""
        parser = parse.TimePointParser()
        start_date = self.metadata_info["data"].get("start_date")
        end_date = self.metadata_info["data"].get("end_date")
        base_date = self.metadata_info["metadata"].get("base_date")
        start_date_err_msg = "invalid datetime format for start_date"
        end_date_err_msg = "invalid datetime format for end_date"

        try:
            if start_date_err_msg not in self.errors["datetime"] and end_date_err_msg not in self.errors["datetime"]:
                if parser.parse(end_date) < parser.parse(start_date):
                    self.errors["datetime_logic"] = "end date cannot be earlier than start date"
                if parser.parse(start_date) < parser.parse(base_date):
                    self.errors["datetime_logic"] = "Start date cannot be earlier than the base date: 1850-01-01"
        except KeyError:
            if parser.parse(end_date) < parser.parse(start_date):
                self.errors["datetime_logic"] = "end date cannot be earlier than start date"
            if parser.parse(start_date) < parser.parse(base_date):
                self.errors["datetime_logic"] = "Start date cannot be earlier than the base date: 1850-01-01"

    def check_fixed_fields(self):
        """Checks that all fields that can only be a fixed value or one of a set of fixed values are as expected."""
        unrecognised_inputs = []

        # Check that branch method is either 'no parent' or 'standard'
        if self.metadata_info["metadata"].get("branch_method") not in ("no parent", "standard"):
            unrecognised_inputs.append("branch_method must have the value 'no parent' or 'standard'")

        # Confirm that mip era and parent mip era are both CMIP7
        if self.metadata_info["metadata"].get("branch_method") == "standard":
            eras = (self.metadata_info["metadata"].get("mip_era"), self.metadata_info["metadata"].get("parent_mip_era"))
            for era in eras:
                if era != "CMIP7":
                    unrecognised_inputs.append("mip_era and parent_mip_era must have the value 'CMIP7'")

        # Confirm that model ID is valid
        model_id = self.metadata_info["metadata"].get("model_id")
        if model_id not in ("UKCM2-0-LL", "UKCM2a-0-HH", "UKESM1-3-LL", "HadGEM3-GC31-MM"):
            unrecognised_inputs.append("model_id must have the value 'UKCM2-0-LL', 'UKCM2a-0-HH', 'UKESM1-3-LL' or "
                                    "'HadGEM3-GC31-MM'")

        if self.metadata_info["metadata"].get("branch_method") == "standard":
            # The parent model ID and model ID should match
            if model_id != self.metadata_info["metadata"].get("parent_model_id"):
                unrecognised_inputs.append(f"parent_model_id must match model_id '{model_id}'")

            if self.metadata_info["metadata"].get("parent_time_units") != "days since 1850-01-01":
                unrecognised_inputs.append("parent_time_units must have the value 'days since 1850-01-01'")

        # Confirm that mass_data_class is either ens or crum (default)
        if self.metadata_info["data"].get("mass_data_class") not in ("ens", "crum"):
            unrecognised_inputs.append("mass_data_class must have the value 'ens' or 'crum'")

        if unrecognised_inputs:
            self.errors["unrecognised_input"] = unrecognised_inputs

    def check_cvs(self):
        """Checks that inputs are present within the CV and are the expected value for a given experiment. Each
        experiment is expected to have one of a specific list of parent experiments, mips etc. This must be checked and
        consistent to avoid errors in CDDS. There may be cases where what is expected by the CVs does not match what was
        used in real life. These cases should be handled independently so an erata can be issued noting that the
        metadata for that workflow is not accurate. Complete transparency is important in these situations."""
        branch_method = self.metadata_info["metadata"].get("branch_method")
        cv_errors = []

        institution = self.metadata_info["metadata"].get("institution_id")
        if institution not in CMOR_CV_JSON["CV"]["institution_id"]:
            cv_errors.append(f"institution_id '{institution}' could not be found in the cvs")

        experiment = self.metadata_info["metadata"].get("experiment_id")
        if experiment not in CMOR_CV_JSON["CV"]["experiment_id"]:
            cv_errors.append(f"experiment id '{experiment}' could not be found in the cvs")
            self.errors["cv_error"] = cv_errors
            return

        experiment_cv_info = CMOR_CV_JSON["CV"]["experiment_id"][experiment]
        mip = self.metadata_info["metadata"].get("mip")
        mip_in_cv = experiment_cv_info["activity_id"]
        if mip not in mip_in_cv:
            cv_errors.append(f"mip '{mip}' does not match one of the expected values '{mip_in_cv}' given in the cvs")

        # Check parent fields only when branch method is 'standard', otherwise these should be None.
        if branch_method == "standard":
            parent_experiment = self.metadata_info["metadata"].get("parent_experiment_id")
            parent_experiment_in_cv = experiment_cv_info["parent_experiment_id"]
            if parent_experiment not in parent_experiment_in_cv:
                cv_errors.append(
                    f"parent experiment id '{parent_experiment}' does not match one of the expected values "
                    f"'{parent_experiment_in_cv}' given in the cvs"
                )
            parent_mip = self.metadata_info["metadata"].get("parent_mip")
            parent_mip_in_cv = experiment_cv_info["parent_activity_id"]
            if parent_mip not in parent_mip_in_cv:
                cv_errors.append(f"parent mip '{parent_mip}' does not match one of the expected values "
                                f"'{parent_mip_in_cv}' given in the cvs")

        # Check whether the end date matches the year given in the CVs. This should only produce a warning.
        cv_end_year = experiment_cv_info["end_year"]
        if cv_end_year:
            end_year = self.metadata_info["data"].get("end_date").split("-")[0]
            if str(end_year) != str(cv_end_year):
                self.warnings["end_date"] = ("end date does not match the value in the CVs. Expected an end year of "
                                        f"{cv_end_year}, got {end_year}")

        if cv_errors:
            self.errors["cv_error"] = cv_errors

    def validate_all(self):
        """Wrapper function to handle all validation tasks."""
        Validate.check_for_missing_inputs(self)
        Validate.check_parent_fields(self)
        Validate.check_datetime_fields(self)
        Validate.check_start_end_logic(self)
        Validate.check_fixed_fields(self)
        Validate.check_cvs(self)
        Validate.check_mass_data_class_attributes(self)
        Validate.check_model_workflow_id(self)
        Validate.check_variant_labels(self)
        Validate.check_atmos_timestep(self)

        return self
