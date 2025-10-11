# KrakQL: LLM-Guided Blind Introspection of GraphQL Schemas 
This is the artifact of the paper "KrakQL: LLM-Guided Blind Introspection of GraphQL Schemas".

## Important
`clairvoyanceplus` is a modified version of `clairvoyance` to enable logging necessary to calculate the results.

## Requirements
- Python3.11+

# IMPORTANT
Section under refactoring, come back in a few days.

## Run the paper experiments
```
export OPENAI_API_KEY="<your key>"
./run_experiments.sh --exp_name paper_experiments --case_studies dvga,fruits-api,payload,react-ecommerce,react-finland,rick-and-morty-api --tools clairvoyanceplus,KrakQL --time_budget 10800 --max_parallel_tests 10
```

### Print results
All results can be printed from the `BenGQL` directory.

### Install requirements
```
cd BenGQL
python3 -m venv venv # Build virtual environment
source venv/bin/activate # Activate virtual environment
pip install -r requirements.txt # Install dependencies
```

#### RQ1
```
python3 analysis/schema_coverage/analyse_experiment.py ./results/paper_experiments/ ./case_studies/

```

#### RQ2
```
python3 analysis/schema_coverage/analyse_probe_rates.py paper_experiments
```

#### RQ3
```
python3 analysis/schema_coverage/tokenomics.py paper_experiments
```