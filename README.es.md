<div align="center">

# 🚀 AstroBench

### Benchmark de manipulación de objetos en flotación libre

**Capturar un objeto en movimiento y mantenerlo sujeto después del contacto.**

[🌐 Sitio web](https://astroup.com/astrobench/) · [📖 Especificación (inglés)](https://astroup.com/astrobench/docs/current/index.html) · [🎬 Vídeos](https://astroup.com/astrobench/#videos) · [🐛 Incidencias](https://github.com/Brickkkkkk/AstroBench/issues)

[English](README.md) | [简体中文](README.zh-CN.md) | [日本語](README.ja.md) | [한국어](README.ko.md) | **Español** | [Français](README.fr.md) | [Deutsch](README.de.md)

[![CI](https://github.com/Brickkkkkk/AstroBench/actions/workflows/protocol.yml/badge.svg)](https://github.com/Brickkkkkk/AstroBench/actions/workflows/protocol.yml)
[![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)](pyproject.toml)
[![Protocol](https://img.shields.io/badge/Protocol-0.1_draft-orange)](docs/protocol.md)

<a href="https://astroup.com/astrobench/#videos"><img src="https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg" alt="Un brazo robótico de base fija se aproxima a un carrete que flota en una cabina. Pulsa para ver los vídeos." width="760"></a>

</div>

## 🪐 ¿Qué es AstroBench?

AstroBench estudia la manipulación de objetos en flotación libre mediante un brazo robótico de base fija dentro de una cabina sin gravedad. Al no haber una superficie de apoyo, el primer contacto puede alejar el objeto o hacerlo girar. Cerrar la pinza no basta: hay que mantener un agarre estable.

La evaluación distingue la **captura**, que establece un agarre estable, de la **retención final**, que lo mantiene hasta el fin del episodio. El diseño general también incluye mecanismos de cabina, inserción, reorientación y almacenamiento.

Este repositorio contiene el protocolo de evaluación portable: planes de episodios deterministas, puntuación de trayectorias y contabilización completa de resultados. Funciona en CPU con la biblioteca estándar de Python. Un adaptador del entorno suministra las trayectorias medidas; el paquete no incluye el entorno completo ni políticas preentrenadas.

### ✨ Características principales

- **Contacto y retención:** evalúa contacto bilateral con el objeto objetivo, cierre medido, movimiento relativo y sujeción continua.
- **Planes reproducibles:** vincula la identidad del objeto, los grupos geométricos, el movimiento y el protocolo mediante hashes de episodio.
- **Cobertura explícita:** separa fallos de tarea, errores de ejecución y episodios ausentes; no publica una media macro completa si faltan resultados.
- **Dos puntos de vista:** 40 ejemplos seleccionados de 20 tipos de objetos, con cámaras exterior y de cabina.
- **README en siete idiomas:** la especificación técnica completa está disponible en inglés y chino.

## 🧭 Contenido

- [🎬 Vídeos de las tareas](#watch)
- [⚡ Inicio rápido](#quickstart)
- [📏 Evaluación](#evaluation)
- [🧩 Diseño de tareas](#tasks)
- [📊 Experimento de desarrollo](#evidence)
- [🗂️ Estructura del repositorio](#layout)
- [🛠️ Estado de publicación](#roadmap)
- [🤝 Contribuir y citar](#contributing)

<a id="watch"></a>

## 🎬 Vídeos de las tareas

| Carrete en movimiento | Llave en movimiento | Carrete inicialmente inmóvil |
| --- | --- | --- |
| [![Carrete en movimiento](https://astroup.com/astrobench/posters/dynamic-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-spool-ExternalCamera.mp4) | [![Llave en movimiento](https://astroup.com/astrobench/posters/dynamic-wrench-ExternalCamera.jpg)](https://astroup.com/astrobench/media/dynamic-wrench-ExternalCamera.mp4) | [![Carrete inicialmente inmóvil](https://astroup.com/astrobench/posters/static-spool-ExternalCamera.jpg)](https://astroup.com/astrobench/media/static-spool-ExternalCamera.mp4) |

En la [galería interactiva](https://astroup.com/astrobench/#videos) puedes buscar objetos, cambiar de cámara y consultar registros de movimiento. Hay **20 tipos de objetos · 40 episodios seleccionados · 80 vídeos**. Los ejemplos seleccionados no representan una tasa de éxito del conjunto de prueba. Las etiquetas históricas de sujeción corresponden a la versión de grabación y se interpretan por separado del evaluador actual de retención final.

<a id="quickstart"></a>

## ⚡ Inicio rápido

**Requisitos:** Python 3.11+, sin GPU ni dependencias de ejecución aparte de la biblioteca estándar. Los comandos utilizan una shell POSIX.

### 1. Instalar y verificar

```bash
git clone https://github.com/Brickkkkkk/AstroBench.git
cd AstroBench
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
python -m unittest discover -s tests -v
```

Las pruebas verifican el protocolo y los cálculos estadísticos.

### 2. Generar el plan de episodios

```bash
astrobench plan examples/catalog.json --seed 42 --output plan.json
python -c 'import json; print(json.load(open("plan.json"))["episodes"][0]["episode_id"])'
```

El catálogo incluido es una entrada sintética para probar la interfaz; no contiene recursos físicos. Para un experimento, proporciona recursos verificados con `object_id`, `asset_sha256`, `geometry_group` y `split`. El planificador rechaza recursos o grupos geométricos compartidos entre particiones.

### 3. Evaluar una trayectoria medida

```bash
astrobench score plan.json EPISODE_ID trace.json --output episode-result.json
```

Exporta primero `trace.json` con el adaptador del entorno y sustituye `EPISODE_ID` por el identificador mostrado. La trayectoria contiene `episode_id`, `spec_hash` y `samples`. Cada muestra registra tiempo, fuerzas sobre el objetivo por dedo, cierre medido, contacto prohibido, salida del espacio de trabajo, velocidades y pose relativas. Consulta el [contrato de campos (inglés)](docs/protocol.md#trace-and-adapter-contract).

### 4. Agregar resultados

```bash
python -c 'import json; json.dump([json.load(open("episode-result.json"))], open("results.json", "w"))'
astrobench report plan.json results.json --output report.json
```

Este ejemplo agrupa un solo resultado, por lo que un plan de varios episodios aparecerá incompleto. Para un informe completo, incluye todos los resultados previstos de una misma política/checkpoint en el array JSON. La CLI no sobrescribe archivos existentes: usa rutas nuevas para cada ejecución.

<a id="evaluation"></a>

## 📏 Evaluación

Catálogo verificado → plan registrado con hashes de identidad → trayectoria medida por el adaptador → evaluación de captura/retención final → éxito, cobertura e incertidumbre. La versión pública es `astrobench.capture-retain/0.1-draft`.

| Parámetro | Valor |
| --- | --- |
| Duración del episodio | 12 s |
| Ventana de sujeción continua | 1.0 s transcurrido según las marcas de tiempo |
| Frecuencia nominal / intervalo máximo | 50 Hz / 25 ms |
| Fuerza sobre el objetivo | Al menos 0.5 N por dedo |
| Velocidad relativa lineal / angular máxima | 0.02 m/s / 0.2 rad/s |
| Variación relativa máxima de posición / orientación | 0.01 m / 0.1 rad |

**Capturar pronto y perder después el objeto no cuenta como éxito.** La ventana continua válida debe llegar al final del episodio. Se rechazan registros inválidos o truncados. Agotar el tiempo de tarea cuenta como fallo; los errores de ejecución y episodios ausentes se contabilizan aparte.

El planificador ofrece `static`, `drift`, `tumble` y `fast_tumble`. Son condiciones de movimiento provisionales, no un benchmark de generalización definitivo. Los umbrales requieren calibración con el adaptador. El evaluador comprueba registros; el adaptador debe verificar la configuración física y la correspondencia de sensores.

📖 [Especificación (inglés)](https://astroup.com/astrobench/docs/current/index.html) · [Protocol reference (English)](docs/protocol.md)

<a id="tasks"></a>

## 🧩 Diseño de tareas

| Categoría | Familias | Evidencia de finalización |
| --- | --- | --- |
| Agarre en flotación libre | Capturar y retener | Contacto bilateral, cierre real y retención |
| Interacción con mecanismos | Puertas, cajones, botones, mandos/válvulas, palancas | Estado articular o recorrido, dirección y secuencia |
| Acoplamiento de precisión | Inserción de pasadores, conectores, módulos | Alineación, profundidad y asentamiento |
| Manipulación de objetos | Reorientar, guardar y cerrar | Pose objetivo o colocación, liberación y cierre ordenados |

El diseño de 11 familias supera el alcance de los vídeos y del evaluador de agarre actuales. Las demás familias necesitan validación y evaluadores propios. Las particiones oficiales de objetos y movimiento aún no están fijadas.

<a id="evidence"></a>

## 📊 Experimento de desarrollo

Un piloto pareado de 40 episodios con un cubo compara un checkpoint ACT congelado con una referencia de realimentación de estado adaptada: diez posiciones de desarrollo, dos condiciones de movimiento y dos métodos, sin reentrenamiento.

| Método | Condición inicial | Agarre adquirido | Retención final |
| --- | --- | --- | --- |
| ACT | Inmóvil | 8 / 10 | 3 / 10 |
| ACT | En movimiento | 6 / 10 | 0 / 10 |
| Referencia de estado | Inmóvil | 8 / 10 | 8 / 10 |
| Referencia de estado | En movimiento | 0 / 10 | 0 / 10 |

El piloto utiliza un **protocolo nativo de 15 Hz y 20 segundos**, distinto del evaluador público de 12 segundos. La referencia utiliza estado privilegiado; todos sus episodios en movimiento alcanzaron un límite de seguimiento propio del controlador. Sus agarres estáticos ocurrieron más tarde, dejando menos tiempo para observar la retención. Son diagnósticos de desarrollo, no una clasificación con igualdad de información ni un resultado de generalización sobre 20 objetos. Véanse [configuración, intervalos e interpretación (inglés)](https://astroup.com/astrobench/docs/current/index.html#pilot).

<a id="layout"></a>

## 🗂️ Estructura del repositorio

```text
AstroBench/
├── astrobench/
├── docs/protocol.md
├── examples/catalog.json
├── tests/
├── .github/workflows/
├── README.md
└── README.*.md
```

`astrobench/`: planes, puntuación, agregación y CLI; `docs/protocol.md`: contrato de trayectorias; `examples/`: catálogo sintético; `tests/`: pruebas del protocolo y estadísticas; `.github/workflows/`: CI; `README.*.md`: guías por idioma.

<a id="roadmap"></a>

## 🛠️ Estado de publicación

- [x] Paquete portable de planificación, evaluación y agregación
- [x] Pruebas del protocolo y CI con GitHub Actions
- [x] Página y especificación en inglés/chino; README multilingüe
- [x] Vídeos seleccionados con dos cámaras
- [x] Piloto pareado de desarrollo con un cubo
- [ ] Entorno completo portable y distribución de recursos
- [ ] Particiones fijas de objetos y condiciones de movimiento calibradas
- [ ] Evaluación más amplia de referencias y retención durante intervalos iguales
- [ ] Publicación del artículo

La recopilación automática de datos, las políticas de demostración/docentes, los procesos de entrenamiento y los conjuntos de datos brutos quedan fuera de esta publicación.

<a id="contributing"></a>

## 🤝 Contribuir y citar

Si encuentras un caso límite de puntuación o una interfaz poco clara, [abre una incidencia](https://github.com/Brickkkkkk/AstroBench/issues) con la versión del protocolo, una trayectoria mínima reproducible y el resultado esperado. Para cambios de umbrales o semántica temporal, explica cómo versionar resultados anteriores. Ejecuta las pruebas antes de enviar un PR.

El artículo está en revisión y todavía no tiene identificador arXiv. Hasta disponer de una cita formal, referencia la URL del repositorio, el commit exacto y la versión del protocolo utilizados.

Trabajo relacionado: [Space Robotics Bench](https://arxiv.org/abs/2509.23328).

