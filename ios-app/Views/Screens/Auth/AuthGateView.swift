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
        ZStack {
            if showRegister {
                RegisterView(showRegister: $showRegister)
                    .transition(
                        .asymmetric(
                            insertion: .move(edge: .trailing).combined(with: .opacity),
                            removal: .move(edge: .leading).combined(with: .opacity)
                        )
                    )
                    .zIndex(1)
            } else {
                LoginView(showRegister: $showRegister)
                    .transition(
                        .asymmetric(
                            insertion: .move(edge: .leading).combined(with: .opacity),
                            removal: .move(edge: .trailing).combined(with: .opacity)
                        )
                    )
                    .zIndex(0)
            }
        }
        .animation(.spring(response: 0.4, dampingFraction: 0.9), value: showRegister)
    }
}

#Preview {
    AuthGateView()
        .environmentObject(AuthManager())
}
