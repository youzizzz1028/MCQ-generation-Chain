from generate import *
import os
# API-KEY Settings
os.environ["OPENAI_API_KEY"] = "REPLACE YOUR API KEY HERE"
os.environ["SERPAPI_API_KEY"] = "REPLACE YOUR API KEY HERE"
# question settings
cnt = 1
knowledge = '简易方程'
difficulty_level = 0
isScene = True
otherRestriction = ""
difficulty_list = ['初级', '中级', '高级']
difficulty = difficulty_list[difficulty_level]
if isScene:
    otherRestriction += "你需要为题目编一个适用于教育的情境，创设的题目需要以生活中真实发生的问题为背景，使用在生活中会真实出现的数字，问题是要解决生活中实际出现的问题"


def generate_problem():
    example_problem = search_example_problems(knowledge)
    generated_questions = generate_questions(cnt, knowledge, difficulty, otherRestriction, example_problem)
    # generated_questions=['小明和小华是邻居，他们决定一起种植蔬菜。小明的花园可以种植30棵蔬菜，而小 华的花园可以种植的蔬菜数量是小明的两倍。由于小华的花园土壤更肥沃，他决定把其中的10棵蔬菜搬到小明的花园中。这样做之后，小华的花园里的蔬菜数量是小明的花园的多少倍？']
    question_with_answer = solve_problems(generated_questions)
    question_completed = add_choices(question_with_answer)
    print("############################最终生成题目结果##################################")
    print(question_completed)


if __name__ == '__main__':
    generate_problem()
