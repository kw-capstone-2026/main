package com.capstone.survival_api.domain.entity;

import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;

@Entity
@Table(name = "blocks")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Builder
@AllArgsConstructor
public class Block {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, unique = true, length = 20)
    private String basId;

    @Column(length = 100)
    private String name;

    @Column(length = 100)
    private String region;

    @Column(length = 50)
    private String mainIndustry;

    @Column(precision = 4, scale = 2)
    private BigDecimal csiScore;

    @Column(precision = 10, scale = 7)
    private BigDecimal lat;

    @Column(precision = 10, scale = 7)
    private BigDecimal lng;

    @Column(precision = 12, scale = 2)
    private BigDecimal area;

    @Column(length = 20)
    private String admDrCd;

    @Column(length = 100)
    private String admDrNm;
}
