import SwiftUI
import UIKit

struct ProfileView: View {
    private enum ProfileStage {
        case paired
        case solo
    }

    @EnvironmentObject private var authManager: AuthManager

    @State private var notificationsEnabled = true
    @State private var darkModeEnabled = false
    @State private var language = "English"
    @State private var showInviteComposer = false
    @State private var inviteTarget = ""
    @State private var didCopyInviteCode = false

    // Frontend-only mock stage switch. Keep `solo` until data wiring exists.
    private let stage: ProfileStage = .solo

    private var primaryName: String {
        let trimmed = authManager.currentUser?.displayName.trimmingCharacters(in: .whitespacesAndNewlines) ?? ""
        return trimmed.isEmpty ? "Profile" : trimmed
    }

    private var inviteCode: String? {
        let code = authManager.currentUser?.code?.trimmingCharacters(in: .whitespacesAndNewlines)
        guard let code, !code.isEmpty else { return nil }
        return code.uppercased().replacingOccurrences(of: "-", with: ".")
    }

    var body: some View {
        ZStack {
            ScrollView {
                VStack(alignment: .leading, spacing: AppSpacing.lg) {
                    header

                    if stage == .solo {
                        soloHeroCard
                        inviteCard
                        storyEmptySection
                        preferencesSection
                        accountSection
                        supportSection
                        footer
                    } else {
                        pairedHeroCard
                        storySection
                        preferencesSection
                        accountSection
                        supportSection
                        footer
                    }
                }
                .padding(AppSpacing.md)
                .padding(.bottom, AppSpacing.xl)
            }
            .background(GlassBackgroundView())
            .task {
                await authManager.fetchProfile()
            }

            if showInviteComposer {
                inviteComposerOverlay
                    .transition(.opacity.combined(with: .scale(scale: 0.98)))
            }
        }
        .animation(.spring(response: 0.35, dampingFraction: 0.88), value: showInviteComposer)
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

    private var soloHeroCard: some View {
        PrimaryCard {
            HStack(spacing: AppSpacing.md) {
                HStack(spacing: AppSpacing.xs) {
                    avatar(symbol: "person.fill", color: AppColors.blush.opacity(0.85), size: 60)

                    ZStack {
                        Circle()
                            .stroke(style: StrokeStyle(lineWidth: 2, dash: [5, 5]))
                            .foregroundStyle(AppColors.blush.opacity(0.45))
                            .frame(width: 56, height: 56)

                        Button {
                            showInviteComposer = true
                        } label: {
                            Circle()
                                .fill(AppColors.blush.opacity(0.92))
                                .frame(width: 28, height: 28)
                                .overlay(
                                    Image(systemName: "plus")
                                        .font(.system(size: 13, weight: .bold))
                                        .foregroundStyle(.white)
                                )
                        }
                        .buttonStyle(.plain)
                    }
                }

                VStack(alignment: .leading, spacing: AppSpacing.xs) {
                    Text(primaryName)
                        .font(AppTypography.title)
                        .foregroundStyle(AppColors.primaryText)

                    Text("Solo for now 🌸")
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.secondaryText)
                }

                Spacer(minLength: 0)
            }
        }
    }

