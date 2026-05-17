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
    @Published var searchText = "" {
        didSet {
            scheduleSearch()
        }
    }

    private let locationService: LocationService
    private weak var authManager: AuthManager?
    private var searchTask: Task<Void, Never>?

    var hasActiveSearch: Bool {
        !searchText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty
    }

    init(locationService: LocationService? = nil) {
        self.locationService = locationService ?? LocationService()
        bindLocation()
    }

    func startLocation() {
        locationService.start()
    }

    func load(authManager: AuthManager) async {
        self.authManager = authManager
        await fetchPlaces(authManager: authManager, query: searchText)
    }

    func clearSearch() {
        searchText = ""
    }

    private func fetchPlaces(authManager: AuthManager, query: String) async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let results = try await authManager.fetchDiscoveryTrending(query: query)
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
                    photoURL: URL(string: place.photoURL ?? ""),
                    videosAvailable: place.videosAvailable
                )
            }
        } catch {
            places = []
            errorMessage = error.localizedDescription
        }
    }

    private func scheduleSearch() {
        searchTask?.cancel()
        guard let authManager else { return }
        let query = searchText
        searchTask = Task { [weak self, weak authManager] in
            try? await Task.sleep(for: .milliseconds(300))
            guard !Task.isCancelled, let self, let authManager else { return }
            await self.fetchPlaces(authManager: authManager, query: query)
        }
    }

    private func formattedDistance(from distanceKm: Double?) -> String {
        guard let distanceKm else {
            return "—"
        }
        return String(format: "%.1f km", distanceKm)
    }

    private func tags(for place: DiscoveryPlaceDTO) -> [String] {
        let mediaBadges = place.videosAvailable ? ["Videos"] : []
        let candidates = mediaBadges + place.suggestionBadges + [place.primaryTypeDisplayName, place.category]
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
