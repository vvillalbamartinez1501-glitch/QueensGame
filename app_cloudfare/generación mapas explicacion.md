# Explicación de la generación de mapas

## Respuesta breve

Los mapas **no son infinitos** y el servidor **no crea uno matemáticamente nuevo en cada partida**. La aplicación elige al azar entre mapas predefinidos. Por eso los mapas pueden repetirse, incluso en partidas consecutivas.

## Cómo funciona

1. Al abrir la aplicación, pulsar **Nuevo mapa** o elegir otro tamaño, el cliente solicita una partida nueva a `POST /api/games`.
2. La petición incluye el tamaño del tablero. El servidor acepta tamaños del **4x4 al 12x12**.
3. En [`puzzles.json`](./puzzles.json) hay un banco fijo: **20 mapas distintos por cada tamaño**, es decir, 180 mapas en total entre los nueve tamaños.
4. El servidor busca el banco correspondiente al tamaño y selecciona una entrada al azar. La selección se hace **con reemplazo**: el mapa elegido no se retira ni se marca como usado, y no se consulta qué mapas se jugaron antes.
5. Para esa partida, se copia la distribución de regiones y su solución guardada en el banco. El tablero de juego empieza vacío. Se crea un identificador de partida nuevo y el estado se guarda en D1.

La selección al azar solo elige cuál de esos mapas existentes se juega; **no genera nuevas regiones**. Además, cada mapa lleva una solución precalculada, que el servidor usa para ofrecer pistas.

## ¿Se repiten?

Sí. Para un mismo tamaño hay 20 opciones y cada nueva partida vuelve a elegir entre ellas sin evitar la última selección ni las anteriores. Por tanto, puede salir el mismo mapa dos veces seguidas y, con suficientes partidas, volverán a aparecer mapas ya jugados. No hay un orden fijo o una rotación garantizada: una secuencia puede parecer repetitiva, pero depende de las selecciones aleatorias.

Cambiar el tamaño usa el banco de ese tamaño. En cambio, **reiniciar** la partida limpia las jugadas y conserva el mapa actual; para obtener otra selección hay que crear un mapa/partida nueva.

## Código relacionado

- [`functions/api/game.ts`](./functions/api/game.ts): valida el tamaño, selecciona el mapa aleatorio, inicializa el tablero vacío y guarda la partida.
- [`puzzles.json`](./puzzles.json): banco de mapas y soluciones precalculadas.
- [`lib/main.dart`](./lib/main.dart): solicita una partida nueva al iniciar, al cambiar el tamaño o al usar el control «Nuevo mapa».
