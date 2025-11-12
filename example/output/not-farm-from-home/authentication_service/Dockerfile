FROM openjdk:17-jdk-alpine
VOLUME /tmp
COPY target/authentication_service.jar authentication_service.jar
ENTRYPOINT ["java","-jar","/authentication_service.jar"]