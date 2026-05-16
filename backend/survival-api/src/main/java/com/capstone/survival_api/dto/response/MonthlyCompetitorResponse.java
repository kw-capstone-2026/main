package com.capstone.survival_api.dto.response;

import lombok.Builder;
import lombok.Getter;

import java.util.List;

@Getter
@Builder
public class MonthlyCompetitorResponse {
    private Long blockId;
    private int months;
    private List<TrendItem> trend;

    @Getter
    @Builder
    public static class TrendItem {
        private String month;
        private Long competitorCount;
    }
}
