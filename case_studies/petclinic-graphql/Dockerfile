FROM maven:3.9.9-eclipse-temurin-21-alpine

# Install dependencies
RUN apk update && apk add --no-cache docker docker-compose git pnpm

# Clone the repo and checkout the specific commit
RUN git clone https://github.com/spring-petclinic/spring-petclinic-graphql.git
WORKDIR /spring-petclinic-graphql/
RUN git checkout 0aa4212fb4b10bb5e3e112425cef5c7bca8e3a59

# Build the application
RUN cd petclinic-graphiql && pnpm install && pnpm build && pnpm copy-to-backend && cd ..
RUN ./mvnw -DskipTests -pl backend package

#RUN chmod +x build-local.sh
#CMD ["./build-local.sh"]