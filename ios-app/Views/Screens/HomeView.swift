import SwiftUI

struct HomeView: View {
    @EnvironmentObject private var authManager: AuthManager
    @StateObject private var viewModel = HomeViewModel()
    @State private var showProfile = false
    @State private var showNotifications = false
    @State private var plannerPrompt = ""
    @State private var showPlannerChat = false
    @FocusState private var isPlannerPromptFocused: Bool

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: AppSpacing.lg) {
                header
                upcomingSection
                plannerComposerSection
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
        .fullScreenCover(isPresented: $showPlannerChat) {
            PlannerChatView(
                isPresented: $showPlannerChat,
                initialPrompt: plannerPrompt
            )
            .environmentObject(authManager)
        }
        .task {
            await viewModel.loadEvents(authManager: authManager)
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

    private func upcomingPlanCard(_ plan: Plan) -> some View {
        PrimaryCard {
            VStack(alignment: .leading, spacing: AppSpacing.sm) {
                Text(plan.title).font(AppTypography.title).foregroundStyle(AppColors.primaryText)
                Text(plan.date.formatted(date: .abbreviated, time: .shortened))
                    .font(AppTypography.body)
                    .foregroundStyle(AppColors.secondaryText)
                ChipView(title: plan.vibe, isActive: true, variant: .blush)
                if !plan.location.isEmpty {
                    Text(plan.location)
                        .font(AppTypography.caption)
                        .foregroundStyle(AppColors.secondaryText)
                }
            }
            .frame(width: 248, alignment: .leading)
        }
    }

    private var upcomingSection: some View {
        VStack(alignment: .leading, spacing: AppSpacing.sm) {
            SectionHeader(title: "Upcoming plans", subtitle: "A few things to look forward to")
            if viewModel.upcomingPlans.isEmpty {
                PrimaryCard {
                    Text("No upcoming plans yet")
                        .font(AppTypography.body)
                        .foregroundStyle(AppColors.secondaryText)
                }
            } else {
                ScrollView(.horizontal, showsIndicators: false) {
                    HStack(spacing: AppSpacing.sm) {
                        ForEach(viewModel.upcomingPlans) { plan in
                            upcomingPlanCard(plan)
                        }
                    }
                }
            }
        }
    }

    private var plannerComposerSection: some View {
        VStack(alignment: .leading, spacing: AppSpacing.sm) {
            VStack(alignment: .leading, spacing: AppSpacing.md) {
                HStack(alignment: .top, spacing: AppSpacing.sm) {
                    ZStack {
                        Circle()
                            .fill(
                                LinearGradient(
                                    colors: [AppColors.blush.opacity(0.9), AppColors.lavender.opacity(0.85)],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                )
                            )
                        Image(systemName: "sparkles")
                            .font(.system(size: 14, weight: .semibold))
                            .foregroundStyle(.white)
                    }
                    .frame(width: 34, height: 34)

                    TextField("", text: $plannerPrompt, axis: .vertical)
                        .lineLimit(2...4)
                        .font(.system(size: 19, weight: .medium, design: .rounded))
                        .foregroundStyle(AppColors.primaryText)
                        .scrollContentBackground(.hidden)
                        .focused($isPlannerPromptFocused)
                        .overlay(alignment: .topLeading) {
                            if plannerPrompt.isEmpty {
                                Text("Let me help you plan your evening or date...")
                                    .font(.system(size: 18, weight: .medium, design: .rounded))
                                    .foregroundStyle(AppColors.secondaryText.opacity(0.8))
                                    .lineLimit(2)
                                    .fixedSize(horizontal: false, vertical: true)
                                    .allowsHitTesting(false)
                            }
                        }

                    Button(action: submitPlannerPrompt) {
                        Image(systemName: "arrow.up")
                            .font(.system(size: 15, weight: .bold))
                            .foregroundStyle(.white)
                            .frame(width: 34, height: 34)
                            .background(AppColors.primaryText)
                            .clipShape(Circle())
                    }
                    .buttonStyle(.plain)
                }

                HStack(spacing: AppSpacing.xs) {
                    plannerHintChip("Cozy night")
                    plannerHintChip("Dinner date")
                    plannerHintChip("Low effort")
                }
            }
            .padding(AppSpacing.md)
            .background(Color.white)
            .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))
            .shadow(color: AppColors.primaryText.opacity(AppShadows.opacity), radius: AppShadows.radius, x: 0, y: AppShadows.y)
            .scaleEffect(isPlannerPromptFocused ? 1.025 : 1, anchor: .bottom)
            .offset(y: isPlannerPromptFocused ? -72 : 0)
            .shadow(
                color: AppColors.primaryText.opacity(isPlannerPromptFocused ? 0.12 : 0),
                radius: isPlannerPromptFocused ? 18 : 0,
                x: 0,
                y: isPlannerPromptFocused ? 14 : 0
            )
            .zIndex(isPlannerPromptFocused ? 2 : 0)
            .animation(.snappy(duration: 0.32, extraBounce: 0.12), value: isPlannerPromptFocused)
        }
    }

    private func plannerHintChip(_ title: String) -> some View {
        Button {
            plannerPrompt = title
            focusPlannerPrompt()
        } label: {
            Text(title)
                .font(AppTypography.caption.weight(.semibold))
                .foregroundStyle(AppColors.primaryText.opacity(0.85))
                .padding(.horizontal, 12)
                .padding(.vertical, 8)
                .background(
                    Capsule()
                        .fill(.white.opacity(0.75))
                )
                .overlay {
                    Capsule()
                        .stroke(AppColors.neutralChip.opacity(0.85), lineWidth: 1)
                }
        }
        .buttonStyle(.plain)
    }

    private func focusPlannerPrompt() {
        withAnimation(.snappy(duration: 0.32, extraBounce: 0.12)) {
            isPlannerPromptFocused = true
        }
    }

    private func submitPlannerPrompt() {
        guard isPlannerPromptFocused else {
            focusPlannerPrompt()
            return
        }

        isPlannerPromptFocused = false
        openPlannerChat()
    }

    private func openPlannerChat() {
        showPlannerChat = true
    }
}

