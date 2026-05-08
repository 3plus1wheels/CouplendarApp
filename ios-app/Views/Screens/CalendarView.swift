import SwiftUI

struct CalendarView: View {
    @EnvironmentObject private var authManager: AuthManager
    @StateObject private var viewModel = CalendarViewModel()
    @State private var showProfile = false
    @State private var showAddEvent = false
    private let columns = Array(repeating: GridItem(.flexible(), spacing: AppSpacing.xs), count: 7)

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

                switch viewModel.mode {
                case .day:
                    dayModeCard
                case .week:
                    weekModeCard
                case .month:
                    monthModeCard
                }
            }
            .padding(AppSpacing.md)
        }
        .overlay(alignment: .bottomTrailing) {
            Button {
                showAddEvent = true
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
        .fullScreenCover(isPresented: $showAddEvent) {
            AddEventView(
                isPresented: $showAddEvent,
                onEventCreated: {
                    Task { await viewModel.loadEvents(authManager: authManager) }
                }
            )
            .environmentObject(authManager)
        }
        .task {
            await viewModel.loadEvents(authManager: authManager)
        }
    }

    @ViewBuilder
    private func dayCell(_ day: CalendarViewModel.DayCell) -> some View {
        let isSelected = Calendar.current.isDate(day.date, inSameDayAs: viewModel.selectedDate)

        Button {
            viewModel.selectDate(day.date)
        } label: {
            VStack(spacing: 3) {
                Text(day.dayNumber)
                    .font(.subheadline.weight(isSelected ? .semibold : .regular))
                Circle()
                    .fill(day.hasPlan ? AppColors.blush : .clear)
                    .frame(width: 5, height: 5)
            }
            .foregroundStyle(
                isSelected ? Color.white :
                    (day.isInDisplayedMonth ? AppColors.primaryText : AppColors.secondaryText.opacity(0.45))
            )
            .frame(maxWidth: .infinity)
            .frame(height: 40)
            .background(
                ZStack {
                    if isSelected {
                        Circle().fill(AppColors.blush)
                    } else if day.isToday {
                        Circle().stroke(AppColors.blush.opacity(0.65), lineWidth: 1.5)
                    }
                }
            )
            .contentShape(Circle())
        }
        .buttonStyle(.plain)
    }

    private var dayModeCard: some View {
        PrimaryCard {
            VStack(alignment: .leading, spacing: AppSpacing.sm) {
                Text(viewModel.selectedDate.formatted(.dateTime.weekday(.wide)))
                    .font(.caption.weight(.medium))
                    .foregroundStyle(AppColors.secondaryText)
                Text(viewModel.selectedDate.formatted(.dateTime.day().month(.wide).year()))
                    .font(AppTypography.section)
                    .foregroundStyle(AppColors.primaryText)

                Divider()
                    .overlay(AppColors.neutralChip)

                if viewModel.plansForSelectedDate.isEmpty {
                    Text("No plans")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.secondaryText)
                } else {
                    ForEach(viewModel.plansForSelectedDate) { plan in
                        VStack(alignment: .leading, spacing: 2) {
                            Text(plan.title).font(AppTypography.cardTitle)
                            Text(plan.date.formatted(date: .omitted, time: .shortened)).font(AppTypography.caption)
                            Text(plan.location).font(AppTypography.caption).foregroundStyle(AppColors.secondaryText)
                        }
                        .padding(.vertical, 2)
                    }
                }
            }
        }
    }

    private var weekModeCard: some View {
        PrimaryCard {
            VStack(alignment: .leading, spacing: AppSpacing.sm) {
                Text(viewModel.selectedDate.formatted(.dateTime.month(.wide).year()))
                    .font(AppTypography.section)
                    .foregroundStyle(AppColors.primaryText)

                HStack(spacing: AppSpacing.xs) {
                    ForEach(viewModel.weekDays) { day in
                        weekDayCell(day)
                    }
                }

                Divider()
                    .overlay(AppColors.neutralChip)

                Text(viewModel.selectedDate.formatted(.dateTime.weekday(.wide).day().month(.abbreviated)))
                    .font(AppTypography.caption)
                    .foregroundStyle(AppColors.secondaryText)

                if viewModel.plansForSelectedDate.isEmpty {
                    Text("No plans")
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.secondaryText)
                } else {
                    ForEach(viewModel.plansForSelectedDate) { plan in
                        VStack(alignment: .leading, spacing: 2) {
                            Text(plan.title).font(AppTypography.cardTitle)
                            Text(plan.date.formatted(date: .omitted, time: .shortened)).font(AppTypography.caption)
                            Text(plan.location).font(AppTypography.caption).foregroundStyle(AppColors.secondaryText)
                        }
                        .padding(.vertical, 2)
                    }
                }
            }
        }
    }

    private var monthModeCard: some View {
        PrimaryCard {
            VStack(spacing: AppSpacing.md) {
                HStack {
                    Button {
                        viewModel.showPreviousMonth()
                    } label: {
                        Image(systemName: "chevron.left")
                            .font(.headline.weight(.semibold))
                            .foregroundStyle(AppColors.secondaryText)
                            .frame(width: 30, height: 30)
                            .background(AppColors.neutralChip.opacity(0.7), in: Circle())
                    }
                    .buttonStyle(.plain)

                    Spacer()
                    Text(viewModel.monthTitle)
                        .font(AppTypography.section)
                        .foregroundStyle(AppColors.primaryText)
                    Spacer()

                    Button {
                        viewModel.showNextMonth()
                    } label: {
                        Image(systemName: "chevron.right")
                            .font(.headline.weight(.semibold))
                            .foregroundStyle(AppColors.secondaryText)
                            .frame(width: 30, height: 30)
                            .background(AppColors.neutralChip.opacity(0.7), in: Circle())
                    }
                    .buttonStyle(.plain)
                }

                LazyVGrid(columns: columns, spacing: AppSpacing.sm) {
                    ForEach(viewModel.weekdaySymbols, id: \.self) { symbol in
                        Text(symbol)
                            .font(.caption2.weight(.semibold))
                            .foregroundStyle(AppColors.secondaryText)
                            .frame(maxWidth: .infinity)
                    }
                }

                LazyVGrid(columns: columns, spacing: AppSpacing.sm) {
                    ForEach(viewModel.monthGrid) { day in
                        dayCell(day)
                    }
                }
            }
        }
    }

    @ViewBuilder
    private func weekDayCell(_ day: CalendarViewModel.WeekDay) -> some View {
        let isSelected = Calendar.current.isDate(day.date, inSameDayAs: viewModel.selectedDate)

        Button {
            viewModel.selectDate(day.date)
        } label: {
            VStack(spacing: 4) {
                Text(day.date.formatted(.dateTime.weekday(.narrow)))
                    .font(.caption2.weight(.semibold))
                Text(day.dayNumber)
                    .font(.subheadline.weight(.semibold))
                Circle()
                    .fill(day.hasPlan ? AppColors.blush : .clear)
                    .frame(width: 5, height: 5)
            }
            .foregroundStyle(isSelected ? Color.white : AppColors.primaryText)
            .frame(maxWidth: .infinity)
            .padding(.vertical, 8)
            .background(
                RoundedRectangle(cornerRadius: 12, style: .continuous)
                    .fill(isSelected ? AppColors.blush : AppColors.neutralChip.opacity(day.isToday ? 0.95 : 0.6))
            )
        }
        .buttonStyle(.plain)
    }
}

#Preview {
    CalendarView()
        .environmentObject(AuthManager())
}
