"""Weather retrieval and deterministic, hourly solar estimation."""

from datetime import date, timedelta

import httpx
import pandas as pd
import pvlib
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models import Setup, WeatherCache, utcnow

HOURLY_FIELDS = (
    "shortwave_radiation,direct_normal_irradiance,diffuse_radiation,"
    "temperature_2m,wind_speed_10m,cloud_cover"
)


def default_dates() -> tuple[date, date]:
    end = date.today() - timedelta(days=1)
    return end - timedelta(days=29), end


def validate_dates(start: date, end: date) -> None:
    if start > end or end >= date.today() or start < date.today() - timedelta(days=365):
        raise HTTPException(422, "Choose one day to one year of past dates.")


def fetch_weather(db: Session, setup: Setup, start: date, end: date, force: bool = False) -> dict:
    validate_dates(start, end)
    key = f"{setup.latitude:.4f}:{setup.longitude:.4f}:{start}:{end}"
    cached = db.scalar(select(WeatherCache).where(WeatherCache.cache_key == key))
    if cached and not force:
        return cached.payload
    try:
        response = httpx.get(
            "https://archive-api.open-meteo.com/v1/archive",
            params={
                "latitude": setup.latitude,
                "longitude": setup.longitude,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "hourly": HOURLY_FIELDS,
                "timezone": "auto",
                "timeformat": "unixtime",
            },
            timeout=30,
        )
        response.raise_for_status()
        payload = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, "Weather service is unavailable. Please try again.") from exc
    hourly = payload.get("hourly") or {}
    if not hourly.get("time"):
        raise HTTPException(502, "Weather service returned no hourly data.")
    timezone_name = payload.get("timezone") or "UTC"
    try:
        expected = pd.date_range(
            start=f"{start} 00:00",
            end=f"{end + timedelta(days=1)} 00:00",
            freq="h",
            inclusive="left",
            tz=timezone_name,
        )
        actual = pd.to_datetime(hourly["time"], unit="s", utc=True).tz_convert(timezone_name)
        if len(actual) != len(expected) or not actual.equals(expected):
            raise HTTPException(502, "Weather service returned an incomplete date range.")
    except (KeyError, TypeError, ValueError) as exc:
        raise HTTPException(502, "Weather service returned invalid hourly dates.") from exc
    if cached:
        cached.payload = payload
        cached.fetched_at = utcnow()
    else:
        db.add(WeatherCache(cache_key=key, payload=payload))
    db.commit()
    return payload


def estimate(setup: Setup, weather: dict) -> dict:
    hourly = weather.get("hourly", {})
    required = [
        "time",
        "shortwave_radiation",
        "direct_normal_irradiance",
        "diffuse_radiation",
        "temperature_2m",
        "wind_speed_10m",
        "cloud_cover",
    ]
    if any(not hourly.get(field) for field in required):
        raise HTTPException(422, "Some required weather values are missing.")
    lengths = {len(hourly[key]) for key in required}
    if len(lengths) != 1:
        raise HTTPException(422, "Weather contains missing hours. This estimate is incomplete.")
    rows = pd.DataFrame({key: hourly[key] for key in required})
    if rows.isna().any().any():
        raise HTTPException(422, "Weather contains missing hours. This estimate is incomplete.")
    if rows["time"].duplicated().any():
        raise HTTPException(422, "Weather contains duplicate hours.")
    if rows["time"].sort_values().diff().dropna().ne(3600).any():
        raise HTTPException(422, "Weather contains missing hours. This estimate is incomplete.")
    timezone_name = weather.get("timezone", "UTC")
    times = pd.to_datetime(rows["time"], unit="s", utc=True).dt.tz_convert(timezone_name)
    sun = pvlib.solarposition.get_solarposition(
        times - pd.Timedelta(minutes=30), setup.latitude, setup.longitude
    )
    sunlight = pvlib.irradiance.get_total_irradiance(
        surface_tilt=setup.tilt,
        surface_azimuth=setup.orientation,
        solar_zenith=sun["apparent_zenith"].to_numpy(),
        solar_azimuth=sun["azimuth"].to_numpy(),
        dni=rows["direct_normal_irradiance"].clip(lower=0).to_numpy(),
        ghi=rows["shortwave_radiation"].clip(lower=0).to_numpy(),
        dhi=rows["diffuse_radiation"].clip(lower=0).to_numpy(),
    )["poa_global"]
    poa = (
        pd.Series(sunlight.to_numpy() if hasattr(sunlight, "to_numpy") else sunlight)
        .fillna(0)
        .clip(lower=0)
    )
    wind_m_s = rows["wind_speed_10m"].clip(lower=0) / 3.6
    cell_temp = pvlib.temperature.faiman(poa, rows["temperature_2m"], wind_speed=wind_m_s)
    rated_w = setup.panel_count * setup.panel.rated_w
    dc = pvlib.pvsystem.pvwatts_dc(
        poa,
        cell_temp,
        pdc0=rated_w,
        gamma_pdc=setup.panel.temp_coefficient,
    )
    ac = pvlib.inverter.pvwatts(
        pd.Series(dc).clip(lower=0) * (1 - setup.loss_pct / 100),
        pdc0=rated_w,
    )
    hourly_result = pd.DataFrame(
        {
            "date": times.dt.date.astype(str),
            "kwh": pd.Series(ac).fillna(0).clip(lower=0) / 1000,
            "cloud": rows["cloud_cover"],
        }
    )
    daily = hourly_result.groupby("date", sort=True).agg(
        kwh=("kwh", "sum"), cloud_pct=("cloud", "mean"), hours=("kwh", "size")
    )
    data = [
        {
            "date": str(day),
            "kwh": round(float(row.kwh), 2),
            "cloud_pct": round(float(row.cloud_pct)),
            "hours": int(row.hours),
        }
        for day, row in daily.iterrows()
    ]
    latest_day = data[-1]["date"] if data else None
    day_curve = [
        {"hour": int(times.iloc[index].hour), "kwh": round(float(kwh), 3)}
        for index, kwh in enumerate(hourly_result["kwh"])
        if hourly_result.iloc[index]["date"] == latest_day
    ]
    return {
        "daily": data,
        "day_curve": day_curve,
        "total_kwh": round(float(hourly_result["kwh"].sum()), 2),
        "rated_kw": round(rated_w / 1000, 3),
        "area_m2": round(setup.panel_count * setup.panel.area_m2, 2),
        "timezone": timezone_name,
        "source": "Open-Meteo Historical Weather API",
        "model": "pvlib PVWatts v1",
    }


def geocode(query: str) -> list[dict]:
    if len(query.strip()) < 2:
        return []
    try:
        response = httpx.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": query, "count": 6, "language": "en", "format": "json"},
            timeout=15,
        )
        response.raise_for_status()
        return [
            {
                "name": ", ".join(
                    filter(None, [place.get("name"), place.get("admin1"), place.get("country")])
                ),
                "latitude": place["latitude"],
                "longitude": place["longitude"],
            }
            for place in response.json().get("results", [])
        ]
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, "Location search is unavailable.") from exc
