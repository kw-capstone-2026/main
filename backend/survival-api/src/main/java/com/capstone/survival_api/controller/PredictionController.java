package com.capstone.survival_api.controller;

import com.capstone.survival_api.dto.response.PredictionResponse;
import com.capstone.survival_api.dto.response.ShapResponse;
import com.capstone.survival_api.dto.response.SurvivalCurveResponse;
import com.capstone.survival_api.service.PredictionService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/blocks/{blockId}")
@RequiredArgsConstructor
public class PredictionController {

    private final PredictionService predictionService;

    @GetMapping("/prediction")
    public ResponseEntity<PredictionResponse> getPrediction(@PathVariable Long blockId) {
        return ResponseEntity.ok(predictionService.getPrediction(blockId));
    }

    @GetMapping("/survival-curve")
    public ResponseEntity<SurvivalCurveResponse> getSurvivalCurve(@PathVariable Long blockId) {
        return ResponseEntity.ok(predictionService.getSurvivalCurve(blockId));
    }

    @GetMapping("/shap")
    public ResponseEntity<ShapResponse> getShap(@PathVariable Long blockId) {
        return ResponseEntity.ok(predictionService.getShap(blockId));
    }
}
