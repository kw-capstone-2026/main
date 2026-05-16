package com.capstone.survival_api.dto.response;

import com.capstone.survival_api.domain.entity.Block;
import com.capstone.survival_api.domain.entity.Prediction;
import lombok.Builder;
import lombok.Getter;

import java.math.BigDecimal;

@Getter
@Builder
public class BlockSummaryDto {
    private Long id;
    private String basId;
    private String name;
    private String region;
    private BigDecimal csiScore;
    private String riskGrade;
    private BigDecimal lat;
    private BigDecimal lng;

    public static BlockSummaryDto of(Block block, Prediction prediction) {
        return BlockSummaryDto.builder()
                .id(block.getId())
                .basId(block.getBasId())
                .name(block.getName())
                .region(block.getRegion())
                .csiScore(block.getCsiScore())
                .riskGrade(prediction != null ? prediction.getRiskGrade() : null)
                .lat(block.getLat())
                .lng(block.getLng())
                .build();
    }
}
