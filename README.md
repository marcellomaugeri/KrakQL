# KrakQL: LLM-Guided Retrieval of GraphQL Schemas
This repository contains the code and resources for the paper "KrakQL: LLM-Guided Retrieval of GraphQL Schemas".
The contribution of this repository is duplex:
- Contains the source code of the KrakQL tool, which is a tool to retrieve GraphQL schemas from a set of GraphQL APIs.
- Provide an extendable benchmark of GraphQL APIs, which can be used to test different tools and techniques for GraphQL APIs.

## Repository structure
- `case_studies`: Contains the case studies (Consisting of a Dockerfile and a docker-compose.yml file). See [./docs/CASE_STUDIES.md](./docs/CASE_STUDIES.md) to add new case studies.
- `tools`: Contains the tools used to test the case studies. See [./docs/TOOLS.md](./docs/TOOLS.md) to add new tools.
- `analysis`: Contains the scripts to analyse the results. See [./docs/ANALYSIS.md](./docs/ANALYSIS.md) to add new analysis scripts.
- `results`: This is the default location for the results of the tests. `analysis` scripts should look for the results here.
- `utils`: Contains miscellaneous scripts.

## Case studies
| Project | Framework | Field suggestion | Introspection available | Build status | Endpoint | Default port |
| ------- | --------- | ---------------- | ----------------------- | ------------ | -------- | ------------ |
| [react-ecommerce](https://github.com/react-shop/react-ecommerce) | Nestjs/GraphQL | :x: | :x: | :x: | /graphql | 4000 |
| [patio-api](https://github.com/patio-team/patio-api) |  | :x: | :x: | :heavy_check_mark: | /graphql | 4000 |
| [react-finland](https://github.com/ReactFinland/graphql-api) | | :x: | :x: | :heavy_check_mark: | /graphql | 4000 |
| [petclinic-graphql](https://github.com/spring-petclinic/spring-petclinic-graphql) | Spring | :x: | :x: | :heavy_check_mark: | /graphql | 8080 |
| [timbuctoo](https://github.com/HuygensING/timbuctoo) | | :x: | :x: | :x: | /graphql | 8080 |
| [countries](https://github.com/trevorblades/countries) | | :x: | :x: | :heavy_check_mark: | /graphql | 8080 |
| [dvga](https://github.com/dolevf/Damn-Vulnerable-GraphQL-Application) | | :x: | :x: | :heavy_check_mark: | /graphql | 8080 |

##### To add:
- [Gitlab](https://docs.gitlab.com/install/docker/)
- [Rick and Morty API](https://github.com/afuh/rick-and-morty-api)
- [Poke-GQL](https://github.com/GregLyons/poke-gql)

## Requirements
- Docker
- Docker Compose
- Python 3.10+

## Run an experiment (TODO)
```bash
python3 -m pip install -r requirements.txt
python3 run_experiment.py
```

#### TO DO (Before releasing)
- [ ] Add a script to start/stop a set of specific case studies (e.g. ./script.sh start/stop <case_study_1> <case_study_2>)

### Useful Resources
- [Graphql-schema-diff](https://github.com/Ambro17/graphql-schema-diff)

#### Future Work
- [ ] Add Artillery for load testing
- [ ] Add Wendigo for load testing