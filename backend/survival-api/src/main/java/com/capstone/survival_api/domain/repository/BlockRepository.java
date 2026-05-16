package com.capstone.survival_api.domain.repository;

import com.capstone.survival_api.domain.entity.Block;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.math.BigDecimal;
import java.util.List;

public interface BlockRepository extends JpaRepository<Block, Long> {

    @Query("""
            SELECT b FROM Block b
            WHERE b.lat BETWEEN :swLat AND :neLat
              AND b.lng BETWEEN :swLng AND :neLng
              AND (:region IS NULL OR b.region = :region)
              AND (:csiMin IS NULL OR b.csiScore >= :csiMin)
              AND (:csiMax IS NULL OR b.csiScore <= :csiMax)
            """)
    List<Block> findByBoundingBox(
            @Param("swLat") BigDecimal swLat,
            @Param("swLng") BigDecimal swLng,
            @Param("neLat") BigDecimal neLat,
            @Param("neLng") BigDecimal neLng,
            @Param("region") String region,
            @Param("csiMin") BigDecimal csiMin,
            @Param("csiMax") BigDecimal csiMax
    );
}
