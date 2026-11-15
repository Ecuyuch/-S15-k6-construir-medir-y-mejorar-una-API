-- =====================================================================
-- ReservaFlow - Inicialización de la base de datos (estado ORIGINAL / v1)
-- ---------------------------------------------------------------------
-- Se ejecuta automáticamente la primera vez que arranca el contenedor
-- de PostgreSQL (docker-entrypoint-initdb.d).
--
-- ATENCIÓN (cuello de botella intencional v1):
--   Solo existen las claves primarias. NO hay índices sobre
--   (resource_id, reservation_date, slot), ni sobre status/reservation_date.
--   El índice de corrección se aplica con db/v2_fix.sql.
-- =====================================================================

CREATE TABLE resources (
    id        SERIAL PRIMARY KEY,
    name      TEXT    NOT NULL,
    capacity  INTEGER NOT NULL CHECK (capacity > 0)   -- personas por franja
);

CREATE TABLE reservations (
    id               BIGSERIAL PRIMARY KEY,
    resource_id      INTEGER     NOT NULL REFERENCES resources(id),
    customer_name    TEXT        NOT NULL,
    reservation_date DATE        NOT NULL,
    slot             SMALLINT    NOT NULL CHECK (slot BETWEEN 9 AND 20), -- hora de inicio
    guests           SMALLINT    NOT NULL CHECK (guests > 0),
    status           TEXT        NOT NULL CHECK (status IN ('confirmed','pending','cancelled')),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 50 recursos (mesas/salas) con capacidad de 20 personas por franja.
INSERT INTO resources (name, capacity)
SELECT 'Recurso ' || lpad(g::text, 2, '0'), 20
FROM generate_series(1, 50) g;

-- ~290,000 reservas ficticias (reproducibles gracias a setseed).
-- Rango de fechas sembradas: hoy-90 .. hoy+90 días.
-- Máximo 3 filas por (recurso, fecha, franja) con <=4 invitados => <=12 <= 20,
-- por lo que nunca se parte de un estado sobre-reservado.
-- Una subconsulta LATERAL sin referencia externa puede evaluarse una sola vez.
-- Derivar cada valor de md5 de una clave estable evita ese defecto y permite
-- restaurar exactamente los mismos registros, fechas, estados e identificadores.
WITH candidates AS (
  SELECT r.id AS resource_id, d, s, k,
         r.id || ':' || d || ':' || s || ':' || k AS key
  FROM resources r
  CROSS JOIN generate_series(-90, 90) d
  CROSS JOIN generate_series(9, 20) s
  CROSS JOIN generate_series(1, 3) k
), seeded AS (
  SELECT *,
    ('x' || substr(md5(key || ':keep'), 1, 8))::bit(32)::bigint AS keep,
    ('x' || substr(md5(key || ':status'), 1, 8))::bit(32)::bigint AS state,
    ('x' || substr(md5(key || ':guests'), 1, 8))::bit(32)::bigint AS guests_seed
  FROM candidates
)
INSERT INTO reservations (resource_id, customer_name, reservation_date, slot, guests, status, created_at)
SELECT resource_id, 'Cliente ' || (guests_seed % 5000),
       DATE '2026-11-14' + d, s, 1 + guests_seed % 4,
       CASE WHEN state % 100 < 70 THEN 'confirmed'
            WHEN state % 100 < 90 THEN 'cancelled' ELSE 'pending' END,
       TIMESTAMPTZ '2026-11-14 12:00:00+00' - (guests_seed % 10368000) * INTERVAL '1 second'
FROM seeded WHERE keep % 100 < 89
ORDER BY resource_id, d, s, k;

ANALYZE;

