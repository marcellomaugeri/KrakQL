FROM base_image

# Install nodejs
RUN apt-get install -y nodejs npm curl wget

# Install yarn and n
RUN npm install -g yarn n

# Clone the repo and install dependencies
RUN git clone https://github.com/react-shop/react-ecommerce.git
WORKDIR /react-ecommerce
RUN git checkout 90e18e2

# Change node version
RUN n 14.21.3

# Set the environment variable (necessary for the babel-loader dependency)
ENV SKIP_PREFLIGHT_CHECK=true

# Install dependencies
RUN yarn

# Run the server
CMD ["yarn", "start"]
