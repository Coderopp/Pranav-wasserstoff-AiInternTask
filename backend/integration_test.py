#!/usr/bin/env python3
"""
Comprehensive Integration Test Script
Tests all API endpoints and HTTP methods to identify potential 405 Method Not Allowed errors
"""

import requests
import json
import time
from typing import Dict, List, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IntegrationTester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
        
    def test_endpoint(self, method: str, endpoint: str, data: Dict = None, 
                     expected_status: List[int] = None, description: str = "") -> Dict[str, Any]:
        """Test a single endpoint with specified HTTP method"""
        if expected_status is None:
            expected_status = [200, 201, 202]
            
        url = f"{self.base_url}{endpoint}"
        result = {
            "method": method,
            "endpoint": endpoint,
            "url": url,
            "description": description,
            "status": "UNKNOWN",
            "response_code": None,
            "error": None,
            "response_time": None
        }
        
        try:
            start_time = time.time()
            
            if method.upper() == "GET":
                response = self.session.get(url)
            elif method.upper() == "POST":
                response = self.session.post(url, json=data)
            elif method.upper() == "PUT":
                response = self.session.put(url, json=data)
            elif method.upper() == "DELETE":
                response = self.session.delete(url)
            elif method.upper() == "HEAD":
                response = self.session.head(url)
            elif method.upper() == "PATCH":
                response = self.session.patch(url, json=data)
            elif method.upper() == "OPTIONS":
                response = self.session.options(url)
            else:
                result["error"] = f"Unsupported HTTP method: {method}"
                result["status"] = "ERROR"
                return result
                
            end_time = time.time()
            result["response_time"] = round((end_time - start_time) * 1000, 2)
            result["response_code"] = response.status_code
            
            if response.status_code in expected_status:
                result["status"] = "PASS"
            elif response.status_code == 405:
                result["status"] = "METHOD_NOT_ALLOWED"
                result["error"] = "HTTP 405 Method Not Allowed"
            elif response.status_code == 404:
                result["status"] = "NOT_FOUND"
                result["error"] = "HTTP 404 Not Found"
            else:
                result["status"] = "FAIL"
                result["error"] = f"HTTP {response.status_code}: {response.text[:200]}"
                
        except requests.exceptions.ConnectionError:
            result["status"] = "CONNECTION_ERROR"
            result["error"] = "Could not connect to server"
        except Exception as e:
            result["status"] = "ERROR"
            result["error"] = str(e)
            
        self.results.append(result)
        return result
    
    def run_comprehensive_tests(self):
        """Run comprehensive tests on all endpoints with various HTTP methods"""
        logger.info("Starting comprehensive integration tests...")
        
        # Test health check endpoints with all HTTP methods
        health_endpoints = [
            ("/api/health-check", "Simple health check"),
            ("/api/health", "Detailed health check"),
            ("/health", "Root health check (if exists)")
        ]
        
        for endpoint, description in health_endpoints:
            # Test common HTTP methods
            self.test_endpoint("GET", endpoint, description=f"{description} - GET")
            self.test_endpoint("HEAD", endpoint, description=f"{description} - HEAD")
            self.test_endpoint("POST", endpoint, description=f"{description} - POST", expected_status=[405])
            self.test_endpoint("OPTIONS", endpoint, description=f"{description} - OPTIONS")
        
        # Test document endpoints
        document_endpoints = [
            ("/api/documents", "List documents"),
            ("/api/documents/upload", "Upload document"),
            ("/api/documents/list", "List all documents"),
        ]
        
        for endpoint, description in document_endpoints:
            if "upload" in endpoint:
                # Upload endpoint should support POST
                self.test_endpoint("POST", endpoint, data={"test": "data"}, 
                                 expected_status=[200, 201, 400, 422], description=f"{description} - POST")
                self.test_endpoint("GET", endpoint, expected_status=[405], description=f"{description} - GET")
            elif "list" in endpoint:
                # List endpoints should support GET
                self.test_endpoint("GET", endpoint, description=f"{description} - GET")
                self.test_endpoint("POST", endpoint, expected_status=[405], description=f"{description} - POST")
            else:
                # Generic document endpoint
                self.test_endpoint("GET", endpoint, description=f"{description} - GET")
                self.test_endpoint("POST", endpoint, expected_status=[405], description=f"{description} - POST")
        
        # Test query endpoints
        query_endpoints = [
            ("/api/query", "Query documents"),
            ("/api/search", "Search documents"),
        ]
        
        for endpoint, description in query_endpoints:
            # Query endpoints should support POST for query data
            self.test_endpoint("POST", endpoint, data={"query": "test query"}, 
                             expected_status=[200, 201, 400, 422], description=f"{description} - POST")
            self.test_endpoint("GET", endpoint, expected_status=[405], description=f"{description} - GET")
        
        # Test specific document endpoints
        test_doc_id = "test-document-id"
        specific_endpoints = [
            (f"/api/documents/{test_doc_id}", "Get specific document"),
            (f"/api/documents/{test_doc_id}/chunks", "Get document chunks"),
            (f"/api/documents/{test_doc_id}/metadata", "Get document metadata"),
        ]
        
        for endpoint, description in specific_endpoints:
            self.test_endpoint("GET", endpoint, expected_status=[200, 404], description=f"{description} - GET")
            self.test_endpoint("DELETE", endpoint, expected_status=[200, 404, 405], description=f"{description} - DELETE")
            self.test_endpoint("PUT", endpoint, data={"test": "data"}, 
                             expected_status=[200, 404, 405, 422], description=f"{description} - PUT")
        
        # Test CORS preflight requests
        cors_endpoints = ["/api/health-check", "/api/documents", "/api/query"]
        for endpoint in cors_endpoints:
            self.test_endpoint("OPTIONS", endpoint, description=f"CORS preflight - {endpoint}")
    
    def generate_report(self) -> str:
        """Generate a comprehensive test report"""
        total_tests = len(self.results)
        passed = len([r for r in self.results if r["status"] == "PASS"])
        method_not_allowed = len([r for r in self.results if r["status"] == "METHOD_NOT_ALLOWED"])
        failed = len([r for r in self.results if r["status"] in ["FAIL", "ERROR", "CONNECTION_ERROR"]])
        not_found = len([r for r in self.results if r["status"] == "NOT_FOUND"])
        
        report = f"""
=== INTEGRATION TEST REPORT ===
Total Tests: {total_tests}
Passed: {passed}
Method Not Allowed (405): {method_not_allowed}
Not Found (404): {not_found}
Failed/Error: {failed}

=== DETAILED RESULTS ===
"""
        
        # Group results by status
        for status in ["PASS", "METHOD_NOT_ALLOWED", "NOT_FOUND", "FAIL", "ERROR", "CONNECTION_ERROR"]:
            status_results = [r for r in self.results if r["status"] == status]
            if status_results:
                report += f"\n{status} ({len(status_results)} tests):\n"
                for result in status_results:
                    report += f"  {result['method']} {result['endpoint']} - {result['description']}\n"
                    report += f"    Status: {result['response_code']} | Time: {result['response_time']}ms\n"
                    if result['error']:
                        report += f"    Error: {result['error']}\n"
                    report += "\n"
        
        # Recommendations
        report += "\n=== RECOMMENDATIONS ===\n"
        
        if method_not_allowed > 0:
            report += "⚠️  HTTP 405 Method Not Allowed errors detected!\n"
            report += "   - Review endpoint HTTP method configurations\n"
            report += "   - Add missing HTTP method decorators (@app.get, @app.post, @app.head, etc.)\n"
            report += "   - Consider adding CORS middleware if needed\n\n"
        
        if failed > 0:
            report += "❌ Failed tests detected!\n"
            report += "   - Check server logs for detailed error information\n"
            report += "   - Verify endpoint implementations\n"
            report += "   - Check request/response data formats\n\n"
        
        if not_found > 0:
            report += "🔍 Not Found (404) errors detected!\n"
            report += "   - Verify endpoint URLs are correctly configured\n"
            report += "   - Check if endpoints are properly registered in FastAPI router\n\n"
        
        report += "✅ Integration test completed!\n"
        return report
    
    def save_report(self, filename: str = "integration_test_report.txt"):
        """Save the test report to a file"""
        report = self.generate_report()
        with open(filename, 'w') as f:
            f.write(report)
        logger.info(f"Test report saved to {filename}")

def main():
    """Run the integration tests"""
    tester = IntegrationTester()
    
    print("🚀 Starting Integration Tests...")
    print("This will test all API endpoints for potential HTTP method issues")
    print("=" * 60)
    
    tester.run_comprehensive_tests()
    
    # Generate and display report
    report = tester.generate_report()
    print(report)
    
    # Save report to file
    tester.save_report()
    
    # Check for critical issues
    method_not_allowed_count = len([r for r in tester.results if r["status"] == "METHOD_NOT_ALLOWED"])
    if method_not_allowed_count > 0:
        print(f"\n⚠️  CRITICAL: {method_not_allowed_count} HTTP 405 Method Not Allowed errors found!")
        print("These issues should be fixed before production deployment.")
        return 1
    else:
        print("\n✅ No HTTP 405 Method Not Allowed errors detected!")
        return 0

if __name__ == "__main__":
    exit(main())