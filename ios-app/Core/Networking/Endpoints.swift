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
        case .register: return "/auth/register/"
        case .login: return "/auth/login/"
        case .refresh: return "/auth/refresh/"
        case .me: return "/auth/me/"
        case .profile: return "/profile/"
        }
    }
}
