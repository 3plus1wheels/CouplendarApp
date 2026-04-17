import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var authManager: AuthManager
    @StateObject private var viewModel = HomeViewModel()
    @State private var showProfile = false

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
                Button {
                    showProfile = true
                } label: {
                    Image(systemName: "person.crop.circle.fill")
                        .font(.system(size: 30))
                        .foregroundStyle(AppColors.blush)
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("open_profile_button")
            }
        }
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

#Preview { HomeView() }
