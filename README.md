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

Legend:
- ✅: Available
- ❌: Not available
- ⚠️: Not enabled by default
- ❓: Not tested

| Project | Framework | Field suggestion | Introspection available | Build status | Endpoint | Clairvoyance/Next |
| ------- | --------- | ---------------- | ----------------------- | ------------ | -------- | --- |
| [react-ecommerce](https://github.com/react-shop/react-ecommerce) | Nestjs/GraphQL | ❓ | ❓ | ❌ | /graphql | ❓/❓ |
| [react-finland](https://github.com/ReactFinland/graphql-api) | [express-graphql](https://www.npmjs.com/package/express-graphql) | ✅ | ✅ | ✅ | /graphql | ❓/❓ |
| [petclinic-graphql](https://github.com/spring-petclinic/spring-petclinic-graphql) | Spring for GraphQL (GraphQL Java) | ❓ | ✅ | ✅ | /graphql | ❓/❓ |
| [timbuctoo](https://github.com/HuygensING/timbuctoo) | GraphQL Java | ❓ | ❓ | ❌ | /graphql | ❓/❓ |
| [countries](https://github.com/trevorblades/countries) | Yoga | ✅ | ✅ | ✅ | /graphql | ❓/❓ |
| [dvga](https://github.com/dolevf/Damn-Vulnerable-GraphQL-Application) | graphql-core | ✅ | ✅ | ✅ | /graphql | ❓/❓ |
| [Gitlab-CE](https://docs.gitlab.com/install/docker/) | GraphQL Ruby | ❓ | ❓ | ✅ | /api/graphql | ❓/❓ |

### Dropped case studies
- [patio-api](https://github.com/patio-team/patio-api) - The project is not maintained anymore and it does not work without a lot of effort. Also, it requires several API keys to work.

##### To add:
- [Rick and Morty API](https://github.com/afuh/rick-and-morty-api)
- [Poke-GQL](https://github.com/GregLyons/poke-gql)

## Requirements
- Docker
- Docker Compose

## Run an experiment (TODO)
```bash
./run_cases.sh up all
# Stop all containers
./run_cases.sh down all
# Run a list of cases
./run_cases.sh up dvga patio-api

# Run a tool on a case (e.g. Clairvoyance) [To change]
cd tools/clairvoyance
docker compose run clairvoyance poetry run clairvoyance http://host.docker.internal:55240/graphql -o /results/test.json
```

#### TO DO
- [ ] Add an environment variable to disable introspection/field suggestion ([See this for Yoga](https://the-guild.dev/graphql/yoga-server/docs/features/introspection), DVGA uses the HTTP Request Header X-DVGA-MODE to disable introspection)

### Useful Resources
- [Graphql-schema-diff](https://github.com/Ambro17/graphql-schema-diff)

#### Future Work
- [ ] Add Artillery for load testing
- [ ] Add Wendigo for load testing

## Known Issues
- The `countries` case study on MacOS (ARM) sometimes fails to compile (qemu: uncaught target signal 11 (Segmentation fault) - core dumped). If this happens, just try to compile the container again and will work like a charm.