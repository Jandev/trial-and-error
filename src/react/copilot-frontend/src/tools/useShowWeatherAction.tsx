import { useFrontendTool } from "@copilotkit/react-core/v2";
import toast from "react-hot-toast";
import { z } from "zod";

import {
  describeWeatherCode,
  fetchCurrentWeather,
  geocodeCity,
  type CurrentWeather,
  type GeocodedCity,
} from "../lib/openMeteoClient";
import { WeatherRender } from "./WeatherRender";

const PARAMS_SCHEMA = z.object({
  city: z
    .string()
    .describe("City name (e.g. 'Amsterdam', 'New York', 'Tokyo')."),
});

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

function summarize({ city, weather }: WeatherResult): string {
  return (
    `${city.name}: ${weather.temperatureC.toFixed(0)}°C, ` +
    `wind ${weather.windSpeedKmh.toFixed(0)} km/h, ` +
    `${describeWeatherCode(weather.weatherCode)}`
  );
}

/**
 * Registers the `showWeather` frontend tool.
 *
 * The agent calls this with `{ city }`; we resolve via Open-Meteo geocoding,
 * fetch the current weather, render a {@link WeatherRender} (which renders a
 * {@link WeatherCard} on success), and return a one-line summary string for
 * the agent.
 *
 * Errors (city not found, network failures) are surfaced as toasts AND
 * returned as plain strings to the agent — never thrown.
 */
export function useShowWeatherAction(): void {
  useFrontendTool({
    name: "showWeather",
    description:
      "Fetch and render a small weather card for a given city. " +
      "Use when the user asks about the weather. Returns a one-line summary " +
      "string for the agent's own response.",
    parameters: PARAMS_SCHEMA,
    handler: async ({ city }) => {
      const result = await lookupWeather(city);
      return typeof result === "string" ? result : summarize(result);
    },
    render: ({ args }) => {
      const city = typeof args?.city === "string" ? args.city : "";
      return <WeatherRender city={city} />;
    },
  });
}
