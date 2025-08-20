# KrakQL


### Current experiment status

Legend:
- ✅: Clairvoyance works
- ❌: Clairvoyance does not work (provide reason)
- ⚠️: Clairvoyance works partially (requires manual intervention)
- ❓: Not tested yet

| Project | Clairvoyance works |
| ------- | ------------------ |
| [amplication](https://github.com/amplication/amplication) | ❌ Different error format |
| [catalysis-hub](https://github.com/SUNCAT-Center/CatalysisHubBackend) | ❌ (No "errors" key) |
| [countries](https://github.com/trevorblades/countries) | ✅ |
| [directus](https://github.com/directus/directus) | ❌ Different error format |
| [dvga](https://github.com/dolevf/Damn-Vulnerable-GraphQL-Application) | ✅ |
| [emb-graphql-ncs](https://github.com/WebFuzzing/EMB/) | ❌ Different error format (partially fixed) |
| [emb-graphql-scs](https://github.com/WebFuzzing/EMB/) | ⚠️ Different error format (partially fixed, requires different regexes) |
| [ehri-rest](https://github.com/EHRI/ehri-rest) | ❌ |
| [fruits-api](https://github.com/Franqsanz/fruits-api) | ✅ |
| [gatsby-starter-default](https://github.com/gatsbyjs/gatsby) | ❌ |
| [gitlab-ce](https://docs.gitlab.com/install/docker/) | ❌ |
| [hey](https://github.com/heyverse/hey) | ❌ |
| [parse-server](https://github.com/parse-community/parse-server) | ❌ |
| [payload](https://github.com/payloadcms/payload) | ✅ |
| [petclinic-graphql](https://github.com/spring-petclinic/spring-petclinic-graphql) | ⚠️ (Object has no attribute data) |
| [react-ecommerce](https://github.com/react-shop/react-ecommerce) | ✅ |
| [react-finland](https://github.com/ReactFinland/graphql-api) | ✅ |
| [redwoodjs-graphql](https://github.com/redwoodjs/graphql) | ❌ |
| [rick-and-morty-api](https://github.com/afuh/rick-and-morty-api) | ✅ |
| [rxdb](https://github.com/pubkey/rxdb) | ❓ |
| [saleor](https://github.com/saleor/saleor) | ❌ |
| [sierra](https://github.com/hivdb/sierra) | ❌ (Unable to get TypeRef) |
| [timbuctoo](https://github.com/HuygensING/timbuctoo) | ❌ (Unable to get TypeRef) |
| [twenty](https://github.com/twentyhq/twenty/) | ❌ (Could not start) |

| Project | Clairvoyance | KrakQL |
| ------- | ------------ | ------ |
| [catalysis-hub](https://github.com/SUNCAT-Center/CatalysisHubBackend) | ❌ (No "errors" key) | ❓ |
| [countries](https://github.com/trevorblades/countries) | ❌ | ❓ |
| [directus](https://github.com/directus/directus) | ❌ Different error format | ❓ |
| [dvga](https://github.com/dolevf/Damn-Vulnerable-GraphQL-Application) | ✅ | ❓ |
| [emb-graphql-scs](https://github.com/WebFuzzing/EMB/) | ⚠️ Different error format (partially fixed, requires different regexes) | ❓ |
| [ehri-rest](https://github.com/EHRI/ehri-rest) | ❌ | ❓ |
| [fruits-api](https://github.com/Franqsanz/fruits-api) | ✅ | ❓ |
| [gatsby-starter-default](https://github.com/gatsbyjs/gatsby) | ❌ | ❓ |
| [hey](https://github.com/heyverse/hey) | ❌ | ❓ |
| [parse-server](https://github.com/parse-community/parse-server) | ❌ | ❓ |
| [payload](https://github.com/payloadcms/payload) | ✅ | ❓ |
| [petclinic-graphql](https://github.com/spring-petclinic/spring-petclinic-graphql) | ⚠️ (Object has no attribute data) | ❓ |
| [react-ecommerce](https://github.com/react-shop/react-ecommerce) | ✅ | ❓ |
| [react-finland](https://github.com/ReactFinland/graphql-api) | ✅ | ❓ |
| [redwoodjs-graphql](https://github.com/redwoodjs/graphql) | ❌ | ❓ |
| [rick-and-morty-api](https://github.com/afuh/rick-and-morty-api) | ✅ | ❓ |
| [rxdb](https://github.com/pubkey/rxdb) | ❓ | ❓ |
| [saleor](https://github.com/saleor/saleor) | ❌ | ❓ |
| [sierra](https://github.com/hivdb/sierra) | ❌ (Unable to get TypeRef) | ❓ |
| [timbuctoo](https://github.com/HuygensING/timbuctoo) | ❌ (Unable to get TypeRef) | ❓ |
| [twenty](https://github.com/twentyhq/twenty/) | ❌ (Could not start) | ❓ |

### Next steps
- From the function krakql in oracle.py, remove the wordlist parameter and use the model parameter instead. In particular, I should instantiate the agent once and call it with a function that takes the schema as sdl (function already defined in graphql.py).
- Try the ones that are not working manually with curl or Postman and try the combinations: a valid query, two fields (one valid and one not), and a query without valid fields.