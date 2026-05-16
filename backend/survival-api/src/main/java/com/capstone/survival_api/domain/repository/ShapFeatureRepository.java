package com.capstone.survival_api.domain.repository;

import com.capstone.survival_api.domain.entity.ShapFeature;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface ShapFeatureRepository extends JpaRepository<ShapFeature, Long> {
    List<ShapFeature> findByBlockIdOrderByRankAsc(Long blockId);
}