private struct PlannerChatView: View {
    @EnvironmentObject private var authManager: AuthManager
    @Binding var isPresented: Bool
    @State private var messageText: String
    @State private var messages: [PlannerChatMessage] = [
        PlannerChatMessage(
            role: .assistant,
            text: "I can help with dinner spots, low-effort evenings, cozy at-home plans, or a full date itinerary."
        ),
        PlannerChatMessage(
            role: .assistant,
            text: "Try: \"Plan a relaxed date night after work\""
        ),
    ]
    @State private var isSending = false
    @State private var errorMessage: String?

    init(isPresented: Binding<Bool>, initialPrompt: String) {
        self._isPresented = isPresented
        self._messageText = State(initialValue: initialPrompt)
    }

    var body: some View {
        ZStack {
            GlassBackgroundView()

            VStack(spacing: 0) {
                HStack {
                    Button {
                        isPresented = false
                    } label: {
                        Image(systemName: "arrow.left")
                            .font(.system(size: 17, weight: .semibold))
                            .foregroundStyle(AppColors.primaryText)
                            .frame(width: 38, height: 38)
                            .background(.white.opacity(0.82))
                            .clipShape(Circle())
                    }
                    .buttonStyle(.plain)

                    Spacer()

                    Text("Planner")
                        .font(AppTypography.cardTitle)
                        .foregroundStyle(AppColors.primaryText)

                    Spacer()

                    Color.clear
                        .frame(width: 38, height: 38)
                }
                .padding(.horizontal, AppSpacing.md)
                .padding(.top, AppSpacing.md)

                ScrollView {
                    VStack(alignment: .leading, spacing: AppSpacing.md) {
                        Text("Let’s shape the night")
                            .font(.system(size: 34, weight: .bold, design: .rounded))
                            .foregroundStyle(AppColors.primaryText)

                        Text("Tell me the vibe, budget, energy level, or time window. I’ll turn it into a date plan.")
                            .font(AppTypography.body)
                            .foregroundStyle(AppColors.secondaryText)

                        ForEach(messages) { message in
                            plannerBubble(message)
                        }

                        if isSending {
                            plannerBubble(
                                PlannerChatMessage(role: .assistant, text: "Thinking...")
                            )
                        }

                        if let errorMessage {
                            Text(errorMessage)
                                .font(AppTypography.caption.weight(.semibold))
                                .foregroundStyle(AppColors.blush)
                                .frame(maxWidth: .infinity, alignment: .leading)
                        }
                    }
                    .padding(.horizontal, AppSpacing.md)
                    .padding(.top, AppSpacing.xl)
                    .padding(.bottom, 140)
                }
            }

            VStack {
                Spacer()

                PrimaryCard {
                    HStack(alignment: .bottom, spacing: AppSpacing.sm) {
                        TextField("", text: $messageText, axis: .vertical)
                            .lineLimit(1...4)
                            .font(.system(size: 18, weight: .medium, design: .rounded))
                            .foregroundStyle(AppColors.primaryText)
                            .overlay(alignment: .topLeading) {
                                if messageText.isEmpty {
                                    Text("Message your planner...")
                                        .font(.system(size: 18, weight: .medium, design: .rounded))
                                        .foregroundStyle(AppColors.secondaryText.opacity(0.8))
                                        .allowsHitTesting(false)
                                }
                            }

                        Button {
                            Task {
                                await sendMessage()
                            }
                        } label: {
                            Image(systemName: "arrow.up")
                                .font(.system(size: 15, weight: .bold))
                                .foregroundStyle(.white)
                                .frame(width: 40, height: 40)
                                .background(canSendMessage ? AppColors.primaryText : AppColors.secondaryText.opacity(0.45))
                                .clipShape(Circle())
                        }
                        .buttonStyle(.plain)
                        .disabled(!canSendMessage)
                    }
                }
                .padding(.horizontal, AppSpacing.md)
                .padding(.bottom, AppSpacing.md)
            }
        }
    }

