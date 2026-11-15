"""Crea el informe editable exclusivamente a partir de resultados locales."""
import json, re, math, textwrap, hashlib
from pathlib import Path
from datetime import datetime, timezone, timedelta
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'results/evaluacion-2026-11-14/mediciones'
OUT=ROOT/'output'; OUT.mkdir(exist_ok=True)
FIG=OUT/'evidencias'; FIG.mkdir(exist_ok=True)
A=json.loads((DATA/'analysis.json').read_text(encoding='utf-8'))
E=json.loads((DATA/'environment.json').read_text(encoding='utf-8'))
M=json.loads((DATA/'code-manifest.json').read_text(encoding='utf-8'))
RUNS=A['runs']
def r(name):return RUNS[name]
def f(x,n=2):return 'sin muestra' if x is None else f'{x:,.{n}f}'
def metric(name,key):return r(name)['latency'].get(key)
def pct(x):return f(100*x)+'%'
def status(x):return 'Aprobado' if x['meta']['exitCode']==0 else 'Interrumpido / falla'
def png_console(name,filename):
    raw=(DATA/(name+'.console.txt')).read_text(encoding='utf-8')
    raw=re.sub(r'\x1b\[[0-9;]*m','',raw)
    lines=raw.splitlines()
    selected=[]
    # Conservar métricas y umbrales de la consola, sin modificar números.
    needles=('p(95)','p(99)','http_req_failed','checks','http_reqs','dropped_iterations','thresholds on metrics',
             'test run was aborted','Insufficient VUs','insufficient VUs')
    for line in lines:
        if any(x in line for x in needles):
            selected.extend(textwrap.wrap(line.strip(),width=103,replace_whitespace=False) or [''])
    selected=selected[:18]
    font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',20)
    title=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',27)
    img=Image.new('RGB',(1400,100+30*len(selected)), '#f5f7fa')
    d=ImageDraw.Draw(img); d.text((28,20),name+' | salida original de k6',fill='#142b44',font=title)
    for i,line in enumerate(selected):d.text((28,78+i*30),line,fill='#171c22',font=font)
    img.save(FIG/filename)
def chart():
    names=['v1-load-1','v1-load-2','v2-load-1','v2-load-2']
    img=Image.new('RGB',(1400,650),'white');d=ImageDraw.Draw(img)
    ft=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',25)
    fb=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',30)
    d.text((50,20),'Latencia p95 en carga de 40 operaciones por segundo',fill='black',font=fb)
    left,bottom,top=180,540,100
    values=[max(metric(n,'p(95)'),.1) for n in names]
    ymax=max(10000,10**math.ceil(math.log10(max(values))))
    def y(v):return bottom-(math.log10(max(v,.1))+1)/(math.log10(ymax)+1)*(bottom-top)
    for tick in [.1,1,10,100,1000,10000]:
        if tick>ymax:continue
        yy=y(tick);d.line((left,yy,1330,yy),fill='#d8dce2',width=2)
        d.text((45,yy-14),str(tick)+' ms',fill='#333333',font=ft)
    yy=y(200);d.line((left,yy,1330,yy),fill='#778899',width=3)
    d.text((1060,yy-31),'Meta 200 ms',fill='#555555',font=ft)
    for i,(name,v) in enumerate(zip(names,values)):
        x=250+i*265; yy=y(v)
        d.rectangle((x,yy,x+150,bottom),fill='#a63838' if name.startswith('v1') else '#247562')
        d.text((x-10,yy-35),f(v)+' ms',fill='black',font=ft)
        d.text((x-6,bottom+15),name,fill='black',font=ft)
    d.text((50,602),'Escala logarítmica. Una interrupción de v1 no equivale a completar los 120 segundos.',fill='#555555',font=ft)
    img.save(FIG/'comparacion_p95.png')

