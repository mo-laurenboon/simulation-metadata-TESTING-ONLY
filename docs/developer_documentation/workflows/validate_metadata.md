<!--(C) British Crown Copyright 2025, Met Office. Please see LICENSE.md for license details.--> 
# Validating CDDS Workflow Metadata Configuration files

## Validating metadata files

The 'validate_metadata_files.yml' workflow is designed to scan all cfg files committed from the 'process_new_metadata.yml' workflow and verify their structure and content on a nightly basis. Although 'process_new_metadata.yml' incorporates robust sanity checking at the submission level, this workflow serves as an additional level of quality assurance. Note that this script has approximately O(n) (linear) efficiency and has been found through testing to validate at a rate of approximately 0.003 seconds per configuration file.

## The workflow components

| File | Functionality | 
| -------- | --------|
| .github/workflows/validate_metadata_files.yml | The main workflow file that performs the scheduled validation. |
| scripts/validate_metadata_conf.py | The script responsible for performing all of the validations on each file. |
| scripts/constants.py | The script that stores lists of required fields and their associated structural requirements which is called upon by 'scripts/validate_metadata_conf.py'. |
| workflow_metadata/<filename>.cfg | The cfg files checked by 'scripts/validate_metadata_conf.py'. |

## Input sanity checks currently performed

| Validation Check | Associated Fields | Additional Details |
| -------- | --------| -------- |
| File structure | All | Ensure that all files contain the [metadata], [data] and [misc], as well as each section containing the expected keys, even if their values are none.
| 'mass_data_class' dependencies | 'mass_data_class', 'mass_ensemble_member' | Ensure that when 'mass_data_class' is set to 'ens', the user also provides an input to 'mass_ensemble_member'. Alternatively, when it is set to 'crum', ensure that 'mass_ensemble_member' is blank. |
| Parent field dependencies | 'branch_method', 'branch_date_in_child', 'branch_date_in_parent', 'parent_experiment_id', 'parent_mip', 'parent_model_id', 'parent_time_units', 'parent_variant_label' | Ensure that when 'branch_method' is set to 'standard', the user also provides an input to all parent fields. |
| Datetime formatting | 'base_date', 'start_date', 'end_date', 'branch_date_in_child', 'branch_date_in_parent' | Ensure all datetime formatted fields adhere to 'YYY-MM-DDTHH:mm:ssZ' formatting. |
| 'model_workflow_id' formatting | 'model_workflow_id' | Ensure the input workflow ID follows the valid 'a-bc123' OR 'ab-cd123' formatting. |
| 'variant_label' formatting | 'variant_label' | Ensure that the input variant label follows the valid regex formatting. |
| 'atmos_timestep' formatting | 'atmos_timestep' | Ensure that the input atmospheric timestep is a non-zero positive integer. |
| Blank field formatting | All | Ensure that no field has the value "_No response_": these fields should instead be left blank. |