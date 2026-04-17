import XCTest

final class cccUITests: XCTestCase {
    override func setUpWithError() throws {
        continueAfterFailure = false
    }

    @MainActor
    func testRootTabsSmoke() throws {
        let app = XCUIApplication()
        app.launch()

        XCTAssertTrue(app.tabBars.buttons["Home"].waitForExistence(timeout: 3))
        XCTAssertTrue(app.tabBars.buttons["Calendar"].exists)
        XCTAssertTrue(app.tabBars.buttons["Explore"].exists)
        XCTAssertTrue(app.buttons["open_profile_button"].exists)
    }
}
