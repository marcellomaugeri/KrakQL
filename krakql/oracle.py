# pylint: disable=anomalous-backslash-in-string, line-too-long

import asyncio
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from krakql import graphql_schema
from krakql.entities import GraphQLPrimitive
from krakql.entities.context import client, config, log
from krakql.entities.errors import EndpointError
from krakql.entities.oracle import FuzzingContext
from krakql.utils import track
from krakql.krakql_agent import KrakQLAgentSingleton 

# yapf: disable

MAIN_REGEX = r"""[_0-9A-Za-z\.\[\]!]+"""
REQUIRED_BUT_NOT_PROVIDED = r"""required(, but it was not provided| but not provided)?\."""

_FIELD_REGEXES = {
    'SKIP': [
        r"""Field ['"]""" + MAIN_REGEX + r"""['"] must not have a selection since type ['"]""" + MAIN_REGEX + r"""['"] has no subfields\.""",
        r"""Field ['"]""" + MAIN_REGEX + r"""['"] of type ['"]""" + MAIN_REGEX + r"""['"] must not have a sub selection\.""",
        r"""Field ['"]""" + MAIN_REGEX + r"""['"] argument ['"]""" + MAIN_REGEX + r"""['"] of type ['"]""" + MAIN_REGEX + r"""['"] is """ + REQUIRED_BUT_NOT_PROVIDED,
        r"""Cannot query field ['"]""" + MAIN_REGEX + r"""['"] on type ['"]""" + MAIN_REGEX + r"""['"]\.""",
        r"""Cannot query field ['"]""" + MAIN_REGEX + r"""['"] on type ['"](""" + MAIN_REGEX + r""")['"]\. Did you mean to use an inline fragment on ['"]""" + MAIN_REGEX + r"""['"]\?""",
        r"""Cannot query field ['"]""" + MAIN_REGEX + r"""['"] on type ['"](""" + MAIN_REGEX + r""")['"]\. Did you mean to use an inline fragment on ['"]""" + MAIN_REGEX + r"""['"] or ['"]""" + MAIN_REGEX + r"""['"]\?""",
        r"""Cannot query field ['"]""" + MAIN_REGEX + r"""['"] on type ['"](""" + MAIN_REGEX + r""")['"]\. Did you mean to use an inline fragment on (['"]""" + MAIN_REGEX + r"""['"],? )+(or ['"]""" + MAIN_REGEX + r"""['"])?\?""",
        r"""Validation error of type FieldUndefined: Field ''""" + MAIN_REGEX + r"""' in type '""" + MAIN_REGEX + r"""' is undefined @ ''""" + MAIN_REGEX + r"""'""" # Java
    ],
    'VALID_FIELD': [
        r"""Field ['"](?P<field>""" + MAIN_REGEX + r""")['"] of type ['"](?P<typeref>""" + MAIN_REGEX + r""")['"] must have a selection of subfields\. Did you mean ['"]""" + MAIN_REGEX + r"""( \{ \.\.\. \})?['"]\?""",
        r"""Field ['"](?P<field>""" + MAIN_REGEX + r""")['"] of type ['"](?P<typeref>""" + MAIN_REGEX + r""")['"] must have a sub selection\."""
    ],
    'SINGLE_SUGGESTION': [
        r"""Cannot query field ['"](""" + MAIN_REGEX + r""")['"] on type ['"]""" + MAIN_REGEX + r"""['"]\. Did you mean ['"](?P<field>""" + MAIN_REGEX + r""")['"]\?"""
    ],
    'DOUBLE_SUGGESTION': [
        r"""Cannot query field ['"]""" + MAIN_REGEX + r"""['"] on type ['"]""" + MAIN_REGEX + r"""['"]\. Did you mean ['"](?P<one>""" + MAIN_REGEX + r""")['"] or ['"](?P<two>""" + MAIN_REGEX + r""")['"]\?"""
    ],
    'MULTI_SUGGESTION': [
        r"""Cannot query field ['"](""" + MAIN_REGEX + r""")['"] on type ['"]""" + MAIN_REGEX + r"""['"]\. Did you mean (?P<multi>(['"]""" + MAIN_REGEX + r"""['"],? )+)(or ['"](?P<last>""" + MAIN_REGEX + r""")['"])?\?"""
    ],
}

