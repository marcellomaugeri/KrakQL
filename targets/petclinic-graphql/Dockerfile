FROM maven:3.9.9-eclipse-temurin-21-alpine

RUN apk update && apk add --no-cache docker docker-compose git pnpm

RUN git clone https://github.com/spring-petclinic/spring-petclinic-graphql.git

WORKDIR /spring-petclinic-graphql/petclinic-graphiql
RUN pnpm install

WORKDIR /spring-petclinic-graphql/

#RUN bash build-local.sh