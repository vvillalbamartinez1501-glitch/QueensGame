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
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn backend.main:app --app-dir .. --host 0.0.0.0 --port 8000 --reload
```

La API queda disponible en `http://127.0.0.1:8000` y su documentación interactiva
en `http://127.0.0.1:8000/docs`. Se enlaza a `0.0.0.0` para aceptar conexiones del
emulador y de otros dispositivos de la red.

### Retomar proyecto ya iniciado

```powershell
cd app_remastered\backend
.\.venv\Scripts\Activate.ps1
python -m uvicorn backend.main:app --app-dir .. --host 0.0.0.0 --port 8000 --reload
```

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

## Ejecutar la app con `flutter run`

Flutter debe compilar el cliente y tener un dispositivo de destino disponible.
Deja FastAPI corriendo en una primera terminal y, en una segunda, entra en el
directorio Flutter:

```powershell
Set-Location C:\MisProyectosLocal\QueensGame\app_remastered\frontend
flutter devices
```

`flutter devices` muestra emuladores y teléfonos conectados. Si no aparece
ninguno, inicia un emulador desde Android Studio (**Device Manager**) o conecta
un teléfono con la depuración USB habilitada. En el teléfono acepta el diálogo
de autorización que aparece al conectarlo. El primer `flutter run` compila la
app; puede tardar más porque descarga y prepara las dependencias y herramientas
de Android. Mientras siga ejecutándose, la terminal muestra los registros:
pulsa `r` para hot reload, `R` para reiniciar la app y `q` para detenerla.

### Ejecutar en un emulador Android

El emulador Android estándar tiene su propia red virtual. Para llegar al PC que
ejecuta FastAPI debe usar `10.0.2.2`, no `localhost`: `localhost` dentro del
emulador se refiere al propio emulador. El valor predeterminado del cliente ya es
`http://10.0.2.2:8000`, así que, con la API en marcha, ejecuta:

```powershell
flutter run
```

Si tienes varios destinos, elige el identificador mostrado por `flutter
devices` y sustituye el ejemplo por ese valor:

```powershell
flutter run -d emulator-5554
```

Comprueba primero la API abriendo `http://127.0.0.1:8000/docs` en el PC. Si el
juego muestra un error de conexión, confirma que Uvicorn sigue activo en el
puerto 8000 y que has seleccionado el emulador correcto.

### Ejecutar en un teléfono Android físico

El teléfono y el PC que ejecuta FastAPI deben estar conectados a la misma red
local (por ejemplo, al mismo Wi-Fi). En el PC, ejecuta `ipconfig` y busca la
dirección **Dirección IPv4** del adaptador que realmente usa esa red, por
ejemplo el adaptador Wi-Fi; no uses la dirección de un adaptador desconectado,
VPN o `127.0.0.1`. Esa dirección es la IP local del servidor, no una dirección
IPTV ni una lista de canales.

Sustituye `192.168.1.25` por esa IPv4 real. Permite que Python/Uvicorn acepte
conexiones privadas en el firewall de Windows para el puerto TCP 8000, si
Windows solicita permiso. Luego ejecuta desde `frontend`:

```powershell
flutter run --dart-define=API_BASE_URL=http://192.168.1.25:8000
```

`--dart-define` fija la dirección de la API al compilar esta ejecución. No
incluyas `/docs` al final: la app agrega rutas como `/api/games` por sí misma.
Para confirmar la conectividad, abre `http://192.168.1.25:8000/docs` en el
navegador del teléfono. Si no carga, revisa que ambos equipos estén en la misma
red, que Uvicorn se haya iniciado con `--host 0.0.0.0` y que el firewall permita
el puerto.

Esta dirección suele cambiar al reconectar el PC a la red. Para uso continuo,
reserva una IP local en el router o configura la dirección que corresponda a la
red de destino. No abras el puerto 8000 de tu router a Internet para probar la
app: para acceso público despliega la API con HTTPS y usa su dominio.

En desarrollo, el manifiesto Android de la variante debug permite HTTP sin TLS;
esta excepción no se aplica al APK release. No habilites tráfico cleartext en
una publicación. Para distribuir la app, configura una API accesible por HTTPS.

### ¿De dónde obtener IPTV?

Esta aplicación es el juego Queens; no reproduce televisión ni consume listas
IPTV, por lo que no necesita una fuente IPTV. Si con “IPTV” querías decir la IP
del PC para conectar el teléfono, sigue el apartado anterior. Si realmente
quieres añadir canales IPTV, es una funcionalidad distinta: necesitarías una
lista o servicio proporcionado legalmente por su operador o titular de derechos;
no viene incluido ni se obtiene de este proyecto.

