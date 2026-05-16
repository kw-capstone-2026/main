package com.capstone.survival_api.dto.response;

import lombok.Builder;
import lombok.Getter;

import java.util.List;

@Getter
@Builder
public class BlockListResponse {
    private int total;
    private List<BlockSummaryDto> blocks;
}
