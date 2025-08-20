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
    step: float,
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
    iterations = 1

    schema = await oracle.init_schema(input_schema)

    # Calculate when to stop based on the time budget
    start_time = time.monotonic()
    end_time = start_time + time_budget
    
    while time.monotonic() < end_time:
        logger.info(f"Iteration {iterations}")
        iterations += 1
        
        # Get next type to probe by novelty score
        next_type = schema.get_next_type_by_novelty()

        # STOPPING CONDITION
        if next_type:
            logger.debug(f"Next type to explore: {next_type.name if next_type else 'None'}")
        else:
            # We stop even if we could probe arguments
            logger.info("No more types to explore ->  Stopping introspection.")
            break

        n_new_fields, n_new_types = await oracle.probe_fields_of_type(agent, schema, next_type)

        # If new fields or types were discovered, update the schema
        if n_new_fields > 0 or n_new_types > 0:
            logger.info(f"Discovered {n_new_fields} new fields and {n_new_types} new types.")
            next_type.increase_novelty(0.1)
        else:
            next_type.reduce_novelty(0.1)
            logger.info("No new fields or types discovered.")
            
        # Get the next field on which probe arguments
        next_field_to_probe_args = next_type.get_next_field_by_novelty()

        if next_field_to_probe_args:
            logger.debug(f"Next field to explore: {next_field_to_probe_args.name if next_field_to_probe_args else 'None'}")
        else:
            logger.info("No more arguments to explore -> Continue")
            continue

        # Get argument suggestions for the next field
        n_new_args, n_new_arg_types = await oracle.probe_arguments_for_field_of_type(agent, schema, next_field_to_probe_args, next_type)

        if n_new_args > 0 or n_new_arg_types > 0:
            logger.info(f"Discovered {n_new_args} new arguments and {n_new_arg_types} new argument types for {next_field_to_probe_args.name}.")
            next_field_to_probe_args.increase_novelty(0.1)
        else:
            logger.info(f"No new arguments discovered for {next_field_to_probe_args.name}.")
            next_field_to_probe_args.reduce_novelty(0.1)
        
        # Save progress
        if output_path:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(schema.sdl_representation())

    if time.monotonic() >= end_time:
        logger.info("Time budget expired.")
    logger.info("Blind introspection complete.")
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
            step=args.step,
            time_budget=args.time_budget,
            proxy=args.proxy,
            max_retries=args.max_retries,
            backoff=args.backoff,
            disable_ssl_verify=args.no_ssl,
        )
    )
