#!/bin/bash

sleep 40
clairvoyance http://react-app:3000/graphql -o /test-app/schema.json
python3 introspection_to_sql.py /test-app/schema.json /test-app/schema.graphql
schemadiff -o /schema.graphqls -n /test-app/schema.graphql --as-json >/test-app/changes.json

exit 0
