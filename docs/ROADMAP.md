# Roadmap canónico — Míster 93/94 v1.1.x Beta / RC

Fecha: 18-08-2026  
Base: **1.1.2-rc-browser-contracts-source**.

## UX-0 — Auditoría viva + Design System · CERRADO BASE

Primitivas compartidas, suelo de legibilidad, focus/reduce-motion y `check:ux` integrado en build.

## UX-1 — Shell y arquitectura de información · CERRADO BASE

HOY / EQUIPO / CLUB / TEMPORADA / CARRERA Y MUNDO, búsqueda Ctrl/Cmd+K y continuidad de decisiones desde Inicio.

## UX-2 — Trabajo diario · CERRADO BASE

Plantilla, Táctica, Entrenamiento, Mercado y Staff comparten jerarquía de cabecera/proceso/acción. Plantilla persiste filtros y orden durante la sesión.

## UX-3 — Contexto de temporada · CERRADO BASE

Calendario, Competiciones, Noticias y Carrera usan estados vacíos explicativos y componentes comunes donde reducen fricción real.

## UX-4 — Navegación de entidades · BROWSER CONTRACT CERRADO / PRODUCCIÓN PENDIENTE

Jugador, club, partido y competición usan navegación contextual; `Football9394App.vue` delega la carga/sincronización en `useEntityNavigation`; las fichas de jugador preservan pestaña en URL/history; Atrás/Adelante/F5 restauran el contexto soportado; la cabecera ofrece retorno visible; Noticias puede saltar a jugador, club o competición. El contrato puro de ruta está verificado con History API real de Chromium (Atrás/Adelante/remount); falta `reload()` literal sobre el bundle de producción.

## UX-5 — Feedback, error y estados runtime · CONTRATO EJECUTABLE CERRADO / PRODUCCIÓN PENDIENTE

Las operaciones lentas muestran feedback a partir de 500 ms; existe timeout de 15 s con lenguaje de jugador; las mutaciones idénticas simultáneas se colapsan para evitar doble envío; los errores de entidad permanecen visibles con Reintentar/Volver; Empty y Error están separados. `check:network` ejecuta dedupe, lentitud, offline, timeout y sanitización 500. Falta observar foco/recuperación sobre la UI de producción.

## UX-6 — Onboarding contextual + velocidad experta · SOURCE CERRADO BASE / PLAYTEST PENDIENTE

La primera carrera muestra una guía contextual y descartable sólo antes del primer partido dirigido, orientada a prioridad → 11+5 → consecuencias; no existe tutorial largo. La command palette admite flechas, selección activa y Enter además de Ctrl/Cmd+K. Falta medir en playtest tiempo a primera decisión y velocidad experta.

## UX-7 — Visual / responsive / accesibilidad · CHROMIUM SOURCE-CSS 8/8 / BUNDLE PENDIENTE

Chromium ya verifica 1920×1080, 1366×768, 1280×720, 1024×768 y sus equivalentes a 200 % sin overflow global, con CTA/topbar/nav/errores visibles y teclado básico. Falta repetir la matriz sobre `frontend/dist` real.

## UX-8 — Playtest · BLOQUE RC

15 min nuevo, 1 h intermedio, varias horas, hardcore, teclado y usuario destructivo/Atrás. Medir clics, tiempo, dudas, retrocesos y abandono.

## UX-9 — Release candidate

Cero P0. P1 finitos y explícitos. Source gates, browser, partido, mercado, transición de temporada, soak y build reproducible desde repo limpio.

## Regla paralela permanente

Cada pasada intenta un micro-lote de assets con trazabilidad y sin bloquear producto. v1.1.2: 4 intentos BDFutbol, 0 añadidos por DNS, 10.195 fotos preservadas.
