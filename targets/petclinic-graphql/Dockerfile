FROM eclipse-temurin:21

# Install necessary tools
RUN apt update && apt install -y curl unzip zip git wget

# ENV JAVA_HOME=/usr/lib/jvm/java-21-openjdk-amd64
# ENV PATH=$JAVA_HOME/bin:$PATH
# Install Maven (download and setup manually)
RUN wget https://dlcdn.apache.org/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.tar.gz && tar -xvf apache-maven-3.9.9-bin.tar.gz && mv apache-maven-3.9.9 /opt/maven && ln -s /opt/maven/bin/mvn /usr/bin/mvn

# Clone the repository
RUN git clone https://github.com/spring-petclinic/spring-petclinic-graphql.git

WORKDIR /spring-petclinic-graphql
ENV SPRING_DOCKER_COMPOSE_ENABLED=false

# Build the project (skip tests if desired)
RUN ./mvnw clean package -DskipTests

# Start the backend service
CMD ["./mvnw", "spring-boot:run", "-pl", "backend"]
