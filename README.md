# KrakQL


### Current experiment status

Legend:
- ✅: Clairvoyance works
- ❌: Clairvoyance does not work (provide reason)
- ⚠️: Clairvoyance works partially (requires manual intervention)
- ❓: Not tested yet

| Project | Clairvoyance works |
| ------- | ------------------ |
| [amplication](https://github.com/amplication/amplication) | ❌ (No "errors" key) |
| [catalysis-hub](https://github.com/SUNCAT-Center/CatalysisHubBackend) | ❌ (No "errors" key) |
| [countries](https://github.com/trevorblades/countries) | ✅ |
| [directus](https://github.com/directus/directus) | ⚠️ (Error 503?) |
| [dvga](https://github.com/dolevf/Damn-Vulnerable-GraphQL-Application) | ✅ |
| [emb-graphql-ncs](https://github.com/WebFuzzing/EMB/) | ❌ (Unable to get TypeRef) |
| [emb-graphql-scs](https://github.com/WebFuzzing/EMB/) | ❌ (Unable to get TypeRef) |
| [ehri-rest](https://github.com/EHRI/ehri-rest) | ❌ (Unable to get TypeRef) |
| [fruits-api](https://github.com/Franqsanz/fruits-api) | ✅ |
| [gatsby-starter-default](https://github.com/gatsbyjs/gatsby) | ❌ (No "errors" key) |
| [gitlab-ce](https://docs.gitlab.com/install/docker/) | ❌ (Unable to get TypeRef) |
| [hey](https://github.com/heyverse/hey) | ❌ (No "errors" key) |
| [parse-server](https://github.com/parse-community/parse-server) | ❌ (Could not start) |
| [payload](https://github.com/payloadcms/payload) | ✅ |
| [petclinic-graphql](https://github.com/spring-petclinic/spring-petclinic-graphql) | ⚠️ (Object has no attribute data) |
| [react-ecommerce](https://github.com/react-shop/react-ecommerce) | ⚠️ (It stops after some iterations, if we have find let's check it) |
| [react-finland](https://github.com/ReactFinland/graphql-api) | ✅ |
| [redwoodjs-graphql](https://github.com/redwoodjs/graphql) | ❌ (Unable to get TypeRef) |
| [rick-and-morty-api](https://github.com/afuh/rick-and-morty-api) | ✅ |
| [rxdb](https://github.com/pubkey/rxdb) | ❓ |
| [saleor](https://github.com/saleor/saleor) | ❌ (Unable to get TypeRef) |
| [sierra](https://github.com/hivdb/sierra) | ❌ (Unable to get TypeRef) |
| [timbuctoo](https://github.com/HuygensING/timbuctoo) | ❌ (Unable to get TypeRef) |
| [twenty](https://github.com/twentyhq/twenty/) | ❌ (Could not start) |

### Next steps
- From the function krakql in oracle.py, remove the wordlist parameter and use the model parameter instead. In particular, I should instantiate the agent once and call it with a function that takes the schema as sdl (function already defined in graphql.py).
- Try the ones that are not working manually with curl or Postman and try the combinations: a valid query, two fields (one valid and one not), and a query without valid fields.