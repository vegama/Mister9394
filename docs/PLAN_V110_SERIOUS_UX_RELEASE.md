# Plan canónico — Míster 93/94 v1.1.x UX / Beta-RC

Fecha: 18-08-2026  
Base: V1.0-M cerrada + checkpoint v1.1.1 de navegación/feedback/onboarding en source.

## Objetivo

Convertir el cierre Beta/RC en una certificación de experiencia de jugador, no sólo de funcionalidad: claridad, continuidad, navegación, feedback, visual runtime, accesibilidad, rendimiento y juego longitudinal.

## Orden de cierre

1. **UX-0 Source contract — CERRADO BASE:** design primitives + `check:ux`.
2. **UX-1 Shell/navegación — CERRADO BASE:** arquitectura mental + command palette + contexto de decisión.
3. **UX-2 Workspaces diarios — CERRADO BASE:** Plantilla/Táctica/Entrenamiento/Mercado/Staff.
4. **UX-3 Contexto de temporada — CERRADO BASE:** Calendario/Competiciones/Noticias/Carrera.
5. **UX-4 Navegación de entidades — SOURCE CERRADO / BROWSER PENDIENTE:** entidades, pestaña de jugador, Back/Fwd/F5 soportados, retorno visible y carga extraída a `useEntityNavigation`.
6. **UX-5 Estados/feedback/error — SOURCE CERRADO / BROWSER PENDIENTE:** >500 ms, timeout 15 s, retry/volver, doble envío colapsado, empty/error separados.
7. **UX-6 Onboarding + experto — SOURCE CERRADO / PLAYTEST PENDIENTE:** FirstRunGuide contextual + palette por flechas/Enter; falta medición humana.
8. **UX-7 Visual/accessibility matrix — BLOQUE RC:** Chromium actual a 1920/1366/1280/1024 + zoom.
9. **UX-8 Playtest — BLOQUE RC:** nuevo/intermedio/hardcore/teclado/destructivo.
10. **UX-9 Release candidate:** cero P0, P1 explícitos y finitos, build reproducible.

## Regla de trabajo

No abrir nuevas features horizontales mientras exista un P1 de comprensión, continuidad, navegación o visual runtime. Al tocar una pantalla se migra sólo lo que reduzca fricción real; no se reescribe por uniformidad estética.

## Carril paralelo de assets

Cada pasada mantiene un microintento acotado. En esta v1.1: 4 retratos BDFutbol intentados; 0 añadidos por fallo temporal DNS; 10.195 fotos runtime preservadas; checkpoint no bloqueado. Ver `docs/v110_ux_asset_microbatch_attempt.json`.
