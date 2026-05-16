package com.capstone.survival_api.service;

import com.capstone.survival_api.domain.entity.IndustryStat;
import com.capstone.survival_api.domain.repository.BlockRepository;
import com.capstone.survival_api.domain.repository.IndustryStatRepository;
import com.capstone.survival_api.domain.repository.StoreRepository;
import com.capstone.survival_api.dto.response.IndustryStatsResponse;
import com.capstone.survival_api.dto.response.IndustrySurvivalResponse;
import com.capstone.survival_api.dto.response.MonthlyCompetitorResponse;
import com.capstone.survival_api.exception.AppException;
import com.capstone.survival_api.exception.ErrorCode;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class IndustryService {

    private final BlockRepository blockRepository;
    private final IndustryStatRepository industryStatRepository;
    private final StoreRepository storeRepository;

    public IndustryStatsResponse getIndustryStats(Long blockId) {
        if (!blockRepository.existsById(blockId)) {
            throw new AppException(ErrorCode.BLOCK_NOT_FOUND);
        }

        List<IndustryStat> stats = industryStatRepository.findByBlockIdOrderByStoreCountDesc(blockId);
        if (stats.isEmpty()) {
            throw new AppException(ErrorCode.INDUSTRY_STATS_NOT_FOUND);
        }

        return IndustryStatsResponse.builder()
                .blockId(blockId)
                .recordedAt(stats.get(0).getRecordedAt())
                .industries(stats.stream().map(IndustryStatsResponse.IndustryItem::from).toList())
                .build();
    }

    public IndustrySurvivalResponse getIndustrySurvival(Long blockId) {
        if (!blockRepository.existsById(blockId)) {
            throw new AppException(ErrorCode.BLOCK_NOT_FOUND);
        }

        List<IndustryStat> stats = industryStatRepository.findByBlockIdOrderByStoreCountDesc(blockId);
        if (stats.isEmpty()) {
            throw new AppException(ErrorCode.INDUSTRY_STATS_NOT_FOUND);
        }

        return IndustrySurvivalResponse.builder()
                .blockId(blockId)
                .survival(stats.stream().map(IndustrySurvivalResponse.SurvivalItem::from).toList())
                .build();
    }

    public MonthlyCompetitorResponse getMonthlyCompetitors(Long blockId, int months) {
        if (months < 1 || months > 60) {
            throw new AppException(ErrorCode.INVALID_MONTHS);
        }
        if (!blockRepository.existsById(blockId)) {
            throw new AppException(ErrorCode.BLOCK_NOT_FOUND);
        }

        List<Object[]> rows = storeRepository.findMonthlyCompetitors(blockId, months);

        List<MonthlyCompetitorResponse.TrendItem> trend = rows.stream()
                .map(row -> MonthlyCompetitorResponse.TrendItem.builder()
                        .month((String) row[0])
                        .competitorCount(((Number) row[1]).longValue())
                        .build())
                .toList();

        return MonthlyCompetitorResponse.builder()
                .blockId(blockId)
                .months(months)
                .trend(trend)
                .build();
    }
}
