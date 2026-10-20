from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import URL

ROOT_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", extra="ignore")

    postgres_user: str
    postgres_password: str
    postgres_db: str
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    jwt_secret: str = ""
    jwt_expire_minutes: int = 60
    upload_dir: str = "uploads"
    max_image_bytes: int = 5 * 1024 * 1024
    link_radius_m: float = 50
    link_window_days: int = 30
    link_weight_geo: float = 0.5
    link_weight_category: float = 0.3
    link_weight_recency: float = 0.2
    # report locations outside this box are refused; all four unset means no check
    region_min_lat: float | None = None
    region_max_lat: float | None = None
    region_min_lng: float | None = None
    region_max_lng: float | None = None
    text_model_path: str = "ml/models/text_classifier.joblib"
    text_confidence_threshold: float = 0.5
    frontend_origin: str = "http://localhost:5173"
    admin_name: str = "Admin"
    admin_email: str = ""
    admin_password: str = ""

    @property
    def database_url(self) -> str:
        url = URL.create(
            "postgresql+psycopg",
            username=self.postgres_user,
            password=self.postgres_password,
            host=self.postgres_host,
            port=self.postgres_port,
            database=self.postgres_db,
        )
        return url.render_as_string(hide_password=False)

    @property
    def upload_path(self) -> Path:
        path = Path(self.upload_dir)
        return path if path.is_absolute() else ROOT_DIR / path

    @property
    def text_model_file(self) -> Path:
        path = Path(self.text_model_path)
        return path if path.is_absolute() else ROOT_DIR / path


settings = Settings()
