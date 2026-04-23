import Foundation

enum HTTPMethod: String {
    case get = "GET"
    case post = "POST"
    case patch = "PATCH"
}

enum Endpoint {
    case register
    case login
    case refresh
    case me
    case profile
    case inviteByCode
    case acceptInvite(id: Int)
    case declineInvite(id: Int)
    case notificationInbox
    case notificationReminders
    case notificationMarkRead(id: Int)
    case notificationMarkAllRead

    var path: String {
        switch self {
        case .register: return "api/auth/register/"
        case .login: return "api/auth/login/"
        case .refresh: return "api/auth/refresh/"
        case .me: return "api/auth/me/"
        case .profile: return "api/profile/"
        case .inviteByCode: return "api/couples/invite/"
        case .acceptInvite(let id): return "api/couples/invite/\(id)/accept/"
        case .declineInvite(let id): return "api/couples/invite/\(id)/decline/"
        case .notificationInbox: return "api/notifications/inbox/"
        case .notificationReminders: return "api/notifications/reminders/"
        case .notificationMarkRead(let id): return "api/notifications/inbox/\(id)/read/"
        case .notificationMarkAllRead: return "api/notifications/inbox/read-all/"
        }
    }
}
