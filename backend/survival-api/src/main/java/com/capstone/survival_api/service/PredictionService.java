package com.capstone.survival_api.service;

import com.capstone.survival_api.domain.entity.Block;
import com.capstone.survival_api.domain.entity.Prediction;
import com.capstone.survival_api.domain.entity.ShapFeature;
import com.capstone.survival_api.domain.entity.SurvivalCurvePoint;
import com.capstone.survival_api.domain.repository.BlockRepository;
import com.capstone.survival_api.domain.repository.PredictionRepository;
import com.capstone.survival_api.domain.repository.ShapFeatureRepository;
import com.capstone.survival_api.domain.repository.SurvivalCurveRepository;
import com.capstone.survival_api.dto.response.PredictionResponse;
import com.capstone.survival_api.dto.response.ShapResponse;
import com.capstone.survival_api.dto.response.SurvivalCurveResponse;
import com.capstone.survival_api.exception.AppException;
import com.capstone.survival_api.exception.ErrorCode;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class PredictionService {

    private final BlockRepository blockRepository;
    private final PredictionRepository predictionRepository;
    private final SurvivalCurveRepository survivalCurveRepository;
    private final ShapFeatureRepository shapFeatureRepository;

    public PredictionResponse getPrediction(Long blockId) {
        Block block = blockRepository.findById(blockId)
                .orElseThrow(() -> new AppException(ErrorCode.BLOCK_NOT_FOUND));

        Prediction prediction = predictionRepository
                .findTopByBlockIdOrderByPredictedAtDesc(blockId)
                .orElseThrow(() -> new AppException(ErrorCode.PREDICTION_NOT_FOUND));

        return PredictionResponse.of(block, prediction);
    }

    public SurvivalCurveResponse getSurvivalCurve(Long blockId) {
        if (!blockRepository.existsById(blockId)) {
            throw new AppException(ErrorCode.BLOCK_NOT_FOUND);
        }

        List<SurvivalCurvePoint> points = survivalCurveRepository.findByBlockIdOrderByMonthAsc(blockId);
        if (points.isEmpty()) {
            throw new AppException(ErrorCode.PREDICTION_NOT_FOUND);
        }

        List<SurvivalCurveResponse.CurvePoint> curve = points.stream()
                .map(SurvivalCurveResponse.CurvePoint::from)
                .toList();

        return SurvivalCurveResponse.builder()
                .blockId(blockId)
                .curve(curve)
                .build();
    }

    public ShapResponse getShap(Long blockId) {
        if (!blockRepository.existsById(blockId)) {
            throw new AppException(ErrorCode.BLOCK_NOT_FOUND);
        }

        List<ShapFeature> features = shapFeatureRepository.findByBlockIdOrderByRankAsc(blockId);
        if (features.isEmpty()) {
            throw new AppException(ErrorCode.PREDICTION_NOT_FOUND);
        }

        List<ShapResponse.Feature> featureDtos = features.stream()
                .map(ShapResponse.Feature::from)
                .toList();

        return ShapResponse.builder()
                .blockId(blockId)
                .features(featureDtos)
                .build();
    }
}
