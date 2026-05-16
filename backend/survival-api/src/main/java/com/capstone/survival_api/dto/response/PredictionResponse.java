package com.capstone.survival_api.dto.response;

import com.capstone.survival_api.domain.entity.Block;
import com.capstone.survival_api.domain.entity.Prediction;
import lombok.Builder;
import lombok.Getter;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Getter
@Builder
public class PredictionResponse {
    private Long blockId;
    private String blockName;
    private BigDecimal csiScore;
    private String riskGrade;
    private BigDecimal closureRate;
    private BigDecimal openRate;
    private Integer riskScore;
    private BigDecimal survival6m;
    private LocalDateTime predictedAt;

    public static PredictionResponse of(Block block, Prediction prediction) {
        return PredictionResponse.builder()
                .blockId(block.getId())
                .blockName(block.getName())
                .csiScore(prediction.getCsiScore())
                .riskGrade(prediction.getRiskGrade())
                .closureRate(prediction.getClosureRate())
                .openRate(prediction.getOpenRate())
                .riskScore(prediction.getRiskScore())
                .survival6m(prediction.getSurvival6m())
                .predictedAt(prediction.getPredictedAt())
                .build();
    }
}
