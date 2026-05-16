package com.capstone.survival_api.domain.repository;

import com.capstone.survival_api.domain.entity.Store;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

import java.util.List;

public interface StoreRepository extends JpaRepository<Store, Long> {

    @Query(value = """
            SELECT TO_CHAR(s.open_date, 'YYYY-MM') AS month,
                   COUNT(*) AS competitor_count
            FROM stores s
            WHERE s.block_id = :blockId
              AND s.open_date >= CURRENT_DATE - MAKE_INTERVAL(months => :months)
            GROUP BY TO_CHAR(s.open_date, 'YYYY-MM')
            ORDER BY month
            """, nativeQuery = true)
    List<Object[]> findMonthlyCompetitors(@Param("blockId") Long blockId, @Param("months") int months);
}
