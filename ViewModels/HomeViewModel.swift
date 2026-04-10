import Foundation
import Combine

@MainActor
final class HomeViewModel: ObservableObject {
    @Published var plans: [Plan] = MockData.plans
    @Published var suggestions: [Suggestion] = MockData.suggestions
    @Published var reminders: [String] = MockData.reminders

    var nextUp: Plan? { plans.sorted { $0.date < $1.date }.first }
}
