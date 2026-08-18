# 0.11 · Carrera del mánager y movilidad entre clubes

## Objetivo

Una destitución deja de ser `game over`. El usuario es ahora un actor persistente del universo: tiene reputación, etapas, ofertas y memoria propia.

## Destitución

Cuando el consejo cierra una etapa:

- se archiva el club, fecha de inicio/fin y motivo;
- el antiguo club contrata un sustituto IA desde el mercado de entrenadores recuperado de la MDB;
- el cambio de entrenador entra en el mundo y en Noticias;
- se generan hasta tres proyectos compatibles;
- `Continuar` queda detenido en una **decisión de carrera**, no en fin de partida.

## Ofertas y cambio de club

En 0.11 las ofertas inmediatas son deliberadamente **de la misma liga**. Es una restricción de realismo técnico: permite heredar la clasificación, resultados y calendario ya simulados sin recalcular ni mover partidos de una competición a otra. El nuevo club conserva sus puntos, plantilla, economía y próximo partido; el mánager conserva reputación, récords, relaciones históricas y trayectoria.

Al aceptar:

- se genera un XI legal del nuevo club;
- se reinicia el contexto de consejo/economía que pertenecía al empleador anterior;
- se cancelan negociaciones y ofertas que pertenecían al club abandonado;
- la watchlist y la memoria personal continúan;
- el entrenador al que sustituyes queda registrado como predecesor contextual;
- Historia añade una nueva etapa a la trayectoria del mánager.

## Reputación

Los partidos oficiales modifican reputación de forma contenida según resultado, dificultad relativa y rivalidad. Los amistosos no cuentan. La reputación no altera atributos de futbolistas: se utiliza para el mercado laboral del entrenador.

## Gate

- Movilidad del mánager: 7/7 PASS.
- Incluye dos cambios de club consecutivos, migración de saves schema 10 → 11 y recuperación automática de antiguos saves ya destituidos.
- Regresión dirigida total de cierre: 61/61 PASS.
- El cambio de club conserva exactamente la tabla de liga existente y deja un XI válido.
- Cross-league midseason mobility queda explícitamente fuera de 0.11 hasta disponer de un swap de estado de competición probado longitudinalmente.
