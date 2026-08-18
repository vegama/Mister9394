# Roadmap canónico V1.0-I → V1.0-N

Fecha: 18-08-2026  
Base: **V1.0-H cerrada**.

## V1.0-I — UX cotidiana

Inicio centrado en Ahora / Próximo partido / Qué cambió / Pulso del club; interrupciones de Continuar justificadas; procesos multi-sistema con estado, responsable, siguiente paso y CTA; retorno contextual; persistencia de filtros, pestañas y selección.

**Gate:** un jugador identifica la siguiente decisión en ≤10 s en al menos el 90 % de escenarios de playtest preparados.

## V1.0-J — Partido

Cerrar el bucle previa → partido/Resultado → postpartido con equivalencia persistente, cambios IA realistas, lesiones/sanciones/expulsiones y relato causal legible.

## V1.0-K — Mercado, staff y entrenamiento

Procesos continuos y explicables: necesidad → dossier → comparación → negociación/espera → decisión → consecuencia. La delegación reduce clics sin ocultar decisiones críticas.

## V1.0-L — Emoción y hitos

Dar peso a campeones, fin de temporada, ascensos, descensos, rivalidades, cambios de club y memoria histórica sin convertirlo en cinemáticas obligatorias.

## V1.0-M — Refactor progresivo

Extraer responsabilidades de `manager_career.py`, `webapp.py`, `Football9394App.vue` y CSS mediante tests de caracterización. No se permite reescritura destructiva.

## V1.0-N — Beta / RC

Pirámide final: smoke rápido, integración, destructivo, soak y playtest humano. Cero P0; P1 explícitos y finitos; candidato reproducible desde repo limpio.

## Regla paralela permanente

Cada pasada intenta avanzar assets mediante un micro-lote acotado y con trazabilidad. Los fallos de red/fuente nunca bloquean el objetivo principal.
