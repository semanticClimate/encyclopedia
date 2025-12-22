"""
Main test runner for text links analysis
Execute all tests and generate reports
"""

import sys
from pathlib import Path
from test.text_links.test_utilities import TextLinksTestRunner, TextLinksReportGenerator
from test.text_links.test_config import OUTPUT_DIR

def main():
    """Main test execution function"""
    print("Starting Text Links Analysis Tests...")
    print(f"Output directory: {OUTPUT_DIR}")
    
    # Initialize test runner
    runner = TextLinksTestRunner()
    
    # Run all tests
    runner.run_all_tests()
    
    # Generate reports
    report_generator = TextLinksReportGenerator(OUTPUT_DIR)
    report_file = report_generator.generate_markdown_report()
    
    print(f"\nTest report generated: {report_file}")
    print("Text Links Analysis Tests completed!")

if __name__ == "__main__":
    main()
