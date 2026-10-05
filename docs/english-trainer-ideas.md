# Ideas rescatadas de English Trainer

Revisión de `english-trainer` y de su variante `english-trainer-vercel`, realizada antes de retirar el repositorio antiguo. Esto es una lista de diseño, **no funciones recién implementadas en FluentLab**. No se importan corpus personales, hojas de vocabulario, cuentas ni credenciales.

## Mejoras prioritarias

1. **Repaso espaciado más completo.** El antiguo `src/lib/srs.ts` conserva facilidad, intervalo, repeticiones y fecha de próxima revisión. Separar fallo explícito y respuestas Fácil/Medio/Difícil; mostrar solo tarjetas pendientes y probar transiciones de fechas.
2. **Type-it con tolerancia controlada.** `src/lib/fuzzy.ts` normaliza espacios y puntuación y utiliza Levenshtein. Distinguir exacta, cercana e incorrecta sin aceptar como correcto un error gramatical relevante. La comparación de definiciones por palabras compartidas no demuestra equivalencia semántica.
3. **Cloze.** Completar el ejemplo de una palabra, con contexto suficiente para distinguir acepciones. Evitar pistas que revelen siempre la respuesta.
4. **Use-it.** Escribir una frase propia y recibir feedback: gramática, significado y naturalidad, con corrección editable y un aviso de que la IA puede fallar.
5. **Reading personalizado.** Texto que use un conjunto concreto del corpus y preguntas de comprensión; registrar qué palabras se utilizaron realmente. No generar información personal a partir de las palabras.
6. **Listening.** Lectura en voz mediante capacidades del dispositivo, transcripción y preguntas. El modo anterior contemplaba IA/YouTube; los recursos externos y sus derechos deben revisarse.
7. **Rapid Fire.** Sesiones breves de 30/60 segundos, opcionales; no penalizar accesibilidad ni confundir velocidad con dominio.

## Organización y arquitectura

- Explorador del corpus con filtros y configuración de sesiones.
- Importación tabular con validación, previsualización y detección de duplicados; no copiar el dataset antiguo automáticamente.
- Preferencias de tema y estudio; soporte de voz mediante `src/lib/tts.ts` como referencia conceptual.
- La variante Vercel contiene un proxy server-side de OpenRouter. Conservar la idea de separar claves del navegador, **no copiar su CORS como mecanismo de autenticación** ni añadir un proveedor remoto sin una decisión explícita.
- Sincronización de cuentas solo después de diseñar autorización, privacidad y recuperación. FluentLab sigue siendo un corpus compartido sin login.

## Orden propuesto

Primero SRS y tests de corrección, después cloze/Type-it; por último generación de lectura y feedback de IA. El código original y su historial se conservan en una copia privada recuperable; no forman parte de este repositorio público.
