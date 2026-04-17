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
    @Binding var isPresented: Bool
    @State private var items: [NotificationItem] = NotificationItem.mock

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
                    Text("\(items.filter { !$0.isRead }.count)")
                        .font(AppTypography.caption.weight(.bold))
                        .foregroundStyle(.white)
                        .padding(.horizontal, AppSpacing.xs)
                        .padding(.vertical, 3)
                        .background(AppColors.blush)
                        .clipShape(Capsule())
                    Spacer()
                    Button {
                        for index in items.indices { items[index].isRead = true }
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
                        ForEach(items) { item in
                            NotificationCard(item: item)
                        }
                    }
                    .padding(.horizontal, AppSpacing.md)
                    .padding(.bottom, AppSpacing.xl)
                }
            }
        }
        .presentationDetents([.large])
        .presentationDragIndicator(.hidden)
    }
}

private struct NotificationCard: View {
    let item: NotificationItem

    var body: some View {
        HStack(alignment: .top, spacing: AppSpacing.sm) {
            ZStack(alignment: .topTrailing) {
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .fill(item.iconBg)
                    .frame(width: 44, height: 44)
                    .overlay(
                        Text(item.icon)
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
                    .foregroundStyle(item.tagColor)
                    .padding(.horizontal, AppSpacing.xs)
                    .padding(.vertical, 3)
                    .background(item.tagColor.opacity(0.15))
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
}

private struct NotificationItem: Identifiable {
    let id: UUID
    var title: String
    var body: String
    var timeAgo: String
    var tag: String
    var tagColor: Color
    var icon: String
    var iconBg: Color
    var isRead: Bool

    static let mock: [NotificationItem] = [
        NotificationItem(
            id: UUID(),
            title: "Alex added a plan",
            body: "\"Rooftop Drinks\" has been added to your shared calendar for Apr 22.",
            timeAgo: "2m ago",
            tag: "PLANS",
            tagColor: AppColors.lavender,
            icon: "🥃",
            iconBg: AppColors.lavender.opacity(0.25),
            isRead: false
        ),
        NotificationItem(
            id: UUID(),
            title: "Coming up soon",
            body: "Candlelit Dinner at La Maison is in 6 days. Confirm reservation soon.",
            timeAgo: "1h ago",
            tag: "REMINDER",
            tagColor: AppColors.blush,
            icon: "💞",
            iconBg: AppColors.blush.opacity(0.22),
            isRead: false
        ),
        NotificationItem(
            id: UUID(),
            title: "New place for you",
            body: "Based on your vibe, try The Botanic Garden, a hidden gem nearby.",
            timeAgo: "3h ago",
            tag: "EXPLORE",
            tagColor: AppColors.mint,
            icon: "🌿",
            iconBg: AppColors.mint.opacity(0.25),
            isRead: false
        ),
        NotificationItem(
            id: UUID(),
            title: "Alex loved your idea",
            body: "Alex reacted to your \"Cherry Blossom Walk\" plan suggestion.",
            timeAgo: "Today",
            tag: "PLANS",
            tagColor: AppColors.lavender,
            icon: "❤️",
            iconBg: AppColors.lavender.opacity(0.18),
            isRead: true
        ),
    ]
}

#Preview { HomeView() }
