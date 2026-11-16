"""Guion editable de una grabación de 2 minutos 55 segundos."""
from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output'
segments = [
('0:00–0:20 | Presentación',
 'Muestra /health y una página de reservas en el navegador.',
 'Soy Eddy Gerardo Cuyuch Lopez, carné 2890-22-8567. Presento ReservaFlow, una API de reservas con Node.js, Express y PostgreSQL. Permite consultar disponibilidad, crear reservas y listar resultados con paginación.'),
('0:20–0:45 | Prueba y criterios',
 'Muestra k6/evaluation/load.js y los umbrales en lib.js.',
 'La carga sostenida programa cuarenta operaciones por segundo durante dos minutos: cuarenta por ciento de disponibilidad, treinta de listados y treinta de creaciones. Exigí p95 menor de doscientos milisegundos, errores menores al uno por ciento y todos los checks aprobados. Conservé estos criterios en ambas versiones.'),
('0:45–1:20 | Evidencia antes/después',
 'Muestra la tabla del informe y las consolas v1-load-1 y v2-load-1.',
 'En las dos pruebas de v1, el p95 llegó a unos seis mil milisegundos y los errores rondaron el veintisiete por ciento. Ambas se interrumpieron por seguridad. En v2, el p95 fue de siete punto sesenta y uno y seis punto noventa y seis milisegundos, sin errores ni iteraciones descartadas, con unas cuarenta peticiones por segundo. Los originales están en el repositorio. Los seis segundos de v1 corresponden al timeout; sus ejecuciones fueron parciales.'),
('1:20–1:55 | Hallazgo y corrección',
 'Muestra listV1, listV2 y db/v2_fix.sql.',
 'La hipótesis fue que el listado N más uno causaba la degradación: una página de cincuenta reservas hacía cincuenta y una consultas. Apliqué la alternativa con JOIN e índices, ya incluida en el proyecto de origen, y la verifiqué. También reparé la semilla para generar datos mixtos reproducibles en ambas versiones; mantuve las reglas de capacidad y las mismas condiciones de prueba.'),
('1:55–2:25 | Estrés, recuperación y regresión',
 'Muestra la sección de estrés y los resultados de regresión del informe.',
 'El estrés subió progresivamente hasta cuarenta usuarios virtuales y bajó para observar recuperación. V2 completó el ensayo; en recuperación su p95 fue de doce punto treinta milisegundos. V1 requirió detener el estrés y pasó una prueba posterior segura. La regresión concurrente confirmó seis reservas aceptadas y catorce conflictos, sin sobrecupos.'),
('2:25–2:55 | Límites y cierre',
 'Muestra README, carpeta de resultados y enlace del repositorio.',
 'La comparación usó los mismos datos, límites de contenedores, carga y umbrales, con dos repeticiones por versión. No alcancé saturación de v2 dentro del límite seguro, por lo que no afirmo su capacidad máxima. El repositorio conserva scripts, recursos, resultados originales y pasos para reproducirlos. Gracias.'),
]

d = Document()
s = d.sections[0]
s.top_margin = s.bottom_margin = Inches(.6)
s.left_margin = s.right_margin = Inches(.7)
normal = d.styles['Normal']
normal.font.name = 'Calibri'; normal.font.size = Pt(10)
normal.paragraph_format.space_after = Pt(4)
normal.paragraph_format.line_spacing = 1
for name in ['Title','Heading 1','Heading 2']:
    d.styles[name].font.color.rgb = RGBColor(0,0,0)
d.add_heading('Guion del video | ReservaFlow',0)
d.add_paragraph('Duración objetivo: 2:55. Lee únicamente el texto de narración; las indicaciones de pantalla son para preparar la grabación.')
md = ['# Guion del video | ReservaFlow', '\nDuración objetivo: 2:55. Lee solo la narración.\n']
for title, screen, narration in segments:
    d.add_heading(title,2)
    p=d.add_paragraph('Pantalla: '+screen);p.runs[0].italic=True
    d.add_paragraph(narration)
    md.extend(['## '+title, '\n**Pantalla:** '+screen, '\n'+narration+'\n'])
d.add_page_break()
d.add_heading('Preparación y archivos para mostrar',1)
instructions = [
 'Abre las pestañas y archivos antes de grabar. No necesitas ejecutar otra prueba de estrés durante el video: explica los resultados reales conservados.',
 'Salud: http://localhost:3001/health',
 'Disponibilidad: http://localhost:3001/availability?resourceId=1&date=2026-12-01',
 'Listado: http://localhost:3001/reservations?page=1&pageSize=5&status=confirmed',
 'Carga y checks: k6/evaluation/load.js y k6/evaluation/lib.js.',
 'Consolas: results/evaluacion-2026-11-14/mediciones/v1-load-1.console.txt y v2-load-1.console.txt.',
 'Resumen: results/evaluacion-2026-11-14/mediciones/RESULTADOS.md. El informe Word incluye la tabla comparativa y la recuperación.',
 'Corrección: abre app/src/listing.ts (listV1 y listV2) y db/v2_fix.sql. Aclara que la alternativa v2 ya existía y se aplicó/verificó en esta evaluación.',
 'Regresión: results/evaluacion-2026-11-14/mediciones/v2-functional-final.json.',
 'Repositorio: https://github.com/Ecuyuch/-S15-k6-construir-medir-y-mejorar-una-API',
 'Usa un grabador de pantalla con micrófono. Ensaya una vez y termina antes de 3:00. Amplía los números para que se lean.',
 'Sube el video a una ubicación accesible para el docente, comprueba el enlace sin iniciar sesión y pégalo en el campo VIDEO del informe Word. El archivo se entrega editable, sin PDF, según tu solicitud.',
]
for item in instructions:d.add_paragraph(item,style='List Bullet')
md.extend(['## Preparación y archivos para mostrar','']+['- '+x for x in instructions])
d.core_properties.author='Eddy Gerardo Cuyuch Lopez'
d.save(OUT/'Guion_Video_ReservaFlow.docx')
(OUT/'GUION_VIDEO.md').write_text('\n'.join(md),encoding='utf-8')
print('Guion Word y Markdown generados')
