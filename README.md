# KrakQL: LLM-Guided Retrieval of GraphQL Schemas

#### Case studies
##### From 'Random Testing and Evolutionary Testing for Fuzzing GraphQL APIs' paper
| Project                                                                 | Framework | Field suggestion | Introspection available | Build status |
|-------------------------------------------------------------------------|-----------|------------------|--------------------------|--------------|
| [e-commerce-server](https://github.com/react-shop/react-ecommerce)     |           | :x:              | :x:                      | :x:          |
| [patio-api](https://github.com/patio-team/patio-api)                   |           | :x:              | :x:                      | :heavy_check_mark:          |
| [react-finland](https://github.com/ReactFinland/graphql-api)           |           | :x:              | :x:                      | :heavy_check_mark:          |
| [petclinic-graphql](https://github.com/spring-petclinic/spring-petclinic-graphql) |           | :x:              | :x:                      | :x:          |
| [timbuctoo](https://github.com/HuygensING/timbuctoo)                   |           | :x:              | :x:                      | :x:          |


graphql-ncs and graphql-scs are adapted from RESTful APIs.

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
