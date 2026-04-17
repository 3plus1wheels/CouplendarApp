import Foundation

struct User: Codable, Equatable, Identifiable {
    let id: Int
    let email: String
    var code: String?
    var displayName: String
    var firstName: String
    var lastName: String
    var city: String
    var profilePhoto: String?

    enum CodingKeys: String, CodingKey {
        case id
        case email
        case code
        case displayName = "display_name"
        case firstName = "first_name"
        case lastName = "last_name"
        case city
        case profilePhoto = "profile_photo"
    }
}
