# v0.26 — Turquía 1993-94 activa

La 1. Lig 1993-94 queda activada con el identificador histórico `930057`. La fila MDB moderna `57` continúa bloqueada y no se reutiliza como si fuese la edición de 1993-94.

El gate de plantilla parte de 16 páginas de temporada de BDFutbol y materializa exactamente 18 participantes reales por club (288 filas, 288 identidades distintas). Los internacionales turcos ya verificados en v0.24 se reutilizan mediante mapeos explícitos; no se permite reconciliación difusa por apellido. Esto evita homónimos como los dos Korkmaz del Galatasaray. Los internacionales verificados que pertenecían a un club activo pero no entraban en el núcleo de 18 se reasignan como profundidad real.

Los jugadores nuevos reciben rol especializado y atributos fijos en la escala existente del juego mediante comparables de la base original. No se usa ninguna regla 75/25 en fútbol ni una fórmula de valoración en runtime. Las inferencias de posición quedan marcadas en el audit y pueden enriquecerse después con perfiles individuales/fotos sin cambiar la identidad.

Gate esperado: 16 clubes, mínimo 18 jugadores activos por club, ningún internacional con club histórico reconocido varado en `Otros-Turquía`, y ninguna fila moderna `57` activa.
