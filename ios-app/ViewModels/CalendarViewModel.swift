import Foundation
import Combine

@MainActor
final class CalendarViewModel: ObservableObject {
    struct WeekDay: Identifiable {
        let date: Date
        let isToday: Bool
        let hasPlan: Bool

        var id: Date { date }
        var dayNumber: String {
            String(Calendar.current.component(.day, from: date))
        }
    }

    struct DayCell: Identifiable {
        let date: Date
        let isInDisplayedMonth: Bool
        let isToday: Bool
        let hasPlan: Bool

        var id: Date { date }
        var dayNumber: String {
            String(Calendar.current.component(.day, from: date))
        }
    }

    enum Mode: String, CaseIterable, Identifiable {
        case day = "Day"
        case week = "Week"
        case month = "Month"
        var id: String { rawValue }
    }

    private let calendar = Calendar.current

    @Published var mode: Mode = .month
    @Published var plans: [Plan] = []
    @Published var displayedMonth: Date
    @Published var selectedDate: Date

    init() {
        let today = Date.now
        self.displayedMonth = calendar.date(from: calendar.dateComponents([.year, .month], from: today)) ?? today
        self.selectedDate = today
    }

    var monthTitle: String {
        displayedMonth.formatted(.dateTime.month(.wide).year())
    }

    var weekdaySymbols: [String] {
        let symbols = calendar.veryShortWeekdaySymbols
        let first = calendar.firstWeekday - 1
        return Array(symbols[first...] + symbols[..<first])
    }

    var monthGrid: [DayCell] {
        guard
            let monthInterval = calendar.dateInterval(of: .month, for: displayedMonth),
            let firstWeekInterval = calendar.dateInterval(of: .weekOfMonth, for: monthInterval.start),
            let lastWeekInterval = calendar.dateInterval(of: .weekOfMonth, for: monthInterval.end.addingTimeInterval(-1))
        else {
            return []
        }

        var dates: [Date] = []
        var current = firstWeekInterval.start
        while current < lastWeekInterval.end {
            dates.append(current)
            current = calendar.date(byAdding: .day, value: 1, to: current) ?? current
        }

        return dates.map { date in
            DayCell(
                date: date,
                isInDisplayedMonth: calendar.isDate(date, equalTo: displayedMonth, toGranularity: .month),
                isToday: calendar.isDateInToday(date),
                hasPlan: plans.contains { calendar.isDate($0.date, inSameDayAs: date) }
            )
        }
    }

    var plansForSelectedDate: [Plan] {
        plans(for: selectedDate)
    }

    var weekDays: [WeekDay] {
        guard let weekInterval = calendar.dateInterval(of: .weekOfYear, for: selectedDate) else {
            return []
        }

        return (0..<7).compactMap { offset in
            guard let date = calendar.date(byAdding: .day, value: offset, to: weekInterval.start) else { return nil }
            return WeekDay(
                date: date,
                isToday: calendar.isDateInToday(date),
                hasPlan: plans.contains { calendar.isDate($0.date, inSameDayAs: date) }
            )
        }
    }

    func showPreviousMonth() {
        guard let date = calendar.date(byAdding: .month, value: -1, to: displayedMonth) else { return }
        displayedMonth = date
        syncSelectionIfNeeded()
    }

    func showNextMonth() {
        guard let date = calendar.date(byAdding: .month, value: 1, to: displayedMonth) else { return }
        displayedMonth = date
        syncSelectionIfNeeded()
    }

    func selectDate(_ date: Date) {
        selectedDate = date
    }

    func plans(for date: Date) -> [Plan] {
        plans
            .filter { calendar.isDate($0.date, inSameDayAs: date) }
            .sorted { $0.date < $1.date }
    }

    private func syncSelectionIfNeeded() {
        if !calendar.isDate(selectedDate, equalTo: displayedMonth, toGranularity: .month) {
            selectedDate = displayedMonth
        }
    }

    func loadEvents(authManager: AuthManager) async {
        do {
            let events = try await authManager.fetchCoupleEvents()
            let mappedPlans = events.compactMap { EventPlanMapper.map($0) }
            plans = mappedPlans.sorted { $0.date < $1.date }
        } catch {
            #if DEBUG
            print("Failed to load events:", error.localizedDescription)
            #endif
        }
    }
}
