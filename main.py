"""LitMat-Agent 主入口"""

import sys

from litmat_agent.agents import create_literature_agent, create_research_agent


def main():
    """主函数：演示Agent使用"""
    print("=" * 60)
    print("LitMat-Agent: 固态电解质文献驱动科学发现系统")
    print("=" * 60)

    # 检查API配置
    from litmat_agent.core.config import settings

    if not settings.openai_api_key and not settings.anthropic_api_key:
        print("\n[警告] 未配置LLM API密钥，请在.env文件中设置：")
        print("  OPENAI_API_KEY=your_key_here")
        print("  或")
        print("  ANTHROPIC_API_KEY=your_key_here")
        print("\n当前模式：演示模式（仅展示Agent结构）\n")
        demo_mode = True
    else:
        demo_mode = False

    # 创建Agent
    print("[1/2] 初始化文献调研Agent...")
    literature_agent = create_literature_agent()
    print("      完成")

    print("[2/2] 初始化研究分析Agent...")
    research_agent = create_research_agent()
    print("      完成")

    print("\n" + "=" * 60)
    print("系统初始化完成！")
    print("=" * 60)

    if demo_mode:
        print("\n[演示模式] Agent已创建，但未连接LLM服务。")
        print("配置API密钥后，可使用以下功能：")
        print("  - 文献检索与筛选")
        print("  - 材料知识抽取")
        print("  - Research Gap识别")
        print("  - 构效关系分析")
        return

    # 交互式查询
    print("\n请输入您的研究问题（输入 'quit' 退出）：")
    print("示例：硫化物固态电解质的离子电导率影响因素有哪些？")

    while True:
        try:
            query = input("\n> ").strip()
            if query.lower() in ("quit", "exit", "q"):
                print("感谢使用LitMat-Agent！")
                break

            if not query:
                continue

            print("\n[文献调研Agent] 正在处理...")
            # result = literature_agent.invoke({"messages": [{"role": "user", "content": query}]})
            # print(result["messages"][-1].content)
            print("（演示模式：实际调用需要配置API密钥）")

        except KeyboardInterrupt:
            print("\n\n感谢使用LitMat-Agent！")
            break
        except Exception as e:
            print(f"错误：{e}")


if __name__ == "__main__":
    main()
