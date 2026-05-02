# KrakQL: LLM-Guided Blind Introspection of GraphQL Schemas 

*KrakQL* is a fork of [*Clairvoyance*](https://github.com/nikitastupin/clairvoyance) that leverages Large Language Models (LLMs) to perform `blind introspection` of GraphQL `schemas` (a.k.a. schema retrieval).
Schema retrieval requires sending a series of `guesses` to a GraphQL endpoint to infer its schema, when the endpoint does not support the standard GraphQL introspection query.
*KrakQL* uses LLMs to generate more effective guesses, which significantly reduces the number of queries needed to retrieve the schema, compared to dictionary-based approaches.

## Citation
*KrakQL* was first presented in the paper ["KrakQL: LLM-Guided Blind Introspection of GraphQL Schemas"](https://link.springer.com/chapter/10.1007/978-3-032-24839-8_2) at the 17th International Symposium on Search-Based Software Engineering (SSBSE 2025).
If you use this code in your research, please cite the following paper:
```
@InProceedings{maugeri2025krakql,
    author="Maugeri, Marcello and Angamo, Abenezer and Bella, Giampaolo",
    editor="Wagner, Markus and Zhang, Man",
    title="KrakQL: LLM-Guided Blind Introspection of GraphQL Schemas",
    booktitle="Search-Based Software Engineering",
    year="2026",
    publisher="Springer Nature Switzerland",
    address="Cham",
    pages="19--33",
    isbn="978-3-032-24839-8"
}
```

## Design and Architecture

*KrakQL* is organised into two main parts: *KrakQL Agent* and *KrakQL Core* (see the architecture figure).
The core loop alternates between exploration decisions and probing requests, updating the partial schema after each response.

![KrakQL architecture](./docs/imgs/architecture.jpg)

1. The *Novelty Search Scheduler* selects the next *Target Path* to probe by ranking discovered types and fields with novelty scores ([`get_by_novelty()`](./krakql/graphql_schema.py#L414), used in the main loop in [`blind_introspection()`](./krakql/cli.py#L44)).
2. The *KrakQL Agent* is a supervisor-style multi-agent architecture built on [Google ADK](https://google.github.io/adk-docs/) (initialisation in [krakql/krakql_agent.py](./krakql/krakql_agent.py#L50)) that routes execution to the appropriate sub-agent depending on the probing context ([`_run_async_impl()`](./krakql/agent/agent.py#L14)).
3. Depending on the selected *Target Path*, the *KrakQL Agent* invokes one of two advisors:
   a. If the *Target Path* points to a type, the *Field Advisor* proposes candidate field names (currently fixed at 64 in the [FieldAdvisorPromptTemplate](./krakql/agent/prompts.py#L44)).
   b. If the *Target Path* points to a field, the *Argument Advisor* proposes candidate argument names (currently fixed at 64 in the [ArgumentAdvisorPromptTemplate](./krakql/agent/prompts.py#L97)).
4. The *Client* sends HTTP requests containing these candidates to the GraphQL endpoint and waits for the response.
5. The response is passed to the *Oracle*, which extracts valid fields and arguments, including the ones retrieved via regex-based parsing in suggestion hints when available ([`get_valid_fields()`](./krakql/oracle.py#L111), [`get_valid_args()`](./krakql/oracle.py#L269)).
6. The *Schema Tracker* updates the partial schema observed so far through `Schema`, `Type`, and `Field` structures ([`Schema`](./krakql/graphql_schema.py#L249)), and the loop continues until time budget expires, or all novelty scores reach 0 (`get_by_novelty` returns `None`).


## Usage
To run *KrakQL*, install the dependencies, configure your OpenAI API key, and start a blind introspection session against a GraphQL endpoint.

### Install dependencies
```bash
git clone https://github.com/marcellomaugeri/KrakQL.git
cd KrakQL
poetry install
```

**Note**: *Poetry* is recommended, but you can install *KrakQL* using `pip` as well. Just make sure to install the required dependencies listed in `pyproject.toml`.


### Configure your OpenAI key
*KrakQL* currently supports OpenAI models (default: `gpt-5-nano`), so you need to set up your OpenAI API key as an environment variable.
However, as *Google ADK* supports multiple LLM providers, please feel free to experiment with other providers and [change it here](./krakql/agent/config.py).

```bash
export OPENAI_API_KEY="<your key>"
```

### Run *KrakQL*
The command below starts a blind introspection session against the target endpoint, incrementally builds the inferred schema, and writes the result to `schema.graphql`.
By default, *KrakQL* uses a time budget of 5 minutes, configurable with `--time-budget` (in seconds).
```bash
poetry run krakql https://example.com/graphql --time-budget 300 -o schema.graphql
```

### Useful options

#### Authentication and/or Authorisation
If the target endpoint requires authentication (or any custom HTTP header), pass each header with `-H "<Header-Name>: <value>"`.
Example:
```bash
poetry run krakql https://example.com/graphql \
    -H "Authorization: Bearer <token>" \
    -H "X-API-Key: <key>" \
    -o schema.graphql
```

#### Tune novelty search
*KrakQL* updates novelty on the selected *Target Path* using `--reward-factor` (`α` in the paper, default `0.1`) and `--decay-factor` (`β` in the paper, default `0.05`).
During field probing, the selected type is rewarded when at least one new field is discovered for that type, and decayed when no new field is found.
The same strategy applies during argument probing: the selected field is rewarded when at least one new argument is discovered, and decayed otherwise.
In practice, larger `--reward-factor` and/or smaller `--decay-factor` make exploration longer, while smaller `--reward-factor` and/or larger `--decay-factor` make it stop earlier.

If you want to experiment with different values, you can set them in this way:
```bash
poetry run krakql https://example.com/graphql \
    --reward-factor 0.15 \
    --decay-factor 0.03 \
    -o schema.graphql
```

## Disclaimer

Please note that the code in this repository is a research prototype and may generate damaging queries.
Do not use this software against any system without explicit prior written authorisation from the legal owner. The authors and maintainers disclaim any liability for misuse or damage caused by unauthorised use.
*KrakQL* is based on [Clairvoyance](https://github.com/nikitastupin/clairvoyance), which is licensed under the Apache 2.0 License.
See [LICENSE](./LICENSE) for licensing details.
Contributions are encouraged through pull requests.
