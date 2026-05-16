package com.capstone.survival_api.domain.entity;

import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;

@Entity
@Table(name = "shap_features")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Builder
@AllArgsConstructor
public class ShapFeature {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "block_id", nullable = false)
    private Block block;

    @Column(nullable = false)
    private Integer rank;

    @Column(nullable = false, length = 100)
    private String name;

    @Column(nullable = false, precision = 8, scale = 4)
    private BigDecimal shapValue;

    @Column(length = 200)
    private String label;
}
