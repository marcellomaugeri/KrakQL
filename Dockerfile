FROM python:latest

COPY ./introspection_to_sql.py /introspection_to_sql.py
COPY ./targets/react-finland/schema.graphqls /schema.graphqls
COPY ./react.sh /react.sh
RUN apt update
RUN apt install python3-venv python3-pip wget -y
RUN pip install clairvoyance
RUN pip install graphql-schema-diff
RUN wget https://github.com/first20hours/google-10000-english/blob/master/20k.txt
RUN chmod +x ./react.sh
# CMD [ "./react.sh" ]
# RUN clairvoyance http://react-app:5000/graphql -o schema.json -w ./20k.txt
# RUN python3 introspection_to_sql.py schema.json ./schema.graphql
# RUN mv -t results/$react_finland schema.json schema.graphql
# RUN pip install graphql-schema-diff
# RUN schemadiff -o targets/$react_finland/schema.graphqls -n results/$react_finland/schema.graphql --as-json >./results/$react_finland/changes.json
