<?php
declare(strict_types=1);
require dirname(__DIR__) . '/src/session.php';

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    exit('Method Not Allowed');
}

$token = $_POST['csrf_token'] ?? null;

if (
    !is_string($token)
    || !isset($_SESSION['csrf_token'])
    || !hash_equals($_SESSION['csrf_token'], $token)
) {
    http_response_code(403);
    exit('Invalid CSRF token');
}

logoutUser();
header('Location: /lab7/public/login.php');
exit;