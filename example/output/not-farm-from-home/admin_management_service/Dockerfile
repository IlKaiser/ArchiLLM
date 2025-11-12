FROM openjdk:17-jdk-alpine
VOLUME /tmp
COPY target/admin_management_service.jar admin_management_service.jar
ENTRYPOINT ["java","-jar","/admin_management_service.jar"]