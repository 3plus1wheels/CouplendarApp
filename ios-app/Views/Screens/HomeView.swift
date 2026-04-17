import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var authManager: AuthManager
    @StateObject private var viewModel = HomeViewModel()
    @State private var showProfile = false
    @State private var showNotifications = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppSpacing.lg) {
                header
                if let next = viewModel.nextUp { nextUpCard(next) }
                upcomingSection
                suggestionSection
                reminderSection
            }
            .padding(AppSpacing.md)
        }
        .background(GlassBackgroundView())
        .sheet(isPresented: $showProfile) {
            NavigationStack {
                ProfileView()
            }
            .environmentObject(authManager)
        }
        .sheet(isPresented: $showNotifications) {
            NotificationsSheetView(isPresented: $showNotifications)
                .environmentObject(authManager)
        }
    }

    private var header: some View {
        VStack(alignment: .leading, spacing: AppSpacing.sm) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: AppSpacing.sm) {
                    Text("Hi Vova")
                        .font(AppTypography.largeTitle)
                        .foregroundStyle(AppColors.primaryText)
                    Text("Let’s make this week feel intentional")
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.secondaryText)
                }
                Spacer()
                HStack(spacing: AppSpacing.sm) {
                    headerCircleButton(
                        symbol: "bell.fill",
                        accent: AppColors.blush,
                        action: { showNotifications = true }
                    )
                    headerCircleButton(
                        symbol: "person.fill",
                        accent: AppColors.blush,
                        action: { showProfile = true },
                        accessibilityIdentifier: "open_profile_button"
                    )
                }
            }
        }
    }

    private func headerCircleButton(
        symbol: String,
        accent: Color,
        action: @escaping () -> Void,
        accessibilityIdentifier: String = ""
    ) -> some View {
        Button(action: action) {
            Image(systemName: symbol)
                .font(.system(size: 16, weight: .semibold))
                .foregroundStyle(accent)
                .frame(width: 38, height: 38)
                .background(.white.opacity(0.85))
                .clipShape(Circle())
        }
        .buttonStyle(.plain)
        .accessibilityIdentifier(accessibilityIdentifier.isEmpty ? "header_\(symbol)_button" : accessibilityIdentifier)
    }

    private func nextUpCard(_ plan: Plan) -> some View {
        PrimaryCard {
            VStack(alignment: .leading, spacing: AppSpacing.sm) {
                Text("Next up").font(AppTypography.caption).foregroundStyle(AppColors.secondaryText)
                Text(plan.title).font(AppTypography.title).foregroundStyle(AppColors.primaryText)
                Text(plan.date.formatted(date: .abbreviated, time: .shortened))
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.secondaryText)
                ChipView(title: plan.vibe, isActive: true, variant: .blush)
            }
        }
        .accessibilityIdentifier("home_next_up")
    }

    private var upcomingSection: some View {
        VStack(alignment: .leading, spacing: AppSpacing.sm) {
            SectionHeader(title: "Upcoming plans", subtitle: "A few things to look forward to")
            ScrollView(.horizontal, showsIndicators: false) {
                HStack(spacing: AppSpacing.sm) {
                    ForEach(viewModel.plans) { plan in
                        PrimaryCard {
                            VStack(alignment: .leading, spacing: AppSpacing.xs) {
                                Text(plan.title).font(AppTypography.cardTitle)
                                Text(plan.location).font(AppTypography.caption).foregroundStyle(AppColors.secondaryText)
                            }
                            .frame(width: 180, alignment: .leading)
                        }
                    }
                }
            }
        }
    }

    private var suggestionSection: some View {
        VStack(alignment: .leading, spacing: AppSpacing.sm) {
            SectionHeader(title: "Suggestions", subtitle: "Tiny actions with big payoff")
            ForEach(viewModel.suggestions) { item in
                PrimaryCard {
                    HStack(spacing: AppSpacing.sm) {
                        Text(item.emoji).font(.title3)
                        VStack(alignment: .leading) {
                            Text(item.title).font(AppTypography.cardTitle)
                            Text(item.subtitle).font(AppTypography.caption).foregroundStyle(AppColors.secondaryText)
                        }
                        Spacer()
                    }
                }
            }
        }
    }

    private var reminderSection: some View {
        VStack(alignment: .leading, spacing: AppSpacing.sm) {
            SectionHeader(title: "Partner pulse", subtitle: nil)
            ForEach(viewModel.reminders, id: \.self) { reminder in
                PrimaryCard {
                    Text(reminder).font(AppTypography.body).foregroundStyle(AppColors.primaryText)
                }
            }
        }
    }
}

private struct NotificationsSheetView: View {
    @EnvironmentObject private var authManager: AuthManager
    @Binding var isPresented: Bool
    @StateObject private var viewModel = NotificationsViewModel()

