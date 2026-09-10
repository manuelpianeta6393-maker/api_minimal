from fastapi import HTTPException

from app.schemas.equipo import EquipoCreate

_equipos: list[dict] = []
_next_id = 1


def listar_equipos() -> list[dict]:
    return _equipos


def obtener_equipo(equipo_id: int) -> dict:
    for e in _equipos:
        if e["id"] == equipo_id:
            return e
    raise HTTPException(
        status_code=404,
        detail="Equipo no encontrado",
    )


def crear_equipo(equipo: EquipoCreate) -> dict:
    global _next_id

    existe = any(
        e["nombre"].lower() == equipo.nombre.lower() for e in _equipos
    )
    if existe:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un equipo con ese nombre",
        )

    nuevo = {
        "id": _next_id,
        "nombre": equipo.nombre,
        "categoria": equipo.categoria,
        "disponible": True,
    }
    _equipos.append(nuevo)
    _next_id += 1

    return nuevo


def actualizar_equipo(equipo_id: int, equipo: EquipoCreate) -> dict:
    actual = obtener_equipo(equipo_id)

    duplicado = any(
        e["id"] != equipo_id and e["nombre"].lower() == equipo.nombre.lower()
        for e in _equipos
    )
    if duplicado:
        raise HTTPException(
            status_code=400,
            detail="Ya existe otro equipo con ese nombre",
        )

    actual["nombre"] = equipo.nombre
    actual["categoria"] = equipo.categoria

    return actual


def eliminar_equipo(equipo_id: int) -> dict:
    equipo = obtener_equipo(equipo_id)
    _equipos.remove(equipo)

    return equipo
