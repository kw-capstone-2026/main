package com.capstone.survival_api.dto.response;

import com.capstone.survival_api.domain.entity.SurvivalCurvePoint;
import lombok.Builder;
import lombok.Getter;

import java.math.BigDecimal;
import java.util.List;

@Getter
@Builder
public class SurvivalCurveResponse {
    private Long blockId;
    private List<CurvePoint> curve;

    @Getter
    @Builder
    public static class CurvePoint {
        private Integer month;
        private BigDecimal survivalRate;

        public static CurvePoint from(SurvivalCurvePoint point) {
            return CurvePoint.builder()
                    .month(point.getMonth())
                    .survivalRate(point.getSurvivalRate())
                    .build();
        }
    }
}
