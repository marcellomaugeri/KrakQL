FROM node:18

RUN apt update && apt install -y python3-venv python3-pip build-essential git
RUN git clone https://github.com/trevorblades/countries.git
WORKDIR /countries
# Add the line send_metrics = false in `wrangler.toml`
RUN echo "send_metrics = false" >> wrangler.toml

RUN yarn

CMD ["yarn", "start"]