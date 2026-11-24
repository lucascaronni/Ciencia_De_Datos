# Del gráfico al capital

## Una fila real de entrenamiento

Buscar `KO_2015-07-14` en el manifiesto. Cada fila de la tabla delimita las ruedas que se agregan en una vela mensual de KO. Por ejemplo, enero abre en 29,299129, alcanza 30,387620, cae hasta 28,501813 y cierra en 28,543409. Los precios están ajustados y expresados en USD.

| Vela | Primera rueda | Última rueda |
|---|---|---|
| Enero | 02/01/2015 | 30/01/2015 |
| Febrero | 02/02/2015 | 27/02/2015 |
| Marzo | 02/03/2015 | 31/03/2015 |
| Abril | 01/04/2015 | 30/04/2015 |
| Mayo | 01/05/2015 | 29/05/2015 |
| Junio | 01/06/2015 | 30/06/2015 |

La diaria usa el 1, 2, 6, 7, 8, 9, 10, 13 y 14 de julio. La primera apertura mensual vale 29,299129 y la primera diaria 27,756065. La apertura inicial de cada vista se dibuja en cero porque ln(1) = 0. Ambas CNN reciben el mismo dibujo mensual. Al cierre del 14/07 la segunda también ve el cierre diario de 29,017696.

Supongamos, solo para explicar la decisión, probabilidades de 0,45 (mensual) y 0,60 (dos vistas) con umbral 0,50 para ambas. La mensual guarda la parte de KO en efectivo. La otra compra el 15/07 a la apertura de 29,003605 y liquida el 11/08 al cierre de 29,236202. La operación habría rendido 29,236202 / 29,003605 − 1 − 0,002 = **+0,6020 %** sobre su parte. La etiqueta de entrenamiento vale 1. En la cartera de 34 activos, KO aportaría unos +0,0177 puntos porcentuales al retorno de ese corte si se ejecutara. Las fechas y precios provienen de la fuente congelada. Las probabilidades son ilustrativas.

## Cuatro estrategias con el mismo dinero

Ejemplo ficticio de un corte con 100 de capital, dos activos y 50 disponibles por activo. A sube 10 % y B baja 4 % entre ejecución y salida. Restar el costo supuesto de 0,20 % produce retornos netos de +9,80 % y −4,20 %. Con umbral 0,50, supongamos p(A, B) = (0,45, 0,60) en mensual y (0,65, 0,40) en dos vistas.

| Estrategia | Compras | Efectivo reservado | Exposición | Operaciones | Capital final | Retorno de cartera |
|---|---|---:|---:|---:|---:|---:|
| CNN mensual | B | 50 | 50 % | 1 | 50 + 50 × 0,958 = 97,90 | −2,10 % |
| CNN mensual + diaria | A | 50 | 50 % | 1 | 50 + 50 × 1,098 = 104,90 | +4,90 % |
| Comprar siempre | A y B | 0 | 100 % | 2 | 54,90 + 47,90 = 102,80 | +2,80 % |
| Efectivo | Ninguna | 100 | 0 % | 0 | 100,00 | 0,00 % |

La diferencia entre las CNN sería +7,00 puntos porcentuales. La estrategia mensual pagó 0,10 por su única operación y comprar siempre pagó 0,20. Esos costos ya están incluidos en la tabla. En el siguiente corte cada estrategia reparte su propio saldo. Por ejemplo, si la de dos vistas rindiera luego −2 %, terminaría con 104,90 × 0,98 = 102,802 y acumularía +2,802 %.
