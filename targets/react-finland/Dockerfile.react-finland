FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive
# Install nodejs
RUN apt update && apt install -y nodejs git npm

# Install yarn and n
# RUN npm install -g yarn n

RUN git clone https://github.com/ReactFinland/graphql-api.git

WORKDIR /graphql-api

RUN npm install


# Set the environment variable (necessary for the babel-loader dependency)
# ENV SKIP_PREFLIGHT_CHECK=true

# Install dependencies
# RUN yarn

# Run the server
# CMD ["yarn", "start"]
