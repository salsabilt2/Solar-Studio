import { MapPin } from "lucide-react";
import {
  CircleMarker,
  MapContainer,
  TileLayer,
  Tooltip,
  useMapEvents,
} from "react-leaflet";
import "leaflet/dist/leaflet.css";
import type { Setup } from "./api";

function MapClick({ onPick }: { onPick?: (lat: number, lon: number) => void }) {
  useMapEvents({
    click: (event) => onPick?.(event.latlng.lat, event.latlng.lng),
  });
  return null;
}

export default function SetupMap({
  setups,
  selected,
  onSelect,
  onPick,
}: {
  setups: Setup[];
  selected?: number;
  onSelect: (id: number) => void;
  onPick?: (lat: number, lon: number) => void;
}) {
  const first = setups[0];
  return (
    <div className="map-frame">
      <MapContainer
        key={
          first
            ? `${first.latitude.toFixed(2)}:${first.longitude.toFixed(2)}`
            : "empty"
        }
        center={first ? [first.latitude, first.longitude] : [50.8278, 12.9214]}
        zoom={first ? 10 : 5}
        scrollWheelZoom={false}
        className="map-inner"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <MapClick onPick={onPick} />
        {setups.map((setup) => (
          <CircleMarker
            key={setup.id}
            center={[setup.latitude, setup.longitude]}
            radius={selected === setup.id ? 13 : 10}
            pathOptions={{
              color: "#fff",
              weight: 3,
              fillColor: "#d6a94f",
              fillOpacity: 1,
            }}
            eventHandlers={{ click: () => onSelect(setup.id) }}
          >
            <Tooltip>{setup.label}</Tooltip>
          </CircleMarker>
        ))}
      </MapContainer>
      <span className="map-hint">
        <MapPin size={14} />{" "}
        {onPick
          ? "Click the map to choose a place"
          : `${setups.length} locations`}
      </span>
    </div>
  );
}
