FROM node:21-alpine

#ENV NODE_ENV=development

# Install dependencies
RUN apk add git

# Clone the db and checkout the specific commit
RUN git clone https://github.com/GregLyons/poke-db.git
WORKDIR /poke-db
RUN git checkout 75162ef652a0bc6cf63084a47ee9acf1a471de6a
RUN sed -i \
-e "s/\.then( () => {/\.then( async () => {/g" \
-e "/console.log('\\nAll tables created and all data inserted!\\n');/a \        await db.end();" \
src/db/index.js
RUN npm i

# Clone the repo and checkout the specific commit
WORKDIR /
RUN git clone https://github.com/GregLyons/poke-gql.git
WORKDIR /poke-gql
RUN git checkout d1fbb8b7465f6e7122dbf28f130a6d68cdf8e746
RUN npm i