    private var inviteCard: some View {
        VStack(alignment: .leading, spacing: AppSpacing.md) {
            HStack(spacing: AppSpacing.sm) {
                inviteIcon(systemName: "person.crop.circle.badge.plus")

                VStack(alignment: .leading, spacing: 2) {
                    Text("Invite your person 💌")
                        .font(AppTypography.title)
                        .foregroundStyle(AppColors.primaryText)
                    Text("Share your code to start planning together")
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.secondaryText)
                }

                Spacer()
            }

                VStack(alignment: .leading, spacing: AppSpacing.xs) {
                    Text("YOUR INVITE CODE")
                        .font(AppTypography.caption.weight(.bold))
                        .tracking(1.0)
                        .foregroundStyle(AppColors.secondaryText)

                HStack {
                    Text(inviteCode ?? "NOT AVAILABLE")
                        .font(.system(size: 33, weight: .bold, design: .rounded))
                        .minimumScaleFactor(0.6)
                        .lineLimit(1)
                        .foregroundStyle(AppColors.primaryText)

                    Spacer()

                    Button {
                        guard let code = inviteCode else { return }
                        UIPasteboard.general.string = code
                        didCopyInviteCode = true
                    } label: {
                        inviteIcon(systemName: "doc.on.doc")
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(AppSpacing.md)
            .background(.white.opacity(0.72))
            .clipShape(RoundedRectangle(cornerRadius: 15, style: .continuous))

            if didCopyInviteCode {
                Text("Copied")
                    .font(AppTypography.caption.weight(.semibold))
                    .foregroundStyle(AppColors.blush)
                    .transition(.opacity)
            }

        }
        .padding(AppSpacing.md)
        .background(AppColors.blush.opacity(0.08))
        .overlay(
            RoundedRectangle(cornerRadius: 24, style: .continuous)
                .stroke(AppColors.blush.opacity(0.35), style: StrokeStyle(lineWidth: 1.2, dash: [4, 4]))
        )
        .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
    }

    private var storyEmptySection: some View {
        PrimaryCard {
            VStack(alignment: .leading, spacing: AppSpacing.md) {
                profileSectionTitle("Your Story")

                HStack(spacing: AppSpacing.sm) {
                    StoryStatCard(value: "—", label: "Days Together", tint: AppColors.blush)
                    StoryStatCard(value: "—", label: "Dates Planned", tint: AppColors.lavender)
                    StoryStatCard(value: "—", label: "Places Visited", tint: AppColors.mint)
                }

                HStack(spacing: AppSpacing.xs) {
                    Text("🧑‍🤝‍🧑")
                    Text("Connect with a partner to start your story")
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.secondaryText)
                }
                .padding(.horizontal, AppSpacing.md)
                .padding(.vertical, 12)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(AppColors.lavender.opacity(0.28))
                .clipShape(RoundedRectangle(cornerRadius: 13, style: .continuous))
            }
        }
    }

    private var pairedHeroCard: some View {
        PrimaryCard {
            HStack(spacing: AppSpacing.md) {
                HStack(spacing: -12) {
                    avatar(symbol: "person.fill", color: AppColors.blush.opacity(0.85), size: 54)
                    avatar(symbol: "person.fill", color: AppColors.lavender.opacity(0.85), size: 54)
                }
                .padding(.trailing, AppSpacing.xs)

                VStack(alignment: .leading, spacing: AppSpacing.xs) {
                    Text(primaryName)
                        .font(AppTypography.title)
                        .foregroundStyle(AppColors.primaryText)
                    Text("& Partner")
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
                DetailRow(
                    icon: "arrow.right.square.fill",
                    iconTint: AppColors.blush,
                    title: "Sign Out",
                    detail: nil,
                    isDestructive: true
                ) {
                    showInviteComposer = false
                    inviteTarget = ""
                    authManager.logout()
                }
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

    private func inviteIcon(systemName: String) -> some View {
        Image(systemName: systemName)
            .font(.system(size: 16, weight: .semibold))
            .foregroundStyle(.white)
            .frame(width: 36, height: 36)
            .background(AppColors.blush)
            .clipShape(RoundedRectangle(cornerRadius: 12, style: .continuous))
            .shadow(color: AppColors.blush.opacity(0.24), radius: 8, x: 0, y: 4)
    }

    private func avatar(symbol: String, color: Color, size: CGFloat) -> some View {
        Image(systemName: symbol)
            .font(.system(size: size * 0.34, weight: .semibold))
            .foregroundStyle(.white)
            .frame(width: size, height: size)
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

    private var inviteComposerOverlay: some View {
        ZStack {
            Color.black.opacity(0.18)
                .ignoresSafeArea()
                .onTapGesture {
                    showInviteComposer = false
                }

            VStack(alignment: .leading, spacing: AppSpacing.md) {
                HStack {
                    Text("Send invite")
                        .font(AppTypography.title)
                        .foregroundStyle(AppColors.primaryText)
                    Spacer()
                    Button {
                        showInviteComposer = false
                    } label: {
                        Image(systemName: "xmark")
                            .font(.system(size: 13, weight: .bold))
                            .foregroundStyle(AppColors.secondaryText)
                            .frame(width: 28, height: 28)
                            .background(.white.opacity(0.7))
                            .clipShape(Circle())
                    }
                    .buttonStyle(.plain)
                }

                TextField("Invite code", text: $inviteTarget)
                    .textInputAutocapitalization(.never)
                    .autocorrectionDisabled()
                    .padding(.horizontal, AppSpacing.md)
                    .padding(.vertical, 14)
                    .background(.white.opacity(0.86))
                    .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))

                if let inviteError = authManager.errorMessage, !inviteError.isEmpty {
                    Text(inviteError)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.blush)
                }

                Button {
                    Task {
                        let sent = await authManager.sendInvite(inviteCode: inviteTarget)
                        if sent {
                            inviteTarget = ""
                            showInviteComposer = false
                        }
                    }
                } label: {
                    Text("Send Invite")
                        .font(AppTypography.cardTitle)
                        .foregroundStyle(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 13)
                        .background(AppColors.blush)
                        .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                }
                .buttonStyle(.plain)
                .disabled(authManager.isLoading || inviteTarget.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty)
                .opacity(authManager.isLoading || inviteTarget.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty ? 0.7 : 1)
            }
            .padding(AppSpacing.md)
            .frame(maxWidth: 320)
            .background(.white.opacity(0.92))
            .clipShape(RoundedRectangle(cornerRadius: 24, style: .continuous))
            .shadow(color: AppColors.primaryText.opacity(0.16), radius: 24, x: 0, y: 12)
            .padding(.horizontal, AppSpacing.lg)
        }
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
    var action: (() -> Void)? = nil

    var body: some View {
        if let action {
            Button(action: action) {
                content
            }
            .buttonStyle(.plain)
            .frame(maxWidth: .infinity, alignment: .leading)
            .contentShape(Rectangle())
        } else {
            content
        }
    }

    private var content: some View {
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
        .environmentObject(AuthManager())
}
