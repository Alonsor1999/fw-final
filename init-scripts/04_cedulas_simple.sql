-- Tabla simple para cédulas y fechas de expedición
-- Versión: 1.0
-- Fecha: 29 de Agosto, 2025

-- Tabla simple: cedulas
CREATE TABLE cedulas (
    cedula VARCHAR(20) PRIMARY KEY,
    fecha_expedicion VARCHAR(100) NOT NULL
);

-- Índice para búsquedas rápidas
CREATE INDEX idx_cedulas_cedula ON cedulas(cedula);

-- Insertar datos de cédulas
INSERT INTO cedulas (cedula, fecha_expedicion) VALUES
-- Primer grupo de datos con formato "DD DE MES DE YYYY"
('1077463022', '15 DE MAYO DE 2012'),
('11811703', '6 DE MAYO DE 1999'),
('1077423.887', '25 DE JULIO DE 2013'),
('1077423721', '25 DE JUNIO DE 2004'),
('1130804279', '6 DE MARZO DE 2005'),
('1077437035', '30 DE OCTUBRE DE 2006'),
('11780130', '12 DE DICIEMBRE DE 1983'),
('11808619', '12 DE JUNIO DE 1997'),
('1077422845', '21 DE ABRIL DE 2009'),
('1001637081', '11 DE MAYO DE 2016'),
('71978384', '28 DE NOVIEMBRE DE 1988'),
('8112473', '9 DE MAYO DE 1998'),
('6706265', '9 DE DICIEMBRE DE 198'),

-- Segundo grupo de datos con formato "YYYY-MM-DD"
('1077858861', '2009-01-28'),
('1080047364', 'NO APARECE EN ANI'),
('27923760', '1961-05-17'),
('93238041', '2003-02-24'),
('1193486932', '2018-11-16'),
('71987317', '1997-03-05'),
('26675973', '1974-01-21'),
('31375142', '1977-04-01'),
('16375380', '2002-04-17'),
('19141064', '1973-02-09'),
('79139659', '1991-02-14'),
('55168676', '1992-04-22'),
('63431150', '1982-08-27'),
('19137165', '1973-01-11'),
('82384064', '1991-01-22'),
('1089801912', 'NO APARECE EN ANI'),
('5714555', '1976-08-31'),
('1128325751', '2024-08-21'),
('96359623', '1990-11-20'),
('1104938596', '2023-11-29'),
('1141314337', '2024-06-06'),
('52808502', '1999-03-15');

-- Comentarios para documentación
COMMENT ON TABLE cedulas IS 'Tabla simple para almacenar cédulas y fechas de expedición para scraping';
COMMENT ON COLUMN cedulas.cedula IS 'Número de cédula de ciudadanía (clave primaria)';
COMMENT ON COLUMN cedulas.fecha_expedicion IS 'Fecha de expedición en formato texto';
