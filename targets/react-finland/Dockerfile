FROM base_image

# Install nodejs
RUN apt-get install -y nodejs npm

# Install yarn and n
# RUN npm install -g yarn n

RUN git clone https://github.com/ReactFinland/graphql-api.git

WORKDIR /graphql-api

RUN NODE_ENV="production"
RUN npm install
# RUN npm run build
CMD ["npm", "start"]

# Set the environment variable (necessary for the babel-loader dependency)
# ENV SKIP_PREFLIGHT_CHECK=true

# Install dependencies
# RUN yarn

# Run the server
# CMD ["yarn", "start"]
