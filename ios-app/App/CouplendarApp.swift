import SwiftUI

@main
struct CouplendarApp: App {
    @StateObject private var authManager = AuthManager()

    var body: some Scene {
        WindowGroup {
            AuthGateView()
                .environmentObject(authManager)
                .task {
                    await authManager.restoreSession()
                }
        }
    }
}
