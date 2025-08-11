import asyncio
import json
import logging
import re
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

from krakql import graphql_schema, oracle
from krakql.client import Client
from krakql.config import Config
from krakql.entities import GraphQLPrimitive
from krakql.entities.context import client, logger_ctx
from krakql.krakql_agent import KrakQLAgentSingleton
from krakql.utils import parse_args, setup_logger


def setup_context(
    url: str,
    logger: logging.Logger,
    headers: Optional[Dict[str, str]] = None,
    concurrent_requests: Optional[int] = None,
    proxy: Optional[str] = None,
    max_retries: Optional[int] = None,
    backoff: Optional[int] = None,
    disable_ssl_verify: Optional[bool] = None,
) -> None:
    """Initialize objects and freeze them into the context."""

    Config()
    Client(
        url,
        headers=headers,
        concurrent_requests=concurrent_requests,
        proxy=proxy,
        max_retries=max_retries,
        backoff=backoff,
        disable_ssl_verify=disable_ssl_verify,
    )
    logger_ctx.set(logger)


async def blind_introspection(  # pylint: disable=too-many-arguments
    url: str,
    logger: logging.Logger,
    model: str,
    max_tries: int,
    time_budget: int,
    concurrent_requests: Optional[int] = None,
    headers: Optional[Dict[str, str]] = None,
    input_document: Optional[str] = None,
    input_schema_path: Optional[str] = None,
    output_path: Optional[str] = None,
    proxy: Optional[str] = None,
    max_retries: Optional[int] = None,
    backoff: Optional[int] = None,
    disable_ssl_verify: Optional[bool] = None,
) -> str:
    setup_context(
        url,
        logger=logger,
        headers=headers,
        concurrent_requests=concurrent_requests,
        proxy=proxy,
        max_retries=max_retries,
        backoff=backoff,
        disable_ssl_verify=disable_ssl_verify,
    )

    logger.info(f"Starting blind introspection on {url}...")

    agent = KrakQLAgentSingleton(model=model)
    await agent.init_session()

    input_schema = None
    if input_schema_path:
        with open(input_schema_path, "r", encoding="utf-8") as f:
            input_schema = json.load(f)

    input_document = input_document or "query { FUZZ }"
    ignored = set(e.value for e in GraphQLPrimitive)
    iterations = 1
    
    # Calculate when to stop based on the time budget
    start_time = time.monotonic()
    end_time = start_time + time_budget
    
    while time.monotonic() < end_time:
        logger.info(f"Iteration {iterations}")
        iterations += 1
        
        # 1. Discover fields for current type using current input_document
        schema = await oracle.krakql(
            agent=agent,
            max_tries=max_tries,
            input_document=input_document,
            input_schema=input_schema,
        )
        
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(schema)

        # 2. Save progress
        input_schema = json.loads(schema)
        s = graphql_schema.Schema(schema=input_schema)

        # Novelty search: Step 1 types without fields
        _next = s.get_type_without_fields(ignored)
        # TODO: add field in ignored if it says it does not have subfields
        if not _next:
            # Novelty search: Step 2 types that led to new fields in the last iteration
            # TODO
            
            # Novelty search: Step 3 types with least tried fields
            _next = s.get_least_tried_type(ignored)


        #if output_path:
        #    with open(output_path, "w", encoding="utf-8") as f:
        #        f.write(schema)

        # 2. Save progress
        #input_schema = json.loads(schema)
        #s = graphql_schema.Schema(schema=input_schema)

        # 3. Find next type that needs exploration
        #_next = s.get_type_without_fields(ignored)
        #ignored.add(_next)

        # 4. STOPPING CONDITION: No more types to explore
        #if _next:
        #    input_document = s.convert_path_to_document(s.get_path_from_root(_next))
        #else:
        #    break

    logger.info("Time budget expired. Blind introspection complete.")
    await client().close()
    return schema


def cli(argv: Optional[List[str]] = None) -> None:
    if argv is None:
        argv = sys.argv[1:]

    args = parse_args(argv)
    setup_logger(args.verbose)

    headers = {}
    for h in args.headers:
        key, value = h.split(": ", 1)
        headers[key] = value

    asyncio.run(
        blind_introspection(
            args.url,
            logger=logging.getLogger("krakql"),
            concurrent_requests=args.concurrent_requests,
            headers=headers,
            input_document=args.document,
            input_schema_path=args.input_schema,
            output_path=args.output,
            model=args.model,
            max_tries=args.max_tries,
            time_budget=args.time_budget,
            proxy=args.proxy,
            max_retries=args.max_retries,
            backoff=args.backoff,
            disable_ssl_verify=args.no_ssl,
        )
    )
