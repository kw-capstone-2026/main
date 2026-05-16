# Stage 1 — Gradle로 JAR 빌드
FROM gradle:8-jdk22-alpine AS build
WORKDIR /app
COPY . .
RUN gradle bootJar --no-daemon -x test

# Stage 2 — 빌드된 JAR만 실행
FROM eclipse-temurin:22-jre-alpine
WORKDIR /app
COPY --from=build /app/build/libs/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
