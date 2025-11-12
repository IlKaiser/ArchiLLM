FROM openjdk:17-jdk-alpine
VOLUME /tmp
COPY target/agricultural_company_service.jar agricultural_company_service.jar
ENTRYPOINT ["java","-jar","/agricultural_company_service.jar"]