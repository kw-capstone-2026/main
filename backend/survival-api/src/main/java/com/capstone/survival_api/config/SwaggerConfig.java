package com.capstone.survival_api.config;

import io.swagger.v3.oas.annotations.OpenAPIDefinition;
import io.swagger.v3.oas.annotations.enums.SecuritySchemeType;
import io.swagger.v3.oas.annotations.info.Info;
import io.swagger.v3.oas.annotations.security.SecurityScheme;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.context.annotation.Configuration;

@Configuration
@OpenAPIDefinition(
        info = @Info(
                title = "CSI Platform API",
                description = "서울 상권 생존 예측 플랫폼 REST API",
                version = "v1"
        ),
        tags = {
                @Tag(name = "Auth",       description = "회원가입 / 로그인 / 로그아웃"),
                @Tag(name = "Blocks",     description = "메인 지도 히트맵용 블록 목록 및 상세 조회"),
                @Tag(name = "Prediction", description = "블록별 폐업률·생존 확률·SHAP 기여도 조회"),
                @Tag(name = "Industry",   description = "블록 내 업종 비율·생존 기간·월별 경쟁 점포 추이 조회")
        }
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
