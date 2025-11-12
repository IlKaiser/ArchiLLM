FROM openjdk:17-jdk-alpine
VOLUME /tmp
COPY target/product_catalog_service.jar product_catalog_service.jar
ENTRYPOINT ["java","-jar","/product_catalog_service.jar"]