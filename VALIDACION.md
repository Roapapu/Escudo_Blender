# Validación de entrega

Revisión realizada el 21 de octubre de 2026.

## Modelo y materiales

- Validador oficial Khronos `gltf-validator 2.0.0-dev.3.10`: **0 errores, 0 advertencias**. Reporte completo en `validation-gltf.json`.
- **4,272 triángulos**, tres mallas web y tres materiales: Acero, Bronce y Madera.
- GLB autocontenido de **4,571,676 bytes (4.36 MiB)**, con texturas embebidas.
- Todos los primitivos exportados contienen UV y tangentes.
- Cada material contiene Base Color, Metallic/Roughness y Normal. Mapas de datos en Non-Color; color en sRGB.
- Los 30 mapas independientes (tres materiales × dos acabados × cinco archivos, incluyendo ORM) tienen resolución **1024 × 1024**.
- Fuente Blender con 58 piezas editables y mapas empaquetados; revisión adicional en `validation-native.json`.
- Inspección de renders frontal y posterior. Se corrigieron huecos junto al borde y se redujo el relieve excesivo del metal.
- Se trianguló antes de exportar para incluir tangentes explícitas y eliminar los avisos de portabilidad del normal map.

## Página e interacción

- Página pública cargada en navegador Chromium mediante HTTPS.
- Se comprobó la carga del modelo y la habilitación de los tres controles.
- Acero oscuro: el borde cambia a un tono azul gris oscuro y el botón refleja su estado.
- Relieve del bronce: se desactiva y restaura el mapa normal, incluso con el acabado gastado.
- Huella del tiempo: se cargan y aplican las texturas gastadas; conserva acero oscuro y el estado del relieve.
- Combinación comprobada: desgastado + acero oscuro + relieve inactivo; después se restauró el relieve conservando los otros dos ajustes.
- Diseño revisado en escritorio y viewport móvil de **390 × 844**: controles y textos legibles, materiales y descarga accesibles.
- Se ajustó la distancia inicial de cámara para mostrar el escudo completo.
- Etiquetas en español, estados `aria-pressed`, mensajes `aria-live` y estilos de foco para teclado.
- Biblioteca model-viewer 4.4.0 incluida en `vendor/`, sin depender de un CDN durante la visita.
- El despliegue final de GitHub Pages terminó correctamente. Los recursos principales responden HTTP 200 y coinciden con los archivos locales (normalizando los saltos de línea de los archivos de texto).

## Alcance de las comprobaciones

Se probó en Chromium y con emulación de tamaño móvil, no en un teléfono físico ni en Safari. El rendimiento depende del equipo y la conexión. El normal map representa microdetalle procedural; el emblema conserva su volumen geométrico al apagarlo. No se utilizó Substance Painter.

## Repetir la validación

```sh
npm ci
npm run validate
blender --background --python scripts/audit_blend.py
```

La segunda orden de Blender abre y guarda la fuente para dejar una vista inicial cómoda de inspección. El detalle del despliegue puede consultarse en la pestaña Actions del repositorio.
