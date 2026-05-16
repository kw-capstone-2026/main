package com.capstone.survival_api.domain.entity;

import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDate;

@Entity
@Table(name = "industry_stats")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Builder
@AllArgsConstructor
public class IndustryStat {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "block_id", nullable = false)
    private Block block;

    @Column(nullable = false, length = 100)
    private String industryName;

    private Integer storeCount;

    private Integer avgSurvivalDays;

    @Column(precision = 5, scale = 2)
    private BigDecimal ratio;

    @Column(nullable = false)
    private LocalDate recordedAt;
}
