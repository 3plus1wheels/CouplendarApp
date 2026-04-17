import SwiftUI

struct ProfileView: View {
    @State private var notificationsEnabled = true
    @State private var darkModeEnabled = false
    @State private var language = "English"

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppSpacing.lg) {
                header
                heroCard
                storySection
                preferencesSection
                accountSection
                supportSection
                footer
            }
            .padding(AppSpacing.md)
            .padding(.bottom, AppSpacing.xl)
        }
        .background(GlassBackgroundView())
    }

    private var header: some View {
        HStack {
            Text("Profile")
                .font(AppTypography.largeTitle)
                .foregroundStyle(AppColors.primaryText)
            Spacer()
            Button("Edit") { }
                .font(AppTypography.cardTitle)
                .foregroundStyle(AppColors.blush)
                .padding(.horizontal, AppSpacing.md)
                .padding(.vertical, AppSpacing.sm)
                .background(.white.opacity(0.8))
                .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
        }
    }

    private var heroCard: some View {
        PrimaryCard {
            HStack(spacing: AppSpacing.md) {
                HStack(spacing: -12) {
                    avatar(symbol: "person.fill", color: AppColors.blush.opacity(0.85))
                    avatar(symbol: "person.fill", color: AppColors.lavender.opacity(0.85))
                }
                .padding(.trailing, AppSpacing.xs)

                VStack(alignment: .leading, spacing: AppSpacing.xs) {
                    Text("Sofia Chen")
                        .font(AppTypography.title)
                        .foregroundStyle(AppColors.primaryText)
                    Text("& Alex Kim")
                        .font(AppTypography.body.weight(.semibold))
                        .foregroundStyle(AppColors.secondaryText)
                    Text("♥ Together since Jan 15, 2023")
                        .font(AppTypography.caption.weight(.semibold))
                        .foregroundStyle(AppColors.blush)
                        .padding(.horizontal, AppSpacing.sm)
                        .padding(.vertical, AppSpacing.xs)
                        .background(AppColors.blush.opacity(0.16))
                        .clipShape(RoundedRectangle(cornerRadius: 10, style: .continuous))
                }
                Spacer()
            }
        }
    }

    private var storySection: some View {
        VStack(alignment: .leading, spacing: AppSpacing.sm) {
            profileSectionTitle("Your Story")
            PrimaryCard {
                HStack(spacing: AppSpacing.sm) {
                    StoryStatCard(value: "1,179", label: "Days Together", tint: AppColors.blush)
                    StoryStatCard(value: "48", label: "Dates Planned", tint: AppColors.lavender)
                    StoryStatCard(value: "23", label: "Places Visited", tint: AppColors.mint)
                }
            }
        }
    }

    private var preferencesSection: some View {
        VStack(alignment: .leading, spacing: AppSpacing.sm) {
            profileSectionTitle("PREFERENCES")
            PrimaryCard {
                VStack(spacing: 0) {
                    ToggleRow(
                        icon: "bell.fill",
                        iconTint: AppColors.blush,
                        title: "Notifications",
                        isOn: $notificationsEnabled,
                        accent: AppColors.blush
                    )
                    divider
                    ToggleRow(
                        icon: "moon.fill",
                        iconTint: AppColors.lavender,
                        title: "Dark Mode",
                        isOn: $darkModeEnabled,
                        accent: AppColors.lavender
                    )
                    divider
                    DetailRow(
                        icon: "globe",
                        iconTint: AppColors.mint,
                        title: "Language",
                        detail: language
                    )
                }
            }
        }
    }

    private var accountSection: some View {
        VStack(alignment: .leading, spacing: AppSpacing.sm) {
            profileSectionTitle("ACCOUNT")
            PrimaryCard {
                VStack(spacing: 0) {
                    DetailRow(icon: "lock.fill", iconTint: .orange, title: "Privacy & Security", detail: nil)
                    divider
                    DetailRow(icon: "paintpalette.fill", iconTint: AppColors.blush, title: "Appearance", detail: nil)
                }
            }
        }
    }

    private var supportSection: some View {
        VStack(alignment: .leading, spacing: AppSpacing.sm) {
            profileSectionTitle("SUPPORT")
            PrimaryCard {
                DetailRow(icon: "questionmark.circle.fill", iconTint: AppColors.lavender, title: "Help & FAQ", detail: nil)
            }
            PrimaryCard {
                DetailRow(icon: "arrow.right.square.fill", iconTint: AppColors.blush, title: "Sign Out", detail: nil, isDestructive: true)
            }
            PrimaryCard {
                DetailRow(icon: "trash.fill", iconTint: AppColors.blush, title: "Delete Account", detail: nil, isDestructive: true)
            }
        }
    }

    private var footer: some View {
        Text("Couplendar v1.0.0 · Made with 💕")
            .font(AppTypography.caption)
            .foregroundStyle(AppColors.secondaryText.opacity(0.7))
            .frame(maxWidth: .infinity, alignment: .center)
            .padding(.top, AppSpacing.xs)
    }

    private var divider: some View {
        Rectangle()
            .fill(AppColors.secondaryText.opacity(0.12))
            .frame(height: 1)
            .padding(.leading, 42)
    }

    private func avatar(symbol: String, color: Color) -> some View {
        Image(systemName: symbol)
            .font(.system(size: 18, weight: .semibold))
            .foregroundStyle(.white)
            .frame(width: 54, height: 54)
            .background(color)
            .clipShape(Circle())
            .overlay(
                Circle()
                    .stroke(.white.opacity(0.9), lineWidth: 3)
            )
    }

    private func profileSectionTitle(_ title: String) -> some View {
        Text(title)
            .font(AppTypography.caption.weight(.bold))
            .tracking(0.9)
            .foregroundStyle(AppColors.secondaryText.opacity(0.9))
            .padding(.leading, 2)
    }
}

