package com.capstone.survival_api.domain.entity;

import jakarta.persistence.*;
import lombok.*;
import org.hibernate.annotations.CreationTimestamp;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(name = "predictions")
@Getter
@NoArgsConstructor(access = AccessLevel.PROTECTED)
@Builder
@AllArgsConstructor
public class Prediction {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "block_id", nullable = false)
    private Block block;

    @Column(precision = 4, scale = 2)
    private BigDecimal csiScore;

    @Column(length = 20)
    private String riskGrade;

    @Column(precision = 5, scale = 2)
    private BigDecimal closureRate;

    @Column(precision = 5, scale = 2)
    private BigDecimal openRate;

    @Column(name = "survival_6m", precision = 5, scale = 2)
    private BigDecimal survival6m;

    private Integer riskScore;

    @CreationTimestamp
    @Column(nullable = false, updatable = false)
    private LocalDateTime predictedAt;
}
