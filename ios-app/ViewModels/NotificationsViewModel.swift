import Foundation
import Combine

@MainActor
final class NotificationsViewModel: ObservableObject {
    @Published private(set) var items: [NotificationFeedItem] = []
    @Published private(set) var isLoading = false
    @Published private(set) var errorMessage: String?

    var unreadCount: Int {
        items.filter { $0.source == .inbox && !$0.isRead }.count
    }

    func load(authManager: AuthManager) async {
        isLoading = true
        errorMessage = nil
        defer { isLoading = false }

        do {
            async let inboxTask: PaginatedResponse<NotificationInboxDTO> = authManager.fetchInboxNotifications()
            async let remindersTask: PaginatedResponse<EventReminderRuleDTO> = authManager.fetchReminderRules()

            let inboxPage = try await inboxTask
            let reminderPage = try await remindersTask

            let inboxItems = inboxPage.results.map { dto in
                NotificationFeedItem(
                    id: "inbox-\(dto.id)",
                    source: .inbox,
                    inboxId: dto.id,
                    title: dto.title,
                    body: dto.body,
                    timeAgo: Self.relativeTimeLabel(from: dto.createdAt),
                    tag: Self.tagForInboxType(dto.type),
                    type: dto.type,
                    inviteId: dto.data?.inviteId,
                    inviteAction: dto.data?.action,
                    isRead: dto.readAt != nil
                )
            }

            let reminderItems = reminderPage.results.map { dto in
                let eventName = dto.eventName?.trimmingCharacters(in: .whitespacesAndNewlines)
                let title = (eventName?.isEmpty == false ? eventName : "Event") ?? "Event"
                let body = "Rule: \(dto.offsetMinutes)m before event via \(dto.channel)."
                return NotificationFeedItem(
                    id: "rule-\(dto.id)",
                    source: .reminderRule,
                    inboxId: nil,
                    title: title,
                    body: body,
                    timeAgo: "Rule",
                    tag: "REMINDER RULE",
                    type: "event_reminder_rule",
                    inviteId: nil,
                    inviteAction: nil,
                    isRead: true
                )
            }

            items = inboxItems + reminderItems
        } catch {
            errorMessage = error.localizedDescription
            items = []
        }
    }

    func markAllRead(authManager: AuthManager) async {
        do {
            _ = try await authManager.markAllNotificationsRead()
            items = items.map { item in
                guard item.source == .inbox else { return item }
                var updated = item
                updated.isRead = true
                return updated
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func markRead(item: NotificationFeedItem, authManager: AuthManager) async {
        guard item.source == .inbox, let inboxId = item.inboxId, !item.isRead else {
            return
        }

        do {
            _ = try await authManager.markNotificationRead(notificationId: inboxId)
            items = items.map { current in
                guard current.id == item.id else { return current }
                var updated = current
                updated.isRead = true
                return updated
            }
        } catch {
            errorMessage = error.localizedDescription
        }
    }

    func acceptInvite(item: NotificationFeedItem, authManager: AuthManager) async {
        guard item.canRespondToInvite, let inviteId = item.inviteId else { return }
        let accepted = await authManager.acceptInvite(inviteId: inviteId)
        if accepted {
            await load(authManager: authManager)
        } else if let message = authManager.errorMessage {
            errorMessage = message
        }
    }

    func declineInvite(item: NotificationFeedItem, authManager: AuthManager) async {
        guard item.canRespondToInvite, let inviteId = item.inviteId else { return }
        let declined = await authManager.declineInvite(inviteId: inviteId)
        if declined {
            await load(authManager: authManager)
        } else if let message = authManager.errorMessage {
            errorMessage = message
        }
    }

    private static func tagForInboxType(_ type: String) -> String {
        switch type {
        case "invite":
            return "INVITE"
        case "event_updated":
            return "EVENT"
        default:
            return "REMINDER"
        }
    }

    private static func relativeTimeLabel(from isoString: String) -> String {
        guard let date = parseISODate(isoString) else {
            return "Now"
        }
        let formatter = RelativeDateTimeFormatter()
        formatter.unitsStyle = .abbreviated
        return formatter.localizedString(for: date, relativeTo: Date())
    }

    private static func parseISODate(_ value: String) -> Date? {
        let withFractional = ISO8601DateFormatter()
        withFractional.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = withFractional.date(from: value) {
            return date
        }

        let basic = ISO8601DateFormatter()
        basic.formatOptions = [.withInternetDateTime]
        return basic.date(from: value)
    }
}
