"""
知识库入库脚本 — 将 data/cleaned/ 下的文档入库到 ChromaDB
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.loopse.kb.vector_store import vector_store


def ingest_docs():
    cleaned_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "cleaned")
    if not os.path.exists(cleaned_dir):
        print(f"⚠️  目录不存在: {cleaned_dir}")
        return

    total = 0
    for fname in sorted(os.listdir(cleaned_dir)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(cleaned_dir, fname)
        content = open(fpath, encoding="utf-8").read()
        # 按段落拆分
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip() and len(p.strip()) > 20]
        for i, para in enumerate(paragraphs):
            doc_id = f"{fname}_{i}"
            chapter = fname.replace("ch", "第").split("_")[0] + "章"
            n = vector_store.add_documents(
                collection_name="course_docs",
                documents=[para],
                ids=[doc_id],
                metadatas=[{"source": fname, "chapter": chapter, "paragraph": i}],
            )
            total += n

    print(f"✅ course_docs 入库完成，共 {total} 条")
    print(f"   course_docs 总量: {vector_store.get_collection_count('course_docs')}")


def ingest_misconceptions():
    misconceptions = [
        {"id": "mis_01", "content": "误以为HTTP直接基于IP传输，不需要TCP。实际上HTTP是基于TCP的，TCP提供可靠传输，HTTP依赖TCP的连接服务。", "metadata": {"error_type": "layer_misplacement", "topic": "HTTP/TCP/IP层次关系"}},
        {"id": "mis_02", "content": "误以为TCP两次握手就够了。实际上必须三次握手，防止已失效的SYN报文到达服务器后建立无效连接。", "metadata": {"error_type": "flow_omission", "topic": "TCP三次握手"}},
        {"id": "mis_03", "content": "混淆SYN和ACK的作用。SYN用于请求建立连接，ACK用于确认收到报文。两者功能完全不同。", "metadata": {"error_type": "concept_confusion", "topic": "TCP控制位"}},
        {"id": "mis_04", "content": "误以为UDP也有握手过程。UDP是无连接协议，不需要建立连接，直接发送数据报。", "metadata": {"error_type": "concept_confusion", "topic": "UDP/TCP区别"}},
        {"id": "mis_05", "content": "误以为TCP四次挥手可以简化为三次。因为TCP是全双工，两个方向的关闭需要独立确认，不能合并。", "metadata": {"error_type": "flow_omission", "topic": "TCP四次挥手"}},
        {"id": "mis_06", "content": "混淆IP地址和MAC地址的作用层次。IP地址是网络层逻辑地址，MAC地址是数据链路层物理地址，两者在不同层次工作。", "metadata": {"error_type": "layer_misplacement", "topic": "IP/MAC地址"}},
        {"id": "mis_07", "content": "误以为拥塞控制就是流量控制。流量控制是端到端的（防止发送方淹没接收方），拥塞控制是全局的（防止网络过载）。", "metadata": {"error_type": "concept_confusion", "topic": "TCP拥塞/流量控制"}},
        {"id": "mis_08", "content": "误以为DNS只使用UDP。DNS查询通常用UDP，但区域传送（_zone transfer_）使用TCP，因为数据量大需要可靠传输。", "metadata": {"error_type": "over_simplification", "topic": "DNS传输协议"}},
        {"id": "mis_09", "content": "混淆OSI传输层和会话层的功能。传输层提供端到端可靠传输（TCP/UDP），会话层管理对话控制，TCP/IP模型中不单独设会话层。", "metadata": {"error_type": "layer_misplacement", "topic": "OSI/TCP-IP模型"}},
        {"id": "mis_10", "content": "误以为HTTPS的加密是对整个连接的。TLS只加密传输中的数据，服务器端解密后数据仍是明文，端到端安全还需应用层保障。", "metadata": {"error_type": "over_simplification", "topic": "HTTPS/TLS"}},
        {"id": "mis_11", "content": "误以为子网掩码255.255.255.0只能用于C类地址。CIDR下任何长度的掩码都可以用于任何地址，不再受类别限制。", "metadata": {"error_type": "concept_confusion", "topic": "子网划分/CIDR"}},
        {"id": "mis_12", "content": "误以为RIP和OSPF功能相同只是协议不同。RIP是距离向量协议（只知跳数），OSPF是链路状态协议（知全网拓扑），算法和适用场景完全不同。", "metadata": {"error_type": "concept_confusion", "topic": "路由算法"}},
        {"id": "mis_13", "content": "混淆TCP序号和确认号。序号是本端发送数据字节的编号，确认号是期望收到对方下一个字节的编号，两者方向相反。", "metadata": {"error_type": "field_misunderstanding", "topic": "TCP报文格式"}},
        {"id": "mis_14", "content": "误以为TIME_WAIT状态没有意义可以跳过。TIME_WAIT持续2MSL确保最后一个ACK能到达对方，并让本连接的延迟报文消失，防止新连接收到旧数据。", "metadata": {"error_type": "reasoning_breakdown", "topic": "TCP四次挥手"}},
        {"id": "mis_15", "content": "误以为以太网帧最短64字节是数据字段长度。64字节是整个帧的最短长度（含首部和FCS），数据字段最短46字节。", "metadata": {"error_type": "field_misunderstanding", "topic": "MAC帧格式"}},
        {"id": "mis_16", "content": "混淆滑动窗口的发送窗口和接收窗口。发送窗口=min(拥塞窗口cwnd, 接收窗口rwnd)，接收窗口是接收方缓冲区大小。", "metadata": {"error_type": "concept_confusion", "topic": "TCP滑动窗口"}},
        {"id": "mis_17", "content": "误以为ARP请求是单播。ARP请求是广播发送（目标MAC=FF:FF:FF:FF:FF:FF），ARP应答才是单播。", "metadata": {"error_type": "concept_confusion", "topic": "ARP协议"}},
        {"id": "mis_18", "content": "误以为HTTP状态码403和404含义相同。403是服务器拒绝访问（权限不足），404是资源不存在，原因和解决方式完全不同。", "metadata": {"error_type": "concept_confusion", "topic": "HTTP状态码"}},
        {"id": "mis_19", "content": "误以为慢启动阶段cwnd从0开始。实际上cwnd从1个MSS开始，每收到一个ACK翻倍（指数增长），不是从0开始。", "metadata": {"error_type": "field_misunderstanding", "topic": "TCP拥塞控制"}},
        {"id": "mis_20", "content": "误以为数据链路层只负责封装帧。数据链路层还负责差错检测（FCS）、流量控制、介质访问控制（CSMA/CD）等功能。", "metadata": {"error_type": "over_simplification", "topic": "数据链路层功能"}},
    ]

    docs = [m["content"] for m in misconceptions]
    ids = [m["id"] for m in misconceptions]
    metas = [m["metadata"] for m in misconceptions]

    n = vector_store.add_documents("misconceptions", docs, ids, metas)
    print(f"✅ misconceptions 入库完成，共 {n} 条")
    print(f"   misconceptions 总量: {vector_store.get_collection_count('misconceptions')}")


if __name__ == "__main__":
    print("=== 开始知识库入库 ===")
    ingest_docs()
    ingest_misconceptions()
    print("=== 入库完成 ===")