_ARG_REGEXES = {
    'SKIP': [
        r"""Unknown argument ['"]""" + MAIN_REGEX + r"""['"] on field ['"]""" + MAIN_REGEX + r"""['"]\.""",
        r"""Unknown argument ['"]""" + MAIN_REGEX + r"""['"] on field ['"]""" + MAIN_REGEX + r"""['"] of type ['"]""" + MAIN_REGEX + r"""['"]\.""",
        r"""Field ['"]""" + MAIN_REGEX + r"""['"] of type ['"]""" + MAIN_REGEX + r"""['"] must have a selection of subfields\. Did you mean ['"]""" + MAIN_REGEX + r"""( \{ \.\.\. \})?['"]\?""",
        r"""Field ['"]""" + MAIN_REGEX + r"""['"] argument ['"]""" + MAIN_REGEX + r"""['"] of type ['"]""" + MAIN_REGEX + r"""['"] is """ + REQUIRED_BUT_NOT_PROVIDED,
    ],
    'SINGLE_SUGGESTION': [
        r"""Unknown argument ['"]""" + MAIN_REGEX + r"""['"] on field ['"]""" + MAIN_REGEX + r"""['"] of type ['"]""" + MAIN_REGEX + r"""['"]\. Did you mean ['"](?P<arg>""" + MAIN_REGEX + r""")['"]\?""",
        r"""Unknown argument ['"]""" + MAIN_REGEX + r"""['"] on field ['"]""" + MAIN_REGEX + r"""['"]\. Did you mean ['"](?P<arg>""" + MAIN_REGEX + r""")['"]\?"""
    ],
    'DOUBLE_SUGGESTION': [
        r"""Unknown argument ['"]""" + MAIN_REGEX + r"""['"] on field ['"]""" + MAIN_REGEX + r"""['"]( of type ['"]""" + MAIN_REGEX + r"""['"])?\. Did you mean ['"](?P<first>""" + MAIN_REGEX + r""")['"] or ['"](?P<second>""" + MAIN_REGEX + r""")['"]\?"""
    ],
    'MULTI_SUGGESTION': [
        r"""Unknown argument ['"]""" + MAIN_REGEX + r"""['"] on field ['"]""" + MAIN_REGEX + r"""['"]\. Did you mean (?P<multi>(['"]""" + MAIN_REGEX + r"""['"],? )+)(or ['"](?P<last>""" + MAIN_REGEX + r""")['"])?\?""",
        r"""Unknown argument ['"]""" + MAIN_REGEX + r"""['"] on field ['"]""" + MAIN_REGEX + r"""['"] of type ['"]""" + MAIN_REGEX + r"""['"]\. Did you mean (?P<multi>(['"]""" + MAIN_REGEX + r"""['"],? )+)(or ['"](?P<last>""" + MAIN_REGEX + r""")['"])?\?"""
    ],
}

_TYPEREF_REGEXES = {
    'FIELD': [
        r"""Field ['"]""" + MAIN_REGEX + r"""['"] of type ['"](?P<typeref>""" + MAIN_REGEX + r""")['"] must have a selection of subfields\. Did you mean ['"]""" + MAIN_REGEX + r"""( \{ \.\.\. \})?['"]\?""",
        r"""Field ['"]""" + MAIN_REGEX + r"""['"] must not have a selection since type ['"](?P<typeref>""" + MAIN_REGEX + r""")['"] has no subfields\.""",
        r"""Cannot query field ['"]""" + MAIN_REGEX + r"""['"] on type ['"](?P<typeref>""" + MAIN_REGEX + r""")['"]\.""",
        r"""Cannot query field ['"]""" + MAIN_REGEX + r"""['"] on type ['"](?P<typeref>""" + MAIN_REGEX + r""")['"]\. Did you mean [^\?]+\?""",
        r"""Field ['"]""" + MAIN_REGEX + r"""['"] of type ['"](?P<typeref>""" + MAIN_REGEX + r""")['"] must not have a sub selection\.""",
        r"""Field ['"]""" + MAIN_REGEX + r"""['"] of type ['"](?P<typeref>""" + MAIN_REGEX + r""")['"] must have a sub selection\.""",
        r"""Validation error of type SubSelectionNotAllowed: Sub selection not allowed on leaf type (?P<typeref>""" + MAIN_REGEX + r""") of field """ + MAIN_REGEX + r""" @ '""" + MAIN_REGEX + r"""'"""
    ],
    'ARG': [
        r"""Field ['"]""" + MAIN_REGEX + r"""['"] argument ['"]""" + MAIN_REGEX + r"""['"] of type ['"](?P<typeref>""" + MAIN_REGEX + r""")['"] is """ + REQUIRED_BUT_NOT_PROVIDED,
        r"""Expected type (?P<typeref>""" + MAIN_REGEX + r"""), found .+\.""",
    ],
}

