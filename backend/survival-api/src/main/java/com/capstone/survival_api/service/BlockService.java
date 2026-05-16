package com.capstone.survival_api.service;

import com.capstone.survival_api.domain.entity.Block;
import com.capstone.survival_api.domain.entity.Prediction;
import com.capstone.survival_api.domain.repository.BlockRepository;
import com.capstone.survival_api.domain.repository.PredictionRepository;
import com.capstone.survival_api.dto.response.BlockDetailResponse;
import com.capstone.survival_api.dto.response.BlockListResponse;
import com.capstone.survival_api.dto.response.BlockSummaryDto;
import com.capstone.survival_api.exception.AppException;
import com.capstone.survival_api.exception.ErrorCode;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;
import java.util.List;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class BlockService {

    private final BlockRepository blockRepository;
    private final PredictionRepository predictionRepository;

    public BlockListResponse getBlocks(BigDecimal swLat, BigDecimal swLng,
                                       BigDecimal neLat, BigDecimal neLng,
                                       String region, BigDecimal csiMin, BigDecimal csiMax) {
        if (csiMin != null && csiMax != null && csiMin.compareTo(csiMax) > 0) {
            throw new AppException(ErrorCode.INVALID_CSI_RANGE);
        }

        List<Block> blocks = blockRepository.findByBoundingBox(swLat, swLng, neLat, neLng, region, csiMin, csiMax);

        List<BlockSummaryDto> dtos = blocks.stream()
                .map(block -> {
                    Prediction prediction = predictionRepository
                            .findTopByBlockIdOrderByPredictedAtDesc(block.getId())
                            .orElse(null);
                    return BlockSummaryDto.of(block, prediction);
                })
                .toList();

        return BlockListResponse.builder()
                .total(dtos.size())
                .blocks(dtos)
                .build();
    }

    public BlockDetailResponse getBlockDetail(Long blockId) {
        Block block = blockRepository.findById(blockId)
                .orElseThrow(() -> new AppException(ErrorCode.BLOCK_NOT_FOUND));

        Prediction prediction = predictionRepository
                .findTopByBlockIdOrderByPredictedAtDesc(blockId)
                .orElse(null);

        return BlockDetailResponse.of(block, prediction);
    }
}
