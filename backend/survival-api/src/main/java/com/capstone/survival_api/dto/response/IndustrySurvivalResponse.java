package com.capstone.survival_api.dto.response;

import com.capstone.survival_api.domain.entity.IndustryStat;
import lombok.Builder;
import lombok.Getter;

import java.util.List;

@Getter
@Builder
public class IndustrySurvivalResponse {
    private Long blockId;
    private List<SurvivalItem> survival;

    @Getter
    @Builder
    public static class SurvivalItem {
        private String industryName;
        private Integer avgSurvivalDays;
        private Integer avgSurvivalMonths;

        public static SurvivalItem from(IndustryStat stat) {
            int months = stat.getAvgSurvivalDays() != null ? stat.getAvgSurvivalDays() / 30 : 0;
            return SurvivalItem.builder()
                    .industryName(stat.getIndustryName())
                    .avgSurvivalDays(stat.getAvgSurvivalDays())
                    .avgSurvivalMonths(months)
                    .build();
        }
    }
}
