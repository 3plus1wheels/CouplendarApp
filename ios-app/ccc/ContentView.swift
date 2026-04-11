import SwiftUI

struct ContentView: View {
    var body: some View {
        AuthGateView()
    }
}

#Preview {
    ContentView()
        .environmentObject(AuthManager())
}
