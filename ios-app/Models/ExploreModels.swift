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

struct DiscoveryPlaceDTO: Decodable {
    let id: Int
    let name: String
    let category: String
    let rating: Double?
    let photoURL: String?
    let distanceKm: Double?

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case category
        case rating
        case photoURL = "photo_url"
        case distanceKm = "distance_km"
    }
}
