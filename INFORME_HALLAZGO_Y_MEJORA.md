# Informe de hallazgo y mejora de ReservaFlow

**Estudiante:** Eddy Gerardo Cuyuch Lopez. **Carné:** 2890-22-8567.
**Fecha:** 15 de noviembre de 2026.
**Entrega:** https://github.com/Ecuyuch/-S15-k6-construir-medir-y-mejorar-una-API

## Resultado y autoría

V2 aprobó ambas cargas de 120 s a 40 operaciones/s, sin errores ni descartes.
V1 activó límites de seguridad por latencia y errores y no completó 120 s.
Su recuperación posterior segura aprobó sin reiniciar API ni DB. V2 completó
estrés y recuperación; no alcanzó saturación dentro de 40 VUs.

La implementación v1/v2 y db/v2_fix.sql ya existían en el origen. Esta evaluación
reparó la siembra, fortaleció scripts y verificó la corrección con evidencia nueva.
Los resultados históricos se conservan separados y no se atribuyen a este equipo.

## Hallazgo e hipótesis

listV1 hace 51 consultas para una página de 50 reservas y carece de índices de
filtro/orden. Hipótesis: JOIN e índices reducen trabajo SQL y cola del pool,
conservando contratos, transacciones FOR UPDATE y capacidad de 20 personas.
Se aplica listV2 mediante APP_VERSION=v2 y db/v2_fix.sql.

La siembra original produjo 325800 cancelled por un LATERAL con random sin
correlación; el check aceptaba un listado vacío de confirmed. Se reparó para
ambos grupos con MD5 por fila, ancla fija y orden estable: 289882 reservas,
202731 confirmed, 58091 cancelled y 29060 pending.

## Condiciones equivalentes

Dell Inspiron 3501, i7-1165G7, 4 núcleos/8 hilos, 8 GB nominales.
API 1 CPU/256 MiB; DB 1 CPU/512 MiB; generador 1 CPU/256 MiB; pool=10.
Versiones exactas e imágenes: environment.json y runtime-versions.json.
Se pausaron siete servicios ajenos con autorización y se restauran al terminar.

Carga ABBA v1/v2/v2/v1: 40 it/s, 120 s, 60 VUs, mezcla 40/30/30 idéntica.
Restauración antes de medir, caché de archivos WSL liberada en ambos grupos y
calentamiento 15 s. Se conservan shared_buffers; no es caché totalmente fría.
Las seis huellas de datos iniciales coinciden.

El plan previo y revisiones de seguridad están en docs/PLAN_EJECUCION_LOCAL.md.
Los umbrales de rendimiento permanecieron iguales: p95<200 ms, p99<500 ms,
errores<1%, checks100%, descartes0 y límites por operación. La revisión de
reserva Windows ocurrió antes de la campaña definitiva y se aplicó a ambos grupos.

# Resultados nuevos obtenidos localmente

| Ensayo | s reales | HTTP | req/s | p95 ms | p99 ms | Error % | Checks % | Descartes | Salida |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| v1-load-1 | 32.9 | 490 | 15.32 | 6000.81 | 6002.00 | 26.94 | 73.06 | 730 | 99 |
| v1-load-2 | 33.3 | 468 | 14.66 | 6000.86 | 6001.99 | 27.56 | 72.44 | 751 | 99 |
| v1-recovery-safe | 32.5 | 54 | 1.78 | 115.60 | 177.13 | 0.00 | 100.00 | No aplica | 0 |
| v1-smoke | 32.3 | 116 | 3.77 | 47.63 | 60.14 | 0.00 | 100.00 | No aplica | 0 |
| v1-stress | 77.1 | 571 | 7.52 | 3400.55 | 5530.11 | 1.05 | 98.95 | No aplica | 99 |
| v2-load-1 | 122.4 | 4800 | 40.03 | 7.61 | 9.03 | 0.00 | 100.00 | 0 | 0 |
| v2-load-2 | 122.4 | 4801 | 40.03 | 6.96 | 8.88 | 0.00 | 100.00 | 0 | 0 |
| v2-smoke | 32.5 | 120 | 3.95 | 9.16 | 10.32 | 0.00 | 100.00 | No aplica | 0 |
| v2-stress | 181.6 | 8697 | 48.27 | 18.10 | 30.35 | 0.00 | 100.00 | No aplica | 0 |

Los tiempos incluyen arranque/cierre del contenedor en meta; req/s usa duración interna de k6.
Las interrupciones conservan el resultado parcial y no equivalen a completar el escenario.
http_req_duration mide solicitudes completadas, incluidas las fallidas; no incluye solicitudes descartadas.
La mejora se calcula con repeticiones, sin promediar percentiles como si fueran una muestra combinada.

## Recuperación y regresión

- V1 posterior: 54 solicitudes, p95 115.60 ms, errores 0.00%.
- V2 integrada: 385 solicitudes, p95 12.30 ms y errores 0%.

Regresión antes/después: salud, 400, 404, paginación no vacía, orden, páginas sin
duplicados y concurrencia. Veinte solicitudes de tres invitados producen seis
201 y catorce 409: 18 ocupados y 2 disponibles. Todos los ensayos conservaron cero
sobrecupos. Estado final: v2, 50 recursos y 289882 reservas restauradas.

## Lectura crítica y límites

- V1 no completó 120 s: misma demanda ofrecida y criterios, distinta duración y
  volumen completado. El timeout de 6 s censura esperas superiores.
- dropped_iterations son operaciones no iniciadas por k6; no son HTTP 500.
  Interpretar VUs, latencia y CPU/RAM de generador y servidor en conjunto.
  No aplica como tasa abierta en el estrés de modelo cerrado.
- req/s incluye peticiones fallidas; la mezcla completada puede variar por
  descartes o abortos. La serie original conserva códigos y etiquetas.
- Dos repeticiones describen variación; no prueban significancia estadística.
- Generador y SUT comparten host. Muestreo cada 5 s puede omitir picos. No se
  midieron temperatura, CPU total del host ni espacio adicional de índices.
- No se observaron regresiones en casos funcionales verificados. No se extrapola
  capacidad más allá de 40 VUs.

## Evidencias y entrega

Campaña principal: results/evaluacion-2026-11-14/mediciones/.
Originales: summary.json, timeseries.json.gz, console.txt, resources.json/jsonl,
meta.json, initial.json, versiones, manifiestos y planes SQL.
analysis.json y RESULTADOS.md son derivados y no sustituyen los originales.
Otros subdirectorios contienen preparaciones o intentos interrumpidos.

Informe Word y guion: output/. Capturas de API y transcripciones identificadas:
output/evidencias/. Pendiente: incorporar enlace de video máximo 3 minutos al
Word. Por solicitud del estudiante no se incluye PDF.

Fuentes oficiales:
- https://grafana.com/docs/k6/latest/using-k6/thresholds/
- https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/dropped-iterations/
- https://devblogs.microsoft.com/commandline/memory-reclaim-in-the-windows-subsystem-for-linux-2/
