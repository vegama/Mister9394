# Plan canónico — Míster 93/94 v1.1.x UX / Beta-RC

Fecha: 18-08-2026  
Base: V1.0-M cerrada + checkpoint v1.1.2 RC production playtest candidate.

## Objetivo

Convertir el cierre Beta/RC en una certificación de experiencia de jugador, no sólo de funcionalidad: claridad, continuidad, navegación, feedback, visual runtime, accesibilidad, rendimiento y juego longitudinal.

## Orden de cierre

1. **UX-0 Source contract — CERRADO BASE:** design primitives + `check:ux`.
2. **UX-1 Shell/navegación — CERRADO BASE:** arquitectura mental + command palette + contexto de decisión.
3. **UX-2 Workspaces diarios — CERRADO BASE:** Plantilla/Táctica/Entrenamiento/Mercado/Staff.
4. **UX-3 Contexto de temporada — CERRADO BASE:** Calendario/Competiciones/Noticias/Carrera.
5. **UX-4 Navegación de entidades — CERRADO PRODUCCIÓN:** entidades, pestaña, Back/Fwd y reload literal preservan contexto sobre el bundle compilado.
6. **UX-5 Estados/feedback/error — CERRADO PRODUCCIÓN:** >500 ms, timeout 15 s, retry/volver, doble envío colapsado, offline/recuperación y empty/error separados.
7. **UX-6 Onboarding + experto — CERRADO PLAYTEST:** FirstRunGuide → Tácticas y Ctrl+K → Mercado → consulta verificados.
8. **UX-7 Visual/accessibility matrix — CERRADO BUNDLE:** 1920/1366/1280/1024 + reflow equivalente 200 %, contraste, sticky topbar y navegación móvil.
9. **UX-8 Playtest — CERRADO BASE RC:** personas 18/18 + gate producción 58/58; uso prolongado queda como regresión continua.
10. **UX-9 Release candidate — CANDIDATO:** cero P0/P1 conocidos; launcher HTTP 6/6, bundle Chromium 58/58, personas 18/18. La única limitación es la navegación Chromium→localhost bloqueada por política corporativa del entorno.

## Regla de trabajo

No abrir nuevas features horizontales mientras exista un P1 de comprensión, continuidad, navegación o visual runtime. Al tocar una pantalla se migra sólo lo que reduzca fricción real; no se reescribe por uniformidad estética.

## Carril paralelo de assets

Cada pasada mantiene un microintento acotado. En esta v1.1: 4 retratos BDFutbol intentados; 0 añadidos por fallo temporal DNS; 10.195 fotos runtime preservadas; checkpoint no bloqueado. Ver `docs/v110_ux_asset_microbatch_attempt.json`.
