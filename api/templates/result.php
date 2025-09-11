<?php
session_start();
if (!isset($_SESSION['email'])) {  // redireciona usuários não autenticados à página de login
    header("Location: login.php");
    exit();
}
?>

<!DOCTYPE html>
<html lang="pt-br">
<head>
    <title>Resultado</title>
    <link rel="stylesheet" type="text/css" href="../static/home.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css">
    <link rel="icon" type="image/png" href="../static/favicon.png">
</head>
<body>
    <header>
        <div class="logo">
            <a href="./home.php">
                ARNA
            </a>
        </div>
        <nav>
            <ul>
                <li class="dropdown">
                    <a href="./home.php">
                        ▼ Analisar
                    </a>
                    <div class="dropdown-content">
                        <a href="/home">CPM</a>
                        <a href="/homePERT">PERT</a>
                        <a href="/monteCarlo">Simulação de Monte Carlo</a>
                    </div>
                </li>
                <li><a class="active" href="#">Resultado</a></li>
                <li><a href="./help.html">Ajuda</a></li>
                <li><a href="./contact.html">Contato</a></li>
            </ul>
        </nav>
        <div class="profile dropdown">
            <div class="profile-dropdown dropdown">
                <img src="../static/avatar.png" alt="Avatar" onclick="toggleDropdown()">
                <div class="dropdown-content dropdown">    
                    <button onclick="window.location.href='logout.php'">Sair</button>
                </div>
            </div>
        </div>
    </header>
<div class="container" style="margin-bottom: 200px;">
    <h1>Resultado da Análise</h1>
    
    <div class="image-box">
        <div class="image-container">
            <div class="image-border">
                <img src="../resultadosCpmatividades_cpm.png" alt="Rede de Atividades">
            </div>
        </div>
    </div>    
    <div class="image-box">
        <div class="image-container">
            <div class="image-border">
                <img src="../resultadosCpm/gantt_cpm.png') }}" alt="Gráfico de Gantt">
            </div>
        </div>
    </div>    
        <!-- <div class="image-box">
        <div class="image-container">
            <div class="image-border">
                <img src="{{ url_for('resultadosCpm', path='/diagrama_na_seta.png') }}" alt="Atividade na Seta">
            </div>
        </div> -->
    </div>    

    <div class="download-buttons">
        <a href="../resultadosCpm/relatorio.pdf" class="download-button" onclick="openReportModal()">
            <i class="fas fa-file-pdf"></i> Baixar Relatório em PDF
        </a>        
        <a href="/download_png_cpm" class="download-button">
            <i class="fas fa-file-image"></i> Baixar PNG
        </a>
        <a href="/download_xls_cpm" class="download-button">
            <i class="fas fa-file-excel"></i> Baixar XLS
        </a>        
        
    </div>
    
</div>


<footer>
    <div class="footer-content">
        <div class="footer-logo">
            <img src="../static/logoPMD.png" alt="Random Logo">
        </div>
        <div class="footer-links">
            <a href="#">Termos</a>
            <a href="#">Privacidade</a>
            <a href="#">Cookies</a>
        </div>
    </div>
</footer>
</body>
</html>