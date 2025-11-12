FROM openjdk:17-jdk-alpine
VOLUME /tmp
COPY target/user_profile_service.jar user_profile_service.jar
ENTRYPOINT ["java","-jar","/user_profile_service.jar"]