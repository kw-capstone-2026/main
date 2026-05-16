package com.capstone.survival_api.controller;

import com.capstone.survival_api.dto.response.IndustryStatsResponse;
import com.capstone.survival_api.dto.response.IndustrySurvivalResponse;
import com.capstone.survival_api.dto.response.MonthlyCompetitorResponse;
import com.capstone.survival_api.service.IndustryService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@Tag(name = "Industry", description = "블록 내 업종 비율·생존 기간·월별 경쟁 점포 추이 조회")
@RestController
@RequestMapping("/api/v1/blocks/{blockId}")
@RequiredArgsConstructor
public class IndustryController {

    private final IndustryService industryService;

    @Operation(summary = "업종 비율 조회", description = "블록 내 업종별 점포 수와 비율을 반환합니다. (도넛 차트용)")
    @GetMapping("/industry-stats")
    public ResponseEntity<IndustryStatsResponse> getIndustryStats(
            @Parameter(description = "블록 ID") @PathVariable Long blockId
    ) {
        return ResponseEntity.ok(industryService.getIndustryStats(blockId));
    }

    @Operation(summary = "업종별 평균 생존 기간 조회", description = "블록 내 업종별 평균 생존 기간(일/개월)을 반환합니다. (막대 그래프용)")
    @GetMapping("/industry-survival")
    public ResponseEntity<IndustrySurvivalResponse> getIndustrySurvival(
            @Parameter(description = "블록 ID") @PathVariable Long blockId
    ) {
        return ResponseEntity.ok(industryService.getIndustrySurvival(blockId));
    }

    @Operation(summary = "월별 경쟁 점포 수 추이 조회", description = "최근 N개월간 개업 점포 수를 월별로 집계합니다. (선 그래프용)")
    @GetMapping("/monthly-competitors")
    public ResponseEntity<MonthlyCompetitorResponse> getMonthlyCompetitors(
            @Parameter(description = "블록 ID") @PathVariable Long blockId,
            @Parameter(description = "조회 개월 수 (기본 12, 최대 60)") @RequestParam(defaultValue = "12") int months
    ) {
        return ResponseEntity.ok(industryService.getMonthlyCompetitors(blockId, months));
    }
}