D=Document()
sec=D.sections[0];sec.top_margin=Inches(.65);sec.bottom_margin=Inches(.65)
sec.left_margin=Inches(.75);sec.right_margin=Inches(.75)
sec.page_width=Inches(8.5);sec.page_height=Inches(11)
normal=D.styles['Normal'];normal.font.name='Calibri';normal.font.size=Pt(10.5)
normal.paragraph_format.space_after=Pt(6);normal.paragraph_format.line_spacing=1.1
for name,size in [('Title',25),('Subtitle',13),('Heading 1',17),('Heading 2',12)]:
    s=D.styles[name];s.font.name='Calibri';s.font.size=Pt(size);s.font.color.rgb=RGBColor(0,0,0)
    s.paragraph_format.space_after=Pt(9)
D.core_properties.author='Eddy Gerardo Cuyuch Lopez'
D.core_properties.title='Evaluación de rendimiento de ReservaFlow'
D.core_properties.subject='Carga estrés recuperación y comparación de dos versiones'
def p(text='',style=None):return D.add_paragraph(text,style)
def h(text):D.add_heading(text,1)
def sub(text):D.add_heading(text,2)
def page(title):D.add_page_break();h(title)
def code(text):
    pp=p();pp.paragraph_format.space_after=Pt(6)
    rr=pp.add_run(text);rr.font.name='Consolas';rr.font.size=Pt(8.3)
    return pp
def table(headers,rows,widths=None):
    t=D.add_table(rows=1, cols=len(headers));t.alignment=WD_TABLE_ALIGNMENT.CENTER;t.autofit=False
    if widths:
        for c,w in zip(t.columns,widths):c.width=Inches(w)
    for i,x in enumerate(headers):t.rows[0].cells[i].text=str(x)
    for row in rows:
        cells=t.add_row().cells
        for i,x in enumerate(row):cells[i].text=str(x)
    for ri,row in enumerate(t.rows):
        trPr=row._tr.get_or_add_trPr()
        if ri==0:trPr.append(OxmlElement('w:tblHeader'))
        trPr.append(OxmlElement('w:cantSplit'))
        for ci,c in enumerate(row.cells):
            if widths:c.width=Inches(widths[ci])
            c.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tcPr=c._tc.get_or_add_tcPr();b=OxmlElement('w:tcBorders')
            for edge in ['top','left','bottom','right']:
                z=OxmlElement('w:'+edge);z.set(qn('w:val'),'single');z.set(qn('w:sz'),'4');z.set(qn('w:color'),'D9D9D9');b.append(z)
            tcPr.append(b);sh=OxmlElement('w:shd');sh.set(qn('w:fill'),'17324D' if ri==0 else 'F0F4F7' if ri%2 else 'FFFFFF');tcPr.append(sh)
            margins=OxmlElement('w:tcMar')
            for edge in ['top','left','bottom','right']:
                z=OxmlElement('w:'+edge);z.set(qn('w:w'),'75');z.set(qn('w:type'),'dxa');margins.append(z)
            tcPr.append(margins)
            for pp in c.paragraphs:
                pp.paragraph_format.space_after=Pt(3);pp.paragraph_format.space_before=Pt(3);pp.paragraph_format.line_spacing=1.05
                for rr in pp.runs:rr.font.size=Pt(9);rr.font.bold=ri==0;rr.font.color.rgb=RGBColor.from_string('FFFFFF' if ri==0 else '000000')
    p()
def image(file,caption,width=6.8):
    D.add_picture(str(FIG/file),width=Inches(width));pp=p(caption);pp.paragraph_format.space_after=Pt(9)
    for rr in pp.runs:rr.italic=True;rr.font.size=Pt(9)
def link(label,url):
    pp=p();run=pp.add_run(label+' ');run.bold=True
    rel=pp.part.relate_to(url,'http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink',is_external=True)
    x=OxmlElement('w:hyperlink');x.set(qn('r:id'),rel);rr=OxmlElement('w:r');props=OxmlElement('w:rPr');col=OxmlElement('w:color');col.set(qn('w:val'),'175A8C');props.append(col);rr.append(props);tt=OxmlElement('w:t');tt.text=url;rr.append(tt);x.append(rr);pp._p.append(x)

