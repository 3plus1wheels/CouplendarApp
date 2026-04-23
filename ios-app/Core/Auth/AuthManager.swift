import Foundation
import Combine

@MainActor
final class AuthManager: ObservableObject {
    @Published private(set) var currentUser: User?
    @Published private(set) var isLoading = false
    @Published private(set) var isRestoringSession = true
    @Published private(set) var errorMessage: String?

    private let apiClient: APIClient
    private let tokenStore: TokenStore

    init(apiClient: APIClient, tokenStore: TokenStore) {
        self.apiClient = apiClient
        self.tokenStore = tokenStore
    }

    convenience init() {
        self.init(apiClient: .shared, tokenStore: .shared)
    }

    var isAuthenticated: Bool {
        currentUser != nil
    }

    func restoreSession() async {
        isRestoringSession = true
        defer { isRestoringSession = false }

        guard tokenStore.readAccessToken() != nil else {
            currentUser = nil
            return
        }
        do {
            try await fetchMe()
        } catch {
            tokenStore.clear()
            currentUser = nil
        }
    }

    func register(email: String, password: String, displayName: String) async {
        struct Request: Encodable {
            let email: String
            let password: String
            let display_name: String
        }

        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let response: AuthResponse = try await apiClient.request(
                .register,
                method: .post,
                body: Request(email: email, password: password, display_name: displayName)
            )
            tokenStore.save(access: response.access, refresh: response.refresh)
            currentUser = response.user
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func login(email: String, password: String) async {
        struct Request: Encodable {
            let email: String
            let password: String
        }

        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let response: AuthResponse = try await apiClient.request(
                .login,
                method: .post,
                body: Request(email: email, password: password)
            )
            tokenStore.save(access: response.access, refresh: response.refresh)
            currentUser = response.user
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func fetchMe() async throws {
        guard let accessToken = tokenStore.readAccessToken() else {
            throw APIError.unauthorized
        }
        let user: User = try await apiClient.request(.me, method: .get, accessToken: accessToken)
        currentUser = user
    }

    func fetchProfile() async {
        do {
            guard let accessToken = tokenStore.readAccessToken() else { return }
            let user: User = try await apiClient.request(.profile, method: .get, accessToken: accessToken)
            currentUser = user
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func updateProfile(displayName: String, firstName: String, lastName: String, city: String) async {
        guard let accessToken = tokenStore.readAccessToken() else { return }
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let payload = ProfilePatchRequest(
                displayName: displayName,
                firstName: firstName,
                lastName: lastName,
                city: city
            )
            let user: User = try await apiClient.request(.profile, method: .patch, body: payload, accessToken: accessToken)
            currentUser = user
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func sendInvite(inviteCode: String) async -> Bool {
        guard let accessToken = tokenStore.readAccessToken() else {
            errorMessage = APIError.unauthorized.localizedDescription
            return false
        }

        struct InviteRequest: Encodable {
            let invite_code: String
        }

        struct InviteResponse: Decodable {
            let status: String
        }

        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        let normalizedCode = inviteCode
            .trimmingCharacters(in: .whitespacesAndNewlines)
            .lowercased()
            .replacingOccurrences(of: ".", with: "-")

        guard !normalizedCode.isEmpty else {
            errorMessage = "Invite code is required"
            return false
        }

        do {
            let _: InviteResponse = try await apiClient.request(
                .inviteByCode,
                method: .post,
                body: InviteRequest(invite_code: normalizedCode),
                accessToken: accessToken
            )
            return true
        } catch {
            errorMessage = error.localizedDescription
            return false
        }
    }

    func acceptInvite(inviteId: Int) async -> Bool {
        guard let accessToken = tokenStore.readAccessToken() else {
            errorMessage = APIError.unauthorized.localizedDescription
            return false
        }

        struct InviteActionResponse: Decodable {
            let status: String
        }

        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let _: InviteActionResponse = try await apiClient.request(
                .acceptInvite(id: inviteId),
                method: .post,
                accessToken: accessToken
            )
            return true
        } catch {
            errorMessage = error.localizedDescription
            return false
        }
    }

    func declineInvite(inviteId: Int) async -> Bool {
        guard let accessToken = tokenStore.readAccessToken() else {
            errorMessage = APIError.unauthorized.localizedDescription
            return false
        }

        struct InviteActionResponse: Decodable {
            let status: String
        }

        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            let _: InviteActionResponse = try await apiClient.request(
                .declineInvite(id: inviteId),
                method: .post,
                accessToken: accessToken
            )
            return true
        } catch {
            errorMessage = error.localizedDescription
            return false
        }
    }

    func fetchInboxNotifications() async throws -> PaginatedResponse<NotificationInboxDTO> {
        guard let accessToken = tokenStore.readAccessToken() else {
            throw APIError.unauthorized
        }
        return try await apiClient.request(.notificationInbox, method: .get, accessToken: accessToken)
    }

    func fetchReminderRules() async throws -> PaginatedResponse<EventReminderRuleDTO> {
        guard let accessToken = tokenStore.readAccessToken() else {
            throw APIError.unauthorized
        }
        return try await apiClient.request(.notificationReminders, method: .get, accessToken: accessToken)
    }

    func markNotificationRead(notificationId: Int) async throws -> NotificationInboxDTO {
        guard let accessToken = tokenStore.readAccessToken() else {
            throw APIError.unauthorized
        }
        return try await apiClient.request(.notificationMarkRead(id: notificationId), method: .patch, accessToken: accessToken)
    }

    func markAllNotificationsRead() async throws -> Int {
        guard let accessToken = tokenStore.readAccessToken() else {
            throw APIError.unauthorized
        }
        let response: MarkAllReadResponse = try await apiClient.request(.notificationMarkAllRead, method: .post, accessToken: accessToken)
        return response.updatedCount
    }

    func logout() {
        tokenStore.clear()
        currentUser = nil
        errorMessage = nil
    }
}
