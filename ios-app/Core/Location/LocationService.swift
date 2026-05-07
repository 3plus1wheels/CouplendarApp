import Combine
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
    private let staleLocationWindow: TimeInterval = 300

    override init() {
        super.init()
        manager.delegate = self
        manager.desiredAccuracy = kCLLocationAccuracyKilometer
        manager.distanceFilter = 500
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
            requestFreshLocation()
        }
    }

    func locationManagerDidChangeAuthorization(_ manager: CLLocationManager) {
        let status = manager.authorizationStatus
        handleAuthorization(status)

        if status == .authorizedAlways || status == .authorizedWhenInUse {
            requestFreshLocation()
        }
    }

    func locationManager(_ manager: CLLocationManager, didUpdateLocations locations: [CLLocation]) {
        guard let location = freshestLocation(from: locations) else {
            lastError = "No location available"
            locationText = "No location available"
            return
        }
        let isSimulated = location.sourceInformation?.isSimulatedBySoftware == true

        manager.stopUpdatingLocation()

        Task { @MainActor in
            await updateLocationText(from: location, isSimulated: isSimulated)
        }
    }

    func locationManager(_ manager: CLLocationManager, didFailWithError error: Error) {
        lastError = error.localizedDescription
        locationText = "No location available"
    }

    private func handleAuthorization(_ status: CLAuthorizationStatus) {
        isDenied = status == .denied
        isRestricted = status == .restricted

        if isDenied || isRestricted {
            locationText = "No location available"
        } else if locationText == "No location available" {
            locationText = "Locating..."
        }
    }

    private func updateLocationText(from location: CLLocation, isSimulated: Bool = false) async {
        do {
            let placemarks = try await geocoder.reverseGeocodeLocation(location)
            guard let placemark = placemarks.first else {
                locationText = "No location available"
                return
            }

            let city = placemark.locality ?? placemark.subLocality
            let state = placemark.administrativeArea

            if let city, let state {
                locationText = isSimulated ? "\(city), \(state) (Simulated)" : "\(city), \(state)"
            } else if let city {
                locationText = isSimulated ? "\(city) (Simulated)" : city
            } else if let state {
                locationText = isSimulated ? "\(state) (Simulated)" : state
            } else {
                locationText = "No location available"
            }
        } catch {
            lastError = error.localizedDescription
            locationText = "No location available"
        }
    }

    private func requestFreshLocation() {
        if let cached = manager.location, isFresh(cached) {
            Task { @MainActor in
                await updateLocationText(from: cached)
            }
            return
        }

        manager.startUpdatingLocation()
        manager.requestLocation()
    }

    private func freshestLocation(from locations: [CLLocation]) -> CLLocation? {
        locations
            .filter { isFresh($0) && $0.horizontalAccuracy >= 0 }
            .sorted { lhs, rhs in
                if lhs.timestamp == rhs.timestamp {
                    return lhs.horizontalAccuracy < rhs.horizontalAccuracy
                }
                return lhs.timestamp > rhs.timestamp
            }
            .first
    }

    private func isFresh(_ location: CLLocation) -> Bool {
        abs(location.timestamp.timeIntervalSinceNow) <= staleLocationWindow
    }
}
