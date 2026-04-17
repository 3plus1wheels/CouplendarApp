import SwiftUI

struct CalendarView: View {
    @EnvironmentObject private var authManager: AuthManager
    @StateObject private var viewModel = CalendarViewModel()
    @State private var showProfile = false

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppSpacing.lg) {
                HStack {
                    Text(viewModel.monthTitle).font(AppTypography.largeTitle).foregroundStyle(AppColors.primaryText)
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

                Picker("Mode", selection: $viewModel.mode) {
                    ForEach(CalendarViewModel.Mode.allCases) { mode in
                        Text(mode.rawValue).tag(mode)
                    }
                }
                .pickerStyle(.segmented)

                ForEach(viewModel.plans) { plan in
                    PrimaryCard {
                        VStack(alignment: .leading, spacing: AppSpacing.xs) {
                            Text(plan.title).font(AppTypography.cardTitle)
                            Text(plan.date.formatted(date: .abbreviated, time: .shortened)).font(AppTypography.caption)
                            Text(plan.location).font(AppTypography.caption).foregroundStyle(AppColors.secondaryText)
                        }
                    }
                }
            }
            .padding(AppSpacing.md)
        }
        .overlay(alignment: .bottomTrailing) {
            Button {
            } label: {
                Image(systemName: "plus")
                    .font(.title3.weight(.bold))
                    .foregroundStyle(.white)
                    .frame(width: 52, height: 52)
                    .background(AppColors.blush)
                    .clipShape(Circle())
                    .shadow(color: AppColors.blush.opacity(0.4), radius: 8, y: 4)
            }
            .padding()
        }
        .background(GlassBackgroundView())
        .sheet(isPresented: $showProfile) {
            NavigationStack {
                ProfileView()
            }
            .environmentObject(authManager)
        }
    }
}

#Preview { CalendarView() }
