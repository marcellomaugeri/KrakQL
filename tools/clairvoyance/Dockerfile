FROM python:3.12.10-alpine3.21

# Install git
RUN apk add --no-cache git

# Clone the repo
RUN git clone https://github.com/nikitastupin/clairvoyance.git
WORKDIR /clairvoyance
RUN git checkout 227f4c5428c18f14021a414bbaa3b203f242131b
# Install dependencies
RUN pip install -r requirements.txt

# Copy the wordlists
COPY ../../utils/wordlists /wordlists