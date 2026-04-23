import Foundation

struct PaginatedResponse<T: Decodable>: Decodable {
    let count: Int
    let next: String?
    let previous: String?
    let results: [T]
}

struct NotificationInboxData: Decodable, Equatable {
    let inviteId: Int?
    let fromUserName: String?
    let toUserName: String?
    let action: String?

    enum CodingKeys: String, CodingKey {
        case inviteId = "invite_id"
        case fromUserName = "from_user_name"
        case toUserName = "to_user_name"
        case action
    }
}

struct NotificationInboxDTO: Decodable, Identifiable {
    let id: Int
    let type: String
    let title: String
    let body: String
    let data: NotificationInboxData?
    let createdAt: String
    let readAt: String?
    let eventId: Int?

    enum CodingKeys: String, CodingKey {
        case id
        case type
        case title
        case body
        case data
        case createdAt = "created_at"
        case readAt = "read_at"
        case eventId = "event_id"
    }
}

struct EventReminderRuleDTO: Decodable, Identifiable {
    let id: Int
    let event: Int
    let eventName: String?
    let user: Int
    let offsetMinutes: Int
    let channel: String
    let isEnabled: Bool
    let createdAt: String
    let updatedAt: String

    enum CodingKeys: String, CodingKey {
        case id
        case event
        case eventName = "event_name"
        case user
        case offsetMinutes = "offset_minutes"
        case channel
        case isEnabled = "is_enabled"
        case createdAt = "created_at"
        case updatedAt = "updated_at"
    }
}

struct MarkAllReadResponse: Decodable {
    let updatedCount: Int

    enum CodingKeys: String, CodingKey {
        case updatedCount = "updated_count"
    }
}

struct NotificationFeedItem: Identifiable, Equatable {
    enum Source: Equatable {
        case inbox
        case reminderRule
    }

    let id: String
    let source: Source
    let inboxId: Int?
    let title: String
    let body: String
    let timeAgo: String
    let tag: String
    let type: String
    let inviteId: Int?
    let inviteAction: String?
    var isRead: Bool

    var canRespondToInvite: Bool {
        source == .inbox
            && type == "invite"
            && inviteId != nil
            && inviteAction == nil
    }
}
