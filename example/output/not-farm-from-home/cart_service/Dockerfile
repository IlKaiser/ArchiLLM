FROM openjdk:17-jdk-alpine
VOLUME /tmp
COPY target/cart_service.jar cart_service.jar
ENTRYPOINT ["java","-jar","/cart_service.jar"]