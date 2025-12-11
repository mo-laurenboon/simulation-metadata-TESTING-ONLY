# (C) British Crown Copyright 2025, Met Office.
# Please see LICENSE.md for license details.
"""This script generates the table and HTML file for CDDS workflow metadata."""

from pathlib import Path
import glob
from configparser import ConfigParser
from constants import (HEADINGS, HEADER_ROW_TEMPLATE, ROW_TEMPLATE, CELL_TEMPLATE, TABLE_TEMPLATE, BGCOLORS,
                       GITURL_MAPPING, HEADER, FOOTER, HYPERLINK)


def get_mappings() -> list[list[str]]:
    """Read all mappings for a given model and return them as a list of lists.

    Returns
    -------
    list[list[str]]
        Table data as a list of lists, where the sub lists contain data matching the HEADINGS fields.
    """
    glob_string = Path("workflow_metadata/*.cfg")
    cfg_files = glob.glob(str(glob_string))

    table_data = []

    for cfg_file in cfg_files:
        print(f"Processing {cfg_file}...")
        mappings_config_object = ConfigParser()
        mappings_config_object.read(cfg_file)
        metadata = mappings_config_object["metadata"]
        data = mappings_config_object["data"]

        table_data.append([
            data["model_workflow_id"],
            metadata['model_id'],
            data["mass_data_class"],
            metadata['mip'],
            metadata['institution_id'],
            metadata['experiment_id'],
            metadata['variant_label'],
            data['start_date'],
            data['end_date'],
            str(Path(cfg_file).stem)
        ])
        print("SUCCESSFUL...")
    table_data = [HEADINGS] + table_data

    return table_data


def build_table(table_data: list[list[str]]) -> str:
    """Build the HTML for table showing the supplied table_data

    Parameters
    ----------
    table_data : list[list[str]])
        The data to populate the table with.

    Returns
    -------
    str
        The table_data formatted as a HTML table.
    """
    print("Building HTML table...")
    html = ''
    for i, row in enumerate(table_data):
        cell_type = 'th' if i == 0 else 'td'
        row_html = ''
        filter_row_html = ''
        if i == 0:
            for entry in row:
                row_html += CELL_TEMPLATE.format(cell_type, entry)
                filter_row_html += CELL_TEMPLATE.format(cell_type, '')
            html += HEADER_ROW_TEMPLATE.format(BGCOLORS[i % len(BGCOLORS)], row_html, filter_row_html)
            continue
        else:
            filename = row.pop()
            for entry in row:
                if entry == table_data[i][0]:
                    row_html += CELL_TEMPLATE.format(cell_type,
                                                     HYPERLINK.format(GITURL_MAPPING.format(filename), entry))
                else:
                    row_html += CELL_TEMPLATE.format(cell_type, entry)

            html += ROW_TEMPLATE.format(BGCOLORS[i % len(BGCOLORS)], row_html)

    table_html = TABLE_TEMPLATE.format(html)
    print("SUCCESSFUL...")

    return table_html


def generate_html(table_html: str) -> None:
    """Generates full HTML file.

    Parameters
    ----------
    table_html : str
        The HTML table.
    """
    print("Building full HTML...")
    html = (HEADER +
            '<h2>CMIP7 Workflow Metadata</h2>' +
            '<p> </p>' + '<p>Use the search box to filter rows, e.g. search for "MOHC" or "NERC".</p>' + '<p> </p>' +
            '<p>To view the full metadata, click the model workflow ID link in the table.</p>' +
            table_html + FOOTER)

    output_directory = Path("metadata_tables")
    output_directory.mkdir(parents=True, exist_ok=True)

    output_filepath = output_directory / "index.html"

    with open(output_filepath, 'w') as f:
        f.write(html)

    print("SUCCESSFUL...")
    print(f"Webpage generated successfully\nFor the raw HTML file see {output_filepath}.")


if __name__ == "__main__":
    generate_html(build_table(get_mappings()))
