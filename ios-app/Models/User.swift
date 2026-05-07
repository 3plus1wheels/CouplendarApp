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
    var isInCouple: Bool
    var partnerName: String?

    enum CodingKeys: String, CodingKey {
        case id
        case email
        case code
        case displayName = "display_name"
        case firstName = "first_name"
        case lastName = "last_name"
        case city
        case profilePhoto = "profile_photo"
        case isInCouple = "is_in_couple"
        case partnerName = "partner_name"
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        id = try container.decode(Int.self, forKey: .id)
        email = try container.decode(String.self, forKey: .email)
        code = try container.decodeIfPresent(String.self, forKey: .code)
        displayName = try container.decode(String.self, forKey: .displayName)
        firstName = try container.decodeIfPresent(String.self, forKey: .firstName) ?? ""
        lastName = try container.decodeIfPresent(String.self, forKey: .lastName) ?? ""
        city = try container.decodeIfPresent(String.self, forKey: .city) ?? ""
        profilePhoto = try container.decodeIfPresent(String.self, forKey: .profilePhoto)
        isInCouple = try container.decodeIfPresent(Bool.self, forKey: .isInCouple) ?? false
        partnerName = try container.decodeIfPresent(String.self, forKey: .partnerName)
    }
}
