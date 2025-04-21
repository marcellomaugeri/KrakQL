FROM python:3.8-alpine

RUN apk add --update curl git

RUN git clone https://github.com/dolevf/Damn-Vulnerable-GraphQL-Application dvga
WORKDIR /dvga
RUN git checkout 124b436e3c98de4d8c4de3838b52a409bbe5fb27

RUN python -m venv venv
RUN source venv/bin/activate
RUN pip3 install --upgrade pip --no-warn-script-location --disable-pip-version-check
RUN pip3 install -r requirements.txt --user --no-warn-script-location
RUN python setup.py