package com.capstone.survival_api.domain.repository;

import com.capstone.survival_api.domain.entity.IndustryStat;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface IndustryStatRepository extends JpaRepository<IndustryStat, Long> {
    List<IndustryStat> findByBlockIdOrderByStoreCountDesc(Long blockId);
}
