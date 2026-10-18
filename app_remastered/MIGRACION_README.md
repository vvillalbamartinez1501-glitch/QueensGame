# Queens Remastered

La aplicación original permanece intacta en la raíz. Esta versión independiente
se compone de una API FastAPI en `backend/` y un cliente Flutter en `frontend/`.

## Requisitos

- Python 3.10 o superior.
- Flutter SDK y Android SDK configurados (`flutter doctor`).
- Un teléfono o emulador para ejecutar Flutter.

## Iniciar FastAPI en Windows

Desde la raíz del repositorio:

```powershell
cd app_remastered\backend
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --app-dir .. --host 0.0.0.0 --port 8000 --reload
```

La API queda disponible en `http://127.0.0.1:8000` y su documentación interactiva
en `http://127.0.0.1:8000/docs`. Se enlaza a `0.0.0.0` para aceptar conexiones del
emulador y de otros dispositivos de la red.

### Reparar `ImportError: cannot import name 'ArgsKwargs'`

Este error suele indicar que `pydantic` y su extensión compilada `pydantic-core`
quedaron instalados en versiones incompatibles o incompletas. Con el entorno
`.venv` activado, desde `app_remastered\backend`, reinstala los paquetes sin usar
la caché:

```powershell
python -m pip install --upgrade --force-reinstall --no-cache-dir -r requirements.txt
python -c "from pydantic_core import ArgsKwargs; import pydantic; print('Pydantic OK:', pydantic.__version__)"
python -m uvicorn backend.main:app --app-dir .. --host 0.0.0.0 --port 8000 --reload
```

Si la importación sigue fallando, cierra las terminales que estén usando el
entorno, vuelve a la raíz del repositorio y recrea únicamente el entorno virtual
de esta aplicación:

```powershell
deactivate
cd ..\..
Remove-Item -Recurse -Force .\app_remastered\backend\.venv
cd .\app_remastered\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --no-cache-dir -r requirements.txt
python -c "from pydantic_core import ArgsKwargs; import pydantic; print('Pydantic OK:', pydantic.__version__)"
```

## Preparar y ejecutar Flutter

El SDK de Flutter debe estar instalado en Windows y su carpeta `bin` debe estar
en `PATH`. El error `flutter no se reconoce` significa que PowerShell no encuentra
`flutter.bat`; no es un error del código del proyecto.

1. Instala el SDK siguiendo la guía oficial:
   <https://docs.flutter.dev/install/manual>.
2. Extrae el SDK en una ruta sencilla, por ejemplo `C:\src\flutter` (evita
   `Program Files` y rutas con espacios).
3. Añade `C:\src\flutter\bin` a la variable de entorno `Path` de usuario desde
   **Editar las variables de entorno de esta cuenta** → **Path** → **Nuevo**.
   Si lo extrajiste en otra carpeta, añade su ruta `bin` correspondiente.
4. Cierra y vuelve a abrir PowerShell o la terminal de VS Code para que recoja
   el nuevo `Path`. Comprueba la instalación:

```powershell
flutter --version
flutter doctor -v
```

Instala Android Studio y los componentes del Android SDK que indique `flutter
doctor`. Acepta las licencias de Android cuando te lo solicite:

```powershell
flutter doctor --android-licenses
flutter doctor
```

En otra terminal, desde la raíz del repositorio, genera los archivos nativos
Android si aún no existen y descarga los paquetes:

```powershell
Set-Location C:\MisProyectosLocal\QueensGame\app_remastered\frontend
flutter create --platforms=android --project-name queens_remastered .
flutter pub get
```

Para el emulador Android estándar, la app ya usa `http://10.0.2.2:8000` (esa
dirección apunta al host desde el emulador). Ejecuta:

```powershell
flutter run
```

Para un teléfono físico, averigua la IPv4 del equipo donde corre FastAPI con
`ipconfig` y permite conexiones entrantes al puerto 8000 en el firewall. Cambia
la URL al ejecutar Flutter; por ejemplo:

```powershell
flutter run --dart-define=API_BASE_URL=http://192.168.1.25:8000
```

Reemplaza `192.168.1.25` por la dirección IPv4 real del equipo servidor. En
Android, permite HTTP sin TLS para desarrollo local añadiendo
`android:usesCleartextTraffic="true"` al elemento `<application>` de
`android/app/src/main/AndroidManifest.xml`. No uses HTTP ni habilites tráfico
cleartext en una publicación de producción: configura HTTPS y una URL segura.

## Generar APK

Con el backend accesible desde el dispositivo de destino:

```powershell
cd app_remastered\frontend
flutter build apk --release --dart-define=API_BASE_URL=http://192.168.1.25:8000
```

Configura la URL de API que realmente estará disponible para los usuarios (en
producción debe ser HTTPS). El APK universal se genera en
`build\app\outputs\flutter-apk\app-release.apk`.
