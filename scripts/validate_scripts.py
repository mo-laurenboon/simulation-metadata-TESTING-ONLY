# (C) British Crown Copyright 2025, Met Office.
# Please see LICENSE.md for license details.
"""
This script validates the coding quality of all python scripts using pycodestyle.
"""

from pathlib import Path
import glob
import pycodestyle


def glob_files() -> list[str]:
    """
    Creates a list of all python files in the repository.

    :returns: A list of all python files in the repository.
    :rtype: list[str]
    """
    glob_string = Path("**/*.py")
    files = glob.glob(str(glob_string))

    return files


def check_file(file: str, style_guide: pycodestyle.StyleGuide, count: int) -> int:
    """
    Applies a pycodestyle check to a single file.

    :param file: The file to be checked.
    :type file: str
    :param style_guide: The style guide format to be applied during the check.
    :type style_guide: pycodestyle.StyleGuide
    :param count: The number of files that have passed the style guide check.
    :type count: int
    :returns: The number of files that have passed the style guide check.
    :rtype: int
    """
    print(f"\nChecking {file}...")

    issues = style_guide.check_files([file])
    if issues.total_errors == 0:
        print("FILE OK")
        count += 1

    return count


def main() -> None:
    """
    Holds the main body of the function.
    """
    style_guide = pycodestyle.StyleGuide(quiet=False, max_line_length=120)

    count = 0

    files = glob_files()
    for file in files:
        count = check_file(file, style_guide, count)

    print("\n" + "="*60)
    print(f"{count}/{len(files)} scripts successfully validated...")
    print("="*60)


if __name__ == "__main__":
    main()
