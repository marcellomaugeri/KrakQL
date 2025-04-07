FROM maven:3.9.9-eclipse-temurin-21-alpine

RUN apk add --no-cache git
RUN git clone https://github.com/HuygensING/timbuctoo.git

WORKDIR /timbuctoo

#add repository
RUN sed -i '/<repositories>/a \
            <repository> \
                <id>mvnrepository</id> \
                <url>https://artifactory.appodeal.com/appodeal-public/</url> \
                <snapshots> \
                    <enabled>true</enabled> \
                </snapshots> \
                <releases> \
                    <enabled>true</enabled> \
                </releases> \
            </repository>' pom.xml

RUN mvn clean package

COPY run.sh /timbuctoo/run.sh

CMD ["bash", "run.sh"]
