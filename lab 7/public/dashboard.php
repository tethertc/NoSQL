<?php
declare(strict_types=1);
require dirname(__DIR__) . '/src/session.php';
requireLogin();

$allowedRows = ['10', '20', '50'];
$rowsPerPage = $_COOKIE['rows_per_page'] ?? '10';

if (!is_string($rowsPerPage) || !in_array($rowsPerPage, $allowedRows, true)) {
    $rowsPerPage = '10';
}

if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['rows_per_page'])) {
    $rowsValue = $_POST['rows_per_page'] ?? null;
    $token = $_POST['csrf_token'] ?? null;

    if (
        is_string($rowsValue)
        && in_array($rowsValue, $allowedRows, true)
        && is_string($token)
        && hash_equals($_SESSION['csrf_token'], $token)
    ) {
        setcookie('rows_per_page', $rowsValue, [
            'expires' => time() + 2592000,
            'path' => '/',
            'secure' => $isHttps,
            'httponly' => true,
            'samesite' => 'Lax',
        ]);
        header('Location: /lab7/public/dashboard.php');
        exit;
    }
}

$role = $_SESSION['role'];
?>
<!doctype html>
<html lang="ru">
<head><meta charset="UTF-8"><title>Кабинет библиотеки</title></head>
<body>
<h1>Электронная библиотека</h1>
<p>Пользователь: <strong><?= h((string) $_SESSION['email']) ?></strong></p>
<p>Роль: <strong><?= h($role) ?></strong></p>
<p>Строк на странице (Cookie): <strong><?= h($rowsPerPage) ?></strong></p>

<form method="post" action="/lab7/public/dashboard.php">
    <input type="hidden" name="csrf_token" value="<?= h($_SESSION['csrf_token']) ?>">
    <label>Количество строк в таблице: 
        <select name="rows_per_page">
            <option value="10" <?= $rowsPerPage === '10' ? 'selected' : '' ?>>10</option>
            <option value="20" <?= $rowsPerPage === '20' ? 'selected' : '' ?>>20</option>
            <option value="50" <?= $rowsPerPage === '50' ? 'selected' : '' ?>>50</option>
        </select>
    </label>
    <button type="submit">Применить</button>
</form>

<hr>

<?php if ($role === 'reader'): ?>
    <h2>Мои выданные книги</h2>
    <table border="1" cellpadding="5">
        <tr><th>№</th><th>Название книги</th><th>Дата выдачи</th><th>Срок возврата</th></tr>
        <tr><td>1</td><td>Программирование на PHP 8.4</td><td>01.10.2026</td><td>01.11.2026</td></tr>
        <tr><td>2</td><td>Архитектура NoSQL баз данных</td><td>05.10.2026</td><td>05.11.2026</td></tr>
    </table>
    <p><em>Читатель видит список своих активных выдач. Отображается по <?= h($rowsPerPage) ?> записей.</em></p>
<?php elseif ($role === 'librarian'): ?>
    <h2>Панель библиотекаря</h2>
    <p style="color: blue; font-weight: bold;">Доступ разрешён: Управление библиотечным фондом.</p>
    <form method="post">
        <input type="hidden" name="csrf_token" value="<?= h($_SESSION['csrf_token']) ?>">
        <label>ID книги для возврата: <input type="text" name="book_id" required></label>
        <button type="submit" name="return_book">Отметить возврат книги</button>
    </form>
<?php endif; ?>

<hr>

<form method="post" action="/lab7/public/logout.php">
    <input type="hidden" name="csrf_token" value="<?= h($_SESSION['csrf_token']) ?>">
    <button type="submit">Выйти из системы</button>
</form>
</body>
</html>