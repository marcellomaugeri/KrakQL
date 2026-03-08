# Paper Results Reproduction

This folder contains the scripts used to analyse experimental outputs for the *KrakQL* paper.
The scripts expect a `results/` directory (relative to this folder) containing the tool outputs and ground truth schemas.

## Requirements

- Python 3.11+

## Setup

Create and activate a virtual environment, then install dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Run the analyses

Run RQ1 (schema coverage analysis):

```bash
python3 rq1.py
```

Run RQ2 (discovery efficiency analysis):

```bash
python3 rq2.py
```

For custom result locations, both scripts accept an optional `results_folder` argument.
