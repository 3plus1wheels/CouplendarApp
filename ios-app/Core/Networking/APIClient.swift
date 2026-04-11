import Foundation

final class APIClient {
    static let shared = APIClient()

    let baseURL: URL

    init(baseURL: URL = URL(string: "http://127.0.0.1:8000/api")!) {
        self.baseURL = baseURL
    }

    func request<Response: Decodable, Body: Encodable>(
        _ endpoint: Endpoint,
        method: HTTPMethod,
        body: Body? = nil,
        accessToken: String? = nil
    ) async throws -> Response {
        guard let url = URL(string: endpoint.path, relativeTo: baseURL) else {
            throw APIError.invalidURL
        }

        var request = URLRequest(url: url)
        request.httpMethod = method.rawValue
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        if let accessToken {
            request.setValue("Bearer \(accessToken)", forHTTPHeaderField: "Authorization")
        }

        if let body {
            request.httpBody = try JSONEncoder().encode(body)
        }

        do {
            let (data, response) = try await URLSession.shared.data(for: request)
            guard let httpResponse = response as? HTTPURLResponse else {
                throw APIError.transport("Invalid server response")
            }

            if httpResponse.statusCode == 401 {
                throw APIError.unauthorized
            }

            guard (200...299).contains(httpResponse.statusCode) else {
                let message = String(data: data, encoding: .utf8)
                throw APIError.server(statusCode: httpResponse.statusCode, message: message)
            }

            do {
                return try JSONDecoder().decode(Response.self, from: data)
            } catch {
                throw APIError.decoding
            }
        } catch let apiError as APIError {
            throw apiError
        } catch {
            throw APIError.transport(error.localizedDescription)
        }
    }

    func request<Response: Decodable>(
        _ endpoint: Endpoint,
        method: HTTPMethod,
        accessToken: String? = nil
    ) async throws -> Response {
        try await request(endpoint, method: method, body: Optional<String>.none, accessToken: accessToken)
    }
}
