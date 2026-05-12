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
    let primaryType: String
    let primaryTypeDisplayName: String
    let placeTypes: [String]
    let businessStatus: String
    let priceLevel: String
    let openNow: Bool?
    let rating: Double?
    let reviewCount: Int
    let photoURL: String?
    let photoURLs: [String]
    let distanceKm: Double?
    let trendScore: Double
    let suggestionScore: Double
    let suggestionReason: String
    let suggestionBadges: [String]
    let reviewsAvailable: Bool
    let reviewsLastUpdated: String?
    let topReviews: [DiscoveryReviewDTO]

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case category
        case primaryType = "primary_type"
        case primaryTypeDisplayName = "primary_type_display_name"
        case placeTypes = "place_types"
        case businessStatus = "business_status"
        case priceLevel = "price_level"
        case openNow = "open_now"
        case rating
        case reviewCount = "review_count"
        case photoURL = "photo_url"
        case photoURLs = "photo_urls"
        case distanceKm = "distance_km"
        case trendScore = "trend_score"
        case suggestionScore = "suggestion_score"
        case suggestionReason = "suggestion_reason"
        case suggestionBadges = "suggestion_badges"
        case reviewsAvailable = "reviews_available"
        case reviewsLastUpdated = "reviews_last_updated"
        case topReviews = "top_reviews"
    }
}

struct DiscoveryReviewDTO: Decodable {
    let authorName: String
    let rating: Double?
    let relativeTimeDescription: String
    let text: String

    enum CodingKeys: String, CodingKey {
        case authorName = "author_name"
        case rating
        case relativeTimeDescription = "relative_time_description"
        case text
    }
}

struct DiscoveryPlaceDetailDTO: Decodable {
    let id: Int
    let name: String
    let category: String
    let primaryType: String
    let primaryTypeDisplayName: String
    let placeTypes: [String]
    let businessStatus: String
    let priceLevel: String
    let openNow: Bool?
    let rating: Double?
    let reviewCount: Int
    let photoURL: String?
    let photoURLs: [String]
    let distanceKm: Double?
    let trendScore: Double
    let suggestionScore: Double
    let suggestionReason: String
    let suggestionBadges: [String]
    let websiteURL: String
    let phoneNumber: String
    let googleMapsURL: String
    let googleURI: String
    let openingHours: [String]
    let editorialSummary: String
    let generativeSummary: String
    let reviewSummary: String
    let amenities: [String: Bool]
    let reviewsAvailable: Bool
    let reviewsLastUpdated: String?
    let topReviews: [DiscoveryReviewDTO]
    let reviewsSyncError: String

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case category
        case primaryType = "primary_type"
        case primaryTypeDisplayName = "primary_type_display_name"
        case placeTypes = "place_types"
        case businessStatus = "business_status"
        case priceLevel = "price_level"
        case openNow = "open_now"
        case rating
        case reviewCount = "review_count"
        case photoURL = "photo_url"
        case photoURLs = "photo_urls"
        case distanceKm = "distance_km"
        case trendScore = "trend_score"
        case suggestionScore = "suggestion_score"
        case suggestionReason = "suggestion_reason"
        case suggestionBadges = "suggestion_badges"
        case websiteURL = "website_url"
        case phoneNumber = "phone_number"
        case googleMapsURL = "google_maps_url"
        case googleURI = "google_uri"
        case openingHours = "opening_hours"
        case editorialSummary = "editorial_summary"
        case generativeSummary = "generative_summary"
        case reviewSummary = "review_summary"
        case amenities
        case reviewsAvailable = "reviews_available"
        case reviewsLastUpdated = "reviews_last_updated"
        case topReviews = "top_reviews"
        case reviewsSyncError = "reviews_sync_error"
    }
}
