import SwiftUI

struct ProfileView: View {
    @EnvironmentObject private var authManager: AuthManager

    @State private var draftDisplayName = ""
    @State private var draftFirstName = ""
    @State private var draftLastName = ""
    @State private var draftCity = ""
    @State private var isEditing = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppSpacing.lg) {
                HStack {
                    Text("Profile").font(AppTypography.largeTitle).foregroundStyle(AppColors.primaryText)
                    Spacer()
                    Button(isEditing ? "Save" : "Edit") {
                        if isEditing {
                            Task {
                                await authManager.updateProfile(
                                    displayName: draftDisplayName,
                                    firstName: draftFirstName,
                                    lastName: draftLastName,
                                    city: draftCity
                                )
                                isEditing = false
                            }
                        } else {
                            isEditing = true
                        }
                    }
                        .font(.headline)
                }

                PrimaryCard {
                    VStack(alignment: .leading, spacing: AppSpacing.sm) {
                        AvatarStackView(
                            first: String((authManager.currentUser?.firstName.first ?? Character("Y"))),
                            second: String((authManager.currentUser?.lastName.first ?? Character("P")))
                        )

                        if isEditing {
                            TextField("Display Name", text: $draftDisplayName)
                                .textFieldStyle(.roundedBorder)
                            TextField("First Name", text: $draftFirstName)
                                .textFieldStyle(.roundedBorder)
                            TextField("Last Name", text: $draftLastName)
                                .textFieldStyle(.roundedBorder)
                            TextField("City", text: $draftCity)
                                .textFieldStyle(.roundedBorder)
                        } else {
                            Text(authManager.currentUser?.displayName ?? "Profile")
                                .font(AppTypography.title)
                            Text(authManager.currentUser?.email ?? "")
                                .font(AppTypography.body)
                                .foregroundStyle(AppColors.secondaryText)
                            Text(authManager.currentUser?.city ?? "")
                                .font(AppTypography.caption)
                                .foregroundStyle(AppColors.secondaryText)
                        }
                    }
                }
                .onAppear {
                    syncDraftFromUser()
                }

                Button("Log Out") {
                    authManager.logout()
                }
                .buttonStyle(.bordered)
            }
            .padding(AppSpacing.md)
        }
        .background(GlassBackgroundView())
        .task {
            await authManager.fetchProfile()
            syncDraftFromUser()
        }
    }

    private func syncDraftFromUser() {
        draftDisplayName = authManager.currentUser?.displayName ?? ""
        draftFirstName = authManager.currentUser?.firstName ?? ""
        draftLastName = authManager.currentUser?.lastName ?? ""
        draftCity = authManager.currentUser?.city ?? ""
    }
}

#Preview {
    ProfileView()
        .environmentObject(AuthManager())
}
