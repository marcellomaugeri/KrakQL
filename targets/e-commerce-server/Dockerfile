FROM base_image

# Install nodejs
RUN apt-get install -y nodejs npm curl wget

# Install yarn and n
RUN npm install -g yarn n

# Clone the repo and install dependencies
RUN git clone https://github.com/react-shop/react-ecommerce.git
WORKDIR /react-ecommerce
RUN git checkout bc0f268e6d38806910e6d1c198460a0c3fdd81d1

# Remove yarn.lock file
#RUN rm yarn.lock

# Install dependencies
RUN yarn

# Run the server
CMD ["yarn", "start"]
