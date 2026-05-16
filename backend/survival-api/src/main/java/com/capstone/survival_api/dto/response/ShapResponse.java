package com.capstone.survival_api.dto.response;

import com.capstone.survival_api.domain.entity.ShapFeature;
import lombok.Builder;
import lombok.Getter;

import java.math.BigDecimal;
import java.util.List;

@Getter
@Builder
public class ShapResponse {
    private Long blockId;
    private List<Feature> features;

    @Getter
    @Builder
    public static class Feature {
        private Integer rank;
        private String name;
        private BigDecimal shapValue;
        private String label;

        public static Feature from(ShapFeature shap) {
            return Feature.builder()
                    .rank(shap.getRank())
                    .name(shap.getName())
                    .shapValue(shap.getShapValue())
                    .label(shap.getLabel())
                    .build();
        }
    }
}
