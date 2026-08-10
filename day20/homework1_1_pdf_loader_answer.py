"""
随堂作业1答案：PDF文档加载与解析
功能：
1. 支持PDFPlumberLoader和PyPDFLoader两种加载方式
2. 添加文档统计功能（文件数量、页数、总字符数）
3. 添加异常处理
"""

import os
from langchain_community.document_loaders import DirectoryLoader, PDFPlumberLoader, PyPDFLoader


def load_and_split_pdfs_with_stats(docs_dir="./docs", loader_type="pdfplumber"):
    """
    加载PDF文档并输出统计信息
    
    参数:
        docs_dir: 文档目录路径
        loader_type: 加载器类型，"pdfplumber" 或 "pypdf"
    
    返回:
        documents: 加载的文档列表
    """
    # 检查目录是否存在
    if not os.path.exists(docs_dir):
        print(f"❌ 错误: 目录 '{docs_dir}' 不存在")
        print(f"💡 提示: 请创建该目录并放入PDF文件后重新运行")
        return []
    
    # 检查目录中是否有PDF文件
    pdf_files = [f for f in os.listdir(docs_dir) if f.lower().endswith('.pdf')]
    if not pdf_files:
        print(f"❌ 错误: 目录 '{docs_dir}' 中没有找到PDF文件")
        print(f"💡 提示: 请将PDF文件放入该目录后重新运行")
        return []
    
    # 选择加载器
    if loader_type == "pdfplumber":
        LoaderClass = PDFPlumberLoader
        print(f"▶ 使用 PDFPlumberLoader 加载器（适合复杂排版）")
    else:
        LoaderClass = PyPDFLoader
        print(f"▶ 使用 PyPDFLoader 加载器（适合纯文本PDF）")
    
    print(f"▶ 正在从 [{docs_dir}] 文件夹批量加载 PDF 文件...")
    print(f"📁 找到 {len(pdf_files)} 个PDF文件: {', '.join(pdf_files)}")
    
    # 使用DirectoryLoader批量加载
    try:
        loader = DirectoryLoader(
            docs_dir,
            glob="**/*.pdf",
            loader_cls=LoaderClass
        )
        documents = loader.load()
    except Exception as e:
        print(f"❌ 加载PDF时发生错误: {e}")
        return []
    
    if not documents:
        print("⚠️ 警告: 未加载到任何文档内容")
        return []
    
    # 文档统计
    print(f"\n📊 文档统计信息:")
    print(f"   - 成功加载文档: {len(documents)} 页")
    
    # 统计每个文件的页数
    file_page_count = {}
    total_chars = 0
    for doc in documents:
        source = doc.metadata.get('source', '未知')
        filename = os.path.basename(source)
        file_page_count[filename] = file_page_count.get(filename, 0) + 1
        total_chars += len(doc.page_content)
    
    print(f"   - 各文件页数:")
    for filename, count in file_page_count.items():
        print(f"     * {filename}: {count}页")
    print(f"   - 总字符数: {total_chars:,}")
    
    # 对比两种加载器的差异
    print(f"\n📝 加载器差异说明:")
    if loader_type == "pdfplumber":
        print("   PDFPlumberLoader 特点:")
        print("   - 解析精度高，支持表格、图片提取")
        print("   - 适合复杂排版的招聘简章")
        print("   - 速度相对较慢")
    else:
        print("   PyPDFLoader 特点:")
        print("   - 简单易用，适合纯文本PDF")
        print("   - 速度快")
        print("   - 复杂排版可能丢失格式")
    
    # 显示第一页内容示例
    print(f"\n📄 第一页内容示例:")
    print("-" * 50)
    print(documents[0].page_content[:300] + "...")
    print("-" * 50)
    
    return documents


if __name__ == "__main__":
    print("=" * 60)
    print("📚 随堂作业1：PDF文档加载与解析")
    print("=" * 60)
    
    # 测试PDFPlumberLoader
    print("\n" + "=" * 60)
    print("测试1: PDFPlumberLoader")
    print("=" * 60)
    docs1 = load_and_split_pdfs_with_stats("./docs", "pdfplumber")
    
    # 测试PyPDFLoader（可选）
    print("\n" + "=" * 60)
    print("测试2: PyPDFLoader")
    print("=" * 60)
    docs2 = load_and_split_pdfs_with_stats("./docs", "pypdf")
    
    # 对比
    if docs1 and docs2:
        print("\n" + "=" * 60)
        print("📊 两种加载器对比:")
        print("=" * 60)
        print(f"PDFPlumberLoader: {len(docs1)} 页, 总字符数: {sum(len(d.page_content) for d in docs1):,}")
        print(f"PyPDFLoader:      {len(docs2)} 页, 总字符数: {sum(len(d.page_content) for d in docs2):,}")