png_console('v1-load-1','consola_v1.png');png_console('v2-load-1','consola_v2.png');chart()
p('Evaluación de rendimiento de ReservaFlow','Title')
p('API de reservas con PostgreSQL','Subtitle')
p('Aseguramiento de la Calidad de Software')
table(['Estudiante','Carné','Fecha del informe'],[['Eddy Gerardo Cuyuch Lopez','2890-22-8567','15 de noviembre de 2026']],[3.4,1.5,2.1])
h('Propósito y resultado')
loads=[r(n) for n in ['v1-load-1','v1-load-2','v2-load-1','v2-load-2']]
v1=[x for x in loads if x['name'].startswith('v1')];v2=[x for x in loads if x['name'].startswith('v2')]
p('Se verificó una API local de reservas, se midieron humo, carga sostenida y estrés, y se comprobó la corrección de acceso a datos disponible en v2. La comparación utiliza la misma demanda configurada de 40 operaciones por segundo, los mismos umbrales y una semilla de 289882 reservas.')
p('La versión v1 obtuvo p95 de '+', '.join(f(x['latency']['p(95)'])+' ms' for x in v1)+
  '; v2 obtuvo '+', '.join(f(x['latency']['p(95)'])+' ms' for x in v2)+'. Los resultados y las interrupciones se detallan en las páginas siguientes; una prueba detenida no cuenta como su duración completa.')
sub('Enlaces de entrega')
link('Repositorio de origen', 'https://github.com/josuesanchez96/ReservaFlowBackend')
p('Repositorio con esta evaluación: AGREGAR EL ENLACE DEL FORK O DE LA RAMA PUBLICADA.')
p('Video de máximo 3 minutos: AGREGAR AQUÍ EL ENLACE ACCESIBLE.')
p('Los cambios y resultados de esta evaluación están en la rama local codex/evaluacion-rendimiento. El origen es público, pero la conexión usada no tiene permiso de escritura; el enlace del origen no prueba que estos cambios estén publicados.')
sub('Alcance y autoría')
p('La implementación de v1, v2 y el parche de índices ya existían en el repositorio de origen. Esta evaluación corrigió la semilla, fortaleció las comprobaciones y obtuvo evidencia local nueva. Los informes históricos se conservan separados y sus cifras no se atribuyen a este equipo.')

page('Aplicación y reproducción')
p('Node.js 20 con Express y TypeScript permite una API pequeña y tipada. PostgreSQL aporta transacciones, restricciones y bloqueo FOR UPDATE para serializar creaciones sobre un recurso. El pool tiene 10 conexiones. Docker fija versiones y separa la base de datos de otros servicios del equipo.')
table(['Operación','Ruta','Comportamiento'],[
['Disponibilidad','GET /availability','Recurso y fecha obligatorios; 12 horarios entre 9 y 20.'],
['Crear reserva','POST /reservations','201 si hay capacidad; 400 inválido; 404 recurso; 409 sobrecupo.'],
['Listado','GET /reservations','Paginación 1..100 filas; orden por fecha e ID descendente; filtro de estado.'],
['Salud','GET /health','Estado del proceso y versión; no valida por sí sola la DB.']],[1.1,1.8,4.1])
p('Regla central: máximo 20 invitados confirmados por recurso, fecha y horario. El nombre debe tener contenido; guests debe ser entero positivo y slot debe estar entre 9 y 20. Las pruebas conservan esas reglas, incluidos los rechazos negativos esperados.')
sub('Instalar e iniciar')
p('Requisitos: Git, Docker Desktop con motor Linux y Compose compatible con !override, y Node.js 22 para el automatizador. El README contiene la ruta completa y los comandos sin abreviar.')
code("git clone https://github.com/josuesanchez96/ReservaFlowBackend.git\ncd ReservaFlowBackend\n$env:Path = 'C:\\Program Files\\Docker\\Docker\\resources\\bin;' + $env:Path\ndocker compose up -d --build\ndocker compose exec -T db psql -U reserva -d reservaflow -f /db/v2_fix.sql\nInvoke-RestMethod http://localhost:3001/health")
sub('Configurar y restablecer')
p('API localhost:3001; PostgreSQL localhost:5433, base reservaflow y credenciales locales reserva/reserva. APP_VERSION selecciona v1 o v2 y requiere recrear solo la API. Los índices son un paso independiente. Los datos persisten en un volumen.')
code("docker compose exec -T db psql -U reserva -d reservaflow -f /db/reset.sql\n# Solo v2: aplicar nuevamente /db/v2_fix.sql\n$env:APP_VERSION='v1'\ndocker compose up -d --no-deps --force-recreate api\n# Detener sin borrar datos: docker compose stop")
p('El restablecimiento elimina solo las tablas de esta API y sus reservas, incluidas las manuales. Se respaldó la DB original antes de restaurar. Para repetir la batería usar una carpeta CAMPAIGN nueva y ejecutar node --expose-gc scripts/benchmark.mjs.')

