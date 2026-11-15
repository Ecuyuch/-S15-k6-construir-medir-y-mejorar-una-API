-- Solo tablas de ReservaFlow. No afecta otras bases de datos ni volúmenes.
\set ON_ERROR_STOP on
BEGIN;
DROP TABLE IF EXISTS reservations;
DROP TABLE IF EXISTS resources;
\i /db/init.sql
COMMIT;
