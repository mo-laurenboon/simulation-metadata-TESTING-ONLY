# (C) British Crown Copyright 2025, Met Office.
# Please see LICENSE.md for license details.
HEADINGS = ['Model Workflow ID', 'Model ID', 'Mass Data Class', 'MIP', 'Institution ID', 'Experiment ID',
            'Variant Label', 'Start Date', 'End Date']
HEADER_ROW_TEMPLATE = ('  <thead>\n   <tr bgcolor="{0}">\n{1}   </tr>\n   \
                       <tr class="filters">\n{2}   </tr>\n   </thead>\n')
ROW_TEMPLATE = '  <tr bgcolor="{0}">\n{1}  </tr>\n'
CELL_TEMPLATE = '     <{0}>{1}</{0}>\n'
TABLE_TEMPLATE = '<table border=1, id="table_id", class="display">\n{}</table>\n'
GITURL_MAPPING = 'https://github.com/UKNCSP/CDDS-simulation-metadata/tree/main/workflow_metadata/{}.cfg'
HYPERLINK = '<a href="{0}">{1}</a>'
BGCOLORS = ['#E0EEFF', '#FFFFFF']
HEADER = """
<html>
<head>
<link rel="stylesheet" type="text/css" charset="UTF-8"
href="https://cdn.datatables.net/2.3.2/css/dataTables.dataTables.min.css"/>
<script type="text/javascript" charset="UTF-8" src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script type="text/javascript" charset="UTF-8" src="https://cdn.datatables.net/2.3.2/js/dataTables.min.js"></script>
<script type="text/javascript">
$(document).ready(function () {
  var table = $('#table_id').DataTable({
    orderCellsTop: true,
    fixedHeader: true,
    pageLength: 100,
    initComplete: function () {
      var api = this.api();

      // Show the tables once DataTables has initialized
      $('#table_id').css('visibility', 'visible');

      // For each column, add a select filter to the second row
      api.columns().eq(0).each(function (colIdx) {
        var cell = $('.filters th').eq(colIdx);
        if (cell.length) {
          var select = $('<select><option value="">All</option></select>')
            .appendTo(cell.empty())
            .on('change', function () {
              api.column(colIdx)
                .search(this.value ? '^' + this.value + '$' : '', true, false)
                .draw();
            });

          api.column(colIdx).data().unique().sort().each(function (d) {
            if (d) select.append('<option value="' + d + '">' + d + '</option>');
          });
        }
      });
    }
  });
});
</script>
</head>
<style>

  /* Hide table until DataTables has fully initialized */
    #table_id {
    visibility: hidden;
   }

  /* Format the datatables */
  table.dataTable {
    table-layout: break-word;
    width: 90%;
  }

  table.dataTable td {
    max-width: 300px;
    white-space: normal;
    word-wrap: break-word;
  }

  pre, code {
    white-space: pre-wrap;
    word-break: break-word;
  }

  table.dataTable thead select {
    width: 100%;
    box-sizing: border-box;
    padding: 4px;
    font-size: 0.9em;
  }

   /* Tooltip container */
   .tooltip {
     position: relative;
     display: inline-block;
     border-bottom: 1px dotted black; /* If you want dots under the hoverable text */
   }

   /* Tooltip text */
   .tooltip .tooltiptext {
     visibility: hidden;
     bottom: 100%;
     left: 50%;
     width: 600px;
     background-color: #FFFFFF;
     color: black;
     text-align: left;
     padding: 18px;
     border-radius: 4px;
     border: 1px solid #000;

     /* Position the tooltip text - see examples below! */
     position: absolute;
     z-index: 1;
   }

   /* Show the tooltip text when you mouse over the tooltip container */
   .tooltip:hover .tooltiptext {
     visibility: visible;
   }
   </style>
<body>"""

FOOTER = """
</body>
</html>"""

SECTIONS = set(['metadata', 'data', 'misc'])
METADATA = set(['base_date', 'branch_method', 'branch_date_in_child', 'branch_date_in_parent', 'parent_experiment_id',
                'parent_mip', 'parent_model_id', 'parent_time_units', 'parent_variant_label', 'calendar',
                'experiment_id', 'institution_id', 'mip', 'mip_era', 'variant_label', 'model_id'])
DATA = set(['start_date', 'end_date', 'mass_data_class', 'mass_ensemble_member', 'model_workflow_id'])
MISC = set(['atmos_timestep'])
REQUIRED = set(['base_date', 'branch_method', 'calendar', 'experiment_id', 'institution_id', 'mip', 'mip_era',
                'variant_label', 'model_id', 'start_date', 'end_date', 'mass_data_class', 'model_workflow_id',
                'atmos_timestep'])
PARENT_REQUIRED = set(['branch_date_in_child', 'branch_date_in_parent', 'parent_experiment_id', 'parent_mip',
                       'parent_model_id', 'parent_time_units', 'parent_variant_label'])
DATETIME_FIELDS = set(['base_date', 'start_date', 'end_date'])
REGEX_FORMAT = {
    "datetime": r"^(?:\d{4})-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12]\d|3[01])T(?:[01]\d|2[0-3]):[0-5]\d:[0-5]\dZ$",
    "model_workflow_id": r"^[a-z]{1,2}-[a-z]{2}\d{3}$",
    "variant_label": r"^(r\d+)(i\d+[a-e]{0,1})(p\d+)(f\d+)$"
}

META_FIELDS = {
        "issue_type": "issue_type",
        "base_date": "base_date",
        "branch_method": "branch_method",
        "child_branch_date": "branch_date_in_child",
        "parent_branch_date": "branch_date_in_parent",
        "parent_experiment_id": "parent_experiment_id",
        "parent_activity_id_(mip)": "parent_mip",
        "parent_model_id": "parent_model_id",
        "parent_time_units": "parent_time_units",
        "parent_variant_label": "parent_variant_label",
        "calendar_type": "calendar",
        "experiment_id": "experiment_id",
        "institution_id": "institution_id",
        "activity_id_(mip)": "mip",
        "mip_era": "mip_era",
        "variant_label": "variant_label",
        "model_id": "model_id",
        "start_date": "start_date",
        "end_date": "end_date",
        "mass_data_class": "mass_data_class",
        "mass_ensemble_member_id": "mass_ensemble_member",
        "model_workflow_id": "model_workflow_id",
        "atmospheric_timestep": "atmos_timestep"
    }
