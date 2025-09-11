<?php
$host = "active-users-db.cnieq0qkqult.us-west-1.rds.amazonaws.com";  // env variables
$port = "5432";
$dbname = "user_login_db";    // env variables
$user = "arna_admin";       // env variables
$password = "4rn4-admin";  // env variables

try {
    $conn = new PDO("pgsql:host=$host;port=$port;dbname=$dbname", $user, $password);
    $conn->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch (PDOException $e) {
    die("Connection failed: " . $e->getMessage());
}
?>
