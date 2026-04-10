import Foundation
import Combine

@MainActor
final class CalendarViewModel: ObservableObject {
    enum Mode: String, CaseIterable, Identifiable {
        case day = "Day"
        case week = "Week"
        case month = "Month"
        var id: String { rawValue }
    }

    @Published var mode: Mode = .week
    @Published var plans: [Plan] = MockData.plans

    var monthTitle: String {
        Date.now.formatted(.dateTime.month(.wide).year())
    }
}
