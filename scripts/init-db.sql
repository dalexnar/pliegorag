-- PliegoRAG: Script de inicialización
-- Se ejecuta solo la primera vez que arranca MariaDB

USE pliegorag;

-- Tabla de pliegos (por si SQLAlchemy no la crea)
CREATE TABLE IF NOT EXISTS pliegos (
    id INT AUTO_INCREMENT PRIMARY KEY,
    numero_proceso VARCHAR(100),
    entidad VARCHAR(255),
    objeto TEXT,
    nombre_archivo VARCHAR(255) NOT NULL,
    ruta_archivo VARCHAR(500) NOT NULL,
    tamano_bytes BIGINT,
    num_paginas INT,
    texto_completo LONGTEXT,
    texto_tokens INT,
    datos_extraidos JSON,
    estado ENUM('procesando', 'listo', 'error') DEFAULT 'procesando',
    error_mensaje TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_numero_proceso (numero_proceso),
    INDEX idx_estado (estado),
    INDEX idx_created (created_at)
);

-- Tabla de conversaciones
CREATE TABLE IF NOT EXISTS conversaciones (
    id INT AUTO_INCREMENT PRIMARY KEY,
    pliego_id INT NOT NULL,
    pregunta TEXT NOT NULL,
    respuesta TEXT,
    modelo_usado VARCHAR(100),
    tokens_prompt INT,
    tokens_respuesta INT,
    tiempo_respuesta_ms INT,
    fue_util TINYINT(1),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pliego_id) REFERENCES pliegos(id) ON DELETE CASCADE,
    INDEX idx_pliego (pliego_id),
    INDEX idx_created (created_at)
);