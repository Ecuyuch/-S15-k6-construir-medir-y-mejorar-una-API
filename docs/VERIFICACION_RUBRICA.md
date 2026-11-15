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

## Pendientes de entrega que no se pueden sustituir por mediciones

1. Grabar video de máximo 3 minutos y agregar enlace público o compartido al Word.
2. Publicar rama y resultados en un repositorio accesible del estudiante o un fork.
   El repositorio de origen es público, pero la conexión actual tiene permiso de
   lectura y carece de permiso de escritura. Los commits locales no están publicados.
3. Verificar acceso al repositorio y video desde una sesión sin autenticación.
4. Exportar el Word actualizado a PDF y entregar ese PDF.