page('Entorno datos y condiciones equivalentes')
host=E['host'];docker=E['docker']
table(['Componente','Registro real'],[
['Equipo',host['Manufacturer']+' '+host['Model']],
['CPU',host['CPU']+'; '+str(host['Cores'])+' núcleos / '+str(host['LogicalProcessors'])+' hilos'],
['RAM física',f(host['PhysicalMemory']/1024**3)+' GiB'],
['Sistema',host['OS']+' '+host['OSVersion']],
['Docker',docker['ServerVersion']+'; '+docker['KernelVersion']],
['Recursos de WSL',str(docker['NCPU'])+' CPU lógicas; '+f(docker['MemTotal']/1024**3)+' GiB'],
['Generador',E['k6']],
['Contenedores','API 1 CPU / 256 MiB; DB 1 CPU / 512 MiB; k6 1 CPU / 256 MiB'],
['Stack','Node 20 Alpine, Express 4, PostgreSQL 16 Alpine; versiones exactas en environment.json'],
['Código',M['gitCommit'][:12]+'; SHA256 por archivo en code-manifest.json'],
['Semilla','50 recursos; 289882 reservas; ancla fija 2026-11-14'],
['Estados','202731 confirmed; 58091 cancelled; 29060 pending']],[1.45,5.55])
p('Los datos se derivan de MD5 de una clave estable por fila y se insertan en orden fijo. Cada horario sembrado tiene como máximo 3 reservas de hasta 4 invitados. No dependen de la fecha de ejecución ni de random sin correlación.')
p('Antes de cada ensayo se restauraron tablas y secuencias, y se aplicaron índices únicamente a v2. Se comprobó la huella SHA256 de todas las filas restauradas: '+('idéntica en los seis ensayos.' if A['identical_seed'] else 'revisar diferencias en los archivos initial.json.'))
p('Orden de cargas ABBA: v1 primera, v2 primera, v2 segunda, v1 segunda. Con autorización se detuvieron cuatro contenedores del otro proyecto y tres servicios nativos de bases de datos. Se registró su estado para restaurarlos al terminar. Los intentos previos se conservaron separados.')
p('Tras cada restauración se sincronizó y liberó la caché de archivos WSL en ambos grupos; se conservaron los shared_buffers de PostgreSQL. Luego hubo 15 s de calentamiento. Se eliminaron sus escrituras, se restableció la secuencia y se ejecutó ANALYZE. No es una prueba de caché totalmente fría.')

