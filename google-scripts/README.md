# Google Sheets Random Number Generator

This Apps Script fills a specified range in the active sheet with random
numbers between 0 and 1.

## Usage
1. Open your Google Sheet.
2. Go to **Extensions > Apps Script** and create a new project.
3. Replace the contents of the default `Code.gs` file with
   `random_numbers.gs` from this repository.
4. Save and run `fillRandomNumbers` with a range string, e.g. `"A1:C10"`.

The script will populate the chosen range with random values.
