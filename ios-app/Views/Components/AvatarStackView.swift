import SwiftUI

struct AvatarStackView: View {
    let first: String
    let second: String

    var body: some View {
        HStack(spacing: -8) {
            avatar(initials: first)
            avatar(initials: second)
        }
    }

    private func avatar(initials: String) -> some View {
        Text(initials)
            .font(.caption.weight(.semibold))
            .foregroundStyle(.white)
            .frame(width: 34, height: 34)
            .background(AppColors.blush)
            .clipShape(Circle())
            .overlay(Circle().stroke(.white, lineWidth: 2))
    }
}
