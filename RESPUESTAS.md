# Explicación escrita — CRUD de la API de Equipos

Completé los dos endpoints que faltaban (`PUT` y `DELETE`) sobre `/equipos/{equipo_id}`.
Abajo explico cómo funciona cada uno y por qué lo hice así.

---

## Sobre `PUT /equipos/{equipo_id}` (actualizar)

### 1. ¿Qué recibe el endpoint y qué devuelve?

Recibe dos cosas por separado:

- `equipo_id`, un entero que viaja **en la ruta** (`/equipos/5`). FastAPI lo detecta porque el
  parámetro de la función se llama igual que la variable de la URL, y además lo convierte a `int`
  automáticamente. Si mando `/equipos/abc`, ni siquiera entra a mi código: FastAPI responde 422.
- El **cuerpo de la petición** en JSON, validado con `EquipoCreate`, que trae `nombre` y `categoria`.

Devuelve el equipo ya actualizado, con código **200**, serializado con `EquipoResponse`
(`id`, `nombre`, `categoria`, `disponible`).

Un detalle que me parece importante: el cuerpo **no** incluye `id` ni `disponible`. El `id` no se
manda porque ya viene en la URL, y permitir cambiarlo sería un problema. Y `disponible` es estado
interno del servidor, no algo que el cliente decida al editar. Por eso después de un PUT esos dos
campos se conservan tal como estaban.

```python
@router.put("/{equipo_id}", response_model=EquipoResponse)
def put_equipo(equipo_id: int, equipo: EquipoCreate):
    return actualizar_equipo(equipo_id, equipo)
```

El endpoint no tiene lógica: solo llama al service y devuelve lo que este le entregue.

### 2. ¿Cómo localiza el equipo a actualizar dentro de la lista?

Reutilizo `obtener_equipo(equipo_id)`, la función que ya venía en el proyecto para el `GET` por id.
Esa función recorre `_equipos` comparando `e["id"] == equipo_id` y devuelve el diccionario que
encuentra.

Lo clave acá es que **devuelve la referencia al diccionario que está dentro de la lista, no una
copia**. En Python, cuando saco un diccionario de una lista, sigo apuntando al mismo objeto. Por eso
puedo escribir directamente:

```python
actual["nombre"] = equipo.nombre
actual["categoria"] = equipo.categoria
```

y el cambio queda reflejado en `_equipos` sin necesidad de buscar la posición y reemplazar el
elemento. Si `obtener_equipo` devolviera una copia, esto no funcionaría y el cambio se perdería.

Preferí reutilizar esa función en vez de escribir otro bucle por dos razones: no duplico código de
búsqueda, y sobre todo no duplico el manejo del 404 (ver pregunta 4).

### 3. ¿Cómo valida el nombre duplicado excluyendo al propio equipo? ¿Por qué es importante?

```python
duplicado = any(
    e["id"] != equipo_id and e["nombre"].lower() == equipo.nombre.lower()
    for e in _equipos
)
```

Son dos condiciones que se tienen que cumplir a la vez:

- `e["id"] != equipo_id` → que sea **otro** equipo, no el que estoy editando.
- `e["nombre"].lower() == equipo.nombre.lower()` → que el nombre coincida, ignorando mayúsculas.

**Por qué es importante la exclusión:** sin ella sería imposible editar un equipo sin cambiarle el
nombre. Imaginemos que el equipo 1 se llama "Proyector Epson" y solo quiero corregirle la categoría.
Tendría que mandar el nombre igual (porque `EquipoCreate` lo exige), y al recorrer la lista el propio
equipo 1 aparecería como "un equipo que ya tiene ese nombre". Me devolvería 400 contra mí mismo, lo
cual no tiene sentido.

La regla que realmente quiero expresar no es "este nombre no puede existir", sino **"este nombre no
puede chocar con el de otro equipo"**. La condición del `id` es exactamente lo que traduce esa
diferencia a código.

Usé `.lower()` a propósito, para que sea el mismo criterio que ya usaba `crear_equipo`. Si al crear
"Proyector" y "proyector" se consideran duplicados, al actualizar tiene que pasar lo mismo; si no,
podría saltarme la regla creando un equipo con otro nombre y renombrándolo después con un PUT.

### 4. ¿Cómo maneja el caso de "equipo no encontrado"? ¿Qué código HTTP devuelve y por qué?

No lo manejo explícitamente dentro de `actualizar_equipo`. La primera línea de la función es:

```python
actual = obtener_equipo(equipo_id)
```

