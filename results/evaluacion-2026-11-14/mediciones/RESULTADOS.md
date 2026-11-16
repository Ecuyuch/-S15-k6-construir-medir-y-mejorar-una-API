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
