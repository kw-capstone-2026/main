package com.capstone.survival_api.controller;

import com.capstone.survival_api.dto.response.BlockDetailResponse;
import com.capstone.survival_api.dto.response.BlockListResponse;
import com.capstone.survival_api.service.BlockService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.math.BigDecimal;

@RestController
@RequestMapping("/api/v1/blocks")
@RequiredArgsConstructor
public class BlockController {

    private final BlockService blockService;

    @GetMapping
    public ResponseEntity<BlockListResponse> getBlocks(
            @RequestParam BigDecimal swLat,
            @RequestParam BigDecimal swLng,
            @RequestParam BigDecimal neLat,
            @RequestParam BigDecimal neLng,
            @RequestParam(required = false) String region,
            @RequestParam(required = false) BigDecimal csiMin,
            @RequestParam(required = false) BigDecimal csiMax
    ) {
        return ResponseEntity.ok(blockService.getBlocks(swLat, swLng, neLat, neLng, region, csiMin, csiMax));
    }

    @GetMapping("/{blockId}")
    public ResponseEntity<BlockDetailResponse> getBlockDetail(@PathVariable Long blockId) {
        return ResponseEntity.ok(blockService.getBlockDetail(blockId));
    }
}
