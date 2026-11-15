"""Deriva tablas del resumen original de k6 y mezcla/fases de la serie original."""
import json, gzip, hashlib, statistics, os
from pathlib import Path
from collections import Counter, defaultdict

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'results'/'evaluacion-2026-11-14'/os.environ.get('CAMPAIGN','mediciones')

def pct(values,p):
    if not values:return None
    v=sorted(values); x=(len(v)-1)*p/100; i=int(x)
    return v[i]+(v[min(i+1,len(v)-1)]-v[i])*(x-i)

def analyze(name):
    summary=json.loads((OUT/(name+'.summary.json')).read_text(encoding='utf-8'))
    meta=json.loads((OUT/(name+'.meta.json')).read_text(encoding='utf-8'))
    m=summary['metrics']; durations=defaultdict(list); counts=Counter(); phases=Counter()
    response_codes=Counter(); points=[]; first_window=[]
    with gzip.open(OUT/(name+'.timeseries.json.gz'),'rt',encoding='utf-8') as f:
        for line in f:
            x=json.loads(line)
            if x.get('type')!='Point':continue
            metric=x.get('metric'); data=x['data']; tags=data.get('tags',{})
            if metric=='http_req_duration':
                durations[tags.get('endpoint','other')].append(data['value'])
                points.append((data['time'],data['value'],tags))
            if metric=='http_reqs':
                counts[tags.get('endpoint','other')]+=data['value']
                phases[tags.get('phase','other')]+=data['value']
                response_codes[tags.get('status','unknown')]+=data['value']
    from datetime import datetime
    start=datetime.fromisoformat(meta['started'].replace('Z','+00:00'))
    for time,value,tags in points:
        t=(datetime.fromisoformat(time.replace('Z','+00:00'))-start).total_seconds()
        if 2<=t<17:first_window.append(value)
    resources=json.loads((OUT/(name+'.resources.json')).read_text(encoding='utf-8'))
    rr=defaultdict(lambda:{'cpu':[],'memory_pct':[],'memory_MiB':[]})
    free=[]
    for sample in resources:
        if 'hostFreeBytes' in sample:free.append(sample['hostFreeBytes']/1024**2)
        for c in sample.get('containers',[]):
            rr[c['Name']]['cpu'].append(float(c['CPUPerc'].rstrip('%')))
            rr[c['Name']]['memory_pct'].append(float(c['MemPerc'].rstrip('%')))
            mem=c['MemUsage'].split('/')[0].strip()
            unit=next((u for u in ['GiB','MiB','KiB','B'] if mem.endswith(u)),None)
            if unit:rr[c['Name']]['memory_MiB'].append(float(mem[:-len(unit)])*{'GiB':1024,'MiB':1,'KiB':1/1024,'B':1/1024**2}[unit])
    failed=[k+': '+expr for k,v in m.items() for expr,bad in v.get('thresholds',{}).items() if bad]
    return dict(name=name,meta=meta,latency=m.get('http_req_duration',{}),error_rate=m.get('http_req_failed',{}).get('value'),
                check_rate=m.get('checks',{}).get('value'),requests=m.get('http_reqs',{}),iterations=m.get('iterations',{}),
                dropped=m.get('dropped_iterations',{}).get('count',0),vus=m.get('vus',{}),
                endpoints={k:{'count':counts[k],'p95':pct(v,95),'p99':pct(v,99),'avg':statistics.mean(v)} for k,v in durations.items()},
                phase_counts=dict(phases),status_codes=dict(response_codes),failed_thresholds=failed,
                recovery={k:v for k,v in m.items() if 'phase:recuperacion' in k or 'phase:base' in k or 'phase:meseta' in k},
                resources={k:{'cpu_avg':statistics.mean(v['cpu']),'cpu_max':max(v['cpu']),
                               'memory_pct_max':max(v['memory_pct']),'memory_MiB_max':max(v['memory_MiB'],default=0)} for k,v in rr.items()},
                host_free_MiB_min=min(free,default=None),resource_samples=len(free),
                early_window_diagnostic={'interval_from_docker_start':'2<=t<17 seconds','samples':len(first_window),'p95':pct(first_window,95),
                                         'note':'Diagnostico exploratorio; ventana de finalizacion desde arranque Docker, no comparación causal equivalente'})

def main():
    runs={}
    for p in OUT.glob('*.meta.json'):
        name=p.name.removesuffix('.meta.json')
        if (OUT/(name+'.summary.json')).exists() and (OUT/(name+'.timeseries.json.gz')).exists():
            runs[name]=analyze(name)
    initial={p.name:json.loads(p.read_text()) for p in OUT.glob('*.initial.json')}
    report={'runs':runs,'initial':initial,'identical_seed':len({x['sha256'] for x in initial.values()})==1}
    (OUT/'analysis.json').write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
    rows=['# Resultados nuevos obtenidos localmente','',
          '| Ensayo | s reales | HTTP | req/s | p95 ms | p99 ms | Error % | Checks % | Descartes | Salida |',
          '|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
    for name,r in runs.items():
        if 'warmup' in name:continue
        rows.append('| '+name+' | '+ ' | '.join([
            f"{r['meta']['seconds']:.1f}",str(r['requests'].get('count',0)),f"{r['requests'].get('rate',0):.2f}",
            f"{r['latency'].get('p(95)',0):.2f}",f"{r['latency'].get('p(99)',0):.2f}",
            f"{100*(r['error_rate'] or 0):.2f}",f"{100*(r['check_rate'] or 0):.2f}",str(r['dropped']),str(r['meta']['exitCode'])])+' |')
    rows.extend(['','Los tiempos incluyen arranque/cierre del contenedor en meta; req/s usa duración interna de k6.',
                 'Las interrupciones conservan el resultado parcial y no equivalen a completar el escenario.',
                 'http_req_duration mide solicitudes completadas, incluidas las fallidas; no incluye solicitudes descartadas.',
                 'La mejora se calcula con repeticiones, sin promediar percentiles como si fueran una muestra combinada.'])
    (OUT/'RESULTADOS.md').write_text('\n'.join(rows)+'\n',encoding='utf-8')
    print('\n'.join(rows))
if __name__=='__main__':main()
