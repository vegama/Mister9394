# v0.16 · Tactical AI 2.0 + reglamento congelado

## Objetivo

Abrir P5 sin conceder omnisciencia a la IA y convertir las reglas 1993-94 en una constante deliberada de toda la carrera.

## Preparación rival

- El juego registra únicamente patrones **expuestos en partidos oficiales** del mánager: formación, presión, amplitud, ritmo y directitud.
- El rival prepara su siguiente partido contra la tendencia observada, no contra la táctica que el usuario acaba de seleccionar en pantalla.
- Si el usuario cambia justo antes del partido puede sorprender al rival.
- La calidad del entrenador determina cuántas contramedidas puede sostener; no concede puntos artificiales a sus futbolistas.
- El plan considera amenazas reales del rival: velocidad al espacio, juego aéreo, creación, amplitud y balón parado.
- La previa explica qué tendencias cree haber detectado el rival y qué intenta contrarrestar.

## Ajustes durante el partido

Los entrenadores pueden reaccionar desde la segunda parte a marcador, volumen de tiros y control territorial. Las decisiones cambian mentalidad, presión, línea o construcción; nunca alteran la media base de los jugadores.

## Calibración

La mayor capacidad defensiva de P5 redujo inicialmente el entorno de gol de Primera a 2,495 goles/partido. No se relajó el gate: el perfil español se recalibró para mantener la nueva inteligencia táctica y volver a 2,592 goles/partido, frente al objetivo histórico 989/380 = 2,603.

## Reglamento permanente

- `rules_policy = frozen_1993_94`.
- Sin Bosman.
- Sin liberalización futura del cupo de extranjeros.
- Sin mercado invernal español moderno desde 1994-95.
- Las reglas de inscripción pre-ventanas continúan aunque la carrera llegue a 2002, 2010 o más allá.

## Estado

Este documento describe la apertura de P5 en 0.16. El bloque fue **cerrado en 0.17**: se añadieron adaptación entre partidos, preparación específica por liga/grupo/eliminatoria/final y aprendizaje táctico longitudinal ligado al entrenador cuando existe una identidad de técnico fuente. Véase `V017_P5_CLOSED_PESETA_CALIBRATION.md`.
