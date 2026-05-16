package com.capstone.survival_api.controller;

import com.capstone.survival_api.dto.response.PredictionResponse;
import com.capstone.survival_api.dto.response.ShapResponse;
import com.capstone.survival_api.dto.response.SurvivalCurveResponse;
import com.capstone.survival_api.service.PredictionService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@Tag(name = "Prediction", description = "블록별 폐업률·생존 확률·SHAP 기여도 조회")
@RestController
@RequestMapping("/api/v1/blocks/{blockId}")
@RequiredArgsConstructor
public class PredictionController {

    private final PredictionService predictionService;

    @Operation(summary = "예측 결과 조회", description = "블록의 폐업률, 개업률, 위험도 등급, 6개월 생존 확률 등 예측 수치를 반환합니다.")
    @GetMapping("/prediction")
    public ResponseEntity<PredictionResponse> getPrediction(
            @Parameter(description = "블록 ID") @PathVariable Long blockId
    ) {
        return ResponseEntity.ok(predictionService.getPrediction(blockId));
    }

    @Operation(summary = "생존 확률 곡선 조회", description = "0~12개월 구간별 생존 확률 데이터를 반환합니다. (꺾은선 그래프용)")
    @GetMapping("/survival-curve")
    public ResponseEntity<SurvivalCurveResponse> getSurvivalCurve(
            @Parameter(description = "블록 ID") @PathVariable Long blockId
    ) {
        return ResponseEntity.ok(predictionService.getSurvivalCurve(blockId));
    }

    @Operation(summary = "SHAP 피처 기여도 조회", description = "예측에 영향을 준 피처 Top5와 SHAP 값을 반환합니다. (막대 차트용)")
    @GetMapping("/shap")
    public ResponseEntity<ShapResponse> getShap(
            @Parameter(description = "블록 ID") @PathVariable Long blockId
    ) {
        return ResponseEntity.ok(predictionService.getShap(blockId));
    }
}
