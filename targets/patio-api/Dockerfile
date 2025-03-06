FROM ubuntu:20.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y openjdk-11-jdk && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN apt update && apt install curl unzip zip git wget -y
RUN apt install default-jre -y
RUN apt install default-jdk -y
RUN apt install gradle -y
ENV JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
ENV PATH=$JAVA_HOME/bin:$PATH
RUN git clone https://github.com/patio-team/patio-api.git
WORKDIR /patio-api
RUN cp src/main/resources/application-prod.yml src/main/resources/application.yml
CMD ["./gradlew", "run"]
