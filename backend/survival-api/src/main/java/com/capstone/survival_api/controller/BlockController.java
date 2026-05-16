package com.capstone.survival_api.controller;

import com.capstone.survival_api.dto.response.BlockDetailResponse;
import com.capstone.survival_api.dto.response.BlockListResponse;
import com.capstone.survival_api.service.BlockService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;

@Tag(name = "Blocks", description = "메인 지도 히트맵용 블록 목록 및 상세 조회")
@RestController
@RequestMapping("/api/v1/blocks")
@RequiredArgsConstructor
public class BlockController {

    private final BlockService blockService;

    @Operation(summary = "전체 블록 목록 조회", description = "지도 화면의 남서/북동 경계 좌표로 블록을 필터링합니다. CSI 범위·지역 필터 선택 가능.")
    @GetMapping
    public ResponseEntity<BlockListResponse> getBlocks(
            @Parameter(description = "남서쪽 위도") @RequestParam BigDecimal swLat,
            @Parameter(description = "남서쪽 경도") @RequestParam BigDecimal swLng,
            @Parameter(description = "북동쪽 위도") @RequestParam BigDecimal neLat,
            @Parameter(description = "북동쪽 경도") @RequestParam BigDecimal neLng,
            @Parameter(description = "지역 필터 (예: 마포구)") @RequestParam(required = false) String region,
            @Parameter(description = "CSI 최솟값 필터") @RequestParam(required = false) BigDecimal csiMin,
            @Parameter(description = "CSI 최댓값 필터") @RequestParam(required = false) BigDecimal csiMax
    ) {
        return ResponseEntity.ok(blockService.getBlocks(swLat, swLng, neLat, neLng, region, csiMin, csiMax));
    }

    @Operation(summary = "블록 상세 조회", description = "사이드 패널에 표시할 선택 블록의 상세 정보를 반환합니다.")
    @GetMapping("/{blockId}")
    public ResponseEntity<BlockDetailResponse> getBlockDetail(
            @Parameter(description = "블록 ID") @PathVariable Long blockId
    ) {
        return ResponseEntity.ok(blockService.getBlockDetail(blockId));
    }
}
