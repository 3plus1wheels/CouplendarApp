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
            let events = try await authManager.fetchCoupleEvents()
            places = events.map { event in
                let placeName = event.place.trimmingCharacters(in: .whitespacesAndNewlines)
                let category = event.calendarName.trimmingCharacters(in: .whitespacesAndNewlines)
                let safeCategory = category.isEmpty ? "Event" : category.capitalized
                let summary = [event.eventDate, event.eventTime]
                    .filter { !$0.isEmpty }
                    .joined(separator: " ")

                return Place(
                    id: UUID(),
                    name: event.name,
                    category: safeCategory,
                    tags: safeCategory == "Event" ? [] : [safeCategory],
                    distance: placeName.isEmpty ? "—" : placeName,
                    summary: summary
                )
            }
        } catch {
            places = []
            errorMessage = error.localizedDescription
        }
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
