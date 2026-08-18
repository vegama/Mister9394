# V1.0.0 · Ola 3 — Matchday destructivo

Checkpoint centrado en la robustez del bucle Inicio → XI → Táctica → Partido → Postpartido.

## Corregido

- recuperación segura del partido/postpartido con F5;
- bloqueo de Atrás/Adelante durante partido iniciado;
- salida segura de una previa a minuto 0;
- expulsados fuera del `on_pitch` operativo y no sustituibles;
- descanso como estado explícito;
- límite histórico de dos cambios visible y aplicado;
- banquillo desactivado antes del saque inicial;
- reparación del XI tras lesión de entrenamiento;
- lesión de partido conectada con área médica/noticia/siguiente XI;
- sanciones reales por roja y ciclo de amarillas usando el ciclo de cada liga;
- sanción liguera respetada en selección automática y consumida en la siguiente jornada;
- smoke de coherencia resultado → clasificación → moral → noticias → siguiente partido.

## Gates

- `test_football9394_v100_destructive_matchday.py`: 7/7.
- core loop + D7/D8 + match engine: 10/10.
- Vue syntax: 28/28.
- SFC structure: verde.
- UI quality: verde.
- Build Vite: no ejecutable en este entorno por ausencia del binario/dependencias, aunque los gates previos del script pasan.

Assets: sin trabajo en esta ola.
