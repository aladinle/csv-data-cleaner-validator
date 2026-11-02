# CSV Data Cleaner and Validator

Personal portfolio demo for Python automation and data quality services. All customer data is synthetic. This is not a paid client engagement. The starter implementation was created with AI assistance; review, run, and understand it before presenting your role or offering this service.

## Business problem

Customer exports often contain inconsistent spacing, duplicate records, missing fields, and formatting errors. This tool separates valid records from records needing review, while keeping an audit trail.

## Run on Windows

Install Python 3.10 or newer if needed, then extract this ZIP. Open PowerShell inside the extracted folder (the folder containing clean_csv.py).

```powershell
py --version
py clean_csv.py demo/customers_messy.csv --output output/my_first_run
Start-Process output/my_first_run/report.html
py -m unittest discover -s tests -v
```

No third-party packages, server, API key, or internet connection is needed to run the tool. If `py` is unavailable but Python is installed, try `python` instead. Use a new output folder for every run; the tool refuses to replace existing outputs.

The pre-generated example report is in `demo_output/report.html`. Open it directly in a browser to inspect the demo without running Python.

## Input contract

A UTF-8, comma-delimited customer CSV with exactly these four columns (order may vary):

```csv
customer_id,name,email,country
C001,Alice Nguyen,alice@example.com,US
```

Headers are trimmed, lowercased, and spaces are replaced with underscores. This version supports CSV only, not XLSX. Excel can open the exported CSV files.

## Rules

- Require all four fields; keep identifiers as text to preserve leading zeros.
- Trim field whitespace; collapse name spacing without changing name capitalization.
- Uppercase country values and require two ASCII letters. This is a shape check, not a country registry lookup.
- Lowercase only the email domain, preserving the local part. Validate basic email shape only; do not verify mailbox existence or delivery.
- Remove exact duplicates across all four normalized fields. Same ID with different data is retained; there is no fuzzy matching or customer reconciliation.
- Quarantine formula-like values starting with `=`, `+`, `-`, or `@` after trimming. This conservative policy can flag legitimate data; review rejected records manually.
- Reject rows with too many or too few cells. Invalid CSV syntax or encoding stops processing with an error.
- Ignore blank physical lines; rows containing four empty cells are rejected.

## Outputs

| File | Purpose |
| --- | --- |
| cleaned.csv | Valid records after normalization and deduplication |
| rejected.csv | Record number, rejection reasons, and original values as JSON |
| issues.csv | One row per informational change, warning, or validation error |
| summary.json | Counts for reproducible checks |
| report.html | Standalone visual report with preview and issue audit |

Record numbers are one-based CSV data-record positions, not physical line numbers. Embedded newlines inside quoted fields count as one record. Original source bytes remain unchanged. Audit CSV cells receive a leading apostrophe if needed to reduce spreadsheet formula interpretation. HTML values are escaped.

## Verified demo results

- 12 input records
- 5 accepted records
- 7 rejected records, including 1 exact duplicate and 6 records with validation errors
- Accepted + rejected = input
- 10 automated tests pass

The HTML preview shows up to 20 accepted records and 50 audit entries. Exported CSV files contain full results. Processing uses memory proportional to input size; this demo is for small or medium CSV files, not huge streaming datasets. Output writes are not transactional; if a disk error occurs, use a new folder when rerunning.

## Suggested portfolio presentation

Use `portfolio_cover.png` as the opening image and `demo_results.png` as a graphic generated from the actual output counts. These are presentation graphics, not application screenshots. Open `demo_output/report.html` on your own machine and take a browser screenshot for additional evidence. Copy the project description from `UPWORK_PORTFOLIO.txt` after reviewing it. Show the command, the source demo, output files, and passing tests in a short screen recording.

Do not claim paid client work, fabricated time savings, or Excel workbook support. Before publishing, run it yourself, review the code, and make a change you can explain (for example, add a phone-number field and tests).

## Next milestone

Add selectable rules or a small desktop interface after this version is understood and verified on your Windows machine. Keep XLSX support as a separate extension with its own tests.
