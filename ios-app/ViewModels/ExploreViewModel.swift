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

    init(locationService: LocationService? = nil) {
        self.locationService = locationService ?? LocationService()
        bindLocation()
    }

    func startLocation() {
        locationService.start()
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
                    discoveryId: place.id,
                    name: place.name,
                    category: place.category,
                    tags: tags(for: place),
                    distance: distance,
                    summary: place.suggestionReason.isEmpty ? place.category : place.suggestionReason,
                    suggestionScore: place.suggestionScore,
                    suggestionBadges: place.suggestionBadges,
                    rating: place.rating,
                    reviewCount: place.reviewCount,
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

    private func tags(for place: DiscoveryPlaceDTO) -> [String] {
        let candidates = place.suggestionBadges + [place.primaryTypeDisplayName, place.category]
        var seen: Set<String> = []
        return candidates.compactMap { value in
            let trimmed = value.trimmingCharacters(in: .whitespacesAndNewlines)
            let key = trimmed.lowercased()
            guard !trimmed.isEmpty, !seen.contains(key) else { return nil }
            seen.insert(key)
            return trimmed
        }
        .prefix(3)
        .map { $0 }
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
