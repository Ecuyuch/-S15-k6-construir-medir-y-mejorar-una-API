# Ejecucion local en este equipo

El proyecto se ejecuta con Docker Desktop. La API usa el puerto 3001 y PostgreSQL
el 5433 para convivir con los servicios existentes del equipo.

## Iniciar

Abre PowerShell en esta carpeta y ejecuta:

```powershell
$env:Path = 'C:\Program Files\Docker\Docker\resources\bin;' + $env:Path
$dockerExe = 'C:\Program Files\Docker\Docker\resources\bin\docker.exe'
& $dockerExe compose up -d --build
& $dockerExe compose exec -T db psql -U reserva -d reservaflow -v ON_ERROR_STOP=1 -f /db/v2_fix.sql
```

La configuracion local usa v2 de forma predeterminada. El segundo comando aplica
sus indices de manera idempotente. Los datos se conservan en un volumen de Docker.

## Consultar

- Estado: http://localhost:3001/health
- Reservas: http://localhost:3001/reservations?page=1&pageSize=20
- Disponibilidad: http://localhost:3001/availability?resourceId=1&date=2026-12-01
- PostgreSQL: localhost:5433, base reservaflow, usuario reserva, clave reserva

Es una API backend; no incluye interfaz web en la ruta raiz.

## Detener y volver a iniciar

En la misma sesion de PowerShell:

```powershell
& $dockerExe compose stop
& $dockerExe compose up -d
```

## Ver estado y registros

```powershell
& $dockerExe compose ps
& $dockerExe compose logs --tail 50 api
```

El archivo docker-compose.override.yml conserva los puertos y permite seleccionar
la version mediante APP_VERSION. El archivo docker-compose.yml original se mantiene.

