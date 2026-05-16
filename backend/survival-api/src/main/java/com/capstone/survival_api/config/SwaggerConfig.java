package com.capstone.survival_api.config;

import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.enums.SecuritySchemeType;
import io.swagger.v3.oas.annotations.info.Info;
import io.swagger.v3.oas.annotations.security.SecurityScheme;
import org.springframework.context.annotation.Configuration;

@Configuration
@OpenAPIDefinition(
        info = @Info(
                title = "CSI Platform API",
                description = "서울 상권 생존 예측 플랫폼 REST API",
                version = "v1"
        )
)
@SecurityScheme(
        name = "Bearer 인증",
        type = SecuritySchemeType.HTTP,
        scheme = "bearer",
        bearerFormat = "JWT",
        description = "로그인 후 발급받은 accessToken을 입력하세요."
)
public class SwaggerConfig {
}