page('Plan previo escenarios y umbrales')
p('La demanda de 40 operaciones/s es una hipótesis académica local, no tráfico productivo observado. Se eligió por los 8 GB del equipo y se mantuvo en ambas versiones. Cada iteración de carga equivale a una petición: 40% disponibilidad, 30% listado y 30% creación, distribuidas por índice global módulo 10.')
table(['Escenario','Perfil','Duración'],[
['Humo','1 VU con pausas de 1 s; salud y pruebas negativas','30 s'],
['Carga','constant-arrival-rate, 40 it/s, 60 VUs preasignadas y máximas','120 s, dos veces por versión'],
['Estrés','2/10/20/40/40/2/2/0 VUs; pausa 0.25 s','20/25/25/20/20/10/50/10 s'],
['Recuperación integrada','2 VUs después del descenso','50 s'],
['Recuperación posterior','1 VU, pausa 0.5 s, si estrés se interrumpe','30 s sin reiniciar API ni DB']],[1.25,3.8,1.95])
table(['Ámbito','Criterio de aprobación'],[
['Carga global','p95 <200 ms; p99 <500 ms; errores <1%; checks=100%; descartes=0'],
['Disponibilidad','p95 <150 ms'],
['Listado y creación','p95 <250 ms cada uno'],
['Humo','checks=100%; errores=0%; p95 <2000 ms'],
['Recuperación','p95 <300 ms; errores <1%; más de 20 peticiones en fase integrada']],[1.65,5.35])
p('Los 200 ms son una meta interactiva propuesta que deja margen al cliente y la red. El p99 de 500 ms limita la cola larga, y errores<1% fija un presupuesto. Son criterios previos de aceptación, no garantías universales. No se modificaron después de observar los resultados.')
sub('Límites y parada')
p('Solo se usa la API propia en red Docker local. Timeout HTTP de 6 s. AbortOnFail si errores alcanzan 10% o p99 alcanza 5000 ms después de 30 s. El monitor toma muestras cada 5 s; tres muestras con RAM libre del host<400 MiB o memoria de contenedor>90% detienen el generador. Preflight exige al menos 500 MiB libres.')
p('Si hay interrupción se conservan resumen, consola y motivo; se verifica recuperación con una prueba posterior segura, sin reiniciar servidor. No se exige saturar v2 más allá de 40 VUs ni bloquear el equipo.')

page('Hallazgo hipótesis y corrección')
sub('Defecto de reproducibilidad detectado')
p('La DB inicial contenía 325800 reservas cancelled y ninguna confirmed. La subconsulta LATERAL con random no referenciaba la fila externa; podía evaluarse una sola vez. El listado de confirmed quedaba vacío y su check solo exigía un arreglo, ocultando el problema.')
p('scripts/check-seed.mjs falló con esa distribución. Se reemplazó random por hashes de una clave recurso/fecha/horario/ordinal y se fijaron fechas y orden. La prueba pasó con tres estados y volumen representativo. Esta reparación es común a v1 y v2; no es la variable de optimización del experimento.')
sub('Problema de rendimiento verificado')
p('En v1, listV1 ejecuta la consulta paginada y luego una consulta por recurso: 51 consultas para una página de 50 filas. No existen índices de filtro u orden. Las lecturas de disponibilidad y validación de capacidad también deben recorrer reservas sin el índice compuesto.')
p('Hipótesis: un JOIN único y los índices de filtro/orden reducirán trabajo SQL y cola del pool, conservarán los resultados y permitirán sostener la misma demanda. Esta hipótesis se prueba con las versiones ya disponibles en el repositorio, sin modificar reglas de negocio.')
code("SELECT r.*, rs.name AS resource_name\nFROM reservations r JOIN resources rs ON rs.id=r.resource_id\nWHERE r.status='confirmed'\nORDER BY r.reservation_date DESC,r.id DESC LIMIT 50;")
p('v2 activa listV2 y aplica db/v2_fix.sql: índice de búsqueda por recurso/fecha/horario/estado con INCLUDE(guests), índice por estado/fecha/ID e índice por fecha/ID. La consulta de listado pasa de 51 viajes SQL a uno.')
def explain_ms(version):
    text=(DATA/(version+'-explain.txt')).read_text()
    found=re.search(r'Execution Time: ([0-9.]+) ms',text)
    return float(found.group(1)) if found else None