WRONG_FIELD_EXAMPLE = 'IAmWrongField'

_WRONG_TYPENAME = [
    r"""Cannot query field ['"]""" + WRONG_FIELD_EXAMPLE + r"""['"] on type ['"](?P<typename>""" + MAIN_REGEX + r""")['"].""",
    r"""Field ['"]""" + MAIN_REGEX + r"""['"] must not have a selection since type ['"](?P<typename>""" + MAIN_REGEX + r""")['"] has no subfields.""",
    r"""Field ['"]""" + MAIN_REGEX + r"""['"] of type ['"](?P<typename>""" + MAIN_REGEX + r""")['"] must not have a sub selection.""",
]

_GENERAL_SKIP = [
    r"""String cannot represent a non string value: .+""",
    r"""Float cannot represent a non numeric value: .+""",
    r"""ID cannot represent a non-string and non-integer value: .+""",
    r"""Enum ['"]""" + MAIN_REGEX + r"""['"] cannot represent non-enum value: .+"""
    r"""Int cannot represent non-integer value: .+""",
    r"""Not authorized""",
]

# yapf: enable

# Compiling all regexes for performance
FIELD_REGEXES = {k: [re.compile(r) for r in v] for k, v in _FIELD_REGEXES.items()}
ARG_REGEXES = {k: [re.compile(r) for r in v] for k, v in _ARG_REGEXES.items()}
TYPEREF_REGEXES = {k: [re.compile(r) for r in v] for k, v in _TYPEREF_REGEXES.items()}
WRONG_TYPENAME = [re.compile(r) for r in _WRONG_TYPENAME]
GENERAL_SKIP = [re.compile(r) for r in _GENERAL_SKIP]


# pylint: disable=too-many-branches
def get_valid_fields(error_message: str) -> Set[str]:
    """Fetching valid fields using regex heuristics."""

    valid_fields: Set[str] = set()

    for regex in FIELD_REGEXES["SKIP"] + GENERAL_SKIP:
        if regex.fullmatch(error_message):
            return valid_fields

    for regex in FIELD_REGEXES["VALID_FIELD"]:
        match = regex.fullmatch(error_message)
        if match:
            valid_fields.add(match.group("field"))
            return valid_fields

    for regex in FIELD_REGEXES["SINGLE_SUGGESTION"]:
        match = regex.fullmatch(error_message)
        if match:
            valid_fields.add(match.group("field"))
            return valid_fields

    for regex in FIELD_REGEXES["DOUBLE_SUGGESTION"]:
        match = regex.fullmatch(error_message)
        if match:
            valid_fields.add(match.group("one"))
            valid_fields.add(match.group("two"))
            return valid_fields

    for regex in FIELD_REGEXES["MULTI_SUGGESTION"]:
        match = regex.fullmatch(error_message)
        if match:

            for m in match.group("multi").split(", "):
                if m:
                    valid_fields.add(m.strip("'\" "))
            if match.group("last"):
                valid_fields.add(match.group("last"))

            return valid_fields

    log().debug(f"Unknown error message for `valid_field`: '{error_message}'")

    return valid_fields


