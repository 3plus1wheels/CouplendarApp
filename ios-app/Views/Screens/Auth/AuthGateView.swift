import SwiftUI

struct AuthGateView: View {
    @EnvironmentObject private var authManager: AuthManager

    var body: some View {
        Group {
            if authManager.isRestoringSession {
                AuthBootLoadingView()
            } else if authManager.isAuthenticated {
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

private struct AuthBootLoadingView: View {
    @State private var pulse = false

    var body: some View {
        ZStack {
            GlassBackgroundView()

            VStack(spacing: 14) {
                ZStack {
                    Circle()
                        .fill(AppColors.blush.opacity(0.22))
                        .frame(width: 90, height: 90)
                        .scaleEffect(pulse ? 1.08 : 0.94)
                    Circle()
                        .stroke(AppColors.lavender.opacity(0.45), lineWidth: 2)
                        .frame(width: 74, height: 74)
                    Image(systemName: "heart.fill")
                        .font(.system(size: 22, weight: .semibold))
                        .foregroundStyle(AppColors.blush)
                }

                Text("Welcome back")
                    .font(AppTypography.title)
                    .foregroundStyle(AppColors.primaryText)

                Text("Syncing your space...")
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.secondaryText)

                ProgressView()
                    .tint(AppColors.blush)
            }
            .padding(.horizontal, 30)
            .padding(.vertical, 26)
            .background(
                RoundedRectangle(cornerRadius: 26, style: .continuous)
                    .fill(AppColors.surface)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 26, style: .continuous)
                    .stroke(AppColors.lavender.opacity(0.18), lineWidth: 1)
            )
            .shadow(color: AppColors.primaryText.opacity(0.1), radius: 24, x: 0, y: 8)
            .padding(.horizontal, 20)
        }
        .onAppear {
            withAnimation(.easeInOut(duration: 1.05).repeatForever(autoreverses: true)) {
                pulse = true
            }
        }
    }
}

#Preview {
    AuthGateView()
        .environmentObject(AuthManager())
}
