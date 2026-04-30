/**
 * Thin client for the public Open-Meteo APIs (no API key required).
 *
 * - Geocoding:  https://geocoding-api.open-meteo.com/v1/search
 * - Forecast:   https://api.open-meteo.com/v1/forecast
 *
 * Functions are pure (no React, no global state) so they're easy to mock
 * from Playwright via route interception.
 */

const GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search";
const FORECAST_URL = "https://api.open-meteo.com/v1/forecast";

export interface GeocodedCity {
  name: string;
  country: string;
  latitude: number;
  longitude: number;
}

export interface CurrentWeather {
  temperatureC: number;
  windSpeedKmh: number;
  weatherCode: number;
}

export interface OpenMeteoError {
  kind: "not_found" | "network" | "unexpected";
  message: string;
}

export type Result<T> = { ok: true; value: T } | { ok: false; error: OpenMeteoError };

export async function geocodeCity(city: string): Promise<Result<GeocodedCity>> {
  const url = `${GEOCODING_URL}?name=${encodeURIComponent(city)}&count=1&language=en&format=json`;
  let response: Response;
  try {
    response = await fetch(url);
  } catch (e) {
    return { ok: false, error: { kind: "network", message: errorMessage(e) } };
  }
  if (!response.ok) {
    return {
      ok: false,
      error: { kind: "network", message: `Geocoding HTTP ${response.status}` },
    };
  }
  const json = (await response.json()) as { results?: Array<Record<string, unknown>> };
  const first = json.results?.[0];
  if (!first || typeof first.latitude !== "number" || typeof first.longitude !== "number") {
    return { ok: false, error: { kind: "not_found", message: `No match for "${city}"` } };
  }
  return {
    ok: true,
    value: {
      name: typeof first.name === "string" ? first.name : city,
      country: typeof first.country === "string" ? first.country : "",
      latitude: first.latitude,
      longitude: first.longitude,
    },
  };
}

export async function fetchCurrentWeather(
  latitude: number,
  longitude: number,
): Promise<Result<CurrentWeather>> {
  const url = `${FORECAST_URL}?latitude=${latitude}&longitude=${longitude}&current_weather=true`;
  let response: Response;
  try {
    response = await fetch(url);
  } catch (e) {
    return { ok: false, error: { kind: "network", message: errorMessage(e) } };
  }
  if (!response.ok) {
    return {
      ok: false,
      error: { kind: "network", message: `Forecast HTTP ${response.status}` },
    };
  }
  const json = (await response.json()) as { current_weather?: Record<string, unknown> };
  const cw = json.current_weather;
  if (
    !cw ||
    typeof cw.temperature !== "number" ||
    typeof cw.windspeed !== "number" ||
    typeof cw.weathercode !== "number"
  ) {
    return {
      ok: false,
      error: { kind: "unexpected", message: "Malformed forecast response" },
    };
  }
  return {
    ok: true,
    value: {
      temperatureC: cw.temperature,
      windSpeedKmh: cw.windspeed,
      weatherCode: cw.weathercode,
    },
  };
}

/**
 * WMO weather code lookup. Source: https://open-meteo.com/en/docs (WMO codes table).
 * Subset is fine — anything we don't have falls back to "code N".
 */
const WEATHER_CODE_LABELS: Readonly<Record<number, string>> = {
  0: "clear sky",
  1: "mainly clear",
  2: "partly cloudy",
  3: "overcast",
  45: "fog",
  48: "depositing rime fog",
  51: "light drizzle",
  53: "moderate drizzle",
  55: "dense drizzle",
  61: "light rain",
  63: "moderate rain",
  65: "heavy rain",
  71: "light snow",
  73: "moderate snow",
  75: "heavy snow",
  80: "rain showers",
  81: "heavy rain showers",
  82: "violent rain showers",
  95: "thunderstorm",
  96: "thunderstorm with hail",
  99: "thunderstorm with heavy hail",
};

export function describeWeatherCode(code: number): string {
  return WEATHER_CODE_LABELS[code] ?? `code ${code}`;
}

function errorMessage(e: unknown): string {
  return e instanceof Error ? e.message : String(e);
}
