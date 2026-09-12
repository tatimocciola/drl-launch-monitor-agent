# Diccionario de datos

## Estructura de entrada

El agente recibe un archivo CSV normalizado. Cada fila representa una combinación de fuente, período, área, calibre y sabor.

## Columnas

| Columna               | Obligatoria | Descripción                                     | Ejemplo       |
| --------------------- | ----------- | ----------------------------------------------- | ------------- |
| `periodo`             | Sí          | Mes correspondiente al dato en formato AAAA-MM  | `2026-07`     |
| `temporalidad`        | Sí          | Tipo de período analizado                       | `LM`          |
| `fuente`              | Sí          | Origen del indicador                            | `sell_in`     |
| `area`                | Sí          | Apertura geográfica o total                     | `TOTAL`       |
| `calibre_ml`          | Sí          | Contenido del envase en mililitros              | `473`         |
| `sabor`               | Sí          | Sabor core analizado                            | `GREEN_APPLE` |
| `volumen_cc`          | Sí          | Volumen en cajas convertidas de 9 litros        | `8433`        |
| `clientes_con_compra` | No          | Cantidad de clientes que compraron el producto  | `120`         |
| `stock_cc`            | No          | Stock agregado en cajas convertidas de 9 litros | `950`         |

## Valores admitidos

### `temporalidad`

* `LM`: último mes.
* `FYTD`: acumulado del año fiscal.
* `L12M`: últimos doce meses.

No deben compararse registros con temporalidades diferentes.

### `fuente`

* `sell_in`
* `sell_out_distribuidores`
* `logyt`

### `area`

* `TOTAL`
* Nombre del área disponible en sell-out de distribuidores.

Para sell-in y Logyt se utilizará `TOTAL` cuando no exista apertura geográfica comparable.

### `sabor`

* `VODKA`
* `LIMON`
* `GREEN_APPLE`
* `RED_BERRIES`
* `TOTAL_DRL`

### `calibre_ml`

* `473`
* `1000`

## Reglas para datos ausentes

* Las celdas sin información deben quedar vacías.
* Una celda vacía no significa cero.
* `clientes_con_compra` sólo se completa para sell-in y sell-out de distribuidores.
* `stock_cc` sólo se completa para Logyt.
* No se deben estimar datos faltantes para completar la tabla.

## Indicadores derivados

### Rotación proxy

Se calcula solamente cuando existen volumen y clientes con compra:

`rotacion_proxy = volumen_cc / clientes_con_compra`

Representa cajas convertidas promedio por cliente con compra. No equivale a rotación por punto de venta ni a consumo final.

### Mix de sabor

`mix_sabor = volumen_cc del sabor / volumen_cc total del calibre`

Debe calcularse dentro de la misma fuente, período, temporalidad, área y calibre.

### Relación stock/sell-out

`relacion_stock_sellout = stock_cc / volumen_cc`

Sólo se calcula para Logyt dentro del mismo período. Es un indicador agregado y no demuestra disponibilidad por tienda.

## Comparaciones válidas

Una comparación requiere que los registros compartan:

* Fuente.
* Temporalidad.
* Área.
* Calibre.
* Períodos comparables.

Los sabores deben compararse dentro del mismo calibre.

## Protección de la información

Las entradas publicadas en el repositorio deben estar anonimizadas cuando contengan información confidencial. Los archivos originales del negocio no se publican.
