import CoreLocation
import Foundation

@MainActor
final class LocationService: NSObject, ObservableObject, CLLocationManagerDelegate {
    @Published var locationText: String = "Locating..."
    @Published var isDenied = false
    @Published var isRestricted = false
    @Published var lastError: String?

    private let manager = CLLocationManager()
    private let geocoder = CLGeocoder()
    private var hasRequested = false

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyKilometer
    }

    func start() {
        let status = manager.authorizationStatus
        handleAuthorization(status)

        if status == .notDetermined && !hasRequested {
            hasRequested = true
            manager.requestWhenInUseAuthorization()
            return
        }

        if status == .authorizedAlways || status == .authorizedWhenInUse {
            manager.requestLocation()
        }
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        let status = manager.authorizationStatus
        handleAuthorization(status)

        if status == .authorizedAlways || status == .authorizedWhenInUse {
            manager.requestLocation()
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = locations.first else {
            lastError = "No location available"
            locationText = "Location unavailable"
            return
        }

        Task { @MainActor in
            await updateLocationText(from: location)
        }
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        lastError = error.localizedDescription
        locationText = "Location unavailable"
    }

    private func handleAuthorization(_ status: CLAuthorizationStatus) {
        isDenied = status == .denied
        isRestricted = status == .restricted

        if isDenied || isRestricted {
            locationText = "Location unavailable"
        } else if locationText == "Location unavailable" {
            locationText = "Locating..."
        }
    }

    private func updateLocationText(from location: CLLocation) async {
        do {
            let placemarks = try await geocoder.reverseGeocodeLocation(location)
            guard let placemark = placemarks.first else {
                locationText = "Location unavailable"
                return
            }

            let city = placemark.locality ?? placemark.subLocality
            let state = placemark.administrativeArea

            if let city, let state {
                locationText = "\(city), \(state)"
            } else if let city {
                locationText = city
            } else if let state {
                locationText = state
            } else {
                locationText = "Location unavailable"
            }
        } catch {
            lastError = error.localizedDescription
            locationText = "Location unavailable"
        }
    }
}