    private var canSendMessage: Bool {
        !messageText.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty && !isSending
    }

    private func sendMessage() async {
        let trimmedMessage = messageText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !trimmedMessage.isEmpty, !isSending else {
            return
        }

        errorMessage = nil
        isSending = true
        messageText = ""
        messages.append(PlannerChatMessage(role: .user, text: trimmedMessage))

        do {
            let response = try await authManager.sendPlannerMessage(trimmedMessage)
            messages.append(PlannerChatMessage(role: .assistant, text: response.reply))
        } catch {
            errorMessage = error.localizedDescription
        }

        isSending = false
    }

    private func plannerBubble(_ message: PlannerChatMessage) -> some View {
        HStack {
            if message.role == .user {
                Spacer(minLength: 48)
            }

            Text(message.text)
                .font(AppTypography.body)
                .foregroundStyle(message.role == .user ? .white : AppColors.primaryText)
                .padding(AppSpacing.md)
                .background {
                    if message.role == .user {
                        RoundedRectangle(cornerRadius: 22, style: .continuous)
                            .fill(AppColors.primaryText)
                    } else {
                        LinearGradient(
                            colors: [AppColors.glass, AppColors.surface],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    }
                }
                .clipShape(RoundedRectangle(cornerRadius: 22, style: .continuous))

            if message.role == .assistant {
                Spacer(minLength: 48)
            }
        }
    }
}

private struct NotificationsSheetView: View {
    @EnvironmentObject private var authManager: AuthManager
    @Binding var isPresented: Bool
    @StateObject private var viewModel = NotificationsViewModel()
    @State private var processingInviteIds: Set<Int> = []

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
                            NotificationCard(
                                item: item,
                                onAcceptInvite: item.canRespondToInvite ? {
                                    guard let inviteId = item.inviteId else { return }
                                    processingInviteIds.insert(inviteId)
                                    Task {
                                        await viewModel.acceptInvite(item: item, authManager: authManager)
                                        processingInviteIds.remove(inviteId)
                                    }
                                } : nil,
                                onDeclineInvite: item.canRespondToInvite ? {
                                    guard let inviteId = item.inviteId else { return }
                                    processingInviteIds.insert(inviteId)
                                    Task {
                                        await viewModel.declineInvite(item: item, authManager: authManager)
                                        processingInviteIds.remove(inviteId)
                                    }
                                } : nil,
                                isInviteActionLoading: item.inviteId.map { processingInviteIds.contains($0) } ?? false
                            )
                            .contentShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
                            .onTapGesture {
                                guard !item.canRespondToInvite else { return }
                                Task {
                                    await viewModel.markRead(item: item, authManager: authManager)
                                }
                            }
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
    let onAcceptInvite: (() -> Void)?
    let onDeclineInvite: (() -> Void)?
    let isInviteActionLoading: Bool

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

                if item.canRespondToInvite {
                    HStack {
                        Spacer()
                        HStack(spacing: AppSpacing.xs) {
                            Button {
                                onDeclineInvite?()
                            } label: {
                                Image(systemName: "xmark")
                                    .font(.system(size: 12, weight: .bold))
                                    .foregroundStyle(.white)
                                    .frame(width: 30, height: 30)
                                    .background(AppColors.blush)
                                    .clipShape(Circle())
                            }
                            .buttonStyle(.plain)
                            .disabled(isInviteActionLoading)
                            .opacity(isInviteActionLoading ? 0.55 : 1)

                            Button {
                                onAcceptInvite?()
                            } label: {
                                Image(systemName: "checkmark")
                                    .font(.system(size: 12, weight: .bold))
                                    .foregroundStyle(.white)
                                    .frame(width: 30, height: 30)
                                    .background(AppColors.mint)
                                    .clipShape(Circle())
                            }
                            .buttonStyle(.plain)
                            .disabled(isInviteActionLoading)
                            .opacity(isInviteActionLoading ? 0.55 : 1)
                        }
                    }
                }
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
