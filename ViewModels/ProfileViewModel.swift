import Foundation
import Combine

@MainActor
final class ProfileViewModel: ObservableObject {
    @Published var profile: UserProfile = MockData.profile
    @Published var isEditing = false

    func toggleEdit() {
        isEditing.toggle()
    }
}
