<!--(C) British Crown Copyright 2025, Met Office. Please see LICENSE.md for license details.--> 
# CDDS Workflow Metadata Configuration files

## Creating metadata files

The 'process_new_metadata.yml' GitHub action workflow maintains and edits the database of CDDS workflow metadata seen in the 'workflow_metadata' directory. This set of actions allows for users to independently contribute to the database using a provided issue template ('add_workflow_metadata.yml'). The workflow structure combined with the form template and built-in sanity checks ensures that users submit metadata in the correct format, making it compatible with other systems. 

## The workflow components

| File | Functionality | 
| -------- | --------|
| .github/ISSUE_TEMPLATE/add_workflow_metadata.yml | The issue template file that structures the user issue submission. |
| .github/workflows/process_new_metadata.yml | The main workflow file responsible for triggering the correct python scripts and responding to inputs based on conditional statements. |
| scripts/create_metadata_conf.py | The python script responsible for parsing the issue body, validating the contents of the issue body and generated the structured configuration file. If any invalid inputs are detected this step will fail and provide feedback to the user. |
| workflow_metadata/<model_workflow_id>.cfg | The directory and file naming structure of the metadata configuration files generated in 'create_metadata_conf.py'. |
| scripts/generate_metadata_tables.py | The python script responsible for generating the searchable web view HTML file using the generated metadata files in 'workflow_metadata/<model_workflow_id>.cfg'. |
| metadata_tables/index.html | The HTML file created in 'scripts/generate_metadata_tables.py'. |
| scripts/constants.py | The HTML configuration and formatting script called upon by 'scripts/generate_metadata_tables.py'. |
| .github/workflows/update_webview.yml | The workflow responsible for updating the HTML file ready to be deployed to pages. This workflow calls on 'scripts/generate_metadata_tables.py' and is triggered by the completion of the '.github/workflows/process_meta_issue.yml workflow'. |
| .github/workflows/deploy_pages.yml | The workflow responsible for publishing the updated HTML to GitHub pages. This workflow is triggered by the completion of '.github/workflows/update_webview.yml'. |

## Input sanity checks currently performed

| Validation Check | Associated Fields | Additional Details |
| -------- | --------| -------- |
| 'mass_data_class' dependencies | 'mass_data_class', 'mass_ensemble_member' | Ensure that when 'mass_data_class' is set to 'ens', the user also provides an input to 'mass_ensemble_member'. |
| Parent field dependencies | 'branch_method', 'branch_date_in_child', 'branch_date_in_parent', 'parent_experiment_id', 'parent_mip', 'parent_model_id', 'parent_time_units', 'parent_variant_label' | Ensure that when 'branch_method' is set to 'standard', the user also provides an input to all parent fields. |
| Datetime formatting | 'base_date', 'start_date', 'end_date', 'branch_date_in_child', 'branch_date_in_parent' | Ensure all datetime formatted fields adhere to 'YYY-MM-DDTHH:mm:ssZ' formatting. |
| 'model_workflow_id' formatting | 'model_workflow_id' | Ensures the input workflow ID follows the valid 'a-bc123' OR 'ab-cd123' formatting. |
| 'variant_label' formatting | 'variant_label' | Ensure that the input variant label follows the valid regex formatting. |
| 'atmos_timestep' formatting | 'atmos_timestep' | Ensure that the input atmospheric timestep is a non-zero positive integer. |
