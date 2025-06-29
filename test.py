import os
from dotenv import load_dotenv


load_dotenv()

def test_api_keys():
    """Test if API keys are properly set"""
    groq_key = os.getenv("GROQ_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    print("🔍 Testing API Key Configuration...")
    
    if not groq_key:
        print("❌ GROQ_API_KEY not found in environment")
        return False
    else:
        print(f"✅ GROQ_API_KEY found (length: {len(groq_key)})")
    
    if not tavily_key:
        print("❌ TAVILY_API_KEY not found in environment")
        return False
    else:
        print(f"✅ TAVILY_API_KEY found (length: {len(tavily_key)})")
    
    return True

def test_groq_connection():
    """Test Groq API connection"""
    try:
        from langchain_groq import ChatGroq
        import requests
        
        groq_key = os.getenv("GROQ_API_KEY")
        
        
        print("🔍 Testing direct Groq API access...")
        headers = {
            "Authorization": f"Bearer {groq_key}",
            "Content-Type": "application/json"
        }
        
        
        test_payload = {
            "messages": [{"role": "user", "content": "Hello"}],
            "model": "llama3-8b-8192",
            "max_tokens": 10
        }
        
        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=test_payload,
                timeout=10
            )
            if response.status_code == 200:
                print("✅ Direct Groq API access successful")
            else:
                print(f"❌ Direct API Error: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Network Error: {str(e)}")
            return False
        
        
        print("🔍 Testing Groq API with LangChain...")
        
        
        models_to_try = ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"]
        
        for model in models_to_try:
            try:
                print(f"   Trying model: {model}")
                llm = ChatGroq(
                    temperature=0.1,
                    model=model,
                    api_key=groq_key,
                    timeout=10
                )
                
                response = llm.invoke("Hello")
                print(f"✅ Groq API successful with model {model}")
                print(f"   Response: {response.content[:100]}...")
                return True
                
            except Exception as model_error:
                print(f"   ❌ Failed with {model}: {str(model_error)}")
                continue
        
        print("❌ All Groq models failed")
        return False
        
    except Exception as e:
        print(f"❌ Groq API Error: {str(e)}")
        return False

def test_tavily_connection():
    """Test Tavily API connection"""
    try:
        
        try:
            from langchain_tavily import TavilySearchResults
            print("🔍 Using new langchain_tavily package...")
        except ImportError:
            from langchain_community.tools.tavily_search import TavilySearchResults
            print("🔍 Using legacy langchain_community package...")
        
        tavily_key = os.getenv("TAVILY_API_KEY")
        search_tool = TavilySearchResults(
            api_key=tavily_key,
            max_results=1
        )
        
        print("🔍 Testing Tavily API connection...")
        result = search_tool.invoke("test search")
        print(f"✅ Tavily API working - found {len(result)} results")
        return True
        
    except Exception as e:
        print(f"❌ Tavily API Error: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Running API Connection Tests...\n")
    
    
    if not test_api_keys():
        print("\n❌ API key configuration failed. Please check your .env file.")
        exit(1)
    
    print()
    
    
    groq_ok = test_groq_connection()
    print()
    tavily_ok = test_tavily_connection()
    
    print("\n" + "="*50)
    if groq_ok and tavily_ok:
        print("✅ All API connections successful! You can run the main application.")
    else:
        print("❌ Some API connections failed. Please check your API keys and internet connection.")
        if not groq_ok:
            print("   - Check your GROQ_API_KEY")
        if not tavily_ok:
            print("   - Check your TAVILY_API_KEY")