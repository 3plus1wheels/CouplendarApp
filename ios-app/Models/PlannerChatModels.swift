import Foundation

struct PlannerChatRequest: Encodable {
    let message: String
}

struct PlannerChatResponse: Decodable {
    let reply: String
}

struct PlannerChatMessage: Identifiable, Equatable {
    enum Role: Equatable {
        case user
        case assistant
    }

    let id = UUID()
    let role: Role
    let text: String
}
