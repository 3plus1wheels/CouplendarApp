import Foundation
import Security

final class TokenStore {
    static let shared = TokenStore()

    private let service = "com.couplendar.tokens"
    private let accessAccount = "access"
    private let refreshAccount = "refresh"

    func save(access: String, refresh: String) {
        save(value: access, account: accessAccount)
        save(value: refresh, account: refreshAccount)
    }

    func readAccessToken() -> String? {
        read(account: accessAccount)
    }

    func readRefreshToken() -> String? {
        read(account: refreshAccount)
    }

    func clear() {
        delete(account: accessAccount)
        delete(account: refreshAccount)
    }

    private func save(value: String, account: String) {
        let data = Data(value.utf8)
        delete(account: account)

        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecValueData as String: data,
        ]
        SecItemAdd(query as CFDictionary, nil)
    }

    private func read(account: String) -> String? {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
            kSecMatchLimit as String: kSecMatchLimitOne,
            kSecReturnData as String: true,
        ]

        var result: AnyObject?
        let status = SecItemCopyMatching(query as CFDictionary, &result)
        guard status == errSecSuccess, let data = result as? Data else {
            return nil
        }
        return String(data: data, encoding: .utf8)
    }

    private func delete(account: String) {
        let query: [String: Any] = [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: service,
            kSecAttrAccount as String: account,
        ]
        SecItemDelete(query as CFDictionary)
    }
}