y `obtener_equipo` ya lanza `HTTPException(status_code=404, detail="Equipo no encontrado")` cuando no
encuentra el id. Como es una **excepción**, corta la ejecución justo ahí: nunca se llega a la
validación de duplicados ni a la asignación de valores. Eso me evita escribir un `if` extra y hace
que el 404 sea idéntico en el GET, el PUT y el DELETE, sin repetir el mensaje en tres lugares.

Devuelve **404 (Not Found)** porque el recurso que la URL identifica no existe. Vale la pena
contrastarlo con el otro error del mismo endpoint:

| Situación | Código | Razón |
|---|---|---|
| El id no existe | 404 | El recurso al que apunta la URL no está |
| El nombre ya es de otro equipo | 400 | El recurso existe, pero lo que pido viola una regla |

Son cosas distintas y por eso llevan códigos distintos. Un 400 diciendo "no encontrado" confundiría a
quien consume la API, porque le haría pensar que el problema está en cómo armó la petición.

---

## Sobre `DELETE /equipos/{equipo_id}` (eliminar)

### 5. ¿Qué recibe el endpoint y qué devuelve?

Recibe **solo** `equipo_id` en la ruta. No lleva cuerpo, porque para borrar algo no hace falta mandar
datos: basta con decir qué se borra.

Devuelve el equipo que acaba de ser eliminado, con código **200** y el mismo `EquipoResponse`.

Podría haber devuelto un **204 No Content** (respuesta vacía), que también es correcto para un DELETE.
Elegí devolver el objeto por dos motivos: sirve de confirmación de qué se borró exactamente (útil si
alguien se equivoca de id y quiere saber qué perdió), y me permite reutilizar `EquipoResponse` como
pedía el enunciado. Con 204 no habría cuerpo que modelar.

### 6. ¿Cómo elimina el equipo de la lista?

```python
def eliminar_equipo(equipo_id: int) -> dict:
    equipo = obtener_equipo(equipo_id)
    _equipos.remove(equipo)

    return equipo
```

Primero lo busco con `obtener_equipo`, que como expliqué me devuelve la referencia al diccionario que
está dentro de `_equipos`. Después `_equipos.remove(equipo)` lo saca de la lista.

Guardo la referencia en la variable **antes** de borrarlo, porque si no, al terminar la función ya no
tendría nada que devolver.

No usé `del _equipos[i]` porque no tengo el índice: `obtener_equipo` me da el objeto, no la posición.
Buscarlo otra vez solo para conseguir el índice sería recorrer la lista dos veces sin necesidad.

Una nota: `remove()` compara con `==`, y en Python dos diccionarios son iguales si tienen las mismas
claves y valores. Acá no es un problema porque los `id` son únicos y `_next_id` nunca se reutiliza
(sigue subiendo aunque borre elementos), así que jamás puede haber dos diccionarios idénticos en la
lista.

### 7. ¿Cómo maneja el caso de "equipo no encontrado"? ¿Qué código HTTP devuelve y por qué?

Exactamente igual que el PUT: `obtener_equipo` lanza el **404** antes de que se intente borrar nada,
así que la línea del `remove()` solo se ejecuta si el equipo realmente existe.

Se nota bien probándolo dos veces seguidas en Swagger: la primera vez que borro el id 3 me responde
200 con el objeto; la segunda vez, 404, porque ya no está. El razonamiento del código es el mismo que
en el PUT: la URL apunta a un recurso que no existe, y eso es un Not Found.

---

## Sobre la arquitectura

### 8. ¿Por qué la lógica va en `equipo_service.py` y los endpoints en `equipos.py`?

Porque son dos responsabilidades distintas y conviene que cada una viva en su propio archivo.

El **router** es la capa HTTP. Su único trabajo es traducir: recibe una petición web (un método, una
ruta, un cuerpo JSON), llama a la función que corresponde y devuelve el resultado. Por eso mis
endpoints son de una sola línea.

El **service** es la lógica de negocio: qué significa actualizar un equipo, qué reglas existen, cuándo
algo es inválido. Ese código no habla de rutas ni de métodos HTTP; habla de equipos.

Las ventajas concretas de separarlas:

- **Se puede probar sin levantar el servidor.** Puedo escribir tests que llamen a
  `actualizar_equipo()` directamente, sin peticiones HTTP de por medio. Son más rápidos y más fáciles
  de escribir.
- **Se puede cambiar el almacenamiento sin tocar los endpoints.** Hoy los datos viven en una lista en
  memoria. Si mañana lo paso a una base de datos, reescribo el service y el router queda intacto,
  porque sigue llamando a las mismas funciones con los mismos argumentos.
