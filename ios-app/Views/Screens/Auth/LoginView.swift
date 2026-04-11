import SwiftUI

struct LoginView: View {
    @EnvironmentObject private var authManager: AuthManager
    @Binding var showRegister: Bool

    @State private var email = ""
    @State private var password = ""

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.lg) {
            Text("Welcome back")
                .font(AppTypography.largeTitle)
                .foregroundStyle(AppColors.primaryText)

            TextField("Email", text: $email)
                .textInputAutocapitalization(.never)
                .keyboardType(.emailAddress)
                .autocorrectionDisabled()
                .textFieldStyle(.roundedBorder)

            SecureField("Password", text: $password)
                .textFieldStyle(.roundedBorder)

            Button {
                Task {
                    await authManager.login(email: email, password: password)
                }
            } label: {
                Text(authManager.isLoading ? "Signing In..." : "Sign In")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .disabled(authManager.isLoading || email.isEmpty || password.isEmpty)

            Button("Create Account") {
                showRegister = true
            }
            .buttonStyle(.plain)

            if let errorMessage = authManager.errorMessage {
                Text(errorMessage)
                    .font(.footnote)
                    .foregroundStyle(.red)
            }

            Spacer()
        }
        .padding(AppSpacing.lg)
        .background(GlassBackgroundView())
    }
}

#Preview {
    NavigationStack {
        LoginView(showRegister: .constant(false))
            .environmentObject(AuthManager())
    }
}
