FROM python:latest

COPY ./introspection_to_sql.py /introspection_to_sql.py
COPY ./targets/patio-api/schema.graphqls /schema.graphqls
COPY ./targets/patio-api/patio.sh /patio.sh
RUN apt update
RUN apt install python3-venv python3-pip wget -y
RUN pip install clairvoyance
RUN pip install graphql-schema-diff
RUN wget https://github.com/first20hours/google-10000-english/blob/master/20k.txt
RUN chmod +x /patio.sh
