package com.capstone.survival_api.controller;

import com.capstone.survival_api.dto.response.IndustryStatsResponse;
import com.capstone.survival_api.dto.response.IndustrySurvivalResponse;
import com.capstone.survival_api.dto.response.MonthlyCompetitorResponse;
import com.capstone.survival_api.service.IndustryService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/blocks/{blockId}")
@RequiredArgsConstructor
public class IndustryController {

    private final IndustryService industryService;

    @GetMapping("/industry-stats")
    public ResponseEntity<IndustryStatsResponse> getIndustryStats(@PathVariable Long blockId) {
        return ResponseEntity.ok(industryService.getIndustryStats(blockId));
    }

    @GetMapping("/industry-survival")
    public ResponseEntity<IndustrySurvivalResponse> getIndustrySurvival(@PathVariable Long blockId) {
        return ResponseEntity.ok(industryService.getIndustrySurvival(blockId));
    }

    @GetMapping("/monthly-competitors")
    public ResponseEntity<MonthlyCompetitorResponse> getMonthlyCompetitors(
            @PathVariable Long blockId,
            @RequestParam(defaultValue = "12") int months
    ) {
        return ResponseEntity.ok(industryService.getMonthlyCompetitors(blockId, months));
    }
}
