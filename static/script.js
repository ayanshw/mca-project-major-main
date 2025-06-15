// import { MarkerClusterer } from "https://unpkg.com/@googlemaps/markerclusterer@2.0.15/dist/index.esm.min.js";

function getLocation(callback) {
  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude;
        const lng = position.coords.longitude;
        callback({ lat, lng });
      },
      () => {
        callback({ lat: 20.5937, lng: 78.9629 }); // fallback India
      }
    );
  } else {
    callback({ lat: 20.5937, lng: 78.9629 });
  }
}

export async function initMap(center, locations = []) {
  const { Map, InfoWindow } = await google.maps.importLibrary("maps");
  // MarkerClusterer is available globally from the HTML import
  const map = new Map(document.getElementById("map"), {
    zoom: 5,
    center: center || { lat: 20.5937, lng: 78.9629 },
    mapId: "DEMO_MAP_ID",
  });

  const infoWindow = new InfoWindow({ content: "", disableAutoPan: true });

  const markers = locations.map((cam) => {
    const position = { lat: cam.latitude, lng: cam.longitude };
    const marker = new google.maps.Marker({
      position,
      label: String(cam.cameraId),
    });

    const infoContent = `
      <div>
        <strong>Camera ID:</strong> ${cam.cameraId}<br>
        <strong>LAT:</strong> ${cam.latitude}<br>
        <strong>LNG:</strong> ${cam.longitude}
      </div>
    `;

    marker.addListener("click", () => {
      infoWindow.setContent(infoContent);
      infoWindow.open(map, marker);
    });

    return marker;
  });

  // Use MarkerClusterer from the global scope (loaded via HTML)
  // eslint-disable-next-line no-undef
  new markerClusterer.MarkerClusterer({ markers, map });
}

window.onload = () => {
  initializeView();
};

function initializeView() {
  if (window.message === "true") {
    document.getElementById("contentContainer").style.display = "block";
    getLocation((center) => initMap(center, window.cameras));
  }
}