table(['Diagnóstico SQL aislado','v1 sin índices','v2 con índices'],[
['EXPLAIN ANALYZE página 10',f(explain_ms('v1'))+' ms',f(explain_ms('v2'))+' ms'],
['Consultas por listado de 50','51 según listV1','1 según listV2']],[3.4,1.8,1.8])
p('Los planes completos con BUFFERS están en v1-explain.txt y v2-explain.txt. Son diagnósticos de una consulta aislada; no sustituyen la latencia HTTP bajo carga ni separan por sí solos el efecto individual del JOIN y de cada índice.')

page('Carga sostenida y comparación')
table(['Ensayo','Duración s','HTTP','req/s','p95 ms','p99 ms'],[
 [x['name'],f(x['meta']['seconds'],1),x['requests']['count'],f(x['requests']['rate']),f(x['latency']['p(95)']),f(x['latency']['p(99)'])] for x in loads],[1.3,1.1,1,1,1.3,1.3])
table(['Ensayo','Error HTTP','Checks','Descartes','Estado'],[
 [x['name'],pct(x['error_rate']),pct(x['check_rate']),x['dropped'],status(x)] for x in loads],[1.3,1.2,1.1,1.1,2.3])
image('comparacion_p95.png','Figura 1. Percentiles de cada ejecución original, sin promediar percentiles ni ocultar interrupciones.')
if any(x['meta']['seconds']<110 for x in v1):
    p('v1 se detuvo antes de completar 120 s. La comparación conserva la misma demanda ofrecida y los límites, pero difiere en duración y volumen completado. La reducción de percentiles describe los ensayos observados; no es una estimación causal sin sesgos ni una comparación de 4800 peticiones completadas en ambos grupos.')
else:
    p('Ambas versiones completaron las cargas de 120 s con condiciones configuradas equivalentes. Los percentiles se presentan por repetición, sin tratarlos como una muestra agregada.')
for label,items in [('v1',v1),('v2',v2)]:
    vals=[x['latency']['p(95)'] for x in items]
    p('Variación de '+label+': p95 entre '+f(min(vals))+' y '+f(max(vals))+' ms; amplitud relativa al menor '+f((max(vals)-min(vals))/min(vals)*100)+'%. Dos repeticiones permiten describir variación, pero no inferir significancia estadística.')

page('Operaciones recursos y lectura crítica')
table(['Operación','v1 primera p95','v1 segunda p95','v2 primera p95','v2 segunda p95'],[
 [ep]+[f(x['endpoints'].get(ep,{}).get('p95'))+' ms' for x in loads] for ep in ['availability','list','create']],[1.3,1.425,1.425,1.425,1.425])
table(['Ensayo','CPU DB máx','RAM DB máx','CPU k6 máx','RAM libre mín'],[
 [x['name'],f(x['resources'].get('reservaflow-db',{}).get('cpu_max'))+'%',
 f(x['resources'].get('reservaflow-db',{}).get('memory_MiB_max'))+' MiB',
 f(x['resources'].get('reservaflow-k6-eval',{}).get('cpu_max'))+'%',
 f(x['host_free_MiB_min'])+' MiB'] for x in loads],[1.3,1.35,1.45,1.35,1.55])