## Generar e instalar un APK Android

Antes de compilar, decide dónde estará alojada la API a la que se conectará la
app. La URL queda incorporada en el APK al compilar: usa la IPv4 local solo
para pruebas en la misma red y una URL HTTPS pública para distribuirlo. Un APK
con una IP privada como `192.168.1.25` no funcionará para usuarios fuera de esa
red.

Desde el directorio Flutter, ejecuta lo siguiente y cambia la URL de ejemplo
por la de tu API:

```powershell
Set-Location C:\MisProyectosLocal\QueensGame\app_remastered\frontend
flutter pub get
flutter build apk --release --dart-define=API_BASE_URL=https://api.ejemplo.com
```

El proceso genera un APK release universal en
`build\app\outputs\flutter-apk\app-release.apk`. Si aún no tienes un servidor
HTTPS, puedes usar la IP local y HTTP para una prueba conectada al mismo Wi-Fi,
pero no para una instalación de producción.

Para instalarlo con el teléfono conectado y autorizado por ADB:

```powershell
flutter install
```

También puedes copiar `app-release.apk` al teléfono y abrirlo; Android pedirá
autorizar la instalación desde esa fuente. Para actualizar una instalación
existente sin desinstalarla, el APK debe estar firmado con la misma clave que la
versión ya instalada.

**Firma para publicación:** la configuración Android de este proyecto usa la
firma debug incluso para la variante release. Esto sirve para pruebas locales,
pero no para distribuir una versión oficial. Antes de publicar, crea y protege
tu propia clave de firma, configura `signingConfig` release en
`android/app/build.gradle.kts` y vuelve a compilar. No guardes contraseñas ni
claves privadas en el repositorio. Para Google Play suele publicarse un Android
App Bundle en lugar de un APK:

```powershell
flutter build appbundle --release --dart-define=API_BASE_URL=https://api.ejemplo.com
```

## Ejecutar y publicar la versión web

El mismo cliente Flutter puede compilarse para navegador; el backend FastAPI
sigue siendo necesario, porque el juego y los récords los gestiona la API. La
primera vez, crea los archivos de plataforma web y descarga dependencias:

```powershell
Set-Location C:\MisProyectosLocal\QueensGame\app_remastered\frontend
flutter create --platforms=web .
flutter pub get
```

Para probar localmente, deja FastAPI ejecutándose en el mismo PC y lanza Chrome:

```powershell
flutter run -d chrome --dart-define=API_BASE_URL=http://127.0.0.1:8000
```

En este caso el navegador también se ejecuta en el PC, por lo que `127.0.0.1`
es el host correcto. Para servir la versión de desarrollo en tu red y abrirla
desde otro dispositivo, usa el modo `web-server`, escucha en todas las
interfaces y asigna a la API la IPv4 local del PC:

```powershell
flutter run -d web-server --web-hostname 0.0.0.0 --web-port 8080 `
  --dart-define=API_BASE_URL=http://192.168.1.25:8000
```

En el navegador del otro dispositivo abre `http://192.168.1.25:8080` y permite
el puerto 8080 en el firewall si Windows lo solicita. Sustituye ambas
apariciones de `192.168.1.25` por la IPv4 real del PC. La API ya habilita CORS
para permitir las peticiones del navegador durante el desarrollo.

Para generar los archivos estáticos de producción, compila con la URL HTTPS
pública de la API:

```powershell
flutter build web --release --dart-define=API_BASE_URL=https://api.ejemplo.com
```

Flutter deja el sitio listo para servir en `build\web`. Publica **el contenido
de esa carpeta** en un alojamiento de sitios estáticos (por ejemplo, un
servidor web o un servicio de hosting estático) y despliega FastAPI por
separado, en una dirección HTTPS accesible desde el navegador. Configura el
hosting para servir `index.html` como página de entrada. Una página web cargada
por HTTPS no debe llamar a una API HTTP: los navegadores pueden bloquear esa
conexión por contenido mixto.

Para producción, limita CORS en FastAPI a los dominios concretos de tu web en
lugar de permitir cualquier origen. Además, esta API mantiene las partidas en
memoria y escribe los récords en `backend/scoreboard.json`; un reinicio puede
perder partidas activas y un hosting efímero puede no conservar los récords.
Antes de un despliegue público con varios usuarios, planifica almacenamiento
persistente y una estrategia de despliegue adecuada.
