import Foundation
import Combine

@MainActor
final class HomeViewModel: ObservableObject {
    @Published var plans: [Plan]
    @Published var suggestions: [Suggestion] = MockData.suggestions
    @Published var reminders: [String] = MockData.reminders

    init(plans: [Plan] = []) {
        self.plans = plans
    }

    var upcomingPlans: [Plan] {
        plans
            .filter { $0.date >= Date.now }
            .sorted { $0.date < $1.date }
    }

    var nextUp: Plan? {
        upcomingPlans.first
    }

    func loadEvents(authManager: AuthManager) async {
        do {
            let events = try await authManager.fetchCoupleEvents()
            plans = events
                .compactMap { EventPlanMapper.map($0) }
                .sorted { $0.date < $1.date }
        } catch {
            #if DEBUG
            print("Failed to load home events:", error.localizedDescription)
            #endif
        }
    }
}
