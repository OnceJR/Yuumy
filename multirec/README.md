# Multirec – Grabador de streams múltiples

Multirec es una aplicación de escritorio multiplataforma para grabar varios
streams en simultáneo de Chaturbate (y otras fuentes compatibles con
`yt-dlp`). Está diseñada para usuarios no técnicos que necesitan capturar
contenido de manera robusta y organizada. Se basa en `yt‑dlp` para
descargar los fragmentos HLS/TS y utiliza `ffmpeg` para remuxear los
archivos a MP4 de forma eficiente.

## Características

- **Grabaciones concurrentes**: admite varias sesiones de captura al mismo
  tiempo respetando un límite de concurrencia configurable.
- **Interfaz moderna**: ventana principal con tabla de sesiones y barra de
  herramientas para agregar nuevas streams.
- **Remux sin pérdidas**: los archivos se remuxean a MP4 con `ffmpeg -c copy`.
- **Consentimiento de uso**: al iniciar se muestra un diálogo recordando el
  uso responsable y la necesidad de respetar términos de servicio.

## Instalación

1. Instala las dependencias de Python (usa `python -m pip install -r requirements.txt`).
2. Asegúrate de tener `yt-dlp` y `ffmpeg` en tu `PATH`.
3. Ejecuta la aplicación con:

   ```bash
   python -m multirec.app
   ```

## Estructura del proyecto

```
multirec/
├── app.py                # Punto de entrada de la aplicación
├── multirec/
│   ├── __init__.py
│   ├── config/           # Carga y validación de configuración
│   ├── db/               # Acceso a base de datos SQLite
│   ├── recorder/         # Lógica de grabación y remux
│   ├── scheduler/        # Planificador de tareas concurrentes
│   ├── ui/               # Interfaz de usuario PySide6
│   ├── utils/            # Utilidades como logging
│   ├── services/         # Servicios auxiliares (por implementar)
│   ├── storage/          # Gestión de rutas y espacio (por implementar)
│   └── assets/           # Recursos (iconos, QSS, etc.)
├── tests/                # Pruebas automáticas (pytest)
├── docs/                 # Documentación (mkdocs)
└── requirements.txt
```

## Uso responsable

Esta herramienta está destinada únicamente a grabar contenido sobre el cual
tienes permiso para hacerlo. Respeta siempre los términos de servicio de las
plataformas y las leyes de tu país. **No utilices Multirec para infringir
derechos de autor ni para evadir protecciones de DRM.**

## Próximos pasos

Este repositorio incluye un esqueleto funcional que permite añadir streams y
comenzar descargas básicas. Sin embargo, quedan por implementar múltiples
funcionalidades descritas en el archivo de requerimientos (configuración
avanzada, división por segmentos, reintentos con backoff, estadísticas,
interfaz completa, empaquetado, pruebas, etc.). Se invita a la comunidad a
contribuir con mejoras y ampliaciones respetando el diseño modular.