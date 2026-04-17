import SwiftUI

struct LoginView: View {
    @EnvironmentObject private var authManager: AuthManager
    @Binding var showRegister: Bool

    @State private var email = ""
    @State private var password = ""
    @State private var isPasswordVisible = false

    private var trimmedEmail: String {
        email.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var trimmedPassword: String {
        password.trimmingCharacters(in: .whitespacesAndNewlines)
    }

    private var canSubmit: Bool {
        !trimmedEmail.isEmpty && !trimmedPassword.isEmpty
    }

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 22) {
                brandRow
                titleBlock
                formBlock
                forgotPassword
                signInButton
                socialDivider
                socialButtons
                footer
            }
            .padding(.horizontal, 18)
            .padding(.top, 16)
            .padding(.bottom, 24)
        }
        .background(Color(red: 0.95, green: 0.94, blue: 0.97).ignoresSafeArea())
    }

    private var brandRow: some View {
        HStack(spacing: 12) {
            RoundedRectangle(cornerRadius: 12, style: .continuous)
                .fill(
                    LinearGradient(
                        colors: [Color(red: 0.91, green: 0.41, blue: 0.63), Color(red: 0.78, green: 0.35, blue: 0.73)],
                        startPoint: .topLeading,
                        endPoint: .bottomTrailing
                    )
                )
                .frame(width: 38, height: 38)
                .overlay {
                    Image(systemName: "heart.fill")
                        .foregroundStyle(.white)
                        .font(.body.weight(.bold))
                }

            Text("Couplendar")
                .font(.title3.weight(.semibold))
                .foregroundStyle(Color(red: 0.18, green: 0.16, blue: 0.26))
        }
    }

    private var titleBlock: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text("Welcome back💕")
                .font(.system(size: 48, weight: .heavy, design: .rounded))
                .minimumScaleFactor(0.75)
                .lineLimit(1)
                .foregroundStyle(Color(red: 0.11, green: 0.10, blue: 0.18))

            Text("Sign in to continue planning with your partner")
                .font(.subheadline.weight(.medium))
                .foregroundStyle(Color(red: 0.50, green: 0.48, blue: 0.60))
        }
    }

    private var formBlock: some View {
        VStack(alignment: .leading, spacing: 12) {
            AuthLabel("Email address")
            AuthInputContainer {
                TextField("you@example.com", text: $email)
                    .textInputAutocapitalization(.never)
                    .keyboardType(.emailAddress)
                    .autocorrectionDisabled()
            }

            AuthLabel("Password")
            AuthInputContainer {
                HStack(spacing: 8) {
                    Group {
                        if isPasswordVisible {
                            TextField("........", text: $password)
                        } else {
                            SecureField("........", text: $password)
                        }
                    }

                    Button {
                        isPasswordVisible.toggle()
                    } label: {
                        Image(systemName: isPasswordVisible ? "eye.slash" : "eye")
                            .foregroundStyle(Color(red: 0.66, green: 0.63, blue: 0.74))
                    }
                    .buttonStyle(.plain)
                    .accessibilityLabel(isPasswordVisible ? "Hide password" : "Show password")
                }
            }
        }
    }

    private var forgotPassword: some View {
        HStack {
            Spacer()
            Button("Forgot password?") {
            }
            .buttonStyle(.plain)
            .font(.headline.weight(.semibold))
            .foregroundStyle(Color(red: 0.78, green: 0.36, blue: 0.70))
        }
    }

    private var signInButton: some View {
        Button {
            Task {
                await authManager.login(email: trimmedEmail, password: trimmedPassword)
            }
        } label: {
            Text(authManager.isLoading ? "Signing In..." : "Sign In")
                .font(.title3.weight(.bold))
                .foregroundStyle(.white)
                .frame(maxWidth: .infinity)
                .padding(.vertical, 18)
                .background(
                    LinearGradient(
                        colors: [Color(red: 0.90, green: 0.38, blue: 0.58), Color(red: 0.74, green: 0.27, blue: 0.72)],
                        startPoint: .leading,
                        endPoint: .trailing
                    ),
                    in: RoundedRectangle(cornerRadius: 16, style: .continuous)
                )
                .shadow(color: Color(red: 0.85, green: 0.35, blue: 0.62).opacity(0.28), radius: 12, y: 7)
        }
        .buttonStyle(.plain)
        .disabled(authManager.isLoading || !canSubmit)
        .opacity(authManager.isLoading || !canSubmit ? 0.7 : 1.0)
    }

    private var socialDivider: some View {
        HStack(spacing: 10) {
            Rectangle()
                .fill(Color(red: 0.87, green: 0.85, blue: 0.92))
                .frame(height: 1)
            Text("or continue with")
                .font(.subheadline)
                .foregroundStyle(Color(red: 0.61, green: 0.58, blue: 0.70))
            Rectangle()
                .fill(Color(red: 0.87, green: 0.85, blue: 0.92))
                .frame(height: 1)
        }
        .padding(.top, 4)
    }

    private var socialButtons: some View {
        HStack(spacing: 12) {
            SocialStubButton(title: "Apple", systemImage: "apple.logo", dark: true)
            SocialStubButton(title: "Google", systemImage: nil, dark: false)
        }
    }

    private var footer: some View {
        HStack(spacing: 4) {
            Spacer()
            Text("New here?")
                .font(.title3.weight(.medium))
                .foregroundStyle(Color(red: 0.56, green: 0.53, blue: 0.65))
            Button("Create an account") {
                withAnimation(.spring(response: 0.4, dampingFraction: 0.9)) {
                    showRegister = true
                }
            }
            .buttonStyle(.plain)
            .font(.title3.weight(.bold))
            .foregroundStyle(Color(red: 0.79, green: 0.35, blue: 0.69))
            Spacer()
        }
        .padding(.top, 6)
    }
}

private struct AuthLabel: View {
    let text: String

    init(_ text: String) {
        self.text = text
    }

    var body: some View {
        Text(text)
            .font(.headline.weight(.semibold))
            .foregroundStyle(Color(red: 0.49, green: 0.47, blue: 0.59))
    }
}

private struct AuthInputContainer<Content: View>: View {
    @ViewBuilder var content: Content

    var body: some View {
        content
            .padding(.horizontal, 14)
            .frame(height: 58)
            .background(.white, in: RoundedRectangle(cornerRadius: 16, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .stroke(Color(red: 0.88, green: 0.86, blue: 0.92), lineWidth: 1)
            )
    }
}

private struct SocialStubButton: View {
    let title: String
    let systemImage: String?
    let dark: Bool

    var body: some View {
        Button {
        } label: {
            HStack(spacing: 8) {
                if let systemImage {
                    Image(systemName: systemImage)
                        .font(.title3.weight(.semibold))
                } else {
                    Text("G")
                        .font(.title3.weight(.bold))
                        .foregroundStyle(Color(red: 0.13, green: 0.48, blue: 0.95))
                }

                Text(title)
                    .font(.headline.weight(.bold))
            }
            .foregroundStyle(dark ? .white : Color(red: 0.21, green: 0.21, blue: 0.28))
            .frame(maxWidth: .infinity)
            .frame(height: 52)
            .background(
                dark ? AnyShapeStyle(Color(red: 0.10, green: 0.10, blue: 0.19)) : AnyShapeStyle(.white),
                in: RoundedRectangle(cornerRadius: 16, style: .continuous)
            )
            .overlay(
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .stroke(Color(red: 0.88, green: 0.86, blue: 0.92), lineWidth: dark ? 0 : 1)
            )
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    NavigationStack {
        LoginView(showRegister: .constant(false))
            .environmentObject(AuthManager())
    }
}
