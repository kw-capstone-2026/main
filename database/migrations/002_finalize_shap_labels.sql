-- SHAP 표시명(label) 확정본 반영
-- 기준: feature_labels_final.csv (32개 중 초안 대비 바뀐 9개만 UPDATE)
-- 키: shap_features.name (피처명은 변경 없음)
-- 2024년 4분기 데이터 기준 예상 변경 행 수: 합계 64,216행

BEGIN;

UPDATE public.shap_features SET label = '상권 개인 점포 비율'          WHERE name = '개인점포비율(%)';           -- 34행
UPDATE public.shap_features SET label = '상권 운영 점포 평균 영업기간' WHERE name = '운영_영업_개월_평균';        -- 9,438행
UPDATE public.shap_features SET label = '상권 폐업 점포 평균 영업기간' WHERE name = '폐업_영업_개월_평균';        -- 20행
UPDATE public.shap_features SET label = '점포당 평균 매출'             WHERE name = '점포당_평균_매출';           -- 19,541행
UPDATE public.shap_features SET label = '작년 같은 분기 대비 폐업 증감' WHERE name = '전년_동기_대비_폐업_증감률'; -- 21,664행
UPDATE public.shap_features SET label = '주변 주민 소득 구간'          WHERE name = '소득_구간_코드';             -- 64행
UPDATE public.shap_features SET label = '업종·상권 적합도'             WHERE name = '상권_업종_적합도';           -- 12,254행
UPDATE public.shap_features SET label = '상권 유사업종 점포 비율'      WHERE name = '유사업종_점포비율';          -- 0행 (4분기 Top5에 없음, 다른 분기 대비용)
UPDATE public.shap_features SET label = '평균 점포 수 대비 매출'       WHERE name = '점포당_매출_밀도';           -- 1,201행

COMMIT;

-- 확인용: 초안 표시명이 남아 있지 않으면 0이 나와야 합니다.
SELECT COUNT(*) AS draft_labels_left
FROM public.shap_features
WHERE label IN (
  '상권 개인 가게 비율', '상권 가게 평균 영업기간', '상권 폐업 가게 평균 영업기간',
  '가게당 평균 매출', '작년 같은 분기보다 폐업이 늘어난 정도', '주변 주민 소득 수준',
  '상권과 업종의 어울림 정도', '상권 유사업종 점포 비중', '가게당 매출 밀도'
);
