from fastapi import APIRouter, status

from app.schemas.equipo import EquipoCreate, EquipoResponse
from app.services.equipo_service import (
    actualizar_equipo,
    crear_equipo,
    eliminar_equipo,
    listar_equipos,
    obtener_equipo,
)

router = APIRouter(prefix="/equipos", tags=["Equipos"])


@router.get("/", response_model=list[EquipoResponse])
def get_equipos():
    return listar_equipos()


@router.get("/{equipo_id}", response_model=EquipoResponse)
def get_equipo(equipo_id: int):
    return obtener_equipo(equipo_id)


@router.post("/", response_model=EquipoResponse, status_code=status.HTTP_201_CREATED)
def post_equipo(equipo: EquipoCreate):
    return crear_equipo(equipo)


@router.put("/{equipo_id}", response_model=EquipoResponse)
def put_equipo(equipo_id: int, equipo: EquipoCreate):
    return actualizar_equipo(equipo_id, equipo)


@router.delete("/{equipo_id}", response_model=EquipoResponse)
def delete_equipo(equipo_id: int):
    return eliminar_equipo(equipo_id)
