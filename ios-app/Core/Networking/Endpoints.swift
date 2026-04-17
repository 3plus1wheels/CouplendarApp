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

    var path: String {
        switch self {
        case .register: return "api/auth/register/"
        case .login: return "api/auth/login/"
        case .refresh: return "api/auth/refresh/"
        case .me: return "api/auth/me/"
        case .profile: return "api/profile/"
        }
    }
}
