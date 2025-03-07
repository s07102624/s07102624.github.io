<?php
header('Content-Type: application/json');

$ip = $_SERVER['REMOTE_ADDR'];
$dbFile = 'visitor_logs.db';

try {
    $db = new SQLite3($dbFile);
    
    // 테이블 생성
    $db->exec('CREATE TABLE IF NOT EXISTS visitor_logs (
        ip_address TEXT PRIMARY KEY,
        last_visit TIMESTAMP
    )');
    
    // IP 체크
    $stmt = $db->prepare('SELECT last_visit FROM visitor_logs WHERE ip_address = :ip');
    $stmt->bindValue(':ip', $ip, SQLITE3_TEXT);
    $result = $stmt->execute();
    $row = $result->fetchArray();
    
    $currentTime = time();
    $hasVisited = false;
    
    if ($row) {
        $lastVisit = strtotime($row['last_visit']);
        if (($currentTime - $lastVisit) < 86400) { // 24시간
            $hasVisited = true;
        } else {
            $stmt = $db->prepare('UPDATE visitor_logs SET last_visit = datetime("now") WHERE ip_address = :ip');
            $stmt->bindValue(':ip', $ip, SQLITE3_TEXT);
            $stmt->execute();
        }
    } else {
        $stmt = $db->prepare('INSERT INTO visitor_logs (ip_address, last_visit) VALUES (:ip, datetime("now"))');
        $stmt->bindValue(':ip', $ip, SQLITE3_TEXT);
        $stmt->execute();
    }
    
    echo json_encode(['hasVisited' => $hasVisited]);
    
} catch (Exception $e) {
    echo json_encode(['error' => $e->getMessage()]);
} finally {
    if ($db) {
        $db->close();
    }
}
?>
