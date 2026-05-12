import Foundation

enum EventPlanMapper {
    private static let calendar = Calendar.current

    static func map(_ event: CoupleEventDTO, vibe: String = "Shared") -> Plan? {
        guard let eventDate = eventDateFormatter.date(from: event.eventDate) else {
            return nil
        }

        let eventTime = eventTimeFormatter.date(from: event.eventTime)
            ?? eventTimeShortFormatter.date(from: event.eventTime)
            ?? eventDate

        let combinedDate = calendar.date(
            bySettingHour: calendar.component(.hour, from: eventTime),
            minute: calendar.component(.minute, from: eventTime),
            second: calendar.component(.second, from: eventTime),
            of: eventDate
        ) ?? eventDate

        return Plan(
            id: UUID(),
            remoteId: event.id,
            title: event.name,
            date: combinedDate,
            location: event.place,
            vibe: vibe
        )
    }
}

private extension EventPlanMapper {
    static let eventDateFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        formatter.timeZone = .current
        formatter.locale = Locale(identifier: "en_US_POSIX")
        return formatter
    }()

    static let eventTimeFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm:ss"
        formatter.timeZone = .current
        formatter.locale = Locale(identifier: "en_US_POSIX")
        return formatter
    }()

    static let eventTimeShortFormatter: DateFormatter = {
        let formatter = DateFormatter()
        formatter.dateFormat = "HH:mm"
        formatter.timeZone = .current
        formatter.locale = Locale(identifier: "en_US_POSIX")
        return formatter
    }()
}
