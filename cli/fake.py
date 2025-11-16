import asyncio
import random
import uuid
from typing import Sequence

import typer
from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Flight, FlightStatus, FlightTheme, Role, User
from core.config import config
from core.database.migration import prepare_database

app = typer.Typer(help="Generate fake demo data for SkyFlow.")
faker = Faker()

DRONE_TYPES = [
    "Cinewhoop HD",
    "FPV Freestyle",
    "Race Quad",
    "Camera Drone",
    "Long Range FPV",
]
VIDEO_EXTENSIONS = ("mp4", "mov", "mkv")
THEMES = list(FlightTheme)
STATUS_WEIGHTS: dict[FlightStatus, float] = {
    FlightStatus.PENDING: 0.5,
    FlightStatus.APPROVED: 0.35,
    FlightStatus.REJECTED: 0.15,
}


def _unique_username() -> str:
    """Build a username that is unlikely to collide with existing records."""
    suffix = uuid.uuid4().hex[:5]
    base = faker.user_name().replace(".", "_")
    return f"{base}_{suffix}"


def _random_tags() -> list[str]:
    """Generate a deduplicated list of short tags."""
    tags = faker.words(nb=random.randint(2, 4))
    seen: dict[str, None] = {}
    for tag in tags:
        normalized = tag.lower().replace(" ", "-")
        seen.setdefault(normalized, None)
    return list(seen.keys())


async def _create_demo_users(
    session: AsyncSession,
    count: int,
    password: str,
) -> list[User]:
    """Create demo users and flush them so they receive database IDs."""
    users: list[User] = []
    for _ in range(count):
        username = _unique_username()
        email_domain = faker.free_email_domain()
        user = User(
            username=username,
            role=Role.USER,
            display_name=faker.name(),
            email=f"{username}@{email_domain}",
            country_code=faker.country_code(representation="alpha-2"),
            total_credits=random.randint(25, 500),
            instagram_url=f"https://instagram.com/{username}",
            youtube_url=f"https://youtube.com/@{username.replace('_', '')}",
            website_url=f"https://{faker.domain_name()}",
        )
        user.password = password
        session.add(user)
        users.append(user)
    await session.flush()
    return users


def _pick_status() -> FlightStatus:
    statuses = list(STATUS_WEIGHTS.keys())
    weights = list(STATUS_WEIGHTS.values())
    return random.choices(statuses, weights=weights, k=1)[0]


async def _create_demo_flights(
    session: AsyncSession,
    users: Sequence[User],
    flights_per_user: int,
) -> int:
    """Create demo flights associated with the provided users."""
    if flights_per_user <= 0 or not users:
        return 0

    flights_created = 0
    for user in users:
        for _ in range(flights_per_user):
            status = _pick_status()
            views = random.randint(0, 5000)
            likes = random.randint(0, views) if views else 0

            approved_at = None
            rejected_reason = None
            if status == FlightStatus.APPROVED:
                approved_at = faker.date_time_between(start_date="-90d", end_date="now")
            elif status == FlightStatus.REJECTED:
                rejected_reason = faker.sentence(nb_words=10)

            flight = Flight(
                pilot=user,
                status=status,
                video_path=f"/videos/{uuid.uuid4()}.{random.choice(VIDEO_EXTENSIONS)}",
                title=faker.sentence(nb_words=6).rstrip("."),
                description=faker.paragraph(nb_sentences=3),
                lat=round(random.uniform(-75, 75), 6),
                lng=round(random.uniform(-170, 170), 6),
                country_code=user.country_code
                or faker.country_code(representation="alpha-2"),
                drone_type=random.choice(DRONE_TYPES),
                duration_seconds=random.randint(45, 240),
                theme=random.choice(THEMES),
                tags=_random_tags(),
                credits=random.randint(1, 10),
                views=views,
                likes=likes,
                approved_at=approved_at,
                rejected_reason=rejected_reason,
            )
            session.add(flight)
            flights_created += 1

    await session.flush()
    return flights_created


async def _async_generate_fake_data(
    user_count: int,
    flights_per_user: int,
    password: str,
) -> tuple[int, int]:
    """Async portion of the fake data generator."""
    await prepare_database()
    engine = create_async_engine(str(config.SQLALCHEMY_DATABASE_URI))
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    try:
        async with session_factory() as session:
            users = await _create_demo_users(session, user_count, password)
            flights = await _create_demo_flights(
                session,
                users,
                flights_per_user,
            )
            await session.commit()
    finally:
        await engine.dispose()

    return len(users), flights


@app.command("generate")
def generate(
    users: int = typer.Option(
        5,
        "--users",
        "-u",
        min=1,
        help="Number of fake users to create.",
    ),
    flights_per_user: int = typer.Option(
        2,
        "--flights-per-user",
        "-f",
        min=0,
        help="How many flights should be attached to every generated user.",
    ),
    password: str = typer.Option(
        "FlyDemo123!",
        "--password",
        "-p",
        help="Password applied to every generated user for quick testing.",
    ),
):
    """Generate fake users and flights for demonstration purposes."""

    created_users, created_flights = asyncio.run(
        _async_generate_fake_data(users, flights_per_user, password)
    )
    typer.echo(
        f"Created {created_users} users and {created_flights} flights with password '{password}'."
    )
