<!--(C) British Crown Copyright 2025, Met Office. Please see LICENSE.md for license details.--> 
# Fixing An Invalid Entry On An 'Add/Modify Workflow Metadata' Issue Form

Once an issue form is submitted, the field entries go through various checks to ensure that they are valid.
In the event that any invalid entries are found, a comment will be left by the github actions bot under the issue that was created when you filled out your issue form. This comment should provide an error message and briefly explain why it is considered invalid. For more information on how to go about fixing these issues, please see the user documentation: [Fixing A Mistake On An 'Add/Modify Workflow Metadata' Issue Form](https://github.com/UKNCSP/CDDS-simulation-metadata/blob/main/docs/user_documentation/fixing_issue_form_mistakes.md). Please see the table below for a more detailed explanation as to why your entry may have been flagged as invalid.

If you are unable to resolve a validation error and you believe your input to be valid, please raise an issue or contact a member of @UKNCSP/CDDS. Validation criteria may continue to change and become more inclusive of edge cases as they are discovered.

# More information on what different error messages mean...
| Error Message |  Additional Details |
| -------- | -------- |
| "Incompatible calendar: expected 360_day or gregorian" | CDDS currently only accepts 2 types of calendar '360_day' or 'gregorian'. Attempting to input any other calendar type will result in the input being flagged as invalid. These inputs are case and whitespace sensitive, if you have input a valid option but it is still being flagged as invalid, please check that the input has been written exactly as shown: '360_day' or 'gregorian'. Inputs such as '360 day' or 'Gregorian' will result in an error. |
| "Invalid datetime format" | The datetime input is invalid and has triggered an [IsodatetimeError](https://github.com/metomi/isodatetime/blob/master/metomi/isodatetime/exceptions.py) or [ISO8601SyntaxError](https://github.com/metomi/isodatetime/blob/master/metomi/isodatetime/exceptions.py). The script expects a yyyy-mm-ddTHH:MM:SSZ format, but can parse shortened versions (e.g. yyyy or yyyy-mm). Issues commonly arise if the user provides a full datetime string but either misses out or makes a typo concerning the T and Z separators. |
| "Missing field" | This is a general error that arises when a required field has no entry. This could be triggered if a core field is missed or in a case where the mass data class has been set to "ens" but no ensemble member ID has been provided. |
| "Missing required parent field" | This is flagged when core parent branch information is missing. These fields are conditional and are only required for workflows with a standard branch method. If this error is appearing for a "no parent" branching method, please verify that you have selected "no parent" under the branching method field on the form. |
| "Unexpected field" | An unnecessary or contradicting field has been provided. Common are if the branching method has been set to "no parent" but parent information has been provided, or if the mass data class has been set to "crum" but a mass ensemble ID has been provided. |
| "Model workflow ID is incorrectly formatted: expected a-bc123" | The model workflow ID does not follow the expected regular expression (typically of the form a-bc123). In some rare cases, the workflow ID may follow the form mi-ab123. |
| "Variant label is incorrectly formatted: expected r1i1p1f2 like format" | Much like the model workflow ID, this error is raised when the variant label does not follow the expected regular expression. |
| "Atmospheric timestep is invalid" | The atmospheric timestep provided is either a non-integer or an impossible value (e.g. is negative). |
| "End date cannot be earlier than start date" | The input start and end date conflict, implying that simulation is running backwards in time (i.e. the end date comes earlier in time than the start date.) |

