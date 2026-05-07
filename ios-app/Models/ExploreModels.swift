import Foundation

struct CoupleEventDTO: Decodable {
    let id: Int
    let name: String
    let place: String
    let eventDate: String
    let eventTime: String
    let calendarName: String

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case place
        case eventDate = "event_date"
        case eventTime = "event_time"
        case calendarName = "calendar_name"
    }
}
