# Míster 93/94 — v1.0.0 · Mercado + Staff + Entrenamiento + delegación · Ola 1

## Objetivo de la ola

Entrar en V1.0-E sin abrir sistemas nuevos: convertir Mercado, Staff y Entrenamiento en procesos continuos donde el jugador pueda responder, sin reconstruir el estado mentalmente, a seis preguntas: qué ocurre, quién lo lleva, en qué fase está, qué se está esperando, qué consecuencia tiene delegarlo y si requiere una decisión del mánager.

## Cambios cerrados

### Mercado

- Nuevo estado de proceso canónico: **Necesidad → Seguimiento → Informes → Consulta → Negociación**.
- Cada fase expone cantidad, estado (`sin actividad`, `en marcha`, `esperando`, `requiere decisión`) y responsable.
- La pantalla separa procesos que están esperando de operaciones que requieren una decisión del usuario.
- Contraofertas y ofertas entrantes cuentan como decisiones pendientes; un scouting o una oferta enviada sólo cuentan como espera.
- El responsable de búsqueda/scouting y el de negociación aparecen con calidad y carga.
- Las negociaciones muestran quién las está llevando, calidad del responsable y próxima fecha de respuesta.
- F5 conserva filtros de mercado y el objetivo seleccionado mediante estado de sesión ligado a la carrera; al recuperar la partida, la búsqueda se reconstruye con el mismo contexto.

### Staff y decisiones/delegación

- Cada responsabilidad declara explícitamente:
  - `Control directo` o `Delegado`;
  - responsable;
  - competencia relevante;
  - calidad efectiva y carga;
  - qué sistema del juego altera realmente;
  - pantalla donde se supervisa o resuelve.
- Los informes de staff se presentan como decisiones/seguimiento conectados, no como mensajes aislados.
- Cada responsabilidad ofrece acceso directo a su área funcional.
- La delegación sigue reduciendo trabajo sin ocultar el efecto de la decisión.

### Entrenamiento

- La pantalla diferencia claramente control directo y ejecución delegada.
- Si está delegado, se explica que el mánager fija instrucciones y el responsable las ejecuta con su calidad efectiva.
- Si está bajo control directo, se hace visible el coste potencial de acumular demasiadas responsabilidades.
- El plan semanal distingue `Guardado` de `Cambios sin guardar`.
- Se añade `Descartar cambios` y se evita que `Guardar plan` parezca una acción necesaria cuando no ha cambiado nada.
- Acceso directo a Staff para cambiar la delegación sin buscar la responsabilidad manualmente.

## Contrato de backend añadido

`club_staff_snapshot()` añade por responsabilidad:

- `mode` / `mode_label`
- `workspace`
- `effect`

`training_snapshot()` añade:

- `responsibility_mode`
- `responsibility_note`

`market_snapshot()` añade `workflow` con:

- `steps`
- `action_required`
- `waiting_count`
- `recruitment_owner`
- `negotiation_owner`

Esto evita que la claridad dependa exclusivamente del frontend y permite reutilizar el mismo estado en Inicio/noticias u otras vistas futuras.

## Regresión

Nueva suite: `test_football9394_v100_management_continuity.py`.

Verifica:

1. que toda responsabilidad relevante explica modo, efecto y destino;
2. que cambiar Entrenamiento de directo a delegado modifica el contrato operativo visible;
3. que seguimiento, scouting, consulta y negociación alimentan el mismo workflow;
4. que una negociación esperando no se confunde con una decisión pendiente;
5. que una contraoferta sí pasa a `requiere decisión`.

Resultados de esta ola:

- Gestión dirigida (NF0 + training/scouting + mercado + nueva continuidad): **16/16 verdes**.
- Core loop v1.0.0: **3/3 verdes**.
- Ola destructiva de partido 4: **6/6 verdes**.
- Frontend estático: **SFC structure verde + UI quality verde + sintaxis Vue 28/28**.
- `vite build` no se certifica en este entorno porque no hay binario/dependencias de Vite instalados; `npm ci` no pudo completarse desde el contenedor.

## Qué NO se ha hecho

- Cero assets nuevos.
- No se han añadido departamentos ni burocracia.
- No se ha reabierto Inicio/Plantilla/partido salvo regresión.
- No se ha convertido la delegación en autoplay opaco: el usuario conserva supervisión y contexto.

## Siguiente ataque dentro de V1.0-E

La siguiente ola debe ser destructiva y funcional, no estética:

1. negociación que cambia de responsable a mitad del proceso;
2. informe de scouting que vence mientras hay negociación abierta;
3. mercado cerrado con consultas/scouting activos pero ofertas bloqueadas;
4. oferta entrante por jugador lesionado/sancionado/clave y consecuencias visibles;
5. renovación rechazada → contrapropuesta → decisión → efecto en relación/plantilla;
6. entrenamiento delegado con responsable sobrecargado y riesgo físico alto;
7. cambio de plan de entrenamiento, Back/F5 y comprobación de borrador vs estado guardado;
8. una misma incidencia recorrida Staff → área funcional → resolución → informe actualizado;
9. revisar alternativas A/B/C y coste de oportunidad antes de abrir la siguiente negociación.

Hasta superar esa ola, V1.0-E queda **activo**, no cerrado.
