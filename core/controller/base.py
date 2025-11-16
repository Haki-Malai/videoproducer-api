from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy.exc import IntegrityError

from core.database import Base
from core.exceptions import BadRequestException, NotFoundException
from core.repository import BaseRepository

ModelType = TypeVar("ModelType", bound=Base)


class BaseController(Generic[ModelType]):
    """Base class for data controllers."""

    def __init__(self, model: type[ModelType], repository: BaseRepository):
        self.model_class = model
        self.repository = repository

    async def create(self, attributes: dict[str, Any]) -> ModelType:
        """Creates a new Object in the DB.

        :param attributes: The attributes to create the object with.

        :return: The created object.
        """
        try:
            return await self.repository.create(attributes)
        except IntegrityError as e:
            raise BadRequestException(f"Database Integrity Error: {e.orig}")

    async def get_all(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        """Returns a list of records based on pagination params.

        :param skip: The number of records to skip.
        :param limit: The number of records to return.

        :return: A list of records.
        """

        return await self.repository.get_all(skip, limit)

    async def get_filtered(
        self, filters: dict[str, Any] | None = None, skip: int = 0, limit: int = 100
    ) -> Sequence[ModelType]:
        """Retrieves a filtered list of model instances based on provided filters.

        :param filters: A dictionary where keys are the model fields and values are the values to filter by.
        :param skip: The number of records to skip.
        :param limit: The number of records to return.

        :return: A list of model instances.
        """
        return await self.repository.get_filtered(filters, skip, limit)

    async def get_by_id(self, id_: int) -> ModelType | None:
        """Returns the model instance matching the id.

        :param id_: The id to match.

        :return: The model instance.
        """

        db_obj = await self.repository.get_by(field="id", value=id_, unique=True)
        if not db_obj:
            raise NotFoundException(
                f"{self.model_class.__tablename__.title()} with id: {id} does not exist"
            )

        return db_obj

    async def update(self, id_: int, attributes: dict[str, Any]) -> ModelType:
        """Updates the Object in the DB.

        :param id_: The id of the object to update.
        :param attributes: The attributes to update the object with.

        :return: The updated object.
        """
        db_obj = await self.get_by_id(id_)
        return await self.repository.update(db_obj, attributes)

    async def delete(self, id_: int) -> None:
        """Deletes the Object from the DB.

        :param id_: The id of the object to delete.

        :return: True if the object was deleted, False otherwise.
        """
        db_obj = await self.get_by_id(id_)
        return await self.repository.delete(db_obj)
