import SwiftUI

struct AddEventView: View {
    @Binding var isPresented: Bool
    @State private var eventName = ""
    @State private var selectedCategory: EventCategory = .dinner
    @State private var displayedMonth: Date = Date()
    @State private var selectedDate: Date = Date()
    @State private var startTime: Date = Date()
    @State private var endTime: Date = Date().addingTimeInterval(2 * 60 * 60)
    @State private var location = ""
    @State private var notes = ""
    @State private var activePicker: TimeField?

    private let calendar = Calendar.current
    private let columns = Array(repeating: GridItem(.flexible(), spacing: AppSpacing.xs), count: 7)

    enum TimeField {
        case start
        case end

        var title: String {
            switch self {
            case .start: return "Start Time"
            case .end: return "End Time"
            }
        }
    }

    enum EventCategory: String, CaseIterable, Identifiable {
        case dinner
        case drinks
        case outdoor
        case picnic

        var id: String { rawValue }
        var label: String {
            switch self {
            case .dinner: return "Dinner"
            case .drinks: return "Drinks"
            case .outdoor: return "Outdoor"
            case .picnic: return "Picnic"
            }
        }
        var emoji: String {
            switch self {
            case .dinner: return "🍽"
            case .drinks: return "🍷"
            case .outdoor: return "🌿"
            case .picnic: return "🧺"
            }
        }
    }

