FROM node:23-alpine

RUN apk add --no-cache python3 py3-pip git
RUN git clone https://github.com/trevorblades/countries.git
WORKDIR /countries
RUN npm install