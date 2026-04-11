import Foundation

enum APIError: LocalizedError {
    case invalidURL
    case unauthorized
    case server(statusCode: Int, message: String?)
    case decoding
    case transport(String)

    var errorDescription: String? {
        switch self {
        case .invalidURL:
            return "Invalid API URL"
        case .unauthorized:
            return "Unauthorized"
        case .server(let statusCode, let message):
            return message ?? "Server error (\(statusCode))"
        case .decoding:
            return "Failed to decode server response"
        case .transport(let message):
            return message
        }
    }
}
