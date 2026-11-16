# Evaluación reproducible de ReservaFlow

Objetivo: verificar la rúbrica con mediciones locales reales y entregar Word editable y PDF.
Especificación: lineamientos proporcionados por el estudiante en esta conversación.

## Decisiones previas

- Conservar Node/Express/PostgreSQL y las implementaciones v1/v2 existentes.
- Trabajar en la carpeta solicitada, en rama codex/evaluacion-rendimiento; conservar originales.
- No afirmar que la corrección v2 fue creada en esta evaluación: ya existe en el repositorio.
- Reparar primero la siembra para que la comparación tenga datos mixtos y reproducibles.
- Carga: 40 iteraciones/s, 120 segundos, mezcla determinista 40/30/30, 60 VUs.
- Dos repeticiones de carga por versión; estrés de 180 s por versión y recuperación segura si aborta.
- Umbrales idénticos: p95 global <200 ms, p99 <500 ms, errores <1%, checks 100%,
  disponibilidad p95 <150 ms, listado y creación p95 <250 ms, dropped_iterations=0.
- Estrés cerrado: 2/10/20/40/2/2/0 VUs; fases 20/25/25/40/10/50/10 segundos.
- Abortos: errores >=10% o p99 >=5000 ms tras 30 s; timeout HTTP 6 s.
- Contenedores: API 1 CPU/256 MiB; DB 1 CPU/512 MiB; generador 1 CPU/256 MiB.
- Monitoreo cada 5 s; parar generador si RAM del host <400 MiB o RAM de contenedor
  >90% del límite durante tres muestras. Nunca detener otros proyectos.
- Semilla fija 2026-11-14, reinicio de tablas propias antes de cada medición,
  calentamiento 15 s, mismas imágenes/pool/concurrencia, sin vaciar caché del SO.
- Guardar resumen, salida JSON comprimida original, consola, recursos, integridad,
  EXPLAIN ANALYZE, huellas SHA256, entorno y código.

## Tareas

- [x] Probar distribución defectuosa; siembra determinista y respaldo de DB original.
- [x] Fortalecer k6, regresión concurrente y automatización con límites y registro.
- [x] Congelar plan y código antes de medir, ejecutar v1/v2 y dos cargas cada una.
- [x] Analizar resultados, variación, recursos y recuperación sin inventar cifras.
- [x] Actualizar README/plan/informe; preparar guion de video y Word y guion verificados (sin PDF por solicitud del estudiante).

## Revisión

Verificar páginas no vacías, fechas fijas, conflictos esperados, sobreventa concurrente,
parada temprana, igualdad de estado inicial y ausencia de secretos en resultados.
Pendiente externo: grabar el video y agregar su enlace accesible al Word.

