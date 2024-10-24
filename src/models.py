from pydantic import BaseModel, Field, field_validator


# --- LADDER CLASSES ---
class Stats(BaseModel):
    played: int
    wins: int
    drawn: int
    lost: int
    byes: int
    points_for: int = Field(
        validation_alias="points for", serialization_alias="pointsFor"
    )
    points_against: int = Field(
        validation_alias="points against", serialization_alias="pointsAgainst"
    )
    points_diff: int = Field(
        validation_alias="points difference", serialization_alias="pointsDiff"
    )
    home_record: str = Field(
        validation_alias="home record", serialization_alias="homeRecord"
    )
    away_record: str = Field(
        validation_alias="away record", serialization_alias="awayRecord"
    )
    points: int
    bonus_points: int = Field(
        validation_alias="bonus points", serialization_alias="bonusPoints"
    )
    streak: str
    form: str
    avg_loss_margin: float | int = Field(
        validation_alias="average losing margin",
        serialization_alias="averageLossMargin",
    )
    avg_win_margin: float | int = Field(
        validation_alias="average winning margin",
        serialization_alias="averageWinMargin",
    )
    golden_point: int = Field(
        validation_alias="golden point", serialization_alias="goldenPoint"
    )
    day_record: str = Field(
        validation_alias="day record", serialization_alias="dayRecord"
    )
    night_record: str = Field(
        validation_alias="night record", serialization_alias="nightRecord"
    )
    players_used: int = Field(
        validation_alias="players used", serialization_alias="playerUsed"
    )
    odds: str | float | None = Field(default=None)

    @field_validator("avg_loss_margin", "avg_win_margin")
    @classmethod
    def force_float_conversion(cls, v: float | int) -> float:
        return v if isinstance(v, float) else float(v)

    @field_validator("odds")
    @classmethod
    def convert_string_to_float(cls, v: str) -> float:
        new_val = v.replace("$", "")
        return float(new_val)


class Ladder(BaseModel):
    name: str
    stats: Stats
