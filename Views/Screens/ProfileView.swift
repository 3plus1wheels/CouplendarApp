import SwiftUI

struct ProfileView: View {
    @StateObject private var viewModel = ProfileViewModel()

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppSpacing.lg) {
                HStack {
                    Text("Profile").font(AppTypography.largeTitle).foregroundStyle(AppColors.primaryText)
                    Spacer()
                    Button(viewModel.isEditing ? "Save" : "Edit") { viewModel.toggleEdit() }
                        .font(.headline)
                }

                PrimaryCard {
                    VStack(alignment: .leading, spacing: AppSpacing.sm) {
                        AvatarStackView(first: String(viewModel.profile.yourName.prefix(1)), second: String(viewModel.profile.partnerName.prefix(1)))
                        Text("\(viewModel.profile.yourName) + \(viewModel.profile.partnerName)").font(AppTypography.title)
                        Text(viewModel.profile.relationshipLabel).font(AppTypography.body).foregroundStyle(AppColors.secondaryText)
                        Text(viewModel.profile.anniversaryText).font(AppTypography.caption).foregroundStyle(AppColors.secondaryText)
                    }
                }

                PrimaryCard {
                    Toggle("Plan reminders", isOn: $viewModel.profile.notificationsEnabled)
                }

                PrimaryCard {
                    VStack(alignment: .leading, spacing: AppSpacing.sm) {
                        Text("Preferences").font(AppTypography.cardTitle)
                        Text("Date vibe: Cozy & low-key").font(AppTypography.body)
                        Text("Budget style: Mid-range").font(AppTypography.body)
                    }
                }
            }
            .padding(AppSpacing.md)
        }
        .background(GlassBackgroundView())
    }
}

#Preview { ProfileView() }