private struct StoryStatCard: View {
    let value: String
    let label: String
    let tint: Color

    var body: some View {
        VStack(spacing: AppSpacing.xs) {
            Text(value)
                .font(.system(size: 32, weight: .bold, design: .rounded))
                .minimumScaleFactor(0.65)
                .lineLimit(1)
                .foregroundStyle(tint)
            Text(label)
                .font(AppTypography.caption.weight(.medium))
                .foregroundStyle(AppColors.secondaryText)
        }
        .frame(maxWidth: .infinity)
        .padding(.vertical, AppSpacing.md)
        .background(tint.opacity(0.14))
        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
    }
}

private struct ToggleRow: View {
    let icon: String
    let iconTint: Color
    let title: String
    @Binding var isOn: Bool
    let accent: Color

    var body: some View {
        HStack(spacing: AppSpacing.sm) {
            rowIcon
            Text(title)
                .font(AppTypography.body.weight(.medium))
                .foregroundStyle(AppColors.primaryText)
            Spacer()
            Toggle("", isOn: $isOn)
                .labelsHidden()
                .tint(accent)
        }
        .padding(.vertical, 12)
    }

    private var rowIcon: some View {
        Image(systemName: icon)
            .font(.system(size: 14, weight: .semibold))
            .foregroundStyle(.white)
            .frame(width: 28, height: 28)
            .background(iconTint)
            .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
    }
}

private struct DetailRow: View {
    let icon: String
    let iconTint: Color
    let title: String
    let detail: String?
    var isDestructive = false

    var body: some View {
        HStack(spacing: AppSpacing.sm) {
            rowIcon
            Text(title)
                .font(AppTypography.body.weight(.medium))
                .foregroundStyle(isDestructive ? AppColors.blush : AppColors.primaryText)
            Spacer()
            if let detail {
                Text(detail)
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.secondaryText)
            }
            Image(systemName: "chevron.right")
                .font(.caption.weight(.semibold))
                .foregroundStyle(AppColors.secondaryText.opacity(0.55))
        }
        .padding(.vertical, 12)
    }

    private var rowIcon: some View {
        Image(systemName: icon)
            .font(.system(size: 14, weight: .semibold))
            .foregroundStyle(.white)
            .frame(width: 28, height: 28)
            .background(iconTint)
            .clipShape(RoundedRectangle(cornerRadius: 8, style: .continuous))
    }
}

#Preview {
    ProfileView()
}
