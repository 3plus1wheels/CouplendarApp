import SwiftUI

struct RegisterView: View {
    @EnvironmentObject private var authManager: AuthManager
    @Environment(\.dismiss) private var dismiss

    @State private var email = ""
    @State private var password = ""
    @State private var displayName = ""

    var body: some View {
        VStack(alignment: .leading, spacing: AppSpacing.lg) {
            Text("Create account")
                .font(AppTypography.largeTitle)
                .foregroundStyle(AppColors.primaryText)

            TextField("Display Name", text: $displayName)
                .textFieldStyle(.roundedBorder)

            TextField("Email", text: $email)
                .textInputAutocapitalization(.never)
                .keyboardType(.emailAddress)
                .autocorrectionDisabled()
                .textFieldStyle(.roundedBorder)

            SecureField("Password", text: $password)
                .textFieldStyle(.roundedBorder)

            Button {
                Task {
                    await authManager.register(email: email, password: password, displayName: displayName)
                    if authManager.isAuthenticated {
                        dismiss()
                    }
                }
            } label: {
                Text(authManager.isLoading ? "Creating..." : "Create Account")
                    .frame(maxWidth: .infinity)
            }
            .buttonStyle(.borderedProminent)
            .disabled(authManager.isLoading || email.isEmpty || password.isEmpty || displayName.isEmpty)

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
    RegisterView()
        .environmentObject(AuthManager())
}
