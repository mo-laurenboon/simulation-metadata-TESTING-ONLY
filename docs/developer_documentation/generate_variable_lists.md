<!--(C) British Crown Copyright 2025, Met Office. Please see LICENSE.md for license details.--> 
# CDDS Experiment Variable Lists

## Creating variable lists

The 'generate_variable_lists.py' script is designed to scan through a given data request file for a given version (e.g. reference_information/dr-1.2.2.2_all.json) and create a plain text file for each experiment consisting of all of the variables for that experiment. These variable list files are saved in a directory structure matching 'variables/data_request_version/experiment_id.txt'.

Within this script, variable names are restructured from the given format of 'realm.variable.branding.frequency.region' to 'realm/variable_branding@frequency:stream' (e.g. atmos.cl.tavg-al-hxy-u.mon.GLB becomes atmos/cl_tavg-al-hxy-u@mon:ap5). The stream section of the variable name may not be present for all variable names since this relies on stash entries that may or may not be present. The stream component is identified using the listed 'usage_profile' that is then mapped to the corresponding stream. In the case where a usage profile is not listed, the variable filename is the same but disregards the stream element (e.g. 'realm/variable_branding@frequency').

Within the variable lists, any variables with a given priority level lower than 'high' (i.e. 'medium' or 'low' priority variables) are commented out and labelled (e.g. #ocean/osaltpadvect_tavg-ol-hxy-sea@yr # priority=low). Similarly, any variables that contain the label 'do-not-produce' are also commented out and marked as such. Variables with this label cannot be produced and hence are commented out irrespective of their priority level in order to avoid errors within the CDDS pipeline. Commented out variables will only show either 'do-not-produce' or 'priority=priority_label' with 'do-not-produce' taking precedence over priority level: variables should never be tagged with both. 

## File Dependencies 

| File | Functionality | Additional Details |
| -------- | --------| --------|
| scripts/generate_variable_lists.py | The main script that generates the variable list files. | - |
| reference_information/dr-1.2.2.2_all.json | Experiment data source file. | This is a required file called upon by the main script. This source file provides the list of experiments, the variables used in each experiment, the priority level of each variable and the data request version. It is expected for this file to be occasionally updated as well as new files following this format to be added upon the creation of new versions. |
| reference_information/mappings.json | Variable data source file. | This is a required file called upon by the main script. This source file provides the model, title, labels and stream for each variable. |
| variables_glb/<version_number>/*.txt | Output directory for the generated variable lists | A new directory is created for each new data request version leaving variable lists for previous versions stored safely in easily accessible directories. |