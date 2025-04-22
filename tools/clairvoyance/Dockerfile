FROM python:latest

COPY introspection_to_sql.py /introspection_to_sql.py
COPY ./targets/country/schema.graphqls /schema.graphqls
COPY ./targets/country/country.sh /country.sh
RUN apt update
RUN apt install python3-venv python3-pip wget -y
RUN pip install clairvoyance
RUN pip install graphql-schema-diff
RUN wget https://github.com/first20hours/google-10000-english/blob/master/20k.txt
