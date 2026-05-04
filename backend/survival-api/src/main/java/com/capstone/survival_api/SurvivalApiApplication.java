package com.capstone.survival_api;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration;
import org.springframework.boot.autoconfigure.jdbc.DataSourceTransactionManagerAutoConfiguration;
import org.springframework.boot.autoconfigure.orm.jpa.HibernateJpaAutoConfiguration;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.client.RestTemplate;

@SpringBootApplication(exclude = {
    DataSourceAutoConfiguration.class, 
    DataSourceTransactionManagerAutoConfiguration.class, 
    HibernateJpaAutoConfiguration.class
})
@RestController
@RequestMapping("/api")
public class SurvivalApiApplication {

    public static void main(String[] args) {
        SpringApplication.run(SurvivalApiApplication.class, args);
    }

    // 1. 서버 연결 확인용 (브라우저에서 http://localhost:8080/api/health 접속)
    @GetMapping("/health")
    public String health() {
        return "{\"status\": \"UP\", \"message\": \"백엔드 서버가 살아있습니다!\"}";
    }

    // 2. 예측 요청 전달 (React -> Spring -> FastAPI)
    @PostMapping("/predict")
    public Object predict(@RequestBody Object requestData) {
        String fastApiUrl = "http://localhost:8000/predict";
        RestTemplate restTemplate = new RestTemplate();
        
        try {
            // FastAPI(ML서버)로 데이터를 전달하고 결과를 받아옴
            return restTemplate.postForObject(fastApiUrl, requestData, Object.class);
        } catch (Exception e) {
            return "{\"error\": \"ML 서버(FastAPI)가 꺼져있거나 연결할 수 없습니다.\"}";
        }
    }
}