from fastapi import APIRouter, Depends, HTTPException, Request


from dependencies import get_token_header
import utils

import jsonschema
from jsonschema import validate
import importlib
import os
import sys
from yorm import yormtools

router = APIRouter(
    prefix="/data",
    tags=[],
    dependencies=[],
    responses={404: {"description": "Not found"}},
)


@router.get("/yorm-map", summary="Get all Olympics")
async def map():
    return yormtools.get_map()
 

@router.get("/{model}", summary="Get all Items from a yorm directory")
async def all(model):
    data = yormtools.get_route_model_class(model).objects.get()
    return data

@router.get("/{model}/{name}", summary="Get an Item by name")
async def get(model,name):
    data =  yormtools.get_route_model_class(model).objects.get(name=name)

    return data

@router.post("/{model}/{name}/update", summary="Update a item")
async def update(model,name, request : Request):
    data = await request.json()
    print(data)
    old = yormtools.get_route_model_class(model).objects.get(name=name).dump()
    response = yormtools.get_route_model_class(model).objects.update(data,name=name)
    print(response)
    await utils.websockets.manager.broadcast({
        "action" : "update",
        "model": model,
        "old": old,
        "data": response.dump()
    })
    return response
 

@router.post("/{model}/create", summary="Create a new item")
async def create(model,request : Request):
    data = await request.json()
    await utils.websockets.manager.broadcast({
        "action" : "create",
        "model": model
    })
    return yormtools.get_route_model_class(model).objects.create(data)


@router.get("/{model}/{name}/delete", summary="Delete an item")
async def delete(model,name):
    await utils.websockets.manager.broadcast({
        "action" : "delete",
        "model": model
    })
    return yormtools.get_route_model_class(model).objects.delete(name=name)