async def probe_valid_fields(
    agent: KrakQLAgentSingleton,
    current_schema: str,
    input_document: str,
) -> Set[str]:
    """Probes the GraphQL endpoint for valid fields using the KrakQL agent.

    Args:
        agent: The KrakQL agent instance.
        current_schema: The current GraphQL schema in SDL
        input_document: The base document.

    Returns:
        A set of discovered valid fields.
    """
    
    # Get new candidate fields from the agent (atomic, updated each time)
    bucket = await agent.suggest_new_fields(current_schema=current_schema, input_document=input_document.replace("FUZZ", "..."))
    if not bucket:
        log().error(f"No suggestions from agent")
        return set()

    document = input_document.replace("FUZZ", " ".join(bucket))
    start_time = time.time()
    response = await client().post(document)
    total_time = time.time() - start_time

    errors = response["errors"]
    
    log().debug(
        f"Sent {len(bucket)} fields, received {len(errors)} errors in {round(total_time, 2)} seconds"
    )

    valid_fields = set(bucket)
    for error in errors:
        error_message = error["message"]
        if ("must not have a selection since type" in error_message
            and "has no subfields" in error_message
            ) or "must not have a sub selection" in error_message:
            return set() # Since the field has no subfields, it cannot be queried
        # First remove field if it produced an 'Cannot query field' error
        log().debug(error)
        error_patterns = [
                re.compile(r"""Cannot query field [\'"](?P<invalid_field>[_A-Za-z][_0-9A-Za-z]*)[\'"]"""),
                re.compile(r"""Validation error of type FieldUndefined: Field ['"](?P<invalid_field>[_A-Za-z][_0-9A-Za-z]*)['"]"""),
            ]
        for error_pattern in error_patterns:
            match = re.search(error_pattern, error_message)
            if match:
                log().debug(f"Found invalid field: {match.group('invalid_field')}")
            # Remove all invalid fields
                valid_fields.discard(match.group("invalid_field"))
        # Now examine the error to extract valid fields | if there is no error the field is already considered valid
        valid_fields |= get_valid_fields(error_message)

    return valid_fields


async def probe_valid_args(
    agent: KrakQLAgentSingleton,
    field: graphql_schema.Field,
    current_schema: str,
    input_document: str,
) -> Set[str]:
    """Sends the bucket as arguments and deduces its type from the error msgs received."""

    bucket = await agent.suggest_new_arguments(current_schema=current_schema, input_document=input_document.replace("FUZZ", f'{field.name}(...)'))
    if not bucket:
        log().error(f"No suggestions from agent")
        return set()

    document = input_document.replace(
        "FUZZ", f'{field.name}({", ".join([w + ": 7" for w in bucket])})'
    )
    start_time = time.time()
    response = await client().post(document=document)
    total_time = time.time() - start_time
    
    valid_args = set(bucket)
    if "errors" not in response:
        return valid_args

    errors = response["errors"]
    
    log().debug(f"Sent {len(bucket)} fields, received {len(errors)} errors in {round(total_time, 2)} seconds")
    for error in errors:
        error_message = error["message"]

        if (
            "must not have a selection since type" in error_message
            and "has no subfields" in error_message
            ) or "must not have a sub selection" in error_message:
            return set()

        # First remove arg if it produced an 'Unknown argument' error
        match = re.search(
            r"""Unknown argument ['"](?P<invalid_arg>[_A-Za-z][_0-9A-Za-z]*)['"] on field ['"][_A-Za-z][_0-9A-Za-z\.]*['"]""",
            error_message,
        )
        if match:
            valid_args.discard(match.group("invalid_arg"))

        duplicate_arg_regex = r"""There can be only one argument named ["'](?P<arg>[_0-9a-zA-Z\.\[\]!]*)["']\.?"""
        if re.fullmatch(duplicate_arg_regex, error_message):
            match = re.fullmatch(duplicate_arg_regex, error_message)
            valid_args.discard(match.group("arg"))  # type: ignore
            continue

        # Second obtain args suggestions from error message
        valid_args |= get_valid_args(error_message)

    return valid_args

def get_valid_args(error_message: str) -> Set[str]:
    """Get the type of an arg using regex."""

    valid_args = set()

    for regex in ARG_REGEXES["SKIP"] + GENERAL_SKIP:
        if re.fullmatch(regex, error_message):
            return set()

    for regex in ARG_REGEXES["SINGLE_SUGGESTION"]:
        if re.fullmatch(regex, error_message):
            match = re.fullmatch(regex, error_message)
            if match:
                valid_args.add(match.group("arg"))

    for regex in ARG_REGEXES["DOUBLE_SUGGESTION"]:
        match = re.fullmatch(regex, error_message)
        if match:
            valid_args.add(match.group("first"))
            valid_args.add(match.group("second"))

    for regex in ARG_REGEXES["MULTI_SUGGESTION"]:
        if re.fullmatch(regex, error_message):
            match = re.fullmatch(regex, error_message)
            if match:
                for m in match.group("multi").split(", "):
                    if m:
                        valid_args.add(m.strip("'\" "))

                if match.group("last"):
                    valid_args.add(match.group("last"))

    if not valid_args:
        log().debug(f"Unknown error message for `valid_args`: '{error_message}'")

    return valid_args


