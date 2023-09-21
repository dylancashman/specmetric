# specmetric

Package to generate visualizations from computational data.

Supplemental Material 2024 CHI Submission ID 6165

Will be open sourced once this corresponding work is published.

## Installation

Requires python 3.10

	pip install -r requirements.txt

## Running

### Use Case 1: Notebook

	cd usecases/notebook
	jupyter notebook use_case_1_regression_metrics.ipynb

Then run all cells.  It should create interactive visualizations as seen in the paper figures.

### Use Case 2: Spreadsheet

	cd usecases/spreadsheet
	python app.py

This runs a simple flask server, and if you navigate to the corresponding localhost url, you will see an editable spreadsheet.  It only matches four types of operations: SUM(), AVERAGE(), and +s and -s.
