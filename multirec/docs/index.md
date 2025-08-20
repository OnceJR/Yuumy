# Documentación de Multirec

Bienvenido a la documentación oficial de Multirec. Aquí encontrarás guías
para usuarios, desarrolladores y administradores.

## Guía de usuario

### Instalación

Sigue estos pasos para instalar y ejecutar Multirec en tu equipo:

1. Instala Python 3.11 o superior.
2. Clona este repositorio y navega al directorio raíz.
3. Instala las dependencias con:

   ```bash
   python -m pip install -r requirements.txt
   ```
4. Asegúrate de tener `yt-dlp` y `ffmpeg` en tu `PATH`.
5. Ejecuta la aplicación:

   ```bash
   python -m multirec.app
   ```

### Uso

Al iniciar la aplicación se mostrará un diálogo de consentimiento. Acepta
para continuar. Desde la ventana principal puedes agregar la URL de un canal
para empezar la grabación. El estado de cada sesión se muestra en la tabla.

## Guía de desarrollador

Esta guía explica la estructura del código, cómo ejecutar pruebas y cómo
contribuir.

### Ejecutar pruebas

Las pruebas están ubicadas en el directorio `tests/` y utilizan `pytest`. Para
ejecutarlas, instala las dependencias de desarrollo y lanza:

```bash
pytest
```

### Contribuir

Los parches se aceptan vía pull request. Por favor utiliza mensajes de commit
que sigan el esquema de Conventional Commits y acompaña tus cambios con pruebas
cuando sea posible.