package com.capstone.survival_api.dto.response;

import com.capstone.survival_api.domain.entity.Block;
import com.capstone.survival_api.domain.entity.Prediction;
import lombok.Builder;
import lombok.Getter;

import java.math.BigDecimal;

@Getter
@Builder
public class BlockDetailResponse {
    private Long id;
    private String basId;
    private String name;
    private String region;
    private BigDecimal csiScore;
    private String riskGrade;
    private String mainIndustry;
    private BigDecimal lat;
    private BigDecimal lng;
    private BigDecimal area;
    private String admDrCd;
    private String admDrNm;

    public static BlockDetailResponse of(Block block, Prediction prediction) {
        return BlockDetailResponse.builder()
                .id(block.getId())
                .basId(block.getBasId())
                .name(block.getName())
                .region(block.getRegion())
                .csiScore(block.getCsiScore())
                .riskGrade(prediction != null ? prediction.getRiskGrade() : null)
                .mainIndustry(block.getMainIndustry())
                .lat(block.getLat())
                .lng(block.getLng())
                .area(block.getArea())
                .admDrCd(block.getAdmDrCd())
                .admDrNm(block.getAdmDrNm())
                .build();
    }
}
