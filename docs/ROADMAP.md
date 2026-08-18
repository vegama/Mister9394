# Roadmap canónico — Míster 93/94 v1.1.x Beta / RC

Fecha: 18-08-2026  
Base: **1.1.2-rc-production-playtest-candidate**.

## UX-0 — Auditoría viva + Design System · CERRADO BASE

Primitivas compartidas, suelo de legibilidad, focus/reduce-motion y `check:ux` integrado en build.

## UX-1 — Shell y arquitectura de información · CERRADO BASE

HOY / EQUIPO / CLUB / TEMPORADA / CARRERA Y MUNDO, búsqueda Ctrl/Cmd+K y continuidad de decisiones desde Inicio.

## UX-2 — Trabajo diario · CERRADO BASE

Plantilla, Táctica, Entrenamiento, Mercado y Staff comparten jerarquía de cabecera/proceso/acción. Plantilla persiste filtros y orden durante la sesión.

## UX-3 — Contexto de temporada · CERRADO BASE

Calendario, Competiciones, Noticias y Carrera usan estados vacíos explicativos y componentes comunes donde reducen fricción real.

## UX-4 — Navegación de entidades · CERRADO EN PRODUCCIÓN

Jugador, club, partido y competición usan navegación contextual; `Football9394App.vue` delega la carga/sincronización en `useEntityNavigation`; las fichas de jugador preservan pestaña en URL/history; Atrás/Adelante/F5 restauran el contexto soportado; la cabecera ofrece retorno visible; Noticias puede saltar a jugador, club o competición. El contrato está verificado también sobre el bundle compilado con History API real, Atrás/Adelante y `page.reload()` literal conservando ruta y carrera.

## UX-5 — Feedback, error y estados runtime · CERRADO EN PRODUCCIÓN

Las operaciones lentas muestran feedback a partir de 500 ms; existe timeout de 15 s con lenguaje de jugador; las mutaciones idénticas simultáneas se colapsan para evitar doble envío; los errores de entidad permanecen visibles con Reintentar/Volver; Empty y Error están separados. `check:network` ejecuta dedupe, lentitud, offline, timeout y sanitización 500; el bundle compilado confirma feedback lento, offline, recuperación y doble clic sin duplicar mutación.

## UX-6 — Onboarding contextual + velocidad experta · PLAYTEST CERRADO

La primera carrera muestra una guía contextual y lleva directamente a Tácticas; el retorno es visible. El flujo experto valida Ctrl+K → Mercado → búsqueda → consulta como proceso visible. Persona gate 18/18.

## UX-7 — Visual / responsive / accesibilidad · BUNDLE CERRADO

Chromium verifica el bundle compilado en 1920×1080, 1366×768, 1280×720, 1024×768 y equivalentes de reflow a 200 %, sin overflow global. Nueva carrera cumple contraste ≥4.5; Mercado no conserva superficies claras heredadas; topbar sticky y navegación móvil inferior quedan protegidas por gate.

## UX-8 — Playtest · CERRADO BASE RC

Playtest ejecutable de persona nueva, experta y ciclo completo partido→postpartido→consecuencia: 18/18. El gate de producción cubre además Atrás/Adelante, reload, offline, petición lenta, doble clic y reflow: 58/58. Uso prolongado seguirá siendo regresión continua de RC, no bloqueo conocido.

## UX-9 — Release candidate · CANDIDATO

Cero P0/P1 conocidos en los recorridos certificados. Source gates, bundle browser, partido, mercado y transición longitudinal están verdes. Launcher HTTP **6/6 PASS** (health/index/assets) y bundle Chromium **58/58 PASS** mediante modo policy-safe. La política `URLBlocklist` impide únicamente unir ambas capas en una navegación Chromium→localhost dentro de este entorno.

## Regla paralela permanente

Cada pasada intenta un micro-lote de assets con trazabilidad y sin bloquear producto. v1.1.2: 4 intentos BDFutbol, 0 añadidos por DNS, 10.195 fotos preservadas.
