from datetime import datetime

import pandas as pd
import polars as pl
import pytest
from pydantic import BaseModel

from xin.parser import deserialize_pydantic_objects, flatten, serialize_table


@pytest.mark.asyncio
async def test_serialize_pandas_table() -> None:
    now = datetime.now()
    data1 = {"n": "xin", "id": 200, "f": ["a", "b", "c"], "c": now, "b": 20.0, "d": {"a": 1}}
    data2 = {"n": "xin", "id": 200, "f": ["d", "e", "f"], "c": now, "b": None, "d": {"a": 1}}

    pydantic_objects = await serialize_table(table_name="some_table", data=pd.DataFrame(data=[data1, data2]))

    assert isinstance(pydantic_objects, list)
    for entry in pydantic_objects:
        assert isinstance(entry, BaseModel)
        assert len(entry.model_fields.keys()) >= 5


@pytest.mark.asyncio
async def test_serialize_polars_table() -> None:
    pass


@pytest.mark.asyncio
async def test_flatten() -> None:
    data = [
        {
            "id": 1,
            "name": "Cole Volk",
            "fitness": {"height": 130, "weight": 60},
        },
        {"name": "Mark Reg", "fitness": {"height": 130, "weight": 60}},
        {
            "id": 2,
            "name": "Faye Raker",
            "fitness": {"height": 130, "weight": 60},
        },
    ]

    df_pandas = pd.DataFrame(data=data)
    df_polars = pl.DataFrame(data=data)

    flat_df = await flatten(data=df_pandas, depth=0)
    assert isinstance(flat_df, pl.DataFrame)
    assert flat_df.shape[1] == df_polars.shape[1]

    flat_df = await flatten(data=df_polars, depth=0)
    assert isinstance(flat_df, pl.DataFrame)
    assert flat_df.shape[1] == df_polars.shape[1]
    for col in flat_df.columns:
        assert col in df_polars.columns
    for col in df_polars.columns:
        assert col in flat_df.columns

    flat_df = await flatten(data=df_polars, depth=1)
    assert isinstance(flat_df, pl.DataFrame)
    assert flat_df.shape[1] == df_polars.shape[1] + 1
    assert "fitness" not in flat_df.columns
    assert "fitness.height" in flat_df.columns
    assert "fitness.weight" in flat_df.columns


@pytest.mark.asyncio
async def test_deserialize_models() -> None:
    class DummyModel(BaseModel):
        x: int
        y: float

    models = [DummyModel(x=1, y=2.0), DummyModel(x=10, y=-1.9)]
    df = await deserialize_pydantic_objects(models=models)

    assert isinstance(df, pl.DataFrame)
    assert df.shape[0] == 2
    assert df.shape[1] == 2
