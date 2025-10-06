-- ===================================================================================
-- API 로그 분석 및 보안 위협 탐지를 위한 SQL 쿼리 모음 (MariaDB 구버전 호환)
-- ===================================================================================

-- 쿼리 1.1: 시간대별 평균 API 요청 수
SELECT
    HOUR(timestamp) AS hour_of_day,
    COUNT(*) AS total_requests,
    CASE 
        WHEN COUNT(DISTINCT DATE(timestamp)) = 0 THEN 0
        ELSE COUNT(*) / COUNT(DISTINCT DATE(timestamp))
    END AS avg_requests_per_day
FROM
    access_logs
GROUP BY
    hour_of_day
ORDER BY
    hour_of_day;

-- 쿼리 1.2: 가장 많이 요청된 API 엔드포인트 TOP 10
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

-- 쿼리 1.3: 엔드포인트별 평균 및 최대 응답 시간
SELECT
    path,
    AVG(response_time_ms) AS avg_response_time_ms,
    MAX(response_time_ms) AS max_response_time_ms
FROM
    access_logs
GROUP BY
    path
ORDER BY
    avg_response_time_ms DESC;

-- 쿼리 2.1: Brute-force 공격 의심 IP 탐지
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
    AND timestamp > UTC_TIMESTAMP() - INTERVAL 24 HOUR
GROUP BY
    ip_address, username
HAVING
    COUNT(*) >= 5
ORDER BY
    failed_attempts DESC;

-- 쿼리 2.2: 웹 스캐너(Web Scanner) 의심 IP 탐지
SELECT
    ip_address,
    COUNT(*) AS not_found_count,
    GROUP_CONCAT(DISTINCT path SEPARATOR ', ') AS scanned_paths
FROM
    access_logs
WHERE
    status_code = 404
GROUP BY
    ip_address
HAVING
    COUNT(*) >= 10
ORDER BY
    not_found_count DESC;

-- 쿼리 2.3: 특정 보안 이벤트(SQL Injection 등) 로그 상세 조회
SELECT
    id,
    timestamp,
    ip_address,
    path,
    details
FROM
    access_logs
WHERE
    event_type = 'SQL_INJECTION_ATTEMPT'
ORDER BY
    timestamp DESC;

-- 쿼리 2.4: [고급] 전일 대비 요청 수가 급증한 IP 탐지 (Self-Join 호환 버전)
-- 설명: Window Function을 지원하지 않는 구버전 MariaDB/MySQL을 위해 Self-Join 방식으로 재작성했습니다.
WITH daily_requests_per_ip AS (
    SELECT
        DATE(timestamp) AS request_date,
        ip_address,
        COUNT(*) AS total_requests
    FROM
        access_logs
    GROUP BY
        request_date,
        ip_address
)
SELECT
    today.request_date,
    today.ip_address,
    today.total_requests,
    -- COALESCE 함수를 사용하여 어제 데이터가 없는 경우 0으로 표시
    COALESCE(yesterday.total_requests, 0) AS previous_day_requests
FROM
    daily_requests_per_ip AS today
LEFT JOIN
    -- 어제 날짜의 데이터를 찾기 위해 자기 자신과 조인
    daily_requests_per_ip AS yesterday ON today.ip_address = yesterday.ip_address
                                     AND today.request_date = DATE_ADD(yesterday.request_date, INTERVAL 1 DAY)
WHERE
    today.total_requests > (COALESCE(yesterday.total_requests, 0) * 5)
    AND today.total_requests > 100
ORDER BY
    today.request_date DESC,
    today.total_requests DESC;

