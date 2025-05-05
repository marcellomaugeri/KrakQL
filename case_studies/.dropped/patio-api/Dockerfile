FROM eclipse-temurin:11-alpine
RUN apk add --no-cache git
RUN git clone https://github.com/patio-team/patio-api.git
WORKDIR /patio-api

RUN ./gradlew build \
-x test \
-x check \
-x jacocoTestReport \
-x jacocoTestCoverageVerification \
-x pmdMain \
-x pmdTest \
-x spotlessCheck \
-x spotbugsMain \
-x spotbugsTest \
-x dependencyCheckAnalyze \
-x generateLicenseReport \
-x licenseMain \
-x licenseTest 

RUN sed -i '/@Singleton/a @Requires(property = "oauth2.apikey")\n@Requires(property = "oauth2.apisecret")\n@Requires(property = "oauth2.callback")' /patio-api/src/main/java/patio/security/services/internal/ScribeOauth2ServiceProvider.java
RUN sed -i '/^package patio\.security\.services\.internal;/a import io.micronaut.context.annotation.Requires;' /patio-api/src/main/java/patio/security/services/internal/ScribeOauth2ServiceProvider.java

COPY application.yml /patio-api/src/main/resources/application.yml

CMD [ "gradlew", "run" ]