    var body: some View {
        NavigationStack {
            ScrollView {
                VStack(alignment: .leading, spacing: AppSpacing.lg) {
                    Text("Add Event")
                        .font(AppTypography.largeTitle)
                        .foregroundStyle(AppColors.primaryText)

                    PrimaryCard {
                        VStack(alignment: .leading, spacing: AppSpacing.sm) {
                            Text("EVENT NAME")
                                .font(.caption.weight(.semibold))
                                .foregroundStyle(AppColors.secondaryText.opacity(0.7))

                            TextField("e.g. Candlelit Dinner...", text: $eventName)
                                .font(.title2.weight(.semibold))
                                .foregroundStyle(AppColors.primaryText)
                                .minimumScaleFactor(0.85)
                                .lineLimit(1)

                            categoryPill(selectedCategory, isCompact: true)
                                .padding(.top, AppSpacing.xs)
                        }
                    }

                    VStack(alignment: .leading, spacing: AppSpacing.sm) {
                        Text("CATEGORY")
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(AppColors.secondaryText.opacity(0.7))
                            .padding(.horizontal, 2)

                        HStack(spacing: AppSpacing.sm) {
                            ForEach(EventCategory.allCases) { category in
                                Button {
                                    selectedCategory = category
                                } label: {
                                    categoryPill(category, isCompact: false)
                                }
                                .buttonStyle(.plain)
                            }
                        }
                    }

                    PrimaryCard {
                        VStack(spacing: AppSpacing.md) {
                            HStack {
                                Button {
                                    shiftMonth(-1)
                                } label: {
                                    Image(systemName: "chevron.left")
                                        .font(.headline.weight(.semibold))
                                        .foregroundStyle(AppColors.secondaryText)
                                        .frame(width: 30, height: 30)
                                        .background(AppColors.neutralChip.opacity(0.65), in: Circle())
                                }
                                .buttonStyle(.plain)

                                Spacer()
                                Text(displayedMonth.formatted(.dateTime.month(.wide).year()))
                                    .font(AppTypography.section)
                                    .foregroundStyle(AppColors.primaryText)
                                Spacer()

                                Button {
                                    shiftMonth(1)
                                } label: {
                                    Image(systemName: "chevron.right")
                                        .font(.headline.weight(.semibold))
                                        .foregroundStyle(AppColors.secondaryText)
                                        .frame(width: 30, height: 30)
                                        .background(AppColors.neutralChip.opacity(0.65), in: Circle())
                                }
                                .buttonStyle(.plain)
                            }

                            Divider().overlay(AppColors.neutralChip)

                            LazyVGrid(columns: columns, spacing: AppSpacing.sm) {
                                ForEach(weekdaySymbols, id: \.self) { symbol in
                                    Text(symbol)
                                        .font(.subheadline.weight(.semibold))
                                        .foregroundStyle(AppColors.secondaryText.opacity(0.6))
                                        .frame(maxWidth: .infinity)
                                }
                            }

                            LazyVGrid(columns: columns, spacing: AppSpacing.sm) {
                                ForEach(monthDates, id: \.self) { date in
                                    dateCell(date)
                                }
                            }
                        }
                    }

                    VStack(alignment: .leading, spacing: AppSpacing.sm) {
                        Text("TIME")
                            .font(.caption.weight(.semibold))
                            .foregroundStyle(AppColors.secondaryText.opacity(0.7))
                            .padding(.horizontal, 2)

                        HStack(spacing: AppSpacing.md) {
                            timeCard(title: "STARTS", time: $startTime, field: .start)
                            timeCard(title: "ENDS", time: $endTime, field: .end)
                        }
                    }

                    PrimaryCard {
                        HStack(spacing: AppSpacing.sm) {
                            Image(systemName: "mappin.and.ellipse")
                                .foregroundStyle(AppColors.secondaryText.opacity(0.5))
                            TextField("Add location (optional)", text: $location)
                                .font(.title3.weight(.medium))
                                .foregroundStyle(AppColors.primaryText)
                        }
                    }

                    PrimaryCard {
                        HStack(alignment: .top, spacing: AppSpacing.sm) {
                            Image(systemName: "document.text")
                                .foregroundStyle(AppColors.secondaryText.opacity(0.5))
                                .padding(.top, 5)
                            TextField("Notes, ideas, reminders... (optional)", text: $notes, axis: .vertical)
                                .font(.title3.weight(.medium))
                                .foregroundStyle(AppColors.primaryText)
                                .lineLimit(3...6)
                        }
                    }
                }
                .padding(.bottom, AppSpacing.xl)
                .padding(AppSpacing.md)
            }
            .scrollIndicators(.hidden)
            .background(AppColors.neutralChip.opacity(0.35))
            .ignoresSafeArea(edges: .bottom)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Close") {
                        isPresented = false
                    }
                }
            }
        }
        .sheet(item: $activePicker) { field in
            TimePickerSheet(
                title: field.title,
                selection: field == .start ? $startTime : $endTime
            )
            .presentationDetents([.medium])
        }
    }

    private var weekdaySymbols: [String] {
        let base = calendar.shortWeekdaySymbols
        let first = calendar.firstWeekday - 1
        return Array(base[first...] + base[..<first])
    }

    private var monthDates: [Date] {
        guard
            let monthInterval = calendar.dateInterval(of: .month, for: displayedMonth),
            let firstWeekInterval = calendar.dateInterval(of: .weekOfMonth, for: monthInterval.start),
            let lastWeekInterval = calendar.dateInterval(of: .weekOfMonth, for: monthInterval.end.addingTimeInterval(-1))
        else { return [] }

        var dates: [Date] = []
        var current = firstWeekInterval.start
        while current < lastWeekInterval.end {
            dates.append(current)
            guard let next = calendar.date(byAdding: .day, value: 1, to: current) else { break }
            current = next
        }
        return dates
    }

    private func shiftMonth(_ offset: Int) {
        guard let next = calendar.date(byAdding: .month, value: offset, to: displayedMonth) else { return }
        displayedMonth = next
    }

    @ViewBuilder
    private func dateCell(_ date: Date) -> some View {
        let inMonth = calendar.isDate(date, equalTo: displayedMonth, toGranularity: .month)
        let isSelected = calendar.isDate(date, inSameDayAs: selectedDate)

        Button {
            selectedDate = date
        } label: {
            Text("\(calendar.component(.day, from: date))")
                .font(.system(size: 20, weight: isSelected ? .semibold : .regular))
                .foregroundStyle(
                    isSelected ? AppColors.blush :
                        (inMonth ? AppColors.primaryText : AppColors.secondaryText.opacity(0.4))
                )
                .frame(maxWidth: .infinity)
                .frame(height: 44)
                .background(
                    Group {
                        if isSelected {
                            Circle()
                                .stroke(AppColors.blush.opacity(0.75), lineWidth: 2)
                        }
                    }
                )
        }
        .buttonStyle(.plain)
    }

    @ViewBuilder
    private func categoryPill(_ category: EventCategory, isCompact: Bool) -> some View {
        let selected = selectedCategory == category

        HStack(spacing: 8) {
            Text(category.emoji)
            Text(category.label)
                .font(isCompact ? .subheadline.weight(.semibold) : .body.weight(.semibold))
        }
        .foregroundStyle(selected ? AppColors.blush : AppColors.secondaryText)
        .padding(.vertical, isCompact ? 8 : 10)
        .padding(.horizontal, isCompact ? 14 : 16)
        .background(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .fill(selected ? AppColors.blush.opacity(0.18) : Color.white.opacity(0.85))
        )
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(selected ? AppColors.blush.opacity(0.35) : Color.clear, lineWidth: 1.5)
        )
    }

    @ViewBuilder
    private func timeCard(title: String, time: Binding<Date>, field: TimeField) -> some View {
        Button {
            activePicker = field
        } label: {
            PrimaryCard {
                VStack(alignment: .leading, spacing: AppSpacing.sm) {
                Text(title)
                    .font(.caption.weight(.semibold))
                    .foregroundStyle(AppColors.secondaryText.opacity(0.7))

                    HStack(alignment: .bottom) {
                        VStack(alignment: .leading, spacing: 0) {
                            Text(time.wrappedValue.formatted(date: .omitted, time: .shortened).replacingOccurrences(of: " AM", with: "").replacingOccurrences(of: " PM", with: ""))
                                .font(.system(size: 50, weight: .semibold, design: .rounded))
                                .foregroundStyle(AppColors.primaryText)
                                .minimumScaleFactor(0.7)
                                .lineLimit(1)
                            Text(time.wrappedValue.formatted(.dateTime.hour(.defaultDigits(amPM: .abbreviated)).minute()).contains("PM") ? "PM" : "AM")
                                .font(.system(size: 30, weight: .semibold, design: .rounded))
                                .foregroundStyle(AppColors.primaryText)
                        }
                        Spacer(minLength: 6)
                        Image(systemName: "chevron.down")
                            .font(.title3.weight(.semibold))
                            .foregroundStyle(AppColors.secondaryText.opacity(0.9))
                            .padding(.bottom, 14)
                    }
                }
                .frame(maxWidth: .infinity, alignment: .leading)
            }
            .frame(maxWidth: .infinity)
            .frame(minHeight: 172)
        }
        .buttonStyle(.plain)
    }
}

extension AddEventView.TimeField: Identifiable {
    var id: String {
        switch self {
        case .start: return "start"
        case .end: return "end"
        }
    }
}

private struct TimePickerSheet: View {
    let title: String
    @Binding var selection: Date
    @Environment(\.dismiss) private var dismiss

    var body: some View {
        NavigationStack {
            VStack(spacing: AppSpacing.md) {
                DatePicker(
                    "",
                    selection: $selection,
                    displayedComponents: .hourAndMinute
                )
                .datePickerStyle(.wheel)
                .labelsHidden()
            }
            .padding(.top, AppSpacing.md)
            .navigationTitle(title)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("Done") { dismiss() }
                }
            }
        }
    }
}

#Preview {
    AddEventView(isPresented: .constant(true))
}
