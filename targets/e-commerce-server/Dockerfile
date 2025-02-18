FROM graphql-base:latest

# Install nodejs
RUN apt-get install -y nodejs npm curl wget

# Install yarn and n
RUN npm install -g yarn n

# Change node version
RUN n 22.14.0

# Clone the repo and install dependencies
RUN git clone https://github.com/react-shop/react-ecommerce.git
WORKDIR /react-ecommerce
RUN git checkout 90e18e2

# Install dependencies
RUN yarn

# Start the server
RUN yarn start