p('Docker expresa 100% CPU aproximadamente como un núcleo lógico. El límite es 1 CPU por contenedor; las muestras instantáneas pueden exceder ligeramente 100% por el intervalo. RAM proviene de docker stats y no es RSS puro. El muestreo cada 5 s puede omitir picos breves; datos completos de API, DB y generador están en resources.json.')
p('dropped_iterations son iteraciones que k6 no inició; no son respuestas HTTP 500 ni pérdida de paquetes. Con arrival-rate aparecen cuando no hay VUs libres. Se deben leer junto a duración de iteración, 60 VUs máximas, CPU/RAM del generador, timeouts y recursos DB. El host compartido y la instrumentación también añaden variación.')
p('Las latencias agregadas solo incluyen peticiones emitidas y finalizadas, incluidas las que fallan; las operaciones descartadas no tienen latencia. La mezcla completada puede diferir del 40/30/30 programado si hay descartes o aborto. Los estados HTTP y conteos por operación se derivan de la serie JSON original.')
for x in loads:
    counts={k:v['count'] for k,v in x['endpoints'].items()}
    p(x['name']+': mezcla completada '+', '.join(k+'='+str(v) for k,v in counts.items())+
      '; estados '+str(x['status_codes'])+'.',None)
p('Los primeros intentos en la carpeta superior se interrumpieron por RAM con otros servicios activos. No se mezclan con esta campaña, realizada con esos cuatro contenedores detenidos. No se atribuye la mejora exclusivamente al servidor a partir de los descartes.')

page('Estrés recuperación e integridad')
stress=[r('v1-stress'),r('v2-stress')]
table(['Ensayo','Duración s','HTTP','p95 ms','p99 ms','Salida'],[
 [x['name'],f(x['meta']['seconds'],1),x['requests']['count'],f(x['latency']['p(95)']),f(x['latency']['p(99)']),x['meta']['exitCode']] for x in stress],[1.3,1.1,1.1,1.3,1.3,.9])
for x in stress:
    sub(x['name'])
    rec=x['recovery'];dur=rec.get('http_req_duration{phase:recuperacion}',{})
    p('Fases con peticiones: '+', '.join(k+'='+str(v) for k,v in x['phase_counts'].items())+'.')
    if x['phase_counts'].get('recuperacion',0)>0:
        p('Recuperación integrada: p95 '+f(dur.get('p(95)'))+' ms; '+
          str(x['phase_counts']['recuperacion'])+' peticiones. Estado general: '+status(x)+'.')
    else:p('No se alcanzó la fase integrada de recuperación; no se interpreta un percentil vacío como aprobación.')
    safe=RUNS.get(x['name'].replace('-stress','-recovery-safe'))
    if safe:p('Prueba posterior segura, sin reinicio de API/DB: '+str(safe['requests']['count'])+
              ' peticiones; p95 '+f(safe['latency']['p(95)'])+' ms; errores '+pct(safe['error_rate'])+
              '; '+status(safe)+'. Se retiraron las escrituras k6 para evitar reutilizar combinaciones de capacidad.')
    p('Motivos/umbrales fallidos: '+('; '.join(x['failed_thresholds']) or 'ninguno')+
      ('. Parada de monitor: '+'; '.join(x['meta']['stopReasons']) if x['meta']['stopReasons'] else '')+'.')
p('En un modelo cerrado el rendimiento alcanzado depende de la latencia y las pausas; 40 VUs no equivalen a 40 solicitudes/s. Si v2 completa el máximo sin saturarse, solo demuestra margen hasta ese límite seguro, no capacidad máxima ni ausencia de problemas a mayor escala.')
sub('Regresión funcional')
func=json.loads((DATA/'v2-functional-final.json').read_text())
table(['Comprobación','Resultado'],[[x['name'],'Pasa' if x['pass'] else x.get('error','Falla')] for x in func['results']],[5.5,1.5])
p('La misma regresión se ejecutó en v1 y v2. La prueba concurrente lanza 20 solicitudes de 3 invitados: 6 creaciones y 14 conflictos, total 18 y disponibilidad 2. También verifica 400, 404, páginas no vacías, orden y ausencia de IDs repetidos entre páginas.')
p('Integridad SQL después de cada ensayo: cero grupos con SUM(guests)>20 para reservas confirmed. Los archivos meta.json conservan los conteos; la validación final restaura datos limpios y deja v2 activa.')