def get_typeref(
    error_message: str,
    context: FuzzingContext,
) -> Optional[graphql_schema.TypeRef]:
    """Using predefined regex deduce the type of a field."""

    def __extract_matching_fields(
        error_message: str,
        context: FuzzingContext,
    ) -> Optional[re.Match]:

        if context == FuzzingContext.FIELD:
            # in the case of a field
            for regex in TYPEREF_REGEXES["ARG"] + GENERAL_SKIP:
                if re.fullmatch(regex, error_message):
                    return None

            for regex in TYPEREF_REGEXES["FIELD"]:
                match = re.fullmatch(regex, error_message)
                if match:
                    return match

        elif context == FuzzingContext.ARGUMENT:
            # in the case of an argument
            # we drop the following messages
            for regex in TYPEREF_REGEXES["FIELD"] + GENERAL_SKIP:
                if re.fullmatch(regex, error_message):
                    return None
            # if not dropped, we try to extract the type
            for regex in TYPEREF_REGEXES["ARG"]:
                match = re.fullmatch(regex, error_message)
                if match:
                    return match

        log().debug(
            f"Unknown error message for `typeref` with context `{context.value}`: '{error_message}'"
        )
        return None

    match = __extract_matching_fields(error_message, context)

    if match:
        tk = match.group("typeref")

        name = tk.replace("!", "").replace("[", "").replace("]", "")
        kind = ""
        if name in GraphQLPrimitive:
            kind = "SCALAR"
        elif context == FuzzingContext.FIELD:
            kind = "OBJECT"
        elif context == FuzzingContext.ARGUMENT:
            kind = "INPUT_OBJECT"
            name = (
                name.removesuffix("Input") + "Input"
            )  # Make sure `Input` is always once at the end
        else:
            log().debug(f"Unknown kind for `typeref`: '{error_message}'")
            return None

        is_list = bool("[" in tk and "]" in tk)
        non_null_item = bool(is_list and "!]" in tk)
        non_null = tk.endswith("!")

        return graphql_schema.TypeRef(
            name=name,
            kind=kind,
            is_list=is_list,
            non_null_item=non_null_item,
            non_null=non_null,
        )

    return None


async def probe_typeref(
    documents: List[str],
    context: FuzzingContext,
) -> Optional[graphql_schema.TypeRef]:
    """Sending a document to attain errors in order to deduce the type of fields."""

    async def __probation(document: str) -> Optional[graphql_schema.TypeRef]:
        """Send a document to attempt discovering a typeref."""

        response = await client().post(document)
        for error in response.get("errors", []):
            if isinstance(error, str):
                continue

            if not isinstance(error["message"], dict):
                typeref = get_typeref(
                    error["message"],
                    context,
                )
            log().debug(f'get_typeref("{error["message"]}", "{context}") -> {typeref}')
            if typeref:
                return typeref

        return None

    tasks: List[asyncio.Task] = []
    for document in documents:
        tasks.append(asyncio.create_task(__probation(document)))

    typeref: Optional[graphql_schema.TypeRef] = None
    results = await asyncio.gather(*tasks)
    for result in results:
        if result:
            typeref = result

    if not typeref and context != FuzzingContext.ARGUMENT:
        error_message = f"Unable to get TypeRef for {documents} in context {context}. "
        error_message += "It is very likely that Field Suggestion is not fully enabled on this endpoint."
        raise EndpointError(error_message)

    return typeref


async def probe_field_type(
    field: str,
    input_document: str,
) -> Optional[graphql_schema.TypeRef]:
    """Wrapper function for sending the queries to deduce the field type."""

    documents = [
        input_document.replace("FUZZ", f"{field}"),
        input_document.replace("FUZZ", f"{field} {{ lol }}"),
    ]

    return await probe_typeref(documents, FuzzingContext.FIELD)


async def probe_arg_typeref(
    field: str,
    arg: str,
    input_document: str,
) -> Optional[graphql_schema.TypeRef]:
    """Wrapper function to deduce the type of an arg."""

    documents = [
        input_document.replace("FUZZ", f"{field}({arg}: 42)"),
        input_document.replace("FUZZ", f"{field}({arg}: {{}})"),
        input_document.replace("FUZZ", f"{field}({arg[:-1]}: 42)"),
        input_document.replace("FUZZ", f'{field}({arg}: "42")'),
        input_document.replace("FUZZ", f"{field}({arg}: false)"),
    ]

    return await probe_typeref(documents, FuzzingContext.ARGUMENT)


