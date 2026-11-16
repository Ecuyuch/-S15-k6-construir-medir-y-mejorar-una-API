import json, hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
P=ROOT/'results/evaluacion-2026-11-14/mediciones'
A=json.loads((P/'analysis.json').read_text(encoding='utf-8'))
R=A['runs']
rows=(P/'RESULTADOS.md').read_text(encoding='utf-8')
text="""# Informe de hallazgo y mejora de ReservaFlow

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

"""
text+=rows+'\n## Recuperación y regresión\n\n'
safe=R['v1-recovery-safe']; v2=R['v2-stress']
text+=f"- V1 posterior: {safe['requests']['count']} solicitudes, p95 {safe['latency']['p(95)']:.2f} ms, errores {100*safe['error_rate']:.2f}%.\n"
rec=v2['recovery']['http_req_duration{phase:recuperacion}']
text+=f"- V2 integrada: {v2['phase_counts']['recuperacion']} solicitudes, p95 {rec['p(95)']:.2f} ms y errores 0%.\n"
text+="""
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
"""
(ROOT/'INFORME_HALLAZGO_Y_MEJORA.md').write_text(text,encoding='utf-8')
import subprocess, sys
subprocess.run([sys.executable, str(ROOT/'scripts/build_video_script.py')],check=True)
hashes={x.name:hashlib.sha256(x.read_bytes()).hexdigest() for x in P.iterdir() if x.is_file() and x.name not in ['artifact-hashes.json','analysis.json','RESULTADOS.md']}
(P/'artifact-hashes.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
print('Informe Markdown guion y huellas de originales generados')

