
<!--(C) British Crown Copyright 2025-2026, Met Office. Please see LICENSE.md for license details.--> 
# CDDS Simulation Metadata For CMIP7
[![Deploy static content to Pages](https://github.com/UKNCSP/CDDS-simulation-metadata/actions/workflows/deploy_pages.yml/badge.svg)](https://github.com/UKNCSP/CDDS-simulation-metadata/actions/workflows/deploy_pages.yml)

CURRENT MAPPINGS FILE VERSION: v2026-08-14

CURRENT DATA REQUEST VERSION: 1.2.2.5

This CDDS simulation metadata repository is designed to process and store CMIP7 workflow metadata. If you have a new workflow that you wish to register, please fill out the issue form marked 'Add/Modify Workflow Metadata'. Upon form completion, you will receive a notification from our GitHub actions bot confirming your submission. If you wish to view the workflow metadata currently stored in the database, you can do so here: [CMIP7 Workflow Metadata](https://ukncsp.github.io/CDDS-simulation-metadata/ "A link to our GitHub pages"). Note that this table consists of only key metadata: to view the full metadata, click the link shown on the model workflow ID of interest. Any new additions may take up to an hour to become available to view and search on [CMIP7 Workflow Metadata](https://ukncsp.github.io/CDDS-simulation-metadata/ "A link to our GitHub pages").

> **IMPORTANT:
>  Do not edit any request or variable list files directly within the repository. Do not merge any pull requests without review from a CDDS team member. To make any changes, you must first download it and only make edits to your local copy. If you need to update or remove information within a workflow metadata configuration file, please open an issue and include the relevant model workflow ID, along with a clear description of the requested change.**

## Registering Workflow Metadata
To register the metadata for a new workflow or edit the metadata for an existing workflow, please navigate to the issue tab at the top of the page, click "new issue" and select "Add/Modify Workflow Metadata". This will open up an issue form for you to fill in. Once filled in , click the create button in the bottom right of the page. This will open an issue that will be automatically validated and processed. You will recieve an email from the github actions bot upon completion confirming your workflow registration and the closure of the issue (this typically takes up to a few minutes). Any errors will be communicated to you by the github actions bot in the comments of your issue which will remain open. If you make an error on your issue form, please edit the issue body with your changes or submit a new form containing the correct information. This will create a pull request that will be reviewed by a member of our team. It would be valuable to us if a brief comment could be left on the pull request explaining the reason for the change. For additional user guidance please see the wiki.

### The 'Add/Modify Workflow Metadata' Issue Form
Please see below for additional information on what each of the different fields in the form are, how we use them and some example inputs.

#### Standard Fields
| Field | What is it? | Example |
| ----- | ----- | ----- |
| Issue Type | This helps us to quickly identify if you are adding metadata for a new workflow or wanting to edit existing information. |  |
| Model Workflow ID | Also sometimes known as the "suite ID". This is a unique identifier used to track an individual workflow. This should generally take the format "u-ab123" but may occasionally look something like "ab-cd123". | "u-dv623" |
| Activity ID | Also sometimes known as the "MIP". This is a standardised, short identifier that specifies which overarching sub-project or MIP (Model Intercomparison Project) a climate simulation belongs to. | "CMIP" |
| Experiment ID | The standardised name used to identify a specific experiment. Please note that case is important here. | "piControl" |
| Model ID | Also sometimes known as the "source ID". This is the short name identifying the model used in the workflow. | |
| Variant Label | This helps us to distinguish between multiple climate simulations run by the same modelling centre and indicates specific changes in how the model was set up or run. This takes the form of r{\d}i{\d}p{\d}f{\d} (e.g. r1i1p1f1) where each component of the label tells us different things. Realization (r): Distinguishes between those that are identical in physics and forcing but start from different initial conditions. Initialisation (i): Differentiates runs that use different initialisation procedures or data assimilation techniques. Physics (p): Identifies variations in the model parameterisations or physics (e.g. changing cloud physics or atmospheric convection schemes). Forcing (f): Indicates runs that apply different external forcing agents (such as altered greenhouse gas emissions or different aerosol data). | "r1i1p1f1" |
| Start Date | The processing start date. This should take the form YYYY-MM-DDThh:mm:ssZ | "1900-01-01T00:00:00Z" |
| End Date | The processing end date. This should take the form YYYY-MM-DDThh:mm:ssZ | "2100-01-01T00:00:00Z" |
| Branch Method | This tells us whether the workflow uses a parent experiment for any initial conditions or not. If the workflow does use a parent experiment you should select "standard", if not, use "no parent". | |
| Calendar Type | The type of calendar used in the workflow. | |
| Institution ID | This is used to identify the specific climate modelling centre or research institution that produced a climate dataset. Please select the default "UKNCSP" unless discussed with the CMIP project team. | |
| MIP Era | This is the era of the model intercomparison project. We expect this to be CMIP7 for all submissions. | |
| Atmospheric Timestep | This is the atmospheric time step used in seconds. This is usually 1200 for n=96, 900 for n=216 and 600 for n=512. | 
| Mass Data Class | This is the root of the location of input dataset on MASS. This is will likely be "crum" for most submissions. When using the mass data class of "crum", the "Mass Ensemble Member ID" field at the base of the form can be safely ignored. However, if using a data class of "ens" this is required. If data exists only on JASMIN, please leave this as the default "crum": this will not affect your processing. | |
| Additional Notes | This is an optional field that gives you the opportunity to note any additional information that you feel is important but not covered elsewhere in the form. Please note this is a public repository, do not include any sensitive information or explicit data paths. | "This data is stored on JASMIN" |

#### Conditional fields
| Field | What is it? | Condition | Example |
| ----- | ----- | ----- | ----- |
| Child Branch Date | The date in this simulation where the initial conditions from parent were applied to the experiment for use as a foundation. | Required when using a `branch method = standard`. | "1900-01-01T00:00:00Z" |
| Parent Branch Date | The date in the parent simulation where the initial conditions were taken from and applied to the experiment for use as a foundation. | Required when using a `branch method = standard`. | "1850-01-01T00:00:00Z" |
| Parent Experiment ID | The experiment ID for the parent as described in the standard fields section. | Required when using a `branch method = standard`. | "piControl-spinup" |
| Parent Activity ID | The activity ID for the parent as described in the standard fields section. | Required when using a `branch method = standard`. | "CMIP" |
| Parent MIP Era | The MIP Era for the parent as described in the standard fields section.. | Required when using a `branch method = standard`. | |
| Parent Model ID | The Model ID for the parent as described in the standard fields section. This should match the Model ID given for the experiment | Required when using a `branch method = standard`. | "UKCM2-0-LL" |
| Parent Time Units | The time units for the parent experiment. We expect this to be "days since 1850-01-01" for most submissions. | Required when using a `branch method = standard`. | | 
| Parent Variant Label | The variant label of the parent as described in the standard fields section. | Required when using a `branch method = standard`. | "r1i1p1f1" |
| Mass Ensemble Member ID | The mass ensemble member identifier. | Required when using ` Mass Data Class = ens`. | |
