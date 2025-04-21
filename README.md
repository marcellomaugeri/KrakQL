# KrakQL: LLM-Guided Retrieval of GraphQL Schemas
This repository contains the code and resources for the paper "KrakQL: LLM-Guided Retrieval of GraphQL Schemas". 


### Repository structure
- `case_studies`: Contains the case studies (Consisting of a Dockerfile and a docker-compose.yml file). See [./docs/CASE_STUDIES.md](./docs/CASE_STUDIES.md) to add new case studies.
- `tools`: Contains the tools used to test the case studies. See [./docs/TOOLS.md](./docs/TOOLS.md) to add new tools.
- `analysis`: Contains the scripts to analyse the results. See [./docs/ANALYSIS.md](./docs/ANALYSIS.md) to add new analysis scripts.
- `results`: This is the default location for the results of the tests. `analysis` scripts should look for the results here.
- `utils`: Contains miscellaneous scripts.

#### Case studies
| Project | Framework | Field suggestion | Introspection available | Build status | Endpoint | Default port |
| ------- | --------- | ---------------- | ----------------------- | ------------ | -------- | ------------ |
| [e-commerce-server](https://github.com/react-shop/react-ecommerce) | Nestjs/GraphQL | :x: | :x: | :x: | /graphql | 4000 |
| [patio-api](https://github.com/patio-team/patio-api) |  | :x: | :x: | :heavy_check_mark: | /graphql | 4000 |
| [react-finland](https://github.com/ReactFinland/graphql-api) | | :x: | :x: | :heavy_check_mark: | /graphql | 4000 |
| [petclinic-graphql](https://github.com/spring-petclinic/spring-petclinic-graphql) | Spring | :x: | :x: | :heavy_check_mark: | /graphql | 8080 |
| [timbuctoo](https://github.com/HuygensING/timbuctoo) | | :x: | :x: | :x: | /graphql | 8080 |
| [dvga](https://github.com/dolevf/Damn-Vulnerable-GraphQL-Application) | | :x: | :x: | :heavy_check_mark: | /graphql | 8080 |


##### Others
- [DVGA](https://github.com/dolevf/Damn-Vulnerable-GraphQL-Application)
- [Gitlab](https://docs.gitlab.com/install/docker/)
- [Rick and Morty API](https://github.com/afuh/rick-and-morty-api)
- [Countries](https://github.com/trevorblades/countries)
- [Poke-GQL](https://github.com/GregLyons/poke-gql)

### Build the base image
```shell
cd base_image
docker build --platform=linux/amd64 -t graphql-base .
cd ..
```

### Build the image for a specific case study
```shell
cd targets/<case_study>
docker build --platform=linux/amd64 -t graphql-<case_study> .
cd ../..
```

#### TO DO (Before releasing)
- [ ] Add a script to start/stop a set of specific case studies (e.g. ./script.sh start/stop <case_study_1> <case_study_2>)

### Useful Resources
- [Graphql-schema-diff](https://github.com/Ambro17/graphql-schema-diff)

#### Future Work
- [ ] Add Artillery for load testing
- [ ] Add Wendigo for load testing