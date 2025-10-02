"""
Qogita API Rate Limiting Explanation

This document explains the rate limiting behavior we're experiencing with the Qogita API
and how our application handles it.
"""

def explain_qogita_rate_limiting():
    """
    QOGITA API RATE LIMITING - DETAILED EXPLANATION
    =============================================
    
    🚨 WHAT HAPPENED:
    When we tested our application multiple times, we received this error:
    "Request was throttled. Expected available in 713 seconds."
    
    📊 THE NUMBERS:
    - 713 seconds = 11 minutes and 53 seconds ≈ 12 minutes
    - This is quite aggressive rate limiting for an API
    
    🔍 WHY THIS HAPPENS:
    
    1. **API Protection**: Qogita protects their servers from being overwhelmed
    2. **Resource Management**: The catalog download endpoint returns large datasets
       - In our test: 1931 L'Oréal products in a single request
       - This is computationally expensive for their servers
    3. **Fair Usage**: Prevents any single user from monopolizing the API
    
    📡 WHAT TRIGGERS THE RATE LIMIT:
    
    1. **Frequency**: Too many requests in a short time period
       - We made several test requests in rapid succession
       - Likely triggered after 2-3 requests within a few minutes
    
    2. **Endpoint Type**: The /variants/search/download/ endpoint is "heavy"
       - Returns complete product catalogs
       - Much more expensive than simple product lookups
    
    3. **Data Volume**: Large responses consume more server resources
       - 1931 products = significant CSV data to generate
    
    🔧 HOW OUR APPLICATION HANDLES IT:
    
    1. **Detection**: We parse the HTTP 429 status code
       ```python
       if response.status_code == 429:
           # Rate limited - extract retry time
           retry_after = parse_retry_time(response)
           raise QogitaRateLimitError(message, retry_after)
       ```
    
    2. **Information Extraction**: We extract the retry time from the error message
       - "Expected available in 713 seconds" → retry_after = 713
    
    3. **Graceful Handling**: We don't crash, we inform the user
       - Clear error messages in the UI
       - Proper exception handling in background threads
    
    4. **Logging**: We log the rate limit for debugging
       ```
       ERROR:core.qogita_api:Rate limited while searching brand 'L'Oréal': 
       Request was throttled. Expected available in 713 seconds.
       ```
    
    💡 RATE LIMITING STRATEGIES:
    
    1. **Built-in Delays**: Our code includes minimum request intervals
       ```python
       self.min_request_interval = 1.0  # 1 second between requests
       ```
    
    2. **Exponential Backoff**: For production use, we could implement:
       - First retry: wait 1 minute
       - Second retry: wait 2 minutes  
       - Third retry: wait 4 minutes
       - etc.
    
    3. **Smart Caching**: Cache results to avoid repeat requests
       - Store brand catalogs locally
       - Only refresh when needed
    
    4. **Batch Processing**: Group multiple brands into single requests when possible
    
    📈 RATE LIMIT PATTERNS (Estimated):
    
    Based on our experience:
    - **Light Usage**: 1-2 requests per minute = OK
    - **Medium Usage**: 3-5 requests per minute = Warning zone
    - **Heavy Usage**: 6+ requests per minute = Rate limited
    - **Recovery Time**: ~12 minutes per violation
    
    🎯 PRODUCTION STRATEGIES:
    
    1. **User Education**: 
       - Warn users about rate limits
       - Suggest optimal usage patterns
    
    2. **Queue Management**:
       - Queue multiple brand requests
       - Process them with appropriate delays
    
    3. **Progress Indication**:
       - Show estimated completion times
       - Allow users to cancel long operations
    
    4. **Smart Scheduling**:
       - Process during off-peak hours
       - Spread requests across time
    
    🔄 RECOVERY PROCESS:
    
    When rate limited:
    1. **Wait**: Respect the retry_after time (713 seconds = 12 minutes)
    2. **Inform**: Tell user exactly how long to wait
    3. **Queue**: Save the request to retry later
    4. **Resume**: Automatically continue when time expires
    
    ✅ OUR IMPLEMENTATION STATUS:
    
    ✅ Rate limit detection working
    ✅ Error parsing working  
    ✅ Graceful error handling
    ✅ User notification system
    ✅ Logging for debugging
    ⚠️  Auto-retry not yet implemented (could be added)
    ⚠️  Caching not yet implemented (could be added)
    
    📊 REAL-WORLD IMPACT:
    
    For typical usage:
    - **Single brand scan**: Works fine, just need to wait between different brands
    - **Multiple brands**: Need to space them out (12+ minutes apart)
    - **Daily operations**: Plan brand scans throughout the day
    - **Bulk analysis**: Best done overnight or during off-peak hours
    
    💼 BUSINESS IMPLICATIONS:
    
    This is actually NORMAL for wholesale APIs:
    - Protects against abuse
    - Ensures fair access for all users
    - Maintains system stability
    - Forces thoughtful usage patterns
    
    🔧 RECOMMENDED WORKFLOW:
    
    1. **Plan Ahead**: Choose 3-5 key brands to analyze daily
    2. **Schedule**: Space brand scans 15-20 minutes apart
    3. **Cache**: Save results locally to avoid re-requesting
    4. **Optimize**: Focus on high-value brands first
    
    This rate limiting is typical for B2B APIs and shows that Qogita
    takes their system stability seriously!
    """
    pass

def show_rate_limit_handling_code():
    """
    CODE EXAMPLES: How We Handle Rate Limits
    =======================================
    """
    
    rate_limit_detection = '''
    # 1. DETECTION (in qogita_api.py)
    if response.status_code == 429:
        error_data = response.json() if response.content else {}
        message = error_data.get("message", "Rate limited")
        
        # Extract retry time from message
        retry_after = None
        if "seconds" in message:
            import re
            match = re.search(r'(\\d+)\\s+seconds', message)
            if match:
                retry_after = int(match.group(1))
        
        raise QogitaRateLimitError(message, retry_after)
    '''
    
    ui_handling = '''
    # 2. UI HANDLING (in qogita_scanner.py)
    def handle_error(self, error_message: str):
        """Handle error messages including rate limits"""
        self.add_log_message(f"ERROR: {error_message}")
        
        if "throttled" in error_message.lower():
            # Extract wait time and show user-friendly message
            QMessageBox.warning(
                self, 
                "Rate Limited", 
                f"Qogita API rate limit reached.\\n\\n"
                f"Please wait before making another request.\\n"
                f"This protects the API from overload.\\n\\n"
                f"Details: {error_message}"
            )
        else:
            QMessageBox.critical(self, "Scan Error", error_message)
        
        # Reset UI state
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)
    '''
    
    smart_retry = '''
    # 3. SMART RETRY (Future Enhancement)
    async def retry_with_backoff(self, operation, max_retries=3):
        """Retry operation with exponential backoff"""
        for attempt in range(max_retries):
            try:
                return await operation()
            except QogitaRateLimitError as e:
                if attempt == max_retries - 1:
                    raise  # Final attempt failed
                
                wait_time = e.retry_after or (2 ** attempt * 60)  # 1min, 2min, 4min
                self.show_retry_message(f"Rate limited. Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
    '''
    
    print("Rate Limit Handling Code Examples:")
    print("=" * 40)
    print("\n1. DETECTION:")
    print(rate_limit_detection)
    print("\n2. UI HANDLING:")
    print(ui_handling)
    print("\n3. SMART RETRY (Future):")
    print(smart_retry)

if __name__ == "__main__":
    print(explain_qogita_rate_limiting.__doc__)
    print("\n" + "="*80 + "\n")
    show_rate_limit_handling_code()
