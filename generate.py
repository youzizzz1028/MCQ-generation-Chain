from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
import os
from langchain.agents import AgentExecutor, create_openai_tools_agent, load_tools,initialize_agent, AgentType
from typing import List, Dict
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate,MessagesPlaceholder




def search_example_problems(knowledge):
    llm = ChatOpenAI(temperature=0, model_name="gpt-4-turbo-preview",max_tokens=500)
    # 谷歌搜索 key
    serpapi_api_key = os.environ["SERPAPI_API_KEY"]
    tools = load_tools(["serpapi"], llm=llm, serpapi_api_key=serpapi_api_key)
    questions = f"请帮我找几道中小学{knowledge}的典型应用题，并总结一下常见题型"
    # 定义prompt
    template = ChatPromptTemplate.from_messages([
    ("system", "你是一名教研专家，下面的问题请你用中文回答"),
    ("human", "{user_input}"),
    MessagesPlaceholder("agent_scratchpad")
    ])
    agent = create_openai_tools_agent(llm, tools, template)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
    example_problem = agent_executor.invoke({"user_input":questions})
    print("例题搜索结果: \n")
    print(example_problem)

    return example_problem["output"]

def generate_questions(cnt, knowledge, difficulty, otherRestriction, example_problem):
    question_list = []
    for i in range(cnt):
        llm = ChatOpenAI(temperature=0.5, model_name="gpt-4-turbo-preview")
        # 谷歌搜索 key
        serpapi_api_key = os.environ["SERPAPI_API_KEY"]
        tools = load_tools(["serpapi"], llm=llm, serpapi_api_key=serpapi_api_key)
        questions = f"""我需要你为我编写1道关于 {knowledge}知识的问题, 
                        参考现有的题目{example_problem}，你可以利用搜索引擎检查问题是否符合生活实际
                        难度为 {difficulty}，{otherRestriction}，只需要给出问题即可,以问句结尾"""
        # 定义prompt
        template = ChatPromptTemplate.from_messages([
        ("system", "你是一名数学教研专家，下面的问题请你用中文回答"),
        ("human", "{user_input}"),
        MessagesPlaceholder("agent_scratchpad")
        ])
        agent = create_openai_tools_agent(llm, tools, template)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
        generated_problem = agent_executor.invoke({"user_input":questions})

        print("生成的题目: \n",generated_problem)
        question_list.append(generated_problem["output"])

    return question_list


def solve_problems(generated_questions):
    llm = ChatOpenAI(temperature=0, model_name="gpt-4-turbo-preview")
    # Next, let's load some tools to use. Note that the `llm-math` tool uses an LLM, so we need to pass that in.
    tools = load_tools(["llm-math"], llm=llm)
    # 定义prompt
    template = ChatPromptTemplate.from_messages([
    ("system", "你是一名数学专家，下面的问题请你用中文回答"),
    ("human", "{user_input}"),
    MessagesPlaceholder("agent_scratchpad")
    ])
    agent = create_openai_tools_agent(llm, tools, template)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)
    
    # 初始化存储问题和答案的列表
    question_with_answer = []
    for question in generated_questions:
        solution = agent_executor.invoke({"user_input":question + "返回解题过程和答案，计算时只能提供单行的python数学表达式，这样的表达式无法被计算'470 // 60, 470 % 60'，如果有多个要计算的表达式请你逐步计算，不能出现未定义的变量"})
        question_with_answer.append({"content": question, "description": solution})
    print(question_with_answer)
    return question_with_answer


class QuestionFormat(BaseModel):
    content: str = Field(description="问题内容")
    options: Dict[str, str] = Field(description="题目选项,键为ABCD,值为选项内容")
    description: str = Field(description="题目解析")
    correct_answer: str = Field(description="正确答案选项")


def add_choices(question_with_answer):
    llm = ChatOpenAI(temperature=0, model_name="gpt-4-turbo-preview")
    # Set up a parser + inject instructions into the prompt template.
    parser = JsonOutputParser(pydantic_object=QuestionFormat)

    template = """现在为你提供针对小初学生的数学问题和答案，请你把其改造为选择题。生成的选项需要具有干扰性，如数值接近或具备倍数关系。问题为：{question},答案为：{answer},
                {format_instructions}
                """
    prompt = PromptTemplate(
        template=template,
        input_variables=["question", "answer"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | llm | parser
    # 初始化题目数组
    question_completed = []
    for item in question_with_answer:
        ans = chain.invoke({"question": item["content"], "answer": item["description"]})
        question_completed.append(ans)

    return question_completed
