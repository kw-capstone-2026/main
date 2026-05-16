package com.capstone.survival_api.dto.response;

import com.capstone.survival_api.domain.entity.IndustryStat;
import lombok.Builder;
import lombok.Getter;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

@Getter
@Builder
public class IndustryStatsResponse {
    private Long blockId;
    private LocalDate recordedAt;
    private List<IndustryItem> industries;

    @Getter
    @Builder
    public static class IndustryItem {
        private String industryName;
        private Integer storeCount;
        private BigDecimal ratio;

        public static IndustryItem from(IndustryStat stat) {
            return IndustryItem.builder()
                    .industryName(stat.getIndustryName())
                    .storeCount(stat.getStoreCount())
                    .ratio(stat.getRatio())
                    .build();
        }
    }
}
