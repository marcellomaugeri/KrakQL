FROM base_image

RUN apt update && apt install curl unzip zip git wget -y
RUN apt install default-jre -y
RUN apt install default-jdk -y
# RUN curl -s "https://get.sdkman.io" | bash
# RUN wget https://services.gradle.org/distributions/gradle-8.12-bin.zip
# RUN unzip -d /opt/gradle gradle-8.12-bin.zip
RUN apt install gradle -y
# RUN wget https://dlcdn.apache.org/maven/maven-3/3.9.9/binaries/apache-maven-3.9.9-bin.tar.gz
# RUN tar -xvf apache-maven-3.9.9-bin.tar.gz
# RUN mv ./apache-maven-3.9.9 /opt/
RUN git clone https://github.com/patio-team/patio-api.git
WORKDIR /patio-api
# ENV M2_HOME='/opt/apache-maven-3.9.9'
# ENV PATH="$M2_HOME/bin:$PATH"
# RUN export PATH
# RUN mvn clean package
CMD ["./gradlew", "build"]
# RUN ./timbuctoo_only.sh
