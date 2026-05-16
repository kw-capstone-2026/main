package com.capstone.survival_api.domain.repository;

import com.capstone.survival_api.domain.entity.Prediction;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface PredictionRepository extends JpaRepository<Prediction, Long> {
    Optional<Prediction> findTopByBlockIdOrderByPredictedAtDesc(Long blockId);
}
