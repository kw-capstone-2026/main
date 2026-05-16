package com.capstone.survival_api.domain.repository;

import com.capstone.survival_api.domain.entity.SurvivalCurvePoint;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface SurvivalCurveRepository extends JpaRepository<SurvivalCurvePoint, Long> {
    List<SurvivalCurvePoint> findByBlockIdOrderByMonthAsc(Long blockId);
}
