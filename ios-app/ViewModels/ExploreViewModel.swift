import Combine
import Foundation

@MainActor
final class ExploreViewModel: ObservableObject {
    @Published private(set) var isLoading = false
    @Published var errorMessage: String?
    @Published var locationText: String = "Locating..."
    @Published var isLocationDenied = false
    @Published var locationError: String?
    @Published var places: [Place] = []

    private let locationService: LocationService
    private let useFixedLocation: Bool

    init(locationService: LocationService? = nil, useFixedLocation: Bool = true) {
        self.locationService = locationService ?? LocationService()
        self.useFixedLocation = useFixedLocation
        if useFixedLocation {
            locationText = "Calgary, AB"
        } else {
            bindLocation()
        }
    }

    func startLocation() {
        if !useFixedLocation {
            locationService.start()
        }
    }

    func load(authManager: AuthManager) async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let results = try await authManager.fetchDiscoveryTrending()
            places = results.map { place in
                let distance = formattedDistance(from: place.distanceKm)
                return Place(
                    id: UUID(),
                    name: place.name,
                    category: place.category,
                    tags: place.category.isEmpty ? [] : [place.category],
                    distance: distance,
                    summary: place.category,
                    rating: place.rating,
                    photoURL: URL(string: place.photoURL ?? "")
                )
            }
        } catch {
            places = []
            errorMessage = error.localizedDescription
        }
    }

    private func formattedDistance(from distanceKm: Double?) -> String {
        guard let distanceKm else {
            return "—"
        }
        return String(format: "%.1f km", distanceKm)
    }

    private func bindLocation() {
        locationService.$locationText
            .receive(on: RunLoop.main)
            .assign(to: &$locationText)

        locationService.$isDenied
            .receive(on: RunLoop.main)
            .assign(to: &$isLocationDenied)

        locationService.$lastError
            .receive(on: RunLoop.main)
            .assign(to: &$locationError)
    }
}
