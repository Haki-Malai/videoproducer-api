from functools import partial

from fastapi import Depends

from app.controllers import FlightController, UserController
from app.models import Flight, User
from app.repositories import FlightRepository, UserRepository
from core.database import get_session


class Factory:
    user_repository = partial(UserRepository, User)
    flight_repository = partial(FlightRepository, Flight)

    def get_user_controller(self, db_session=Depends(get_session)):
        return UserController(
            user_repository=self.user_repository(db_session=db_session)
        )

    def get_flight_controller(self, db_session=Depends(get_session)):
        return FlightController(
            flight_repository=self.flight_repository(db_session=db_session),
            user_repository=self.user_repository(db_session=db_session),
        )
