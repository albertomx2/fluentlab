# FluentLab

Proyecto personal para practicar inglés con gramática graduada, vocabulario propio y tarjetas de repaso. Este repositorio muestra el código del proyecto: **no es un servicio público ni un despliegue de producción**. No incluye datos personales, corpus reales ni direcciones de una instalación privada.

## Funcionalidades

- Nivel de trabajo B1, B2, C1 y C2.
- Zero, first, second y third conditional; mixed conditionals en ambas direcciones; inversión y construcciones avanzadas.
- Ejercicios de completar, identificar, transformar y distinguir el tiempo de la condición y del resultado, con corrección y explicación.
- Corpus de palabras y expresiones: admite `to whisk`, phrasal verbs, idioms y collocations.
- Definiciones, pronunciación cuando está disponible, ejemplos y clasificación gramatical.
- Enriquecimiento mediante Ollama, práctica de vocabulario y tarjetas con programación sencilla de repasos.
- Estadísticas y algunas plantillas de gramática que incorporan vocabulario del corpus.

Los niveles CEFR son estimaciones orientativas, no una certificación. La IA puede equivocarse. El banco de ejercicios es limitado y necesita revisión pedagógica; no se generan lecciones ilimitadas.

## Arquitectura

| Componente | Tecnología | Función |
|---|---|---|
| Interfaz | HTML, CSS y JavaScript | Lecciones, corpus y tarjetas |
| Aplicación | Python 3.13 + FastAPI | API, corrección y archivos estáticos |
| Persistencia | SQLite | Vocabulario, intentos y progreso |
| IA local | Ollama + `qwen2.5:1.5b` | Clasificación, definición y ejemplo |
| Fuentes externas | Free Dictionary API y Datamuse | Información léxica y frecuencia |

## Probar localmente

Necesitas Docker con Docker Compose y conexión a Internet para descargar las imágenes, dependencias y el modelo inicial.

```bash
git clone https://github.com/albertomx2/fluentlab.git
cd fluentlab
docker compose config --quiet
docker compose up -d --build
docker compose logs -f model-init
```

Abre [http://localhost:8082](http://localhost:8082). El puerto se vincula solo a `127.0.0.1`. Es normal que `model-init` termine tras descargar el modelo. Mientras no esté disponible, la aplicación puede utilizar el respaldo del diccionario.

```bash
docker compose ps
docker compose logs --tail=50 fluentlab
curl http://localhost:8082/api/ai/status
```

`OLLAMA_URL` y `OLLAMA_MODEL` se definen en `compose.yml`. Si cambias el modelo, cambia también la descarga de `model-init`. Ollama no publica su puerto al host. La velocidad de inferencia depende de CPU, RAM y GPU; la interfaz no requiere GPU.

## Datos y backups

`fluentlab_data` guarda SQLite en `/data/english-lab.db`; `fluentlab_models` contiene los modelos. Git excluye bases de datos, backups y archivos de entorno.

Para copiar SQLite sin escrituras concurrentes:

```bash
docker compose stop fluentlab
docker compose cp fluentlab:/data/english-lab.db ./fluentlab-backup.db
docker compose start fluentlab
```

Guarda la copia fuera del equipo y comprueba su recuperación. `docker compose down` conserva los volúmenes; **`docker compose down -v` borra los datos**.

## Privacidad y límites de seguridad

Esta versión **no tiene autenticación ni separación entre usuarios**. Todos los visitantes comparten el corpus y pueden modificarlo. No la expongas a Internet con datos reales sin desarrollar control de acceso. Publicar este código no publica una instalación privada; no hay una demo enlazada ni despliegue automático.

Aunque la inferencia sea local, **no es una aplicación completamente offline**: las consultas de vocabulario se envían a Free Dictionary API y Datamuse; la interfaz también carga fuentes desde Google Fonts. No introduzcas información confidencial sin revisar estas conexiones.

Consulta [SECURITY.md](SECURITY.md) para comunicar fallos sensibles.

## Desarrollo

`LESSONS` y `EXERCISES`, en `app.py`, contienen las lecciones y ejercicios. Mantén identificadores únicos y verifica niveles, fórmulas y respuestas.

```bash
python -m unittest discover -s tests -v
python -m compileall -q app.py
node --check static/app.js
```

Las pruebas actuales comprueban el banco estático, no toda la interfaz ni la inferencia. Consulta [CONTRIBUTING.md](CONTRIBUTING.md).

## Siguientes mejoras

- Autenticación y perfiles independientes.
- Más ejercicios y revisión pedagógica de los niveles.
- Exportación/importación del corpus y edición de resultados de IA.
- Pruebas de integración y dependencias de contenedor fijadas por versión o digest.

## Créditos y licencia

[Free Dictionary API](https://dictionaryapi.dev/), [Datamuse](https://www.datamuse.com/api/) y [Ollama](https://github.com/ollama/ollama) tienen sus propias condiciones. Revisa la licencia del modelo antes de redistribuirlo.

El código propio todavía no declara una licencia de reutilización. Publicar el repositorio no concede automáticamente una licencia open source.