async def probe_typename(input_document: str) -> str:

    document = input_document.replace("FUZZ", WRONG_FIELD_EXAMPLE)

    response = await client().post(document=document)
    if "errors" not in response:
        log().warning(
            f"""Unable to get typename from {document}.
                      Field Suggestion might not be enabled on this endpoint. Using default "Query"""
        )
        return "Query"

    errors = response["errors"]

    match = None
    for regex in WRONG_TYPENAME:
        for error in errors:
            match = re.fullmatch(regex, error["message"])
            if match:
                break
        if match:
            break

    if not match:
        log().debug(
            f"""Unkwon error in `probe_typename`: "{errors}" does not match any known regexes.
                    Field Suggestion might not be enabled on this endpoint. Using default "Query"""
        )
        return "Query"

    return match.group("typename").replace("[", "").replace("]", "").replace("!", "")


async def fetch_root_typenames() -> Dict[str, Optional[str]]:
    documents: Dict[str, str] = {
        "queryType": "query { __typename }",
        "mutationType": "mutation { __typename }",
        "subscriptionType": "subscription { __typename }",
    }
    typenames: Dict[str, Optional[str]] = {
        "queryType": None,
        "mutationType": None,
        "subscriptionType": None,
    }

    for name, document in track(
        documents.items(), description="Fetching root typenames"
    ):
        response = await client().post(document=document)

        data = response.get("data", {})
        if data:
            typenames[name] = data["__typename"]

    log().debug(f"Root typenames are: {typenames}")
    return typenames

async def init_schema(input_schema: Optional[Dict[str, Any]] = None) -> graphql_schema.Schema:
    if not input_schema:
        root_typenames = await fetch_root_typenames()
        schema = graphql_schema.Schema(
            query_type=root_typenames["queryType"],
            mutation_type=root_typenames["mutationType"],
            subscription_type=root_typenames["subscriptionType"],
        )
    else:
        schema = graphql_schema.Schema(schema=input_schema)
    return schema

async def probe_fields_of_type(agent: KrakQLAgentSingleton, schema: graphql_schema.Schema, type: graphql_schema.Type) -> Tuple[int, int]:
    """Probes the fields of a specific GraphQL type.
    
    Args:
        agent: The KrakQL agent instance.
        schema: The GraphQL schema.
        type: The GraphQL type to probe.
    
    Returns:
        A tuple containing the number of new fields and new types added.
    """
    _next = type.name
    input_document = schema.convert_path_to_document(schema.get_path_from_root(_next))
    log().debug(f"Input document for {type.name}: {input_document}")
    
    valid_fields = await probe_valid_fields(
        agent,
        schema.sdl_representation(),
        input_document,
    )
    
    new_fields, new_types = (0, 0)
    for field_name in valid_fields:
        if not type.has_field(field_name):
            typeref = await probe_field_type(
                field_name,
                input_document,
            )
            field = graphql_schema.Field(field_name, typeref)
            if type.add_field(field):
                new_fields += 1
            # Ensure eventual new types are registered
            if schema.add_type(field.type.name, "OBJECT"):
                new_types += 1

    return new_fields, new_types

async def probe_arguments_for_field_of_type(agent: KrakQLAgentSingleton, schema: graphql_schema.Schema, field: graphql_schema.Field, type: graphql_schema.Type) -> Tuple[int, int]:
    """Probe arguments for a specific field."""
    input_document = schema.convert_path_to_document(schema.get_path_from_root(type.name))
    
    arg_names = await probe_valid_args(
        agent,
        field,
        current_schema=schema.sdl_representation(),
        input_document=input_document,
    )
    
    new_args, new_args_type = (0, 0)

    for arg_name in arg_names:
        if not field.has_argument(arg_name):
            log().debug(f"Adding argument {arg_name} to field {field.name}")
            arg_typeref = await probe_arg_typeref(field.name, arg_name, input_document)

            if not arg_typeref:
                log().debug(f"Skip argument {arg_name} because TypeRef equals {arg_typeref}")
                continue

            argument = graphql_schema.InputValue(arg_name, arg_typeref)
            if field.add_arg(argument):
                new_args += 1

            if schema.add_type(argument.type.name, "INPUT_OBJECT"):
                new_args_type += 1
                
    return new_args, new_args_type