import SwiftUI

struct AuthGateView: View {
    @EnvironmentObject private var authManager: AuthManager

    var body: some View {
        Group {
            if authManager.isAuthenticated {
                RootTabView()
            } else {
                AuthLandingView()
            }
        }
    }
}

private struct AuthLandingView: View {
    @State private var showRegister = false

    var body: some View {
        NavigationStack {
            LoginView(showRegister: $showRegister)
                .navigationDestination(isPresented: $showRegister) {
                    RegisterView()
                }
        }
    }
}

#Preview {
    AuthGateView()
        .environmentObject(AuthManager())
}
