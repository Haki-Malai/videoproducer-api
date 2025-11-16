import asyncio
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.models import Flight
from core.celery_app import celery_app
from core.config import config
from core.storage import s3

logger = logging.getLogger(__name__)

HLS_ROOT = Path("uploads/hls")


async def _async_process_new_flight(flight_id: int) -> None:
    """Async part of the HLS pipeline for a new flight.
    
    :param flight_id: ID of the flight to process.
    """
    engine = create_async_engine(str(config.SQLALCHEMY_DATABASE_URI))
    session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine, expire_on_commit=False
    )

    try:
        async with session_factory() as session:
            flight = await session.get(Flight, flight_id)
            if not flight:
                logger.warning("Flight %s not found; skipping", flight_id)
                return

            # Fetch the source video either from disk or S3
            source_ref = flight.video_path
            if not source_ref:
                logger.warning("Flight %s has no source video reference", flight_id)
                return
            temp_dir: Path | None = None

            try:
                if s3.is_s3_uri(source_ref):
                    temp_dir = Path(tempfile.mkdtemp(prefix="flight-src-"))
                    src_path = temp_dir / "source_video"
                    logger.info(
                        "Downloading source video for flight %s from %s",
                        flight_id,
                        source_ref,
                    )
                    s3.download_file(source_ref, str(src_path))
                else:
                    src_path = Path(source_ref)
                    if not src_path.is_absolute():
                        src_path = Path.cwd() / src_path

                if not src_path.exists():
                    logger.warning(
                        "Source video not found for flight %s at %s",
                        flight_id,
                        src_path,
                    )
                    return

                # Local HLS output directory
                out_dir = HLS_ROOT / str(flight_id)
                out_dir.mkdir(parents=True, exist_ok=True)
                manifest_path = out_dir / "index.m3u8"

                # Simple HLS generation: copy codecs, no re-encode (fast for dev)
                cmd = [
                    "ffmpeg",
                    "-y",
                    "-i",
                    str(src_path),
                    "-codec",
                    "copy",
                    "-start_number",
                    "0",
                    "-hls_time",
                    "4",
                    "-hls_playlist_type",
                    "vod",
                    "-hls_segment_filename",
                    str(out_dir / "segment_%03d.ts"),
                    str(manifest_path),
                ]
                logger.info("Running ffmpeg for flight %s", flight_id)
                subprocess.run(
                    cmd,
                    check=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )

                # Upload HLS assets to S3/MinIO
                for path in sorted(out_dir.iterdir()):
                    if path.is_dir():
                        continue

                    name = path.name
                    key = f"hls/{flight_id}/{name}"

                    if name.endswith(".m3u8"):
                        content_type = "application/vnd.apple.mpegurl"
                    elif name.endswith(".ts"):
                        content_type = "video/MP2T"
                    else:
                        content_type = "application/octet-stream"

                    s3.upload_file(str(path), key, content_type=content_type)

                manifest_key = f"hls/{flight_id}/index.m3u8"
                public_url = s3.build_public_url(manifest_key)

                flight.video_path = public_url
                await session.commit()

                logger.info(
                    "Flight %s HLS published at %s",
                    flight_id,
                    public_url,
                )
            finally:
                if temp_dir:
                    shutil.rmtree(temp_dir, ignore_errors=True)
    except Exception:  # noqa: BLE001 - log everything here
        logger.exception("Error while processing flight %s", flight_id)
        raise
    finally:
        await engine.dispose()


@celery_app.task(name="flights.process_new_flight")
def process_new_flight(flight_id: int) -> None:
    """Background processing for a newly submitted flight.

    Currently:
      - converts the uploaded MP4 into HLS segments,
      - uploads them to S3/MinIO,
      - updates Flight.video_path to the HLS manifest URL.

    :param flight_id: ID of the flight to process.
    """
    asyncio.run(_async_process_new_flight(flight_id))