- **La lógica se reutiliza.** Si además de la API quisiera un comando de consola o una tarea
  programada que borre equipos, llamaría a `eliminar_equipo()` y las reglas serían las mismas. Si la
  lógica estuviera metida dentro del endpoint, tendría que copiarla, y dos copias de una regla
  terminan desincronizándose.
- **Se lee mejor.** Abriendo `equipos.py` veo de un vistazo qué endpoints existe la API, sin ruido.

Es el mismo motivo por el que el proyecto ya venía organizado así con las tres operaciones
originales: yo solo seguí el patrón que ya estaba.

### 9. ¿Qué papel juegan `EquipoCreate` y `EquipoResponse`?

Son los **contratos** de entrada y de salida, definidos con Pydantic. Cada uno cumple un papel
distinto:

**`EquipoCreate` valida lo que entra.**

```python
class EquipoCreate(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=80)
    categoria: str = Field(..., min_length=3, max_length=50)
```

Exige que lleguen ambos campos, que sean texto y que tengan un largo razonable. Si mando un JSON que
no cumple (falta un campo, el nombre tiene 2 letras, mando un número), FastAPI responde **422** con el
detalle del error y **mi función ni siquiera se ejecuta**. Eso significa que dentro del service puedo
asumir que los datos ya son válidos en cuanto a forma, y concentrarme solo en las reglas de negocio,
como el nombre duplicado.

Fijarse en lo que **no** incluye también dice mucho: no tiene `id` ni `disponible`, porque esos no los
decide el cliente. El `id` lo asigna el servidor y `disponible` es estado interno.

**`EquipoResponse` define lo que sale.**

Al declararlo en `response_model=EquipoResponse`, FastAPI filtra la respuesta a esos cuatro campos. Si
el diccionario interno tuviera datos extra, no se escaparían por accidente. Es una protección que
funciona sola.

Y algo que aplica a los dos: alimentan la documentación. Los esquemas, los ejemplos y el formulario
"Try it out" que aparecen en Swagger UI se generan a partir de estas clases. No escribí ni una línea
de documentación; salió de haber declarado bien los modelos.

Reutilizarlos en el PUT y el DELETE, en vez de inventar modelos nuevos, mantiene la API coherente: un
equipo se ve igual sin importar por cuál endpoint lo pidas.

### 10. ¿Qué es `HTTPException` y por qué se usa para reflejar errores?

Es una excepción que provee FastAPI. Cuando se lanza, FastAPI la atrapa y la convierte en una
respuesta HTTP de error con el `status_code` y el `detail` que le pasé:

```python
raise HTTPException(status_code=404, detail="Equipo no encontrado")
```

se convierte en una respuesta 404 con el cuerpo `{"detail": "Equipo no encontrado"}`.

Se usa por tres razones:

1. **Corta la ejecución en el punto exacto donde detecto el problema.** Al ser una excepción, no
   necesito devolver `None` o una bandera de error y después comprobarla en cada capa. En
   `actualizar_equipo` esto se ve claro: si el equipo no existe, la función se interrumpe en la
   primera línea y el resto ni se evalúa.
2. **Deja que el service exprese el error sin armar respuestas HTTP a mano.** El service no construye
   JSON ni maneja cabeceras; solo declara "esto es un 404" y FastAPI se encarga del resto.
3. **Da códigos de estado semánticamente correctos.** La alternativa sería devolver 200 con un mensaje
   de error dentro del cuerpo, y eso está mal: un programa que consuma la API mira el código de
   estado, no el texto. Si respondo 200, el cliente cree que todo salió bien. Con 404 y 400 cualquier
   consumidor entiende qué pasó sin tener que leer el mensaje.

---

## Resumen de lo probado en Swagger UI

| Operación | Petición | Resultado |
|---|---|---|
| Crear | `POST /equipos/` | 201 con el equipo creado |
| Listar | `GET /equipos/` | 200 con la lista |
| Consultar | `GET /equipos/{id}` | 200 con el equipo |
| Actualizar | `PUT /equipos/1` | 200 con el equipo actualizado |
| Actualizar con nombre de otro | `PUT /equipos/1` | 400 "Ya existe otro equipo con ese nombre" |
| Actualizar id inexistente | `PUT /equipos/99` | 404 "Equipo no encontrado" |
| Eliminar | `DELETE /equipos/3` | 200 con el equipo eliminado |
| Eliminar el mismo otra vez | `DELETE /equipos/3` | 404 "Equipo no encontrado" |
