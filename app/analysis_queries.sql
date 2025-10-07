-- ===================================================================================
-- API 로그 데이터 분석 및 보안 위협 탐지를 위한 SQL 쿼리 모음
-- 데이터베이스 종류(PostgreSQL, MySQL 등)에 따라 일부 함수(날짜/시간)는 수정이 필요할 수 있습니다.
-- ===================================================================================


-- ===================================================================================
-- 분석 1: 서비스 운영을 위한 통계 데이터 추출 (General Statistics)
-- ===================================================================================

-- 쿼리 1.1: 시간대별 평균 API 요청 수 (서버 트래픽 패턴 분석)
-- 설명: 시간대별 트래픽 패턴을 파악하여 리소스 증설, 배치 작업, 서버 점검 등의 최적 시간을 계획하는 데 활용합니다.
SELECT
    -- EXTRACT는 표준 SQL 함수입니다. (MySQL에서는 HOUR() 함수 사용 가능)
    EXTRACT(HOUR FROM timestamp) AS hour_of_day,
    COUNT(*) AS total_requests,
    COUNT(*) / COUNT(DISTINCT CAST(timestamp AS DATE)) AS avg_requests_per_day
FROM
    access_logs
GROUP BY
    hour_of_day
ORDER BY
    hour_of_day;


-- 쿼리 1.2: 가장 많이 요청된 API 엔드포인트 TOP 10 (인기 기능 분석)
-- 설명: 어떤 기능(API)이 사용자들에게 가장 많이 사용되는지 파악하여 서비스 개선의 우선순위를 정하는 데 도움을 줍니다.
SELECT
    path,
    method,
    COUNT(*) AS request_count
FROM
    access_logs
GROUP BY
    path, method
ORDER BY
    request_count DESC
LIMIT 10;


-- 쿼리 1.3: 엔드포인트별 평균 및 최대 응답 시간 (성능 병목 분석)
-- 설명: API별 응답 속도를 분석하여 어떤 엔드포인트의 성능 개선이 시급한지 파악하고, SLO/SLA 지표로 활용할 수 있습니다.
SELECT
    path,
    AVG(response_time_ms) AS avg_response_time_ms,
    MAX(response_time_ms) AS max_response_time_ms,
    -- 95th Percentile: 대부분의 요청이 이 시간 안에 완료됨을 의미 (PostgreSQL)
    PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY response_time_ms) AS p95_response_time_ms
FROM
    access_logs
GROUP BY
    path
ORDER BY
    avg_response_time_ms DESC;


-- ===================================================================================
-- 분석 2: 보안 위협 및 비정상 접근 패턴 탐지 (Security & Anomaly Detection)
-- ===================================================================================

-- 쿼리 2.1: Brute-force 공격 의심 IP 탐지 (로그인 무차별 대입 공격)
-- 설명: 짧은 시간(예: 10분) 내에 기준치(예: 5회) 이상 로그인 실패가 발생한 IP를 탐지합니다.
--      security_events 테이블을 직접 조회하여 더 정확하고 빠르게 탐지합니다.
SELECT
    ip_address,
    username,
    COUNT(*) as failed_attempts,
    MIN(timestamp) as first_attempt,
    MAX(timestamp) as last_attempt
FROM
    security_events
WHERE
    event_type = 'LOGIN_FAIL'
    -- PostgreSQL: NOW() - INTERVAL '10 MINUTE'
    -- MySQL: NOW() - INTERVAL 10 MINUTE
    AND timestamp > NOW() - INTERVAL '10 MINUTE' 
GROUP BY
    ip_address, username
HAVING
    COUNT(*) >= 5
ORDER BY
    failed_attempts DESC;


-- 쿼리 2.2: 웹 스캐너(Web Scanner) 의심 IP 탐지
-- 설명: 존재하지 않는 경로(404 Not Found)에 비정상적으로 많이 접근하는 IP를 탐지하여 웹 취약점 스캐닝 행위를 식별합니다.
SELECT
    ip_address,
    COUNT(*) AS not_found_count,
    -- 어떤 경로들을 스캔했는지 확인
    STRING_AGG(DISTINCT path, ', ') AS scanned_paths
FROM
    access_logs
WHERE
    status_code = 404
GROUP BY
    ip_address
HAVING
    COUNT(*) >= 10 -- 기준치는 서비스 특성에 따라 조절
ORDER BY
    not_found_count DESC;


-- 쿼리 2.3: 특정 보안 이벤트(SQL Injection 등) 로그 상세 조회
-- 설명: 기록된 특정 유형의 보안 이벤트를 모두 조회하여 공격 패턴과 출처, 영향을 파악합니다.
SELECT 
    id,
    timestamp,
    ip_address,
    path,
    details
FROM 
    access_logs
WHERE 
    event_type = 'SQL_INJECTION_ATTEMPT' -- 'PERMISSION_DENIED' 등 다른 이벤트 유형으로 변경하여 조회 가능
ORDER BY
    timestamp DESC;


-- 쿼리 2.4: [고급] 전일 대비 요청 수가 급증한 IP 탐지 (DDoS 등 이상 징후)
-- 설명: CTE(Common Table Expression)와 Window Function(LAG)을 사용하여, 특정 IP의 요청량이 전날에 비해 비정상적으로 급증했는지 탐지합니다.
WITH daily_requests_per_ip AS (
    -- 1. IP별, 날짜별 요청 수를 계산
    SELECT
        CAST(timestamp AS DATE) AS request_date,
        ip_address,
        COUNT(*) AS total_requests
    FROM
        access_logs
    GROUP BY
        request_date,
        ip_address
),
requests_with_previous_day AS (
    -- 2. LAG 함수로 바로 이전 날짜의 요청 수를 'previous_day_requests' 컬럼으로 가져옴
    SELECT
        request_date,
        ip_address,
        total_requests,
        LAG(total_requests, 1, 0) OVER (PARTITION BY ip_address ORDER BY request_date) AS previous_day_requests
    FROM
        daily_requests_per_ip
)
-- 3. 이전 날짜보다 요청이 5배 이상 급증하고, 총 요청이 100건 이상인 경우를 탐지
SELECT
    request_date,
    ip_address,
    total_requests,
    previous_day_requests
FROM
    requests_with_previous_day
WHERE
    total_requests > (previous_day_requests * 5) AND total_requests > 100
ORDER BY
    request_date DESC,
    total_requests DESC;
