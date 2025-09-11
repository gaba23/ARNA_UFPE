<?php

session_start();
require_once 'config.php';

if (isset($_POST['register'])) {  // register
    $name = $_POST['name'];
    $email = $_POST['email'];
    $password = password_hash($_POST['password'], PASSWORD_DEFAULT);
    $role = "user";  // you can only register as a user (not admin)

    $stmt = $conn->prepare("SELECT 1 FROM users WHERE email = :email");  // check if email exists in user db
    $stmt->execute([':email' => $email]);

    if ($stmt->fetch()) {
        $_SESSION['register_error'] = 'Email is already registered';
        $_SESSION['active_form'] = 'register';
    } else {
        $stmt = $conn->prepare("INSERT INTO users (name, email, password, role) 
                                VALUES (:name, :email, :password, :role)");
        $stmt->execute([
            ':name' => $name,
            ':email' => $email,
            ':password' => $password,
            ':role' => $role
        ]);
    }

    header("Location: login.php");
    exit();
}


if (isset($_POST['login'])) {  // login
    $email = $_POST['email'];
    $password = $_POST['password'];

    $stmt = $conn->prepare("SELECT * FROM users WHERE email = :email");
    $stmt->execute([':email' => $email]);
    $user = $stmt->fetch(PDO::FETCH_ASSOC);

    if ($user && password_verify($password, $user['password'])) {
        $_SESSION['name'] = $user['name'];
        $_SESSION['email'] = $user['email'];

        header("Location: home.php");
        exit();
    }

    $_SESSION['login_error'] = 'Incorrect email or password.';
    $_SESSION['active_form'] = 'login';
    header("Location: login.php");
    exit();
}

?>
