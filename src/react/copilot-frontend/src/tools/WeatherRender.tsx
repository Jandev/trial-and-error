import { useEffect, useState } from "react";
import toast from "react-hot-toast";

import {
  fetchCurrentWeather,
  geocodeCity,
  type CurrentWeather,
  type GeocodedCity,
} from "../lib/openMeteoClient";
import { WeatherCard } from "./WeatherCard";

interface WeatherResult {
  city: GeocodedCity;
  weather: CurrentWeather;
}

async function lookupWeather(city: string): Promise<WeatherResult | string> {
  const geo = await geocodeCity(city);
  if (!geo.ok) {
    const msg = `Could not find city "${city}": ${geo.error.message}`;
    toast.error(msg);
    return msg;
  }
  const weather = await fetchCurrentWeather(geo.value.latitude, geo.value.longitude);
  if (!weather.ok) {
    const msg = `Weather lookup failed for ${geo.value.name}: ${weather.error.message}`;
    toast.error(msg);
    return msg;
  }
  return { city: geo.value, weather: weather.value };
}

type State =
  | { kind: "loading"; city: string }
  | { kind: "ok"; city: string; value: WeatherResult }
  | { kind: "err"; city: string; message: string };

/**
 * Self-fetching weather renderer keyed on the requested city.
 *
 * State is keyed by city so we never have to reset state from inside
 * useEffect (forbidden in React 19). When `city` changes, the previous
 * fetch's result is ignored via the `cancelled` flag and the keyed-state
 * check below.
 */
export function WeatherRender({ city }: { city: string }) {
  const [state, setState] = useState<State>({ kind: "loading", city });

  useEffect(() => {
    let cancelled = false;
    void lookupWeather(city).then((r) => {
      if (cancelled) return;
      if (typeof r === "string") {
        setState({ kind: "err", city, message: r });
      } else {
        setState({ kind: "ok", city, value: r });
      }
    });
    return () => {
      cancelled = true;
    };
  }, [city]);

  // If the user retriggered for a different city, ignore stale state.
  const current: State = state.city === city ? state : { kind: "loading", city };

  if (current.kind === "err") {
    return (
      <div data-testid="weather-error" style={{ color: "#b91c1c", padding: 8 }}>
        {current.message}
      </div>
    );
  }
  if (current.kind === "loading") {
    return (
      <div
        data-testid="weather-loading"
        style={{ padding: 12, color: "#6b7280", fontStyle: "italic" }}
      >
        Looking up weather for {city}…
      </div>
    );
  }
  return <WeatherCard city={current.value.city} weather={current.value.weather} />;
}
