import Foundation

struct AuthResponse: Codable, Equatable {
    let access: String
    let refresh: String
    let user: User
}

struct ProfilePatchRequest: Codable {
    let displayName: String?
    let firstName: String?
    let lastName: String?
    let city: String?

    enum CodingKeys: String, CodingKey {
        case displayName = "display_name"
        case firstName = "first_name"
        case lastName = "last_name"
        case city
    }
}