    var body: some View {
        ZStack {
            GlassBackgroundView()
            VStack(spacing: AppSpacing.md) {
                Capsule()
                    .fill(AppColors.lavender.opacity(0.4))
                    .frame(width: 46, height: 5)
                    .padding(.top, AppSpacing.sm)

                HStack(spacing: AppSpacing.xs) {
                    Text("Notifications")
                        .font(AppTypography.title)
                        .foregroundStyle(AppColors.primaryText)
                    Text("\(viewModel.unreadCount)")
                        .font(AppTypography.caption.weight(.bold))
                        .foregroundStyle(.white)
                        .padding(.horizontal, AppSpacing.xs)
                        .padding(.vertical, 3)
                        .background(AppColors.blush)
                        .clipShape(Capsule())
                    Spacer()
                    Button {
                        Task {
                            await viewModel.markAllRead(authManager: authManager)
                        }
                    } label: {
                        Text("Mark all read")
                            .font(AppTypography.caption.weight(.semibold))
                            .foregroundStyle(AppColors.blush)
                            .padding(.horizontal, AppSpacing.sm)
                            .padding(.vertical, AppSpacing.xs)
                            .background(AppColors.blush.opacity(0.15))
                            .clipShape(Capsule())
                    }
                    .buttonStyle(.plain)

                    Button {
                        isPresented = false
                    } label: {
                        Image(systemName: "xmark")
                            .font(.system(size: 12, weight: .bold))
                            .foregroundStyle(AppColors.secondaryText)
                            .frame(width: 30, height: 30)
                            .background(.white.opacity(0.75))
                            .clipShape(Circle())
                    }
                    .buttonStyle(.plain)
                }
                .padding(.horizontal, AppSpacing.md)

                ScrollView {
                    VStack(spacing: AppSpacing.sm) {
                        if viewModel.isLoading && viewModel.items.isEmpty {
                            ProgressView()
                                .padding(.top, AppSpacing.lg)
                        }

                        if let errorMessage = viewModel.errorMessage, !errorMessage.isEmpty {
                            PrimaryCard {
                                Text(errorMessage)
                                    .font(AppTypography.body)
                                    .foregroundStyle(AppColors.blush)
                            }
                        }

                        if !viewModel.isLoading && viewModel.items.isEmpty {
                            PrimaryCard {
                                Text("No notifications yet")
                                    .font(AppTypography.body)
                                    .foregroundStyle(AppColors.secondaryText)
                            }
                        }

                        ForEach(viewModel.items) { item in
                            Button {
                                Task {
                                    await viewModel.markRead(item: item, authManager: authManager)
                                }
                            } label: {
                                NotificationCard(item: item)
                            }
                            .buttonStyle(.plain)
                        }
                    }
                    .padding(.horizontal, AppSpacing.md)
                    .padding(.bottom, AppSpacing.xl)
                }
            }
        }
        .presentationDetents([.large])
        .presentationDragIndicator(.hidden)
        .task {
            await viewModel.load(authManager: authManager)
        }
    }
}

private struct NotificationCard: View {
    let item: NotificationFeedItem

    var body: some View {
        HStack(alignment: .top, spacing: AppSpacing.sm) {
            ZStack(alignment: .topTrailing) {
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .fill(iconBackgroundColor)
                    .frame(width: 44, height: 44)
                    .overlay(
                        Text(iconEmoji)
                            .font(.system(size: 20))
                    )
                if !item.isRead {
                    Circle()
                        .fill(AppColors.blush)
                        .frame(width: 8, height: 8)
                        .offset(x: 3, y: -3)
                }
            }

            VStack(alignment: .leading, spacing: 4) {
                HStack(alignment: .firstTextBaseline) {
                    Text(item.title)
                        .font(AppTypography.cardTitle)
                        .foregroundStyle(AppColors.primaryText)
                    Spacer()
                    Text(item.timeAgo)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.secondaryText.opacity(0.8))
                }
                Text(item.body)
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.secondaryText)
                Text(item.tag)
                    .font(AppTypography.caption.weight(.bold))
                    .foregroundStyle(tagColor)
                    .padding(.horizontal, AppSpacing.xs)
                    .padding(.vertical, 3)
                    .background(tagColor.opacity(0.15))
                    .clipShape(RoundedRectangle(cornerRadius: 6, style: .continuous))
            }
        }
        .padding(AppSpacing.md)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(.white.opacity(0.8))
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(item.isRead ? .clear : AppColors.lavender.opacity(0.3), lineWidth: 1)
        )
    }

    private var tagColor: Color {
        switch item.tag {
        case "INVITE":
            return AppColors.lavender
        case "EVENT":
            return AppColors.mint
        case "REMINDER RULE":
            return AppColors.secondaryText
        default:
            return AppColors.blush
        }
    }

    private var iconEmoji: String {
        switch item.tag {
        case "INVITE":
            return "💌"
        case "EVENT":
            return "📅"
        case "REMINDER RULE":
            return "⚙️"
        default:
            return "⏰"
        }
    }

    private var iconBackgroundColor: Color {
        tagColor.opacity(0.22)
    }
}

#Preview { HomeView() }
