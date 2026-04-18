# Despliegue en Render

## 1. Subir el proyecto

Sube este repositorio a GitHub con estos archivos incluidos:

- `app.py`
- `requirements.txt`
- `render.yaml`
- `runtime.txt`
- `artifacts/`
- `templates/`
- `static/`

## 2. Crear el servicio

1. Entra a Render.
2. Elige `New +`.
3. Selecciona `Blueprint`.
4. Conecta tu repositorio de GitHub.
5. Render detectara `render.yaml` y creara:
   - una base de datos PostgreSQL
   - un servicio web Python

## 3. Variables obligatorias

Antes del primer deploy, configura estas variables en Render:

- `ADMIN_EMAIL`
- `ADMIN_PASSWORD`

Variables que ya quedan resueltas desde `render.yaml`:

- `DATABASE_URL`
- `DB_SSLMODE`
- `FLASK_SECRET_KEY`
- `ADMIN_NAME`
- `PYTHON_VERSION`

## 4. Inicio de sesion inicial

Cuando termine el deploy:

- correo: el valor de `ADMIN_EMAIL`
- clave: el valor de `ADMIN_PASSWORD`

## 5. Si algo falla

Revisa los logs de Render. Los errores mas comunes son:

- Falta `ADMIN_EMAIL` o `ADMIN_PASSWORD`
- La base de datos aun no termina de crearse
- El deploy no incluyo la carpeta `artifacts/`
