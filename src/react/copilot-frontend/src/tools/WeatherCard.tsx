import type { CurrentWeather, GeocodedCity } from "../lib/openMeteoClient";
import { describeWeatherCode } from "../lib/openMeteoClient";

interface WeatherCardProps {
  city: GeocodedCity;
  weather: CurrentWeather;
}

export function WeatherCard({ city, weather }: WeatherCardProps) {
  const label = describeWeatherCode(weather.weatherCode);
  const location = city.country ? `${city.name}, ${city.country}` : city.name;
  return (
    <div
      data-testid="weather-card"
      style={{
        border: "1px solid #d1d5db",
        borderRadius: 8,
        padding: 12,
        margin: "8px 0",
        background: "#f9fafb",
        maxWidth: 320,
      }}
    >
      <div style={{ fontWeight: 600, marginBottom: 4 }}>{location}</div>
      <div style={{ fontSize: "1.4rem", margin: "4px 0" }}>
        {weather.temperatureC.toFixed(0)}°C
      </div>
      <div style={{ color: "#4b5563", fontSize: "0.9rem" }}>
        {label} · wind {weather.windSpeedKmh.toFixed(0)} km/h
      </div>
    </div>
  );
}