page('Evidencias originales y límites')
image('consola_v1.png','Figura 2. Transcripción visual de líneas de la consola original v1-load-1.console.txt. No sustituye el archivo completo.',6.8)
image('consola_v2.png','Figura 3. Transcripción visual de líneas de la consola original v2-load-1.console.txt. Números sin editar.',6.8)
p('Estas imágenes se generan de registros originales para facilitar lectura y trazabilidad; no son fotografías de una terminal. Las capturas de la API y el análisis, cuando se incluyen en la carpeta evidencias, se obtienen del servicio local.')

page('Entrega referencias y video')
sub('Ubicación de los resultados')
p('Raíz local: C:\\Users\\Usuario\\Desktop\\Decimo Semestre\\Aseguramiento de la Calidad de Software\\ReservaFlowBackend.')
p('Campaña principal: results/evaluacion-2026-11-14/mediciones/. Intentos interrumpidos y respaldo: carpeta superior. Las series originales son archivos .timeseries.json.gz, legibles con gzip; contienen puntos, marcas de tiempo y etiquetas por petición.')
table(['Archivo','Contenido'],[
['*.summary.json / *.console.txt','Resumen y salida original de k6, incluidos thresholds y errores.'],
['*.timeseries.json.gz','Puntos originales para percentiles, mezcla, fases y códigos HTTP.'],
['*.resources.json / *.meta.json','CPU/RAM/I/O/PIDs, RAM host, tiempos, salida e integridad.'],
['*.initial.json / measured-start.json','Huella de datos, índices y volumen antes de medir.'],
['environment.json / code-manifest.json','Hardware, versiones, imágenes y SHA256 del código.'],
['v1-explain.txt / v2-explain.txt','Planes SQL con tiempos reales y buffers.'],
['analysis.json / RESULTADOS.md','Análisis derivado, nunca reemplazo de los originales.']],[2.8,4.2])
sub('Guion para video de máximo tres minutos')
p('0:00 a 0:25. Presentar nombre, carné, API y rutas. Abrir /health, disponibilidad y listado en localhost:3001.')
p('0:25 a 1:05. Mostrar k6/evaluation/load.js: 40 it/s, 120 s, mezcla y umbrales. Explicar límite seguro y carpeta de resultados.')
p('1:05 a 1:55. Abrir las consolas reales v1/v2 y comparar p95, errores y rendimiento; explicar toda interrupción, sin presentarla como prueba completa.')
p('1:55 a 2:30. Mostrar listV1/listV2 y db/v2_fix.sql. Explicar 51 consultas frente a una e índices; señalar que la corrección ya venía en la base del proyecto.')
p('2:30 a 2:55. Mostrar recuperación y regresión concurrente. Declarar límites de hardware, máximo 40 VUs y dos repeticiones. Finalizar antes de 3:00.')
sub('Pasos pendientes de publicación')
p('Publicar la rama local y sus resultados en un fork o repositorio con acceso de lectura. Sustituir el enlace de la primera página, grabar el video, comprobar ambos enlaces sin autenticación y exportar este Word actualizado a PDF.')
sub('Referencias oficiales')
link('Umbrales de k6','https://grafana.com/docs/k6/latest/using-k6/thresholds/')
link('Iteraciones descartadas','https://grafana.com/docs/k6/latest/using-k6/scenarios/concepts/dropped-iterations/')
link('Recuperación de memoria WSL','https://devblogs.microsoft.com/commandline/memory-reclaim-in-the-windows-subsystem-for-linux-2/')

# Numeración discreta de páginas.
for section in D.sections:
    pp=section.footer.paragraphs[0];pp.alignment=WD_ALIGN_PARAGRAPH.RIGHT
    rr=pp.add_run('ReservaFlow  |  ');rr.font.size=Pt(8)
    field=OxmlElement('w:fldSimple');field.set(qn('w:instr'),'PAGE');pp._p.append(field)
path=OUT/'Informe_ReservaFlow_Eddy_Cuyuch.docx'
D.save(path)
print(path)

