# mcq_generator.py

from langchain_ibm import WatsonxLLM
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv
import streamlit as st


def generate_mcqs(topic, num_questions=3, difficulty="Medium", question_type="General"):
    """
    Generate MCQs with enhanced parameters
    """
    # Load environment variables
    #load_dotenv(dotenv_path=".env")

    # Corrected: Use 'apikey' instead of 'api_key'
    apikey = st.secrets.get("WATSONX_API_KEY") or st.secrets.get("WATSONX_APIKEY")

    # Validate environment variables
    if not all([os.getenv("WATSONX_URL"), apikey, os.getenv("WATSONX_PROJECT_ID")]):
        missing_vars = []
        if not os.getenv("WATSONX_URL"): missing_vars.append("WATSONX_URL")
        if not apikey: missing_vars.append("WATSONX_API_KEY or WATSONXAPIKEY")
        if not os.getenv("WATSONX_PROJECT_ID"): missing_vars.append("WATSONX_PROJECT_ID")
        return f"Error: Missing environment variables: {', '.join(missing_vars)}"

    try:
        llm = WatsonxLLM(
            model_id="ibm/granite-3-3-8b-instruct",
            url=os.getenv("WATSONX_URL"),
            apikey=apikey,  # ✅ Correct key name
            project_id=os.getenv("WATSONX_PROJECT_ID"),
            params={
                "max_new_tokens": 1000,
                "min_new_tokens": 200,
                "temperature": 0.3,
                "top_p": 0.9,
                "repetition_penalty": 1.05,
                "stop_sequences": ["###", "---"]
            }
        )

        template = """Generate {num_questions} multiple choice questions on the topic "{topic}".

Each question should be based on {difficulty} level and follow this exact format:

Q1. <question>
A) <option 1>
B) <option 2>
C) <option 3>
D) <option 4>
Answer: <A/B/C/D>

Continue for all questions

Q1. [Write your question here]
A) [Option 1]
B) [Option 2] 
C) [Option 3]
D) [Option 4]
Answer: [A/B/C/D]

Q2. [Write your question here]
...

Continue for all {num_questions} questions.

Topic: {topic}
Start generating:"""

        prompt = PromptTemplate.from_template(template)
        output_parser = StrOutputParser()
        mcq_chain = prompt | llm | output_parser

        response = mcq_chain.invoke({
            "topic": topic,
            "num_questions": num_questions,
            "difficulty": difficulty,
            "question_type": question_type
        })

        if response:
            response = response.strip()
            question_count = response.count("Q")

            if question_count < num_questions:
                return f"Partial response detected. Got {question_count} questions instead of {num_questions}.\n\nResponse:\n{response}"

            if len(response) < 100:
                return f"Response too short ({len(response)} characters). This might indicate an API issue.\n\nResponse:\n{response}"

            return response
        else:
            return "Error: Empty response from Watson API"

    except Exception as e:
        return f"Error generating MCQs: {str(e)}\n\nPlease check:\n1. API credentials\n2. Network connection\n3. Watson service status"


def test_connection():
    """Test Watson connection with minimal request"""
    load_dotenv(dotenv_path=".env")
    apikey = st.secrets.get("WATSONX_API_KEY") or st.secrets.get("WATSONXAPIKEY")

    try:
        llm = WatsonxLLM(
            model_id="ibm/granite-13b-instruct-v2",
            url=os.getenv("WATSONX_URL"),
            apikey=apikey,  # ✅ Correct key name
            project_id=os.getenv("WATSONX_PROJECT_ID"),
            params={"max_new_tokens": 50, "temperature": 0.1}
        )

        response = llm.invoke("Hello")
        return f"Connection successful! Test response: {response}"

    except Exception as e:
        return f"Connection failed: {str(e)}" 