<?php
declare(strict_types=1);
require dirname(__DIR__) . '/src/session.php';

if (isset($_SESSION['user_id'])) {
    header('Location: /lab7/public/dashboard.php');
    exit;
}

$error = '';
$email = '';
$_SESSION['login_csrf'] ??= bin2hex(random_bytes(32));

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $emailValue = $_POST['email'] ?? null;
    $passwordValue = $_POST['password'] ?? null;
    $tokenValue = $_POST['csrf_token'] ?? null;

    if (
        is_string($emailValue)
        && is_string($passwordValue)
        && is_string($tokenValue)
        && hash_equals($_SESSION['login_csrf'], $tokenValue)
    ) {
        $email = strtolower(trim($emailValue));

        $readerHash = password_hash('Reader123!', PASSWORD_DEFAULT);
        $librarianHash = password_hash('Librarian123!', PASSWORD_DEFAULT);

        if (hash_equals('reader@atu.edu.kz', $email) && password_verify($passwordValue, $readerHash)) {
            loginUser(301, $email, 'reader');
            header('Location: /lab7/public/dashboard.php');
            exit;
        } elseif (hash_equals('librarian@atu.edu.kz', $email) && password_verify($passwordValue, $librarianHash)) {
            loginUser(302, $email, 'librarian');
            header('Location: /lab7/public/dashboard.php');
            exit;
        } else {
            $error = 'Неверный e-mail или пароль.';
        }
    }
}
?>
<!doctype html>
<html lang="ru">
<head><meta charset="UTF-8"><title>Вход — Электронная библиотека</title></head>
<body>
<h1>Электронная библиотека — Вход</h1>
<?php if (isset($_GET['expired'])): ?>
<p style="color: red;">Сеанс завершён из-за бездействия.</p>
<?php endif; ?>
<?php if ($error !== ''): ?>
<p style="color: red;"><?= h($error) ?></p>
<?php endif; ?>
<form method="post" action="/lab7/public/login.php">
    <input type="hidden" name="csrf_token" value="<?= h($_SESSION['login_csrf']) ?>">
    <label>E-mail: <input name="email" type="email" required value="<?= h($email) ?>"></label><br><br>
    <label>Пароль: <input name="password" type="password" required></label><br><br>
    <button type="submit">Войти</button>
</form>
<p><small>Тестовый читатель: reader@atu.edu.kz / Reader123!<br>Тестовый библиотекарь: librarian@atu.edu.kz / Librarian123!</small></p>
</body>
</html>