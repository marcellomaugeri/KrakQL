# KrakQL: LLM-Guided Blind Introspection of GraphQL Schemas [Artifact]
This is the artifact of the paper "KrakQL: LLM-Guided Blind Introspection of GraphQL Schemas" submitted to SSBSE2025.

## Abstract
```

```

## Requirements
- Docker
- Docker Compose
- Python (for some analysis scripts or standalone installation)

## Run the paper experiments
```
./run_experiments.sh --exp_name paper_experiments --case_studies countries,dvga,fruits-api,payload,react-ecommerce,react-finland,rick-and-morty-api --tools clairvoyanceplus,KrakQL --time_budget 10800 --max_parallel_tests 10
```

## Print Experiment Results
### Install requirements
```
python3 -m venv venv # Build virtual environment
source venv/bin/activate # Activate virtual environment
pip install -r requirements.txt # Install dependencies
```

### Print results
```
python3 analysis/schema_coverage/analyse_experiment.py ./results/paper_experiments/ ./case_studies/
```

### Current experiment status

| Project | Clairvoyance | KrakQL |
| ------- | ------------ | ------ |
| [countries](https://github.com/trevorblades/countries) | ⚠️ | ✅ |
| [dvga](https://github.com/dolevf/Damn-Vulnerable-GraphQL-Application) | ✅ (Just query) | ✅ |
| [fruits-api](https://github.com/Franqsanz/fruits-api) | ✅ | ✅ |
| [payload](https://github.com/payloadcms/payload) | ✅ (Just query) | ✅ |
| [react-ecommerce](https://github.com/react-shop/react-ecommerce) | ✅ | ✅ |
| [react-finland](https://github.com/ReactFinland/graphql-api) | ✅ | ✅ |
| [rick-and-morty-api](https://github.com/afuh/rick-and-morty-api) | ✅ | ✅ |
