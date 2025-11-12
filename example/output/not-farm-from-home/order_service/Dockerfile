FROM openjdk:17-jdk-alpine
VOLUME /tmp
COPY target/order_service.jar order_service.jar
ENTRYPOINT ["java","-jar","/order_service.jar"]