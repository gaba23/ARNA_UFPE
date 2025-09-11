<?php
session_start();

$errors = [
    'login' => $_SESSION['login_error'] ?? '',
    'register' => $_SESSION['register_error'] ?? ''
];
$activeForm = $_SESSION['active_form'] ?? 'login';

session_unset();

function showError($error) {
    return !empty($error) ? "<p class='error-message'>$error</p>" : '';
}

function isActiveForm($formName, $activeForm) {
    return $formName === $activeForm ? 'active' : '';
}

?>


<!DOCTYPE html>
<html lang="pt-br">
<head>
    <title>Login</title>
    <link rel="stylesheet" type="text/css" href="../static/login.css">
    <link rel="icon" type="image/png" href="../static/favicon.png">
</head>
<body>
<header>
    <div class="logo">
        ARNA
    </div>
    <div class="profile">
        <img src="../static/avatar.png" alt="Avatar">
    </div>
</header>
<div class="content">
    <div class="container">
        
        <div class="form-box <?= isActiveForm('login', $activeForm); ?>" id="login-form">
            <h1>Login</h1>

            <!-- <form action="/login" method="POST"> -->
            <form action="login_register.php" method="POST">
                <!-- {% if erro %}
                <div class="errormessage">{{ erro }}</div>
                {% endif %} -->
                <?= showError($errors['login']); ?>

                <div class="input-box">
                    <input type="text" name="email" placeholder="Email">
                </div>
                <div class="input-box">
                    <input type="password" name="senha" placeholder="Senha">
                </div>
                <button class="login-button" type="submit">Logar</button>
            </form>

            <div class="register-link">
                Não possui uma conta? <a href="#" onclick="showForm('register-form')">Cadastre-se</a>
            </div>
        </div>



        <div class="form-box" <?= isActiveForm('register', $activeForm); ?> id="register-form">
            <h1>Registre-se</h1>

            <!-- <form action="/login#" method="POST"> -->
            <form action="login_register.php" method="POST">
                <!-- {% if erro %}
                <div class="errormessage">{{ erro }}</div>
                {% endif %} -->
                <?= showError($errors['register']); ?>

                <div class="input-box">
                    <input type="text" name="username" placeholder="Nome">
                </div>                
                <div class="input-box">
                    <input type="text" name="usersurname" placeholder="Sobrenome">
                </div>                
                <div class="input-box">
                    <input type="text" name="email" placeholder="Email">
                </div>
                <div class="input-box">
                    <input type="password" name="senha" placeholder="Senha">
                </div>
                <button class="register-button" type="submit">Criar conta</button>
            </form>

            <div class="login-link">
                Já possui uma conta? <a href="#" onclick="showForm('login-form')">Login</a>
            </div>
        </div>
        
    </div>
</div>

<script>
    function showForm(formId) {
        document.querySelectorAll(".form-box").forEach(form => form.classList.remove("active"));
        document.getElementById(formId).classList.add("active")
    }
</script>
 
</body>
</html>