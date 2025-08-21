from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.tools import Tool
from tools import get_tools
from verification import ClaimTracker
import os
import time

class ResearchAgent:
    def __init__(self, agent_type, groq_api_key):
        self.agent_type = agent_type
        
        
        models_to_try = ["llama3-8b-8192", "llama3-70b-8192", "mixtral-8x7b-32768"]
        
        self.llm = None
        for model in models_to_try:
            try:
                self.llm = ChatGroq(
                    temperature=0.1,
                    model=model,
                    api_key=groq_api_key,
                    timeout=60, 
                    max_retries=3,  
                    request_timeout=30
                )
                
                test_response = self.llm.invoke("Hello")
                print(f" Successfully initialized with model: {model}")
                break
            except Exception as e:
                print(f" Failed to initialize model {model}: {str(e)}")
                continue
        
        if not self.llm:
            raise Exception("Failed to initialize any Groq model. Please check your API key and connection.")
        
       
        try:
            self.tools = self._convert_tools(get_tools(agent_type))
            print(f" Initialized {len(self.tools)} tools for {agent_type}")
        except Exception as e:
            print(f" Warning: Tool initialization failed: {e}")
            self.tools = []  
        self.claim_tracker = ClaimTracker()
        
      
        if agent_type == "researcher":
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a senior technical researcher. Gather comprehensive information about the user's query.
                - Extract key claims with sources
                - Compare technologies objectively
                - Include recent developments (2023-2024)
                - Format claims as bullet points starting with '- '
                
                Use the available tools to research thoroughly. If tools are not available, use your knowledge."""),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}")
            ])
        elif agent_type == "critic":
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a quality assurance expert. The user will provide research content to analyze.
                - Verify factual accuracy using available tools when possible
                - Identify unsupported claims
                - Check for bias or staleness
                - Flag any contradictions
                - Format feedback as bullet points"""),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}")
            ])
        else:  
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", """You are a technical writer. The user will provide research and critique content to synthesize.
                - Create structured comparison tables
                - Highlight verified vs contested claims
                - Provide clear recommendations
                - Include sources
                - Use markdown formatting"""),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}")
            ])
        
      
        try:
            self.agent = create_tool_calling_agent(self.llm, self.tools, self.prompt)
            self.executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=False,
                handle_parsing_errors=True,
                max_iterations=5,  
                max_execution_time=120  
            )
        except Exception as e:
            print(f" Failed to create agent: {e}")
           
            self.agent = None
            self.executor = None
    
    def _convert_tools(self, tools_list):
        """Convert tools to LangChain Tool format if needed"""
        if not tools_list:
            return []
            
        converted_tools = []
        for tool in tools_list:
            try:
                if hasattr(tool, 'name'): 
                    converted_tools.append(tool)
                elif isinstance(tool, dict):  
                    converted_tools.append(
                        Tool(
                            name=tool["name"],
                            func=tool["func"],
                            description=tool["description"]
                        )
                    )
            except Exception as e:
                print(f"⚠️ Warning: Failed to convert tool: {e}")
                continue
        return converted_tools
    
    def run(self, input_data, max_retries=3):
        
        
       
        if isinstance(input_data, str):
            input_data = {"input": input_data}
        elif isinstance(input_data, dict) and "input" not in input_data:
            input_data = {"input": str(input_data)}
        
       
        if not self.executor:
            return self._fallback_run(input_data["input"])
        
        last_error = None
        for attempt in range(max_retries):
            try:
                print(f"Attempt {attempt + 1} for {self.agent_type} agent")
                
               
                if attempt > 0:
                    time.sleep(2 ** attempt) 
                
                result = self.executor.invoke(input_data)
                
               
                if self.agent_type == "researcher" and result.get("output"):
                    try:
                        claims = self.claim_tracker.extract_claims(result["output"])
                        self.claim_tracker.add_claims(claims, "Researcher Agent")
                    except Exception as e:
                        print(f"Warning: Claim tracking failed: {e}")
                
                return result.get("output", "No output generated")
                
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                
                print(f"❌ Attempt {attempt + 1} failed: {str(e)}")
                
                
                if any(keyword in error_msg for keyword in ["connection", "timeout", "network"]):
                    if attempt < max_retries - 1:
                        print(f" Connection issue detected. Retrying in {2 ** attempt} seconds...")
                        continue
                    else:
                        return self._fallback_run(input_data["input"])
                
                elif "rate limit" in error_msg or "quota" in error_msg:
                    if attempt < max_retries - 1:
                        print(f"⏳ Rate limit hit. Waiting {5 * (attempt + 1)} seconds...")
                        time.sleep(5 * (attempt + 1))
                        continue
                    else:
                        return "❌ Rate limit exceeded. Please try again later."
                
                elif "no healthy upstream" in error_msg:
                    return "❌ API Connection Error: Unable to connect to Groq API. Please check your API key and internet connection."
                
                else:
                   
                    return self._fallback_run(input_data["input"])
        
       
        return self._fallback_run(input_data["input"])
    
    def _fallback_run(self, input_text):
        """Fallback method using direct LLM call without tools"""
        try:
            print(f"🔄 Using fallback mode for {self.agent_type} agent")
            
          
            if self.agent_type == "researcher":
                prompt = f"""As a technical researcher, analyze this query and provide comprehensive information:
                
Query: {input_text}

Please provide:
- Key technical details and comparisons
- Recent developments and trends
- Practical recommendations
- Format as bullet points where appropriate

Response:"""
            
            elif self.agent_type == "critic":
                prompt = f"""As a quality assurance expert, analyze this research content:

Content: {input_text}

Please provide:
- Assessment of factual accuracy
- Identification of unsupported claims
- Bias or outdated information detection
- Contradictions or inconsistencies
- Format as bullet points

Analysis:"""
            
            else: 
                prompt = f"""As a technical writer, synthesize this research and critique:

Content: {input_text}

Please provide:
- Structured summary with comparison tables
- Clear recommendations
- Source attribution
- Markdown formatting

Final Report:"""
            
            response = self.llm.invoke(prompt)
            
            
            if hasattr(response, 'content'):
                return response.content
            elif isinstance(response, str):
                return response
            else:
                return str(response)
                
        except Exception as e:
            return f"❌ Fallback failed for {self.agent_type}: {str(e)}"
    
    def close(self):
        """Clean up resources"""
        try:
            if hasattr(self, 'claim_tracker'):
                self.claim_tracker.close()
        except Exception as e:
            print(f"Warning: Error during cleanup: {e}")
