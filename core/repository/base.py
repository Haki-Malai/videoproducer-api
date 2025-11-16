from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import select

from core.database import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Base class for data repositories."""

    def __init__(self, model: type[ModelType], db_session: AsyncSession):
        self.session: AsyncSession = db_session
        self.model_class: type[ModelType] = model

    async def create(self, attributes: dict[str, Any] | None = None) -> ModelType:
        """Creates the model instance.

        :param attributes: The attributes to create the model with.

        :return: The created model instance.
        """
        if attributes is None:
            attributes = {}
        model = self.model_class(**attributes)
        self.session.add(model)
        await self.session.commit()
        return model

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        """Returns a list of model instances.

        :param skip: The number of records to skip.
        :param limit: The number of record to return.

        :return: A list of model instances.
        """
        query = select(self.model_class)
        query = query.offset(skip).limit(limit)

        return await self._all_unique(query)

    async def get_filtered(
        self, filters: dict[str, Any] | None = None, skip: int = 0, limit: int = 100
    ) -> Sequence[ModelType]:
        """Retrieves a filtered list of model instances based on provided filters.

        :param filters: A dictionary where keys are the model fields and values are the values to filter by.
        :param skip: The number of records to skip.
        :param limit: The number of records to return.

        :return: A list of model instances.
        """
        query = select(self.model_class)
        if filters:
            for field, value in filters.items():
                if isinstance(value, tuple | list) and len(value) == 2:
                    query = query.where(
                        getattr(self.model_class, field).between(*value)
                    )
                else:
                    query = query.where(getattr(self.model_class, field) == value)

        query = query.offset(skip).limit(limit)
        return await self._all_unique(query)

    async def get_by(
        self,
        field: str,
        value: Any,
        unique: bool = False,
    ) -> ModelType | Sequence[ModelType] | None:
        """Returns the model instance matching the field and value.

        :param field: The field to match.
        :param value: The value to match.

        :return: The model instance.
        """
        query = select(self.model_class)
        query = await self._get_by(query, field, value)
        if unique:
            return await self._one(query)

        return await self._all(query)

    async def update(self, model: ModelType, attributes: dict[str, Any]) -> ModelType:
        """Updates the model instance.

        :param model: The model to update.
        :param attributes: The attributes to update the model with.

        :return: The updated model instance.
        """
        for key, value in attributes.items():
            if value:
                setattr(model, key, value)

        self.session.add(model)
        await self.session.commit()
        return model

    async def delete(self, model: ModelType) -> None:
        """Deletes the model.

        :param model: The model to delete.
        """
        await self.session.delete(model)
        await self.session.commit()

    async def _all(self, query: Select) -> Sequence[ModelType]:
        """Returns all results from the query.

        :param query: The query to execute.

        :return: A list of model instances.
        """
        result = await self.session.execute(query)
        return result.scalars().all()

    async def _all_unique(self, query: Select) -> Sequence[ModelType]:
        """Returns all unique results from the query.

        :param query: The query to execute.

        :return: A list of unique model instances.
        """
        result = await self.session.execute(query)
        return result.scalars().all()

    async def _first(self, query: Select) -> ModelType | None:
        """Returns the first result from the query.

        :param query: The query to execute.

        :return: The first model instance.
        """
        results = await self.session.execute(query)

        return results.scalar()

    async def _one(self, query: Select) -> ModelType | None:
        """Returns the first result from the query or raises NoResultFound.

        :param query: The query to execute.

        :return: The first model instance.
        """
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_by(self, query: Select, field: str, value: Any) -> Select:
        """Returns the query filtered by the given column.

        :param query: The query to filter.
        :param field: The column to filter by.
        :param value: The value to filter by.

        :return: The filtered query.
        """
        return query.where(getattr(self.model_class, field) == value)
