# Plan previo de medición local

Fecha de definición: 14 de noviembre de 2026, America/Guatemala.
Estudiante: Eddy Gerardo Cuyuch Lopez. Carné: 2890-22-8567.

## Demanda

Hipótesis de demanda académica, no tráfico productivo observado: 40 operaciones/s.
Cada iteración representa una operación HTTP. Mezcla por índice global de iteración
módulo 10: 4 disponibilidades, 3 listados de 50 elementos, 3 creaciones.
Los descartes pueden modificar la mezcla efectivamente completada; se informa la
mezcla observada a partir de la salida original de k6.

Fechas de lectura en 2026-08-16 a 2027-02-12, relativas a ancla fija 2026-11-14.
Fechas de escritura desde ancla+400 días, con combinación recurso/fecha/horario única
por iteración; de ese modo los conflictos funcionales deliberados se miden en humo
y regresión, y no se mezclan con errores inesperados de carga.

## Escenarios y criterios

| Escenario | Perfil | Duración | Criterio |
|---|---|---|---|
| Humo | 1 VU, pausa 1 s | 30 s | checks 100%, errores 0%, p95<2000 ms |
| Calentamiento | 1 VU, pausa 0.5 s | 15 s | No es medición principal |
| Sostenida | 40 it/s, 60 VUs preasignadas y máximas | 120 s | p95<200 ms, p99<500 ms, errores<1%, checks=100%, descartes=0 |
| Estrés | 2/10/20/40/40/2/2/0 VUs | 20/25/25/20/20/10/50/10 s | errores<10%, p99<5000 ms |
| Recuperación integrada | 2 VUs, pausa 0.25 s | 50 s después de descenso | p95<300 ms, errores<1%, >20 solicitudes |
| Recuperación posterior segura | 1 VU, pausa 0.5 s | 30 s, si el estrés falla/aborta | p95<300 ms, errores<1%, checks=100% |

Umbrales adicionales de carga por operación: disponibilidad p95<150 ms, listado y
creación p95<250 ms. Los umbrales son metas propuestas para una API interactiva:
200 ms deja margen a red/interfaz, 500 ms controla cola larga y errores<1% define
el presupuesto. No son una obligación universal ni una medición previa.

## Seguridad

Solo contenedores propios en red reservaflowbackend_default; BASE_URL restringida
a API local. Sin Canvas, servicios públicos ni inyección de carga hacia GitHub.
Timeout HTTP 6 s. AbortOnFail cuando errores>=10% o p99>=5000 ms, después de 30 s.
Se conservan esos límites y umbrales en v1 y v2.

API: 1 CPU y 256 MiB. DB: 1 CPU y 512 MiB. Generador: 1 CPU y 256 MiB.
Muestras cada 5 s de CPU, RAM, I/O, PIDs y RAM libre del host. Tres muestras seguidas
con RAM libre del host<400 MiB o RAM de un contenedor>90% activan parada del generador.
Si se interrumpe: registrar código/motivo y ejecutar recuperación posterior sin
reiniciar la API ni PostgreSQL. Los demás proyectos quedan ejecutándose.

## Comparación y trazabilidad

Carga dos veces por versión en orden v1/v2/v2/v1 (ABBA); luego estrés v1/v2.
Mismo hardware, imágenes, límites, pool=10, scripts, thresholds y datos.
Restaurar las tablas propias antes de cada prueba mediante db/reset.sql.
Aplicar db/v2_fix.sql solo a v2. La semilla crea 289882 reservas:
202731 confirmed, 58091 cancelled y 29060 pending.
La corrección de datos es común a ambos grupos, no la variable de optimización.

Cada medición se calienta 15 s; luego se borran solo las escrituras del
calentamiento, se restablece secuencia y se ejecuta ANALYZE. No se vacía caché del SO.
La huella SHA256 de todas las filas al restaurar debe coincidir en los seis ensayos.
El reinicio de API por versión vacía su pool; el proceso DB continúa ejecutándose.
No se afirma una comparación con caché fría.

Guardar meta, integridad antes/después, resumen JSON, serie JSON gzip original,
consola y recursos. Registrar versión del código y SHA256 de archivos medidos.
Con dos repeticiones solo se describe variación; no se infiere significancia
estadística. Si varía sustancialmente se investiga/repite sin bajar carga o umbrales.
Si 40 VUs no saturan v2, declarar que no se alcanzó su saturación dentro del límite.

Fuentes oficiales:
- https://grafana.com/docs/k6/latest/using-k6/thresholds/
- https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/dropped-iterations/

Preparación de campaña principal: se detuvieron temporalmente cuatro contenedores de presencia con autorización del estudiante. Antes de la campaña se sincronizó y liberó caché de páginas WSL (echo 1 > /proc/sys/vm/drop_caches). No se vacía caché entre versiones; se aplica el mismo calentamiento en cada ensayo. Fuente: https://devblogs.microsoft.com/commandline/memory-reclaim-in-the-windows-subsystem-for-linux-2/

Ajuste antes de la primera medición válida: la restauración vuelve a llenar caché WSL. Por ello se sincroniza y libera su caché de archivos después de CADA restauración en AMBAS versiones, antes del calentamiento de 15 s. Se conservan shared_buffers PostgreSQL y no se declara caché totalmente fría. Preflight espera hasta 180 s por 500 MiB libres; la regla de parada de 400 MiB permanece. Este párrafo sustituye la indicación anterior de no vaciar caché entre ensayos. Los intentos previos se conservan como interrumpidos y no son el comparador principal.

Campaña definitiva: además de los cuatro contenedores, se detuvieron temporalmente OracleServiceXE, MSSQLSERVER y MSSQL$SQLEXPRESS con autorización. Sus estados se guardan para restaurarlos. La preparación anterior se conserva en preparacion-con-servicios-nativos y no se combina con la campaña definitiva mediciones. Las reglas de parada y demanda permanecen idénticas.


Revisión final de seguridad ANTES de la primera carga de la campaña definitiva: la reserva de 700 MiB bloqueaba incluso el reposo. Se observaron ~27 MiB de k6 en el intento inicial, DB por debajo de su límite de 512 MiB y más de 2 GiB MemAvailable dentro de WSL. Con siete servicios ajenos detenidos, se fija preflight>=500 MiB Windows, parada <400 MiB durante tres muestras y parada inmediata <250 MiB. Se registra como revisión de seguridad del entorno, no como mejora de la API. Se aplicará sin cambios a ambos grupos. Carga 40it/s, duración120s, p95<200, p99<500, errores<1%, checks100%, descartes0 y abortos HTTP permanecen idénticos. Los intentos previos se conservan y se excluyen de la comparación principal.
