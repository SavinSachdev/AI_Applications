"""
Test script to diagnose OpenAI API connection issues.
"""
import os
from dotenv import load_dotenv
from openai import OpenAI

def test_openai_connection():
    """Test OpenAI API connection and diagnose issues."""
    print("="*60)
    print("🔍 OpenAI API Connection Diagnostic")
    print("="*60)
    
    # Load environment variables
    load_dotenv()
    
    # Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        print("   Please check your .env file")
        return False
    
    print(f"✅ API Key found (length: {len(api_key)})")
    print(f"   Starts with: {api_key[:10]}...")
    
    # Test connection
    try:
        print("\n🔌 Testing connection to OpenAI API...")
        client = OpenAI(api_key=api_key)
        
        # Make a simple test request
        print("   Sending test request...")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Say 'Connection successful!' if you can read this."}
            ],
            max_tokens=20
        )
        
        result = response.choices[0].message.content
        print(f"✅ Connection successful!")
        print(f"   Response: {result}")
        print("\n" + "="*60)
        print("✅ OpenAI API is working correctly")
        print("="*60)
        return True
        
    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        
        print(f"\n❌ Connection failed")
        print(f"   Error Type: {error_type}")
        print(f"   Error Message: {error_msg}")
        print("\n" + "="*60)
        print("❌ Troubleshooting Steps:")
        print("="*60)
        
        if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            print("1. Check your internet connection")
            print("2. Try accessing https://api.openai.com in your browser")
            print("3. Check if you're behind a firewall or proxy")
            print("4. Verify your network allows HTTPS connections")
        elif "api" in error_msg.lower() and "key" in error_msg.lower():
            print("1. Verify your API key is correct in .env file")
            print("2. Check if your API key is active at https://platform.openai.com/api-keys")
            print("3. Ensure your OpenAI account has credits/billing set up")
        elif "rate" in error_msg.lower():
            print("1. You've hit the API rate limit")
            print("2. Wait a few minutes and try again")
            print("3. Consider upgrading your OpenAI plan")
        else:
            print("1. Check the error message above for details")
            print("2. Visit https://platform.openai.com/docs for API documentation")
            print("3. Verify your OpenAI account status")
        
        print("="*60)
        return False

if __name__ == "__main__":
    success = test_openai_connection()
    exit(0 if success else 1)
