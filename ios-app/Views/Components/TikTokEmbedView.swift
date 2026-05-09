import SwiftUI
import WebKit

struct TikTokEmbedView: UIViewRepresentable {
    let videoId: String

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.allowsInlineMediaPlayback = true
        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.isOpaque = false
        webView.backgroundColor = .clear
        webView.scrollView.isScrollEnabled = false
        return webView
    }

    func updateUIView(_ webView: WKWebView, context: Context) {
        let html = Self.embedHTML(videoId: videoId)
        webView.loadHTMLString(html, baseURL: URL(string: "https://www.tiktok.com"))
    }

    private static func embedHTML(videoId: String) -> String {
        return """
        <!doctype html>
        <html>
          <head>
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
            <style>
              body { margin: 0; padding: 0; background: transparent; }
              blockquote { margin: 0; }
            </style>
          </head>
          <body>
            <blockquote class=\"tiktok-embed\" cite=\"https://www.tiktok.com/v/\(videoId)\" data-video-id=\"\(videoId)\" style=\"max-width: 100%;\">
              <section></section>
            </blockquote>
            <script async src=\"https://www.tiktok.com/embed.js\"></script>
          </body>
        </html>
        """
    }
}
