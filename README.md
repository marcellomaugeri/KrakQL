# graphql-schema-retriever-with-llm

#### Case studies
##### From 'Random Testing and Evolutionary Testing for Fuzzing GraphQL APIs' paper
- [e-commerce-server](https://github.com/react-shop/react-ecommerce)
- [patio-api](https://github.com/patio-team/patio-api)
- [react-finland](https://github.com/ReactFinland/graphql-api)
- [petclinic-graphql](https://github.com/spring-petclinic/spring-petclinic-graphql)
- [timbuctoo](https://github.com/HuygensING/timbuctoo)

graphql-ncs and graphql-scs are adapted from RESTful APIs.

##### Others
- [DVGA](https://github.com/dolevf/Damn-Vulnerable-GraphQL-Application)
- [Gitlab](https://docs.gitlab.com/install/docker/)

### Build the base image
```shell
cd base_image
docker build -t graphql-base .
cd ..
```

### Build the image for a specific case study
```shell
cd targets/<case_study>
docker build -t graphql-<case_study> .
cd ../..
```

### Useful Resources
- [Graphql-schema-diff](https://github.com/Ambro17/graphql-schema-diff)