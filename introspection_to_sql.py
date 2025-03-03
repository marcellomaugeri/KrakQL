import json
import argparse
import os
from graphql import build_client_schema, print_schema

parser = argparse.ArgumentParser(description='Convert introspection JSON to GraphQL SDL')
parser.add_argument('input', help='Path to the introspection JSON file')
parser.add_argument('output', help='Path to the output SDL file')
args = parser.parse_args()

with open(args.input, 'r') as file:
    introspection_data = json.load(file)

schema_data = introspection_data.get("data", introspection_data)

schema = build_client_schema(schema_data)

sdl = print_schema(schema)

output_dir = os.path.dirname(args.output)
if output_dir and not os.path.exists(output_dir):
    os.makedirs(output_dir)

with open(args.output, 'w') as outfile:
    outfile.write(sdl)

print(f"Schema has been written to {args.output}")
