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
    let reviewCount: Int
    let photoURL: String?
    let distanceKm: Double?
    let reviewsAvailable: Bool
    let reviewsLastUpdated: String?
    let topReviews: [DiscoveryReviewDTO]

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case category
        case rating
        case reviewCount = "review_count"
        case photoURL = "photo_url"
        case distanceKm = "distance_km"
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

struct DiscoveryVideoDTO: Decodable {
    let id: String
    let source: String
    let sourceURL: String
    let title: String
    let isShort: Bool
    let caption: String
    let url: String
    let thumbnailURL: String
    let creatorUsername: String
    let creatorDisplayName: String
    let likesCount: Int?
    let commentsCount: Int?
    let sharesCount: Int?
    let viewsCount: Int?
    let postedAt: String?

    enum CodingKeys: String, CodingKey {
        case id
        case source
        case sourceURL = "source_url"
        case title
        case isShort = "is_short"
        case caption
        case url
        case thumbnailURL = "thumbnail_url"
        case creatorUsername = "creator_username"
        case creatorDisplayName = "creator_display_name"
        case likesCount = "likes_count"
        case commentsCount = "comments_count"
        case sharesCount = "shares_count"
        case viewsCount = "views_count"
        case postedAt = "posted_at"
    }
}

struct DiscoveryVideoRefreshDTO: Decodable {
    let spotId: Int
    let status: String
    let videos: [DiscoveryVideoDTO]
}

struct DiscoveryPlaceDetailDTO: Decodable {
    let id: Int
    let name: String
    let category: String
    let rating: Double?
    let reviewCount: Int
    let photoURL: String?
    let distanceKm: Double?
    let websiteURL: String
    let phoneNumber: String
    let googleMapsURL: String
    let reviewsAvailable: Bool
    let reviewsLastUpdated: String?
    let topReviews: [DiscoveryReviewDTO]
    let videosAvailable: Bool
    let videosLastUpdated: String?
    let videoRefreshError: String
    let videos: [DiscoveryVideoDTO]

    enum CodingKeys: String, CodingKey {
        case id
        case name
        case category
        case rating
        case reviewCount = "review_count"
        case photoURL = "photo_url"
        case distanceKm = "distance_km"
        case websiteURL = "website_url"
        case phoneNumber = "phone_number"
        case googleMapsURL = "google_maps_url"
        case reviewsAvailable = "reviews_available"
        case reviewsLastUpdated = "reviews_last_updated"
        case topReviews = "top_reviews"
        case videosAvailable = "videos_available"
        case videosLastUpdated = "videos_last_updated"
        case videoRefreshError = "video_refresh_error"
        case videos
    }
}
