import SwiftUI
import WebKit

struct YouTubeEmbedView: UIViewRepresentable {
    let videoId: String
    var isShort: Bool = false

    func makeUIView(context: Context) -> WKWebView {
        let configuration = WKWebViewConfiguration()
        configuration.allowsInlineMediaPlayback = true
        let webView = WKWebView(frame: .zero, configuration: configuration)
        webView.isOpaque = false
        webView.backgroundColor = .clear
        webView.scrollView.isScrollEnabled = false
        return webView
    }

    private static func embedHTML(videoId: String, isShort: Bool) -> String {
        let embedURL = "https://www.youtube.com/embed/\(videoId)?playsinline=1&rel=0"
        let bodyStyle = isShort ? "padding-top: 177.78%;" : "padding-top: 56.25%;"
        return """
        <!doctype html>
        <html>
          <head>
            <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
            <style>
              body { margin: 0; padding: 0; background: transparent; }
              .frame { position: relative; width: 100%; \(bodyStyle) overflow: hidden; border-radius: 16px; }
              iframe { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; }
            </style>
          </head>
          <body>
            <div class=\"frame\">
              <iframe
                src=\"\(embedURL)\"
                title=\"YouTube video player\"
                allow=\"accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share\"
                allowfullscreen>
              </iframe>
            </div>
          </body>
        </html>
        """
    }

    func updateUIView(_ webView: WKWebView, context: Context) {
        let html = Self.embedHTML(videoId: videoId, isShort: isShort)
        webView.loadHTMLString(html, baseURL: URL(string: "https://www.youtube.com"))
    }
}
