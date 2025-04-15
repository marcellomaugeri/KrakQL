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

RUN cp src/main/resources/application-prod.yml src/main/resources/application.yml

CMD [ "gradlew", "run" ]