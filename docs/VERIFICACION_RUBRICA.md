# Verificación de los lineamientos

## Situación encontrada antes de esta evaluación

- API Express/TypeScript con PostgreSQL y tres operaciones solicitadas: presente.
- Implementaciones v1 (N+1) y v2 (JOIN) e índices de corrección: ya presentes.
- Scripts originales de humo/carga/estrés: presentes; fechas y mezcla aleatorias.
- Solo había resúmenes históricos de carga v2 y estrés v2. No había resultado
  original de v1 que respaldara su tabla comparativa.
- El informe histórico indicaba un Lenovo con 16 GB; el equipo real es Dell
  Inspiron 3501 con 8 GB. Esas cifras históricas no son mediciones de esta sesión.
- La siembra original produjo 325800 reservas cancelled y ninguna confirmed.
  El LATERAL con random sin correlación externa se evaluó una sola vez.
  El check del listado aceptaba un arreglo vacío y ocultaba esa falta de datos.
- El compose original fijaba APP_VERSION=v2; no respetaba el cambio por variable
  de entorno descrito en su README. El override local ahora sí lo respeta.
- Faltaban límites explícitos de contenedores, medición de recursos, repeticiones
  equivalentes, regresión concurrente registrada y los entregables Word/PDF.

## Trabajo de esta evaluación

Se conserva el contenido anterior en docs/originales, results y imgs. Se añade
una batería canónica en k6/evaluation y resultados nuevos en
results/evaluacion-2026-11-14. El plan se congela antes de medir.
Se corrige la reproducibilidad de datos para ambas versiones por igual.
La comparación de rendimiento verifica la corrección v2 ya disponible; no se
presenta como una optimización escrita por primera vez en esta sesión.

## Estado final de la evaluación

Se completaron humo, dos cargas por versión, estrés con recuperación, regresión
funcional, análisis de recursos y comparación con condiciones equivalentes.
V1 se interrumpió por seguridad y se verificó su recuperación con una prueba segura.
V2 aprobó las cargas y completó el máximo seguro de 40 VUs sin alcanzar saturación.
Los resultados originales están en results/evaluacion-2026-11-14/mediciones/.
El informe editable y el guion del video están en output/.

Repositorio de entrega:
https://github.com/Ecuyuch/-S15-k6-construir-medir-y-mejorar-una-API

## Pendiente del estudiante

Grabar un video de máximo tres minutos, verificar que el docente pueda acceder
al enlace y pegarlo en el informe Word. El guion contiene narración, tiempos y
archivos para mostrar. La consigna original pide PDF; por solicitud expresa del
estudiante, esta entrega contiene Word y no incluye PDF.
