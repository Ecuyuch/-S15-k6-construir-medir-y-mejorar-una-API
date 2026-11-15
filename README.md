# ReservaFlow API y evaluación reproducible

API de reservas con Node.js 20, Express 4, TypeScript y PostgreSQL 16. No incluye
frontend. Evaluación individual de Eddy Gerardo Cuyuch Lopez, carné 2890-22-8567.

El código de origen incluye v1 (consulta N+1) y v2 (JOIN e índices). Esta entrega
verifica ambas con datos reparados, carga equivalente y resultados locales reales.
Los documentos y resultados históricos se conservan, pero no se usan como mediciones
de este equipo. La batería vigente está en `k6/evaluation/`.

## Requisitos e instalación

- Windows con Docker Desktop funcionando (motor Linux y Docker Compose >=2.24.4).
- Git. Node.js 22 para el automatizador; Node.js 20 de la API se instala en su imagen.
- Internet para descargar imágenes y dependencias; las pruebas solo apuntan a la API local.
- Al menos 500 MiB libres en Windows antes de inyectar carga. Cerrar aplicaciones no utilizadas.

```powershell
git clone https://github.com/Ecuyuch/-S15-k6-construir-medir-y-mejorar-una-API.git ReservaFlowBackend
Set-Location -LiteralPath '.\ReservaFlowBackend'
$env:Path = 'C:\Program Files\Docker\Docker\resources\bin;' + $env:Path
docker compose up -d --build
docker compose exec -T db psql -U reserva -d reservaflow -v ON_ERROR_STOP=1 -f /db/v2_fix.sql
Invoke-RestMethod http://localhost:3001/health
```

Repositorio de entrega: https://github.com/Ecuyuch/-S15-k6-construir-medir-y-mejorar-una-API (rama main). La rama de trabajo local es codex/evaluacion-rendimiento.

## Configuración y decisiones

`docker-compose.override.yml` se aplica automáticamente y conserva los servicios
existentes del equipo: API `127.0.0.1:3001`, DB `127.0.0.1:5433`.
DB: `reservaflow`; usuario y clave locales de desarrollo: `reserva` / `reserva`.
Los datos se guardan en el volumen `reservaflowbackend_pgdata`.

- API: Node 20 + Express + TypeScript por simplicidad y tipado; pool PG de 10 conexiones.
- PostgreSQL: transacciones y bloqueo de fila `FOR UPDATE` para respetar capacidad con concurrencia.
- API 1 CPU/256 MiB; DB 1 CPU/512 MiB. Generador k6 1 CPU/256 MiB.
- v2 es predeterminada. Para cambiar: `$env:APP_VERSION='v1'` o `'v2'`, seguido de
  `docker compose up -d --no-deps --force-recreate api`.
- Los índices se aplican aparte: cambiar APP_VERSION no los crea ni elimina.

## Operaciones y reglas

| Método | Ruta | Resultado |
|---|---|---|
| GET | `/health` | Salud del proceso y versión; no sustituye una consulta real a DB |
| GET | `/availability?resourceId=1&date=2026-12-01` | 12 horarios 9 a 20, capacidad, ocupación y disponibilidad |
| POST | `/reservations` | 201, o 400 por validación, 404 recurso, 409 falta de capacidad |
| GET | `/reservations?page=1&pageSize=50&status=confirmed` | Página ordenada por fecha e ID descendente, hasNext |

Reserva de ejemplo: `{"resourceId":1,"customerName":"Cliente","date":"2028-01-01","slot":10,"guests":2}`.
Máximo 20 invitados confirmados por recurso, fecha y horario; guests>=1; nombre no
vacío; slot 9..20; page>=1; pageSize 1..100; estados confirmed/pending/cancelled.

## Datos reproducibles y restablecimiento

La semilla usa hashes MD5 de claves por fila y ancla **2026-11-14**, sin depender
del reloj ni de random no correlacionado. Crea 50 recursos y **289882 reservas**:
202731 confirmed, 58091 cancelled y 29060 pending; máximo 12 invitados por franja sembrada.

**Restablecer borra solamente las reservas y recursos de esta API**, incluidos los
creados manualmente, y los reconstruye; no afecta otros proyectos ni volúmenes.
Antes de la primera restauración de esta evaluación se guardó un respaldo original.

```powershell
docker compose exec -T db psql -U reserva -d reservaflow -v ON_ERROR_STOP=1 -f /db/reset.sql
# Solo si se desea medir/usar v2, volver a aplicar índices
docker compose exec -T db psql -U reserva -d reservaflow -v ON_ERROR_STOP=1 -f /db/v2_fix.sql
node scripts/check-seed.mjs
node scripts/functional.mjs
```

## Ejecutar humo carga estrés y recuperación

El plan previo, mezcla, justificación de umbrales y límites están en
`docs/PLAN_EJECUCION_LOCAL.md`. El automatizador ejecuta dos cargas por versión en
orden ABBA, estrés v1/v2, regresiones y recuperación posterior si hay interrupción.
Restaura datos antes de cada medición y deja la API en v2 con datos limpios al final.
Solo debe ejecutarse cuando no se esté utilizando la DB para datos que deban conservarse.

```powershell
docker pull grafana/k6:1.0.0
# CAMPAIGN identifica carpeta nueva para no sobrescribir resultados anteriores
$env:CAMPAIGN = 'repeticion-01'
node --expose-gc scripts/benchmark.mjs
```

Para una prueba individual (con estado inicial preparado de la versión elegida):

```powershell
$testRoot = (Get-Location).Path.Replace('\','/')
docker run --rm --cpus 1 --memory 256m --network reservaflowbackend_default `
  -v "${testRoot}/k6:/scripts:ro" -e BASE_URL=http://api:3000 `
  -e K6_NO_USAGE_REPORT=true grafana/k6:1.0.0 run /scripts/evaluation/smoke.js
# Sustituir smoke.js por load.js o stress_recovery.js
```

Los códigos no cero de k6 se conservan: 99 indica thresholds incumplidos, 105 una
interrupción por señal; revisar consola/meta para la causa precisa. No confundir
una prueba interrumpida con 120 o 180 segundos completados.

## Evidencias y documentación

- `results/evaluacion-2026-11-14/`: intentos interrumpidos y respaldo original.
- `results/evaluacion-2026-11-14/mediciones/`: campaña principal, resúmenes, series JSON
  gzip originales, consola, recursos, integridad, planes SQL, manifiesto y entorno.
- `scripts/analyze.py`: deriva análisis de las series originales y resúmenes.
- `docs/VERIFICACION_RUBRICA.md`: revisión de faltantes y pendientes externos.
- `output/`: informe editable, PDF, guion y material preparado para entregar.

`dropped_iterations` mide iteraciones no iniciadas por k6. Evaluar configuración,
VUs y recursos del generador junto a latencia y recursos del servidor; no atribuir
el descarte automáticamente a PostgreSQL. No se reduce carga ni se relajan thresholds
entre versiones. Los resultados históricos en `results/load_v2.json` y
`results/stress_recovery_v2.json` no pertenecen a esta evaluación local.

## Detener y reanudar sin borrar datos

```powershell
docker compose stop
docker compose up -d
```

## Referencias

- [Thresholds de k6](https://grafana.com/docs/k6/latest/using-k6/thresholds/)
- [Dropped iterations](https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/dropped-iterations/)
- [Repositorio de origen](https://github.com/josuesanchez96/ReservaFlowBackend)


