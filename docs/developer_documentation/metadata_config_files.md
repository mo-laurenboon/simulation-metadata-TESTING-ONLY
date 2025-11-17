# CDDS Workflow Metadata Configuration files

## Creating metadata files

The 'process_new_metadata.yml github' action workflow maintains and edits the database of CDDS workflow metadata seen in the 'workflow_metadata' directory. This set of actions allows for users to independantly contribute to the database using a provided issue template ('metadata_config_tempalte.yml'). The workflow structure combined with the form template and built-in sanity checks ensures that users submit metadata in the correct format making it useful to other systems. 

## The workflow components

| File | Functionality | 
| -------- | --------|
| metadata_config_tempalte.yml | The issue template file that structures the user issue submission. |
| process_meta_issue.yml | The main workflow file responsible for triggering the correct python scripts and responding to inputs based on conditonal statements. |
| create_metadata_conf.py | The python script responsible for parsing the issue body, validating the contents of the issue body and generated the structured configuration file. If any invalid inputs are detected this step will fail and provide feedback to the user. |
| workflow_metadata/<model_workflow_id>.cfg | The directory and file naming structure of the metadata configuration files generated in create_metadata_conf.py |

## Input sanity checks currently performed

| Validation Check | Asociated Fields | Additional Details |
| -------- | --------| -------- |
| "mass_data_class" dependancies | "mass_data_class", "mass_ensemble_member" | Ensure that when "mass_data_class" is set to "ens", the user also provides an input to "mass_ensemble_member". |
| Parent field dependancies | "branch_method", "branch_date_in_child", "branch_date_in_parent", "parent_experiment_id", "parent_mip", "parent_model_id", "parent_time_units", "parent_variant_label" | Ensure that when "branch_method" is set to "standard", the user also provides an input to all parent fields. |
| Datetime formatting | "base_date", "start_date", "end_date", "branch_date_in_child", "branch_date_in_parent" | Ensure all datetime formatted fields adhere to 'YYY-MM-DDTHH:mm:ssZ' formatting. |
| "model_workflow_id" formatting | "model_workflow_id" | Ensures the input workflow ID follows the valid 'a-bc123' OR 'ab-cd123' formatting. |



(C) British Crown Copyright 2025, Met Office.
Please see LICENSE.md for license details.