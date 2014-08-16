# Ingeniería de Aplicaciones Web
# Sistema de organización de eventos

## Autores
Ana Laura Muller y Victoria Martínez de la Cruz

## Requerimientos
- [Python 2.7.8] (https://www.python.org/downloads/)
- [MongoDB] (http://www.mongodb.org/downloads)
- [pip] (https://pip.pypa.io/en/latest/installing.html#install-pip)

## Instalación

- Instalar librerías detalladas en requirements.txt, con el comando `pip install -r requirements.txt`

## Ejecución

- En el directorio de la aplicación iniciar el servidor con el comando `python web.py`. Por defecto
será accesible desde `http://localhost:8080`.

## IDE
- [PyCharm] (http://www.jetbrains.com/pycharm/download/)

## Cambios a agregar en próximas versiones

- Ocultar eventos y charlas expirados de forma que los usuarios sólo vean eventos próximos a realizarse.
  Los eventos y charlas ya expirados, sin embargo, podrán accederse a través del permalink.
- Registro 'intermedio' de usuarios invitados permitiendo que confirmen la invitación a un evento sin
  necesidad de completar el formulario de registro.
- Posibilidad de usar la aplicación usando las credenciales de redes sociales populares (e.g. Facebook, Twitter, Google)
- Integración de Google Maps. Sustitución de los vínculos usados para indicar el lugar de un evento por mapas embebidos.
- Carga automática de invitados. El organizador del evento podría realizar su lista de invitados en una planilla o XML
  y cargar los datos de sus invitados en masa.
- Opción de embeber un determinado evento en sitios externos.
- Agregar soporte para i18n.
- TBD.

## Cambios posteriores a la defensa
- Agregamos un campo *Name* obligatorio al formulario de invitación de usuarios (tanto para eventos como para charlas).
  Los usuarios pueden ser identificados por su nombre y no sólo por su email, mejorando la experiencia de usuario.
- Incluimos el theme [Simplex] (http://bootswatch.com/simplex/). El nuevo estilo sigue siendo responsivo pero con un
  diseño más atractivo que la versión anterior.
- Eliminamos algunas opciones del editor WYSIWYG para los *Summaries* tanto de los eventos como de las charlas. El *summary*
  debe ser un texto corto sin información multimedia.
- Se organizó el listado de presentadores y asistentes de un evento o charla en filas de tres usuarios. Con esto facilitamos la
  navegación de los mismos en eventos con gran cantidad de asistentes.


