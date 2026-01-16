<!--(C) British Crown Copyright 2025, Met Office. Please see LICENSE.md for license details.--> 
# Fixing A Mistake On An 'Add/Modify Workflow Metadata' Issue Form

# What to do ...
In the event that you make a mistake when filling out the '"Add/Modify Workflow Metadata' issue form (e.g. an input gets flagged as invalid or you notice a typo in one of your inputs(not including the model workflow ID)) there are 2 potential solutions, the method that you choose is up to your personal preference:

1. Navigate to the issue that was created when you filled out the form. Note that this issue may be marked as 'closed'. At the top of the box containing the issue body select the options button (shown as 3 horizontal dots that will read as "issue body actions" when hovered over). This will allow you to edit the issue body and make any changes that you need. If choosing this option, it is important that the markdown structure of the issue body remains unchanged to avoid parsing errors. Once you have made your changes, ensure that you save them by clicking the save button at the base of the issue body. If you do not hit save, these changes will not be applied.

2. If you are not confident with markdown structure or would prefer a more structured solution, you can simply fill out a new issue form containing the corrected information. This method may be more time consuming as you will be required to re fill out all of the information within the form. However, this option is typically safer if fixing multiple errors or for those who are less confident with markdown syntax.


# What to do if you've entered an incorrect model workflow ID...
If an error is made when entering the model workflow ID, please raise a standard issue (not a new 'Add/Modify Workflow Metadata' form). The issue body should contain the following information:
- The model workflow id of the incorrectly submitted metadata
- The correct model workflow id
- If the submitted metadata configuration file contained any other errors or typos
This issue will then be handled directly by a member of the team who will either advise you on next steps or make the required changes manually.


# What happens once the changes have been made...
After saving your changes or re submitting your form, the workflow which handles your submission will be re triggered and your inputs will be re verified. If any invalid inputs are found you will receive a comment from the github actions bot under the issue related to your submission notifying you of any problems. These can be fixed as described above. If all entries are valid, a pull request will be created so that your changes can be reviewed by a member of the team. It would be valuable to us if a brief comment could be left under this pull request explaining the reason for the change so that full transparency is maintained and changes can be easily traced. Please do not attempt to merge pull requests or delete incorrect metadata files yourself - these actions will be handled by a member of the @UKNCSP/CDDS team.

If you come across any issues that you are unable to resolve or are unsure with how to proceed, please raise an issue or contact a member of the @UKNCSP/CDDS team.