from langchain_core.tools import Tool
import os
import time

def safe_search_wrapper(search_func, tool_name):
    """Wrapper to add retry logic and error handling to search tools"""
    def wrapped_search(query, max_retries=2):
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    time.sleep(2)  
                result = search_func(query)
                return result
            except Exception as e:
                error_msg = str(e).lower()
                if attempt < max_retries - 1:
                    if any(keyword in error_msg for keyword in ["connection", "timeout", "network"]):
                        print(f"🔄 {tool_name} connection issue, retrying...")
                        continue
                    elif "rate limit" in error_msg:
                        print(f"⏳ {tool_name} rate limit, waiting...")
                        time.sleep(5)
                        continue
                
                
                return f"❌ {tool_name} search failed: {str(e)}"
        
        return f"❌ {tool_name} search failed after {max_retries} attempts"
    
    return wrapped_search

def get_tools(agent_type):
    """Get tools for different agent types with improved error handling"""
    tools = []
    
    
    tavily_api_key = os.getenv("TAVILY_API_KEY")
    if tavily_api_key:
        try:
            
            try:
                from langchain_tavily import TavilySearchResults
                print("✅ Using new langchain_tavily package")
            except ImportError:
                from langchain_community.tools.tavily_search import TavilySearchResults
                print("⚠️ Using legacy langchain_community package")
            
            tavily_search = TavilySearchResults(
                api_key=tavily_api_key,
                max_results=3,
                description="Search web for latest technical information"
            )
            
            
            safe_tavily = safe_search_wrapper(tavily_search.run, "Tavily")
            tavily_tool = Tool(
                name="web_search",
                func=safe_tavily,
                description="Search the web for current technical information and recent developments"
            )
            tools.append(tavily_tool)
            print("✅ Tavily search tool initialized")
            
        except Exception as e:
            print(f"⚠️ Tavily tool initialization failed: {e}")
    else:
        print("⚠️ TAVILY_API_KEY not found")
    
    
    try:
        from langchain_community.utilities import WikipediaAPIWrapper
        
        wikipedia = WikipediaAPIWrapper(
            top_k_results=2,
            doc_content_chars_max=4000
        )
        
        safe_wikipedia = safe_search_wrapper(wikipedia.run, "Wikipedia")
        wikipedia_tool = Tool(
            name="wikipedia",
            func=safe_wikipedia,
            description="Access encyclopedic knowledge about technical concepts and technologies"
        )
        tools.append(wikipedia_tool)
        print("✅ Wikipedia tool initialized")
        
    except Exception as e:
        print(f"⚠️ Wikipedia tool initialization failed: {e}")
    
    
    if agent_type == "researcher":
        try:
            from langchain_community.utilities.arxiv import ArxivAPIWrapper
            
            arxiv = ArxivAPIWrapper(
                top_k_results=2,
                doc_content_chars_max=4000
            )
            
            safe_arxiv = safe_search_wrapper(arxiv.run, "ArXiv")
            arxiv_tool = Tool(
                name="arxiv",
                func=safe_arxiv,
                description="Access academic papers and research about technical topics"
            )
            tools.append(arxiv_tool)
            print("✅ ArXiv tool initialized")
            
        except Exception as e:
            print(f"⚠️ ArXiv tool initialization failed: {e}")
    
    print(f"📋 Initialized {len(tools)} tools for {agent_type} agent")
